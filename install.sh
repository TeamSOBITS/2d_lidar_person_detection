#!/bin/bash

echo "╔══╣ Setup: 2d_lidar_person_detection (STARTING) ╠══╗"


# Download dependencies
python3 -m pip install -U pip --break-system-packages
python3 -m pip install --break-system-packages \
    argparse \
    numpy \
    matplotlib \
    scipy \
    scikit-learn \
    setuptools \
    gdown \
    tqdm \
    python-lzf \
    tensorboardX

# Install PyTorch
python3 -m pip install torch torchvision torchaudio --break-system-packages

# Install dr_spaam python package
DIR="$( pwd )"
cd dr_spaam
sudo python3 -m pip install . --break-system-packages
cd $DIR

# Download weight files
python3 -m gdown https://drive.google.com/drive/folders/1OI99VfUBkmRSijgmMYYku9Pc_nS3v8sj \
    -O dr_spaam_ros/weights \
    --folder

# Download ROS dependencies
sudo apt update
sudo apt install -y \
    ros-$ROS_DISTRO-rosbag2 \
    ros-$ROS_DISTRO-tf2 \
    ros-$ROS_DISTRO-tf2-ros \
    ros-$ROS_DISTRO-sensor-msgs \
    ros-$ROS_DISTRO-geometry-msgs \
    ros-$ROS_DISTRO-visualization-msgs \

# Clone sobits_interfaces
cd ~/colcon_ws/src/
git clone -b $ROS_DISTRO-devel https://github.com/TeamSOBITS/sobits_interfaces/
cd sobits_interfaces
bash install.sh
cd $DIR


echo "╚══╣ Setup: 2d_lidar_person_detection (FINISHED) ╠══╝"
