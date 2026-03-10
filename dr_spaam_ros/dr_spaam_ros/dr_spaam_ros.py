# import time
import numpy as np
import os

import rclpy
from rclpy.node import Node
from ament_index_python.packages import get_package_share_directory

from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Point, Pose, PoseArray
from visualization_msgs.msg import Marker
from std_srvs.srv import SetBool

from dr_spaam.detector import Detector
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSReliabilityPolicy, QoSHistoryPolicy


class DrSpaamROS(Node):
    """ROS node to detect pedestrian using DROW3 or DR-SPAAM."""

    def __init__(self):
        super().__init__('dr_spaam_ros')
        self._read_params()
        self._detector = Detector(
            self.weight_file,
            model=self.detector_model,
            gpu=self.use_gpu,
            stride=self.stride,
            panoramic_scan=self.panoramic_scan,
        )
        self._init()

    def _read_params(self):
        """
        @brief      Reads parameters from ROS server.
        """
        package_share_directory = get_package_share_directory('dr_spaam_ros')

        self.weight_file    = os.path.join(package_share_directory, "weights", self.declare_parameter("weight_file", "ckpt_jrdb_ann_ft_dr_spaam_e20.pth").value)
        self.detector_model = self.declare_parameter("detector_model", "DR-SPAAM").value
        self.use_gpu        = self.declare_parameter("use_gpu", False).value
        self.conf_thresh    = self.declare_parameter("conf_thresh", 0.5).value
        self.stride         = self.declare_parameter("stride", 1).value
        self.panoramic_scan = self.declare_parameter("panoramic_scan", False).value
        self.queue_size     = self.declare_parameter("queue_size", 1).value

        self.scan_topic     = self.declare_parameter("scan_topic_name", "/scan").value
        self.detect_mode    = self.declare_parameter("execute_default", True).value

    def _init(self):
        """
        @brief      Initialize ROS connection.
        """
        qos_policy = rclpy.qos.QoSProfile(
            # reliability=rclpy.qos.ReliabilityPolicy.RELIABLE,
            reliability=rclpy.qos.ReliabilityPolicy.BEST_EFFORT,
            history=rclpy.qos.HistoryPolicy.KEEP_LAST,
            depth=1
        )

        # Publisher
        self._dets_pub = self.create_publisher(
            PoseArray, "dr_spaam_detections", qos_policy,
        )

        self._rviz_pub = self.create_publisher(
            Marker, "dr_spaam_rviz", qos_policy,
        )

        # Subscriber
        self._scan_sub = self.create_subscription(
            LaserScan, self.scan_topic, self._scan_callback, qos_policy,
        )

        # Service
        self._run_ctrl_srv = self.create_service(
            SetBool, "dr_spaam_ros/run_ctr", self._run_ctrl_callback
        )

    def _run_ctrl_callback(self, request, response):
        """
        @brief      Callback function for service call.
        """
        if ((request.data == True) or (request.data == False)):
            response.success = True
            self.detect_mode = request.data
        else:
            response.success = False
            self.detect_mode = False
            self.get_logger().debug("[DrSpaamROS] Unknown command: %d" % request.data)

        return response

    def _scan_callback(self, msg):
        if not self.detect_mode:
            return

        if (
            self._dets_pub.get_subscription_count() == 0
            and self._rviz_pub.get_subscription_count() == 0
        ):
            return

        # TODO check the computation here
        if not self._detector.is_ready():
            self._detector.set_laser_fov(msg.angle_increment * len(msg.ranges))

        scan = np.array(msg.ranges)
        scan[scan == 0.0] = 29.99
        scan[np.isinf(scan)] = 29.99
        scan[np.isnan(scan)] = 29.99

        dets_xy, dets_cls, _ = self._detector(scan)

        offset_ang = (msg.angle_max + msg.angle_min) / 2.0

        # confidence threshold
        conf_mask = (dets_cls >= self.conf_thresh).reshape(-1)
        dets_xy = dets_xy[conf_mask]

        for i in range(len(dets_xy)):
            xy = dets_xy[i]
            dets_xy[i][0] = xy[0] * np.cos(offset_ang) - xy[1] * np.sin(offset_ang)
            dets_xy[i][1] = xy[0] * np.sin(offset_ang) + xy[1] * np.cos(offset_ang)

        # convert to ros msg and publish
        dets_msg = detections_to_pose_array(dets_xy)
        dets_msg.header = msg.header
        self._dets_pub.publish(dets_msg)

        rviz_msg = detections_to_rviz_marker(dets_xy)
        rviz_msg.header = msg.header
        self._rviz_pub.publish(rviz_msg)


def detections_to_rviz_marker(dets_xy):
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
    msg.color.g = 0.0
    msg.color.b = 0.0
    msg.color.a = 1.0

    # circle
    r = 0.4
    ang = np.linspace(0, 2 * np.pi, 20)
    xy_offsets = r * np.stack((np.cos(ang), np.sin(ang)), axis=1)

    # to msg
    for d_xy in dets_xy:
        for i in range(len(xy_offsets) - 1):
            # start point of a segment
            p0 = Point()
            p0.x = d_xy[0] + xy_offsets[i, 0]
            p0.y = d_xy[1] + xy_offsets[i, 1]
            p0.z = 0.0
            msg.points.append(p0)

            # end point
            p1 = Point()
            p1.x = d_xy[0] + xy_offsets[i + 1, 0]
            p1.y = d_xy[1] + xy_offsets[i + 1, 1]
            p1.z = 0.0
            msg.points.append(p1)

    return msg


def detections_to_pose_array(dets_xy):
    pose_array = PoseArray()
    for d_xy in dets_xy:
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
    rclpy.spin(drspaamros)
    drspaamros.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()