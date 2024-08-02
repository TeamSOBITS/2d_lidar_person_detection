# import time
import numpy as np
import os

import rclpy
from rclpy.node import Node
from ament_index_python.packages import get_package_share_directory

from sensor_msgs.msg import LaserScan
from geometry_msgs.msg import Point, Pose, PoseArray
from visualization_msgs.msg import Marker
from sobits_msgs.srv import RunCtrl

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

        self.weight_file    = os.path.join(package_share_directory, "weights", self.declare_parameter("weight_file", "default_weight_file").value)
        self.conf_thresh    = self.declare_parameter("conf_thresh", 0.5).value
        self.stride         = self.declare_parameter("stride", 1).value
        self.use_gpu        = self.declare_parameter("use_gpu", False).value
        self.detector_model = self.declare_parameter("detector_model", "default_model").value
        self.panoramic_scan = self.declare_parameter("panoramic_scan", False).value
        self.detect_mode    = self.declare_parameter("detect_mode", False).value

    def _init(self):
        """
        @brief      Initialize ROS connection.
        """
        # QoS profile with Transient Local durability for latching behavior
        # qos_profile = QoSProfile(depth=10)
        # qos_profile.durability = QoSDurabilityPolicy.TRANSIENT_LOCAL
        qos_profile = QoSProfile(
            durability=QoSDurabilityPolicy.VOLATILE,
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=10
        )

        # Publisher
        # det_topic, det_queue_size = read_publisher_param(self, "detections")
        det_topic = "/dr_spaam_detections"
        self._dets_pub = self.create_publisher(
            PoseArray, det_topic, qos_profile
        )

        # rviz_topic, rviz_queue_size = read_publisher_param(self, "rviz")
        rviz_topic = "/dr_spaam_rviz"
        self._rviz_pub = self.create_publisher(
            Marker, rviz_topic, qos_profile
        )

        # Subscriber
        # scan_topic, scan_queue_size = read_subscriber_param(self, "scan")
        # scan_topic = "/scan"
        scan_topic = "/kachaka/lidar/scan"
        self._scan_sub = self.create_subscription(
            LaserScan, scan_topic, self._scan_callback, qos_profile
        )

        # Service
        self._run_ctrl_srv = self.create_service(
            RunCtrl, "/run_ctrl", self._run_ctrl_callback
        )

    def _run_ctrl_callback(self, request, response):
        """
        @brief      Callback function for service call.
        """
        if request.request == True:
            response.detect_mode = True
        elif request.request == False:
            response.detect_mode = False
        else:
            self.get_logger().debug("[DrSpaamROS] Unknown command: %d" % request.request)

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
            self._detector.set_laser_fov(
                np.rad2deg(msg.angle_increment * len(msg.ranges))
            )

        scan = np.array(msg.ranges)
        scan[scan == 0.0] = 29.99
        scan[np.isinf(scan)] = 29.99
        scan[np.isnan(scan)] = 29.99

        print(f"scan shape: {scan.shape}")
        # print(f"scan_phi shape: {self._detector._scan_phi.shape}")

        # t = time.time()
        dets_xy, dets_cls, _ = self._detector(scan)
        # print("[DrSpaamROS] End-to-end inference time: %f" % (t - time.time()))

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
    for d_xy, d_cls in zip(dets_xy, dets_cls):
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


def detections_to_pose_array(dets_xy, dets_cls):
    pose_array = PoseArray()
    for d_xy, d_cls in zip(dets_xy, dets_cls):
        # Detector uses following frame convention:
        # x forward, y rightward, z downward, phi is angle w.r.t. x-axis
        p = Pose()
        p.position.x = float(d_xy[0])
        p.position.y = float(d_xy[1])
        p.position.z = 0.0
        pose_array.poses.append(p)

    return pose_array


# def read_subscriber_param(node, name):
#     """
#     @brief      Convenience function to read subscriber parameter.
#     """
#     topic = node.declare_parameter(f"subscriber/{name}/topic", "default_topic").value
#     queue_size = node.declare_parameter(f"subscriber/{name}/queue_size", 10).value
#     return topic, queue_size


# def read_publisher_param(node, name):
#     """
#     @brief      Convenience function to read publisher parameter.
#     """
#     topic = node.declare_parameter(f"publisher/{name}/topic", "default_topic").value
#     queue_size = node.declare_parameter(f"publisher/{name}/queue_size", 10).value
#     return topic, queue_size


def main(args=None):
    rclpy.init(args=args)
    drspaamros = DrSpaamROS()
    rclpy.spin(drspaamros)
    drspaamros.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()