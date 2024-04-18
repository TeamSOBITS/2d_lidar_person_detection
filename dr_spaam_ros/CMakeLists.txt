cmake_minimum_required(VERSION 3.10.2)
project(dr_spaam_ros)

find_package(catkin REQUIRED COMPONENTS
  rospy
  rosbag
  rospack
  sensor_msgs
  geometry_msgs
  tf2_msgs
  visualization_msgs
)

catkin_package()

include_directories(
# include
  ${catkin_INCLUDE_DIRS}
)

catkin_python_setup()
