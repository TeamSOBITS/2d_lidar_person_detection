#!/bin/bash

echo "╔══╣ Setup: 2d_lidar_person_detection (STARTING) ╠══╗"


# Download dependencies
python3 -m pip install -U pip
python3 -m pip install \
    argparse \
    numpy \
    matplotlib \
    scipy \
    scikit-learn \
    setuptools \
    gdown \
    json \
    tqdm \
    functools \
    python-lzf \
    tensorboardX

# Install PyTorch
python3 -m pip install torch torchvision torchaudio

# Install dr_spaam python package
DIR="$( pwd )"
cd dr_spaam
sudo python3 -m pip install .
cd $DIR

# Download weight files
python3 -m gdown https://drive.google.com/drive/folders/1OI99VfUBkmRSijgmMYYku9Pc_nS3v8sj \
    -O dr_spaam_ros/weights \
    --folder

# Download ROS dependencies
sudo apt-get update
sudo apt-get install -y \
    ros-$ROS_DISTRO-rosbag \
    ros-$ROS_DISTRO-tf2 \
    ros-$ROS_DISTRO-tf2-ros \
    ros-$ROS_DISTRO-sensor-msgs \
    ros-$ROS_DISTRO-geometry-msgs \
    ros-$ROS_DISTRO-visualization-msgs \

# Clone sobits_msgs
cd ..
git clone https://github.com/TeamSOBITS/sobits_msgs/
cd $DIR


echo "╚══╣ Setup: SOBIT PRO (FINISHED) ╠══╝"
