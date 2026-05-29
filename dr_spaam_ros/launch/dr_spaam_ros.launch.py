import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


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

    namespace_arg = DeclareLaunchArgument(
        "namespace",
        description="Namespace (default: Empty)",
        default_value="",
    )

    auto_configure_arg = DeclareLaunchArgument(
        "auto_configure",
        description="Automatically configure the lifecycle node on startup",
        default_value="True",
    )

    auto_activate_arg = DeclareLaunchArgument(
        "auto_activate",
        description="Automatically activate the lifecycle node on startup",
        default_value="True",
    )

    param_file = LaunchConfiguration("param_file")
    scan_topic_name = LaunchConfiguration("scan_topic_name")
    namespace = LaunchConfiguration("namespace")
    auto_configure = LaunchConfiguration("auto_configure")
    auto_activate = LaunchConfiguration("auto_activate")


    dr_spaam_node_cmd = Node(
        package="dr_spaam_ros",
        executable="dr_spaam_ros",
        name="dr_spaam_ros",
        namespace=namespace,
        parameters=[
            param_file,
            {
                "scan_topic_name": scan_topic_name,
                "auto_configure": ParameterValue(auto_configure, value_type=bool),
                "auto_activate": ParameterValue(auto_activate, value_type=bool),
            },
        ],
        output="screen"
    )

    return LaunchDescription([
        param_file_arg,
        scan_topic_name_arg,
        namespace_arg,
        auto_configure_arg,
        auto_activate_arg,
        dr_spaam_node_cmd,
    ])
