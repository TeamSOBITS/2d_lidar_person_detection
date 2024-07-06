import torch
import numpy as np

from dr_spaam.model.drow_net import DrowNet
from dr_spaam.model.dr_spaam import DrSpaam
from dr_spaam.utils import utils as u


class Detector(object):
    def __init__(
        self, ckpt_file, model="DROW3", gpu=True, stride=1, panoramic_scan=False, tracking=False, box=False
    ):
        """A warpper class around DROW3 or DR-SPAAM network for end-to-end inference.

        Args:
            ckpt_file (str): Path to checkpoint
            model (str): Model name, "DROW3" or "DR-SPAAM".
            gpu (bool): True to use GPU. Defaults to True.
            stride (int): Downsample scans for faster inference.
            panoramic_scan (bool): True if the scan covers 360 degree.
            tracking (bool): True to enable tracking extension.
        """
        self._gpu = gpu
        self._stride = stride
        self._use_dr_spaam = model == "DR-SPAAM"

        self._scan_phi = None
        self._laser_fov_deg = None

        if model == "DROW3":
            self._model = DrowNet(
                dropout=0.5, cls_loss=None, mixup_alpha=0.0, mixup_w=0.0
            )
        elif model == "DR-SPAAM":
            self._model = DrSpaam(
                dropout=0.5,
                num_pts=56,
                embedding_length=128,
                alpha=0.5,
                window_size=17,
                panoramic_scan=panoramic_scan,
                cls_loss=None,
                mixup_alpha=0.0,
                mixup_w=0.0,
                use_box=box
            )
        else:
            raise NotImplementedError(
                "model should be 'DROW3' or 'DR-SPAAM', received {} instead.".format(
                    model
                )
            )

        ckpt = torch.load(ckpt_file)
        self._model.load_state_dict(ckpt["model_state"])

        self._model.eval()
        if gpu:
            torch.backends.cudnn.benchmark = True
            self._model = self._model.cuda()

        self._tracker = _TrackingExtension() if tracking else None

    def __call__(self, scan):
        if self._scan_phi is None:
            assert self.is_ready(), "Call set_laser_fov() first."
            half_fov_rad = 0.5 * np.deg2rad(self._laser_fov_deg)
            self._scan_phi = np.linspace(
                -half_fov_rad, half_fov_rad, len(scan), dtype=np.float32
            )

        # preprocess
        ct = u.scans_to_cutout(
            scan[None, ...],
            self._scan_phi,
            stride=self._stride,
            centered=True,
            fixed=True,
            window_width=1.0,
            window_depth=0.5,
            num_cutout_pts=56,
            padding_val=29.99,
            area_mode=True,
        )
        ct = torch.from_numpy(ct).float()

        if self._gpu:
            ct = ct.cuda()

        # inference
        with torch.no_grad():
            # one extra dimension for batch
            if self._use_dr_spaam:
                pred_cls, pred_reg, sim_matrix = self._model(ct.unsqueeze(dim=0), inference=True)
            else:
                pred_cls, pred_reg = self._model(ct.unsqueeze(dim=0))

        pred_cls = torch.sigmoid(pred_cls[0]).data.cpu().numpy()
        pred_reg = pred_reg[0].data.cpu().numpy()

        # postprocess
        dets_xy, dets_cls, instance_mask = u.nms_predicted_center(
            scan[:: self._stride],
            self._scan_phi[:: self._stride],
            pred_cls[:, 0],
            pred_reg,
        )

        if self._tracker:
            self._tracker(dets_xy, dets_cls, instance_mask, sim_matrix)

        return dets_xy, dets_cls, instance_mask

    def get_tracklets(self):
        assert self._tracker is not None
        return self._tracker.get_tracklets()

    def set_laser_fov(self, fov_deg):
        self._laser_fov_deg = fov_deg

    def is_ready(self):
        return self._laser_fov_deg is not None


# TODO: move this to a separate file
class _TrackingExtension(object):
    def __init__(self):
        self._prev_dets_xy        = None
        self._prev_dets_cls       = None
        self._prev_instance_mask  = None
        self._prev_dets_to_tracks = None  # a list of track id for each detection

        self._tracks     = []
        self._tracks_cls = []
        self._tracks_age = []

        self._max_track_age  = 5
        self._max_assoc_dist = 0.25

    def __call__(self, dets_xy, dets_cls, instance_mask, sim_matrix):
        # first frame
        if self._prev_dets_xy is None:
            self._prev_dets_xy = dets_xy
            self._prev_dets_cls = dets_cls
            self._prev_instance_mask = instance_mask
            self._prev_dets_to_tracks = np.arange(len(dets_xy), dtype=np.int32)

            for d_xy, d_cls in zip(dets_xy, dets_cls):
                self._tracks.append([d_xy])
                self._tracks_cls.append([d_cls])
                self._tracks_age.append(0)
            return

        # associate detections
        prev_dets_inds = self._associate_prev_det(
            dets_xy, dets_cls, instance_mask, sim_matrix)

        # mapping from detection indices to tracklets indices
        dets_to_tracks = []

        # assign current detections to tracks based on assocation with previous
        # detections
        for d_idx, (d_xy, d_cls, prev_d_idx) in enumerate(
                zip(dets_xy, dets_cls, prev_dets_inds)):
            # distance between assocated detections
            dxy = self._prev_dets_xy[prev_d_idx] - d_xy
            dxy = np.hypot(dxy[0], dxy[1])


            if dxy < self._max_assoc_dist and prev_d_idx >= 0:
                # if current detection is close to the associated detection,
                # append to the tracklet
                ti = self._prev_dets_to_tracks[prev_d_idx]
                self._tracks[ti].append(d_xy)
                self._tracks_cls[ti].append(d_cls)
                self._tracks_age[ti] = -1
                dets_to_tracks.append(ti)
            else:
                # otherwise start a new tracklet
                self._tracks.append([d_xy])
                self._tracks_cls.append([d_cls])
                self._tracks_age.append(-1)
                dets_to_tracks.append(len(self._tracks) - 1)

        # tracklet age
        for i in range(len(self._tracks_age)):
            self._tracks_age[i] += 1

        # prune inactive tracks
        # pop_inds = []
        # for i in range(len(self._tracks_age)):
        #     self._tracks_age[i] = self._tracks_age[i] + 1
        #     if self._tracks_age[i] > self._max_track_age:
        #         pop_inds.append(i)

        # if len(pop_inds) > 0:
        #     pop_inds.reverse()
        #     for pi in pop_inds:
        #         for j in range(len(dets_to_tracks)):
        #             if dets_to_tracks[j] == pi:
        #                 dets_to_tracks[j] = -1
        #             elif dets_to_tracks[j] > pi:
        #                 dets_to_tracks[j] = dets_to_tracks[j] - 1
        #         self._tracks.pop(pi)
        #         self._tracks_cls.pop(pi)
        #         self._tracks_age.pop(pi)

        # update
        self._prev_dets_xy = dets_xy
        self._prev_dets_cls = dets_cls
        self._prev_instance_mask = instance_mask
        self._prev_dets_to_tracks = dets_to_tracks

    def get_tracklets(self):
        tracks, tracks_cls = [], []
        for i in range(len(self._tracks)):
            if self._tracks_age[i] < self._max_track_age and len(self._tracks[i]) > 1:
                tracks.append(np.stack(self._tracks[i], axis=0))
                tracks_cls.append(np.array(self._tracks_cls[i]).mean())

        return tracks, tracks_cls

    def _associate_prev_det(self, dets_xy, dets_cls, instance_mask, sim_matrix):
        prev_dets_inds = []
        occupied_flag = np.zeros(len(self._prev_dets_xy), dtype=bool)
        sim = sim_matrix[0].data.cpu().numpy()

        for d_idx, (d_xy, d_cls) in enumerate(zip(dets_xy, dets_cls)):
            inst_id = d_idx + 1  # instance is 1-based

            # For all the points that belong to the current instance, find their
            # most similar points in the previous scans and take the point with
            # highest support as the associated point of this instance in the 
            # previous scan.
            inst_sim = sim[instance_mask == inst_id].argmax(axis=1)
            assoc_prev_pt_inds = np.bincount(inst_sim).argmax()

            # associated detection
            prev_d_idx = self._prev_instance_mask[assoc_prev_pt_inds] - 1  # instance is 1-based

            # only associate one detection
            if occupied_flag[prev_d_idx]:
                prev_dets_inds.append(-1)
            else:
                prev_dets_inds.append(prev_d_idx)
                occupied_flag[prev_d_idx] = True

        return prev_dets_inds
