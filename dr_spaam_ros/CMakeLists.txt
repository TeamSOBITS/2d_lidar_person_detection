cmake_minimum_required(VERSION 3.0.2)
project(dr_spaam_ros)
add_compile_options(-std=c++14 -O2 -g -Wall)

find_package(catkin REQUIRED
  COMPONENTS
  message_generation
  sensor_msgs
  std_msgs
  geometry_msgs
)


add_message_files(
  FILES
  LegPoseArray.msg
)


generate_messages(
  DEPENDENCIES
  sensor_msgs
  std_msgs
  geometry_msgs
)

catkin_package(
  CATKIN_DEPENDS
    message_runtime
)

# catkin_python_setup()
