import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    param_file_arg = DeclareLaunchArgument(
        "param_file",
        description="yaml file path for dr spaam ros config",
        default_value=os.path.join(
            get_package_share_directory("dr_spaam_ros"),
            "config",
            "dr_spaam_param.yaml"
        ),
    )

    scan_topic_name_arg = DeclareLaunchArgument(
        "scan_topic_name",
        description="2D LiDAR Topic Name",
        default_value="/scan",
    )

    execute_default_arg = DeclareLaunchArgument(
        "execute_default",
        description="Set to True to enable initialize detection",
        default_value="/scan",
    )

    namespace_arg = DeclareLaunchArgument(
        "namespace",
        description="Namespace (default: Empty)",
        default_value="",
    )

    param_file = LaunchConfiguration("param_file")
    scan_topic_name = LaunchConfiguration("scan_topic_name")
    execute_default = LaunchConfiguration("execute_default")
    namespace = LaunchConfiguration("namespace")


    dr_spaam_node_cmd = Node(
        package="dr_spaam_ros",
        executable="dr_spaam_ros",
        name="dr_spaam_ros",
        namespace=namespace,
        parameters=[
            param_file,
            {
                "scan_topic_name": scan_topic_name,
                "execute_default": execute_default,
            },
        ],
        output="screen"
    )

    return LaunchDescription(
        param_file_arg,
        scan_topic_name_arg,
        execute_default_arg,
        namespace_arg,
        dr_spaam_node_cmd,
    )
