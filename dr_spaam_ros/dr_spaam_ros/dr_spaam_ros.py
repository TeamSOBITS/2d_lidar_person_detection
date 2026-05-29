import gc
import numpy as np
import os
import torch

import rclpy
from rclpy.lifecycle import LifecycleNode, TransitionCallbackReturn, LifecycleState
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, qos_profile_sensor_data
from ament_index_python.packages import get_package_share_directory

from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Point, Pose, PoseArray
from visualization_msgs.msg import Marker

from dr_spaam.detector import Detector


class DrSpaamROS(LifecycleNode):
    """ROS node to detect pedestrian using DROW3 or DR-SPAAM."""

    def __init__(self):
        super().__init__('dr_spaam_ros')
        self._detector = None
        self._dets_pub = None
        self._rviz_pub = None
        self._scan_sub = None
        self._pub_qos_policy = QoSProfile(
            reliability=ReliabilityPolicy.RELIABLE,
            history=HistoryPolicy.KEEP_LAST,
            depth=1
        )
        self._scan_qos_policy = qos_profile_sensor_data
        self._declare_params()

    def _declare_params(self):
        """
        @brief      Declares parameters.
        """
        self.declare_parameter("weight_file", "ckpt_jrdb_ann_ft_dr_spaam_e20.pth")
        self.declare_parameter("detector_model", "DR-SPAAM")
        self.declare_parameter("use_gpu", False)
        self.declare_parameter("conf_thresh", 0.5)
        self.declare_parameter("stride", 1)
        self.declare_parameter("panoramic_scan", False)
        self.declare_parameter("queue_size", 1)
        self.declare_parameter("scan_topic_name", "/scan")
        self.declare_parameter("auto_configure", True)
        self.declare_parameter("auto_activate", True)

    def _read_params(self):
        """
        @brief      Reads parameters from ROS server.
        """
        package_share_directory = get_package_share_directory('dr_spaam_ros')

        weight_file = self.get_parameter("weight_file").get_parameter_value().string_value
        self.weight_file = os.path.join(package_share_directory, "weights", weight_file)
        self.detector_model = self.get_parameter("detector_model").get_parameter_value().string_value
        self.use_gpu = self.get_parameter("use_gpu").get_parameter_value().bool_value
        self.conf_thresh = self.get_parameter("conf_thresh").get_parameter_value().double_value
        self.stride = self.get_parameter("stride").get_parameter_value().integer_value
        self.panoramic_scan = self.get_parameter("panoramic_scan").get_parameter_value().bool_value
        self.queue_size = self.get_parameter("queue_size").get_parameter_value().integer_value
        self.scan_topic = self.get_parameter("scan_topic_name").get_parameter_value().string_value

    def on_configure(self, state: LifecycleState) -> TransitionCallbackReturn:
        self.get_logger().info("Configuring dr_spaam_ros...")
        self._read_params()

        try:
            self._detector = Detector(
                self.weight_file,
                model=self.detector_model,
                gpu=self.use_gpu,
                stride=self.stride,
                panoramic_scan=self.panoramic_scan,
            )
        except Exception as exc:
            self.get_logger().error(f"Failed to initialize detector: {exc}")
            self._detector = None
            return TransitionCallbackReturn.FAILURE

        self._dets_pub = self.create_lifecycle_publisher(
            PoseArray, "dr_spaam_detections", self._pub_qos_policy,
        )
        self._rviz_pub = self.create_lifecycle_publisher(
            Marker, "dr_spaam_rviz", self._pub_qos_policy,
        )
        return TransitionCallbackReturn.SUCCESS

    def _release_detector(self) -> None:
        detector = self._detector
        self._detector = None

        clear_cuda_cache = False
        if detector is not None:
            model = getattr(detector, "_model", None)
            if model is not None:
                try:
                    clear_cuda_cache = next(model.parameters()).is_cuda
                except StopIteration:
                    clear_cuda_cache = False
                except AttributeError:
                    clear_cuda_cache = bool(getattr(detector, "_gpu", False))
                if clear_cuda_cache:
                    model.cpu()
                detector._model = None
                del model
            else:
                clear_cuda_cache = bool(getattr(detector, "_gpu", False))
            detector._scan_phi = None
            del detector

        gc.collect()
        if clear_cuda_cache and torch.cuda.is_available():
            self.get_logger().info("Clearing CUDA cache")
            torch.cuda.synchronize()
            torch.cuda.empty_cache()

    def on_activate(self, state: LifecycleState) -> TransitionCallbackReturn:
        self.get_logger().info("Activating dr_spaam_ros...")
        self._scan_sub = self.create_subscription(
            LaserScan, self.scan_topic, self._scan_callback, self._scan_qos_policy,
        )
        return super().on_activate(state)

    def on_deactivate(self, state: LifecycleState) -> TransitionCallbackReturn:
        self.get_logger().info("Deactivating dr_spaam_ros...")
        if self._scan_sub is not None:
            self.destroy_subscription(self._scan_sub)
            self._scan_sub = None
        return super().on_deactivate(state)

    def on_cleanup(self, state: LifecycleState) -> TransitionCallbackReturn:
        self.get_logger().info("Cleaning up dr_spaam_ros...")
        if self._scan_sub is not None:
            self.destroy_subscription(self._scan_sub)
            self._scan_sub = None
        if self._dets_pub is not None:
            self.destroy_publisher(self._dets_pub)
            self._dets_pub = None
        if self._rviz_pub is not None:
            self.destroy_publisher(self._rviz_pub)
            self._rviz_pub = None
        self._release_detector()
        return TransitionCallbackReturn.SUCCESS

    def on_shutdown(self, state: LifecycleState) -> TransitionCallbackReturn:
        self.on_cleanup(state)
        return TransitionCallbackReturn.SUCCESS

    def _scan_callback(self, msg):
        if self._detector is None or self._dets_pub is None or self._rviz_pub is None:
            return

        if (
            self._dets_pub.get_subscription_count() == 0
            and self._rviz_pub.get_subscription_count() == 0
        ):
            return

        if not self._detector.is_ready():
            self._detector.set_laser_fov(np.rad2deg(msg.angle_max - msg.angle_min))

        scan = np.array(msg.ranges)
        scan[scan == 0.0] = 29.99
        scan[np.isinf(scan)] = 29.99
        scan[np.isnan(scan)] = 29.99

        dets_xy, dets_cls, _ = self._detector(scan)

        # confidence threshold
        conf_mask = (dets_cls >= self.conf_thresh).reshape(-1)
        dets_xy = dets_xy[conf_mask]
        dets_cls = dets_cls[conf_mask]

        # convert to ros msg and publish
        dets_msg = detections_to_pose_array(dets_xy, dets_cls)
        dets_msg.header = msg.header
        self._dets_pub.publish(dets_msg)

        rviz_msg = detections_to_rviz_marker(dets_xy, dets_cls)
        rviz_msg.header = msg.header
        self._rviz_pub.publish(rviz_msg)


def detections_to_rviz_marker(dets_xy, dets_cls):
    """
    @brief     Convert detection to RViz marker msg. Each detection is marked as
               a circle approximated by line segments.
    """
    msg = Marker()
    msg.action = Marker.ADD
    msg.ns = "dr_spaam_ros"
    msg.id = 0
    msg.type = Marker.LINE_LIST

    # set quaternion so that RViz does not give warning
    msg.pose.orientation.x = 0.0
    msg.pose.orientation.y = 0.0
    msg.pose.orientation.z = 0.0
    msg.pose.orientation.w = 1.0

    msg.scale.x = 0.03  # line width
    # red color
    msg.color.r = 1.0
    msg.color.a = 1.0

    # circle
    r = 0.4
    ang = np.linspace(0, 2 * np.pi, 20)
    xy_offsets = r * np.stack((np.cos(ang), np.sin(ang)), axis=1)

    # to msg
    points: list = []
    for d_xy, d_cls in zip(dets_xy, dets_cls):
        for i in range(len(xy_offsets) - 1):
            # start point of a segment
            p0 = Point()
            p0.x = d_xy[0] + xy_offsets[i, 0]
            p0.y = d_xy[1] + xy_offsets[i, 1]
            p0.z = 0.0
            points.append(p0)

            # end point
            p1 = Point()
            p1.x = d_xy[0] + xy_offsets[i + 1, 0]
            p1.y = d_xy[1] + xy_offsets[i + 1, 1]
            p1.z = 0.0
            points.append(p1)
    msg.points = points

    return msg


def detections_to_pose_array(dets_xy, dets_cls):
    pose_array = PoseArray()
    pose_array.poses = []
    for d_xy, d_cls in zip(dets_xy, dets_cls):
        # Detector uses following frame convention:
        # x forward, y rightward, z downward, phi is angle w.r.t. x-axis
        p = Pose()
        p.position.x = float(d_xy[0])
        p.position.y = float(d_xy[1])
        p.position.z = 0.0
        pose_array.poses.append(p)

    return pose_array


def main(args=None):
    rclpy.init(args=args)
    drspaamros = DrSpaamROS()

    auto_configure = drspaamros.get_parameter("auto_configure").get_parameter_value().bool_value
    auto_activate = drspaamros.get_parameter("auto_activate").get_parameter_value().bool_value

    configure_succeeded = True
    if auto_configure or auto_activate:
        configure_result = drspaamros.trigger_configure()
        configure_succeeded = configure_result == TransitionCallbackReturn.SUCCESS
    if auto_activate:
        if configure_succeeded:
            drspaamros.trigger_activate()
        else:
            drspaamros.get_logger().error(
                "Auto-activation requested, but node configuration failed; "
                "skipping activation."
            )

    try:
        rclpy.spin(drspaamros)
    except KeyboardInterrupt:
        pass
    finally:
        drspaamros.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
