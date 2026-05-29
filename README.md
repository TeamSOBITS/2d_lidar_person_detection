<a name="readme-top"></a>

[EN](README.md) | [JA](README_ja.md)

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![License][license-shield]][license-url]

# Person Detection in 2D Range Data

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#introduction">Introduction</a>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li>
      <a href="#launch-and-usage">Launch and Usage</a>
      <ul>
        <li><a href="#subscribers--publishers">Subscribers & Publishers</a></li>
      </ul>
    </li>
    <li><a href="#milestone">Milestone</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

## Introduction

This repository implements DROW3 ([arXiv](https://arxiv.org/abs/1804.02463)) and DR-SPAAM ([arXiv](https://arxiv.org/abs/2004.14079)), real-time person detectors using 2D LiDARs mounted at ankle or knee height.
Also included are experiments from *Self-Supervised Person Detection in 2D Range Data using a Calibrated Camera* ([arXiv](https://arxiv.org/abs/2012.08890)).

<details>
<summary>List of available weight files</summary>

- ckpt_jrdb_ann_dr_spaam_e20.pth
- ckpt_jrdb_ann_drow3_e40.pth
- ckpt_jrdb_ann_ft_dr_spaam_e20.pth
- ckpt_jrdb_ann_ft_drow3_e40.pth
- ckpt_jrdb_pl_dr_spaam_e20.pth
- ckpt_jrdb_pl_dr_spaam_mixup_e20.pth
- ckpt_jrdb_pl_dr_spaam_phce_e20.pth
- ckpt_jrdb_pl_dr_spaam_phce_mixup_e20.pth
- ckpt_jrdb_pl_drow3_e40.pth
- ckpt_jrdb_pl_drow3_phce_e40.pth
- ckpt_jrdb_pl_drow3_phce_mixup_e40.pth
- jrdb_dr_spaam_with_bev_box_e20.pth (Needs to be tested)

</details>

![](imgs/teaser_1.gif)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Getting Started

This section describes how to set up this repository.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Prerequisites

First, please set up the following environment before proceeding to the next installation stage.

| System  | Version |
| --- | --- |
| Ubuntu  | 24.04 (Noble Numbat) |
| ROS 2   | Jazzy Jalisco |
| Python  | 3.8 |
| PyTorch | 2.2.1 (Tested) |

> [!NOTE]
> If you need to install `Ubuntu` or `ROS`, please check our [SOBITS Manual](https://github.com/TeamSOBITS/sobits_manual#%E9%96%8B%E7%99%BA%E7%92%B0%E5%A2%83%E3%81%AB%E3%81%A4%E3%81%84%E3%81%A6).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Installation

1. Go to the `src` folder of ROS.
   ```sh
   $ cd ~/colcon_ws/src/
   ```
2. Clone this repository.
   ```sh
   $ git clone -b humble-devel https://github.com/TeamSOBITS/2d_lidar_person_detection
   ```
3. Navigate into the repository.
   ```sh
   $ cd 2d_lidar_person_detection/
   ```
4. Install the dependent packages.
   ```sh
   $ bash install.sh
   ```
5. Compile the package.
   ```sh
   $ cd ~/colcon_ws
   $ colcon build --symlink-install
   $ source ~/colcon_ws/install/setup.sh
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Launch and Usage

1. Set the parameters in [dr_spaam_param.yaml](dr_spaam_ros/config/dr_spaam_param.yaml).
    ```yaml
    weight_file: "ckpt_jrdb_ann_ft_dr_spaam_e20.pth" # Name of the weight file
    detector_model: "DR-SPAAM"                # DROW3 or DR-SPAAM
    use_gpu: True                             # Set to True to use GPU
    conf_thresh: 0.9                          # Set confidence threshold
    stride: 1                                 # Downsample scans for faster inference
    panoramic_scan: false                     # Set to true for 360-degree scans
    queue_size: 1
    ```
2. Launch the node, optionally overriding launch arguments.
   ```sh
   $ ros2 launch dr_spaam_ros dr_spaam_ros.launch.py
   ```
3. If you do not want automatic lifecycle transitions on startup, set `auto_configure` / `auto_activate`.
    ```sh
    $ ros2 launch dr_spaam_ros dr_spaam_ros.launch.py auto_configure:=False auto_activate:=False
    ```
4. For manual lifecycle control, run:
    ```sh
    $ ros2 lifecycle set /dr_spaam_ros configure
    $ ros2 lifecycle set /dr_spaam_ros activate
    ```
5. If your LiDAR topic is namespaced, pass it explicitly.
    ```sh
    $ ros2 launch dr_spaam_ros dr_spaam_ros.launch.py scan_topic_name:=/sobit_home/lidar_scan
    ```

### Lifecycle and QoS Notes

- `dr_spaam_ros` now runs as a lifecycle node.
- The detector and publishers are created during `configure`.
- The `LaserScan` subscription is created during `activate`.
- The `LaserScan` subscriber uses `qos_profile_sensor_data` (`BEST_EFFORT`).
- This matches most ROS 2 LiDAR drivers and avoids QoS reliability mismatches.

To inspect the publisher QoS:
```sh
$ ros2 topic info /scan --verbose
```

### Main Launch Arguments

| Argument | Description | Default |
| --- | --- | --- |
| `param_file` | Path to the parameter YAML file | `dr_spaam_ros/config/dr_spaam_param.yaml` |
| `scan_topic_name` | Input `LaserScan` topic | `/scan` |
| `namespace` | Node namespace | `""` |
| `auto_configure` | Configure on startup | `True` |
| `auto_activate` | Activate on startup | `True` |

### Main ROS Parameters

| Parameter | Description | Default |
| --- | --- | --- |
| `weight_file` | Weight filename under `weights/` | `ckpt_jrdb_ann_ft_dr_spaam_e20.pth` |
| `detector_model` | `DROW3` or `DR-SPAAM` | `DR-SPAAM` |
| `use_gpu` | Whether to use GPU inference | `False` |
| `conf_thresh` | Detection confidence threshold | `0.5` |
| `stride` | Scan downsampling stride | `1` |
| `panoramic_scan` | Whether the scan covers 360 degrees | `False` |
| `scan_topic_name` | Input `LaserScan` topic name | `/scan` |

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Subscribers & Publishers

- Subscribers:

| Topic | Type | Meaning |
| --- | --- | --- |
| `/scan` or the topic passed by `scan_topic_name` | sensor_msgs/LaserScan | LiDAR scan data |

- Publishers:

| Topic | Type | Meaning |
| --- | --- | --- |
| /dr_spaam_ros/dr_spaam_detections | geometry_msgs/PoseArray   | Person detection result array |
| /dr_spaam_ros/dr_spaam_rviz       | visualization_msgs/Marker | Result Visualization over RViz |

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Lifecycle Control

Use lifecycle transitions, not a service, to stop or resume detection.

```sh
$ ros2 lifecycle set /dr_spaam_ros deactivate
$ ros2 lifecycle set /dr_spaam_ros activate
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Milestone
- [○] Support lifecycle node control
- [○] OSS
    - [x] Improved documentation
    - [x] Unified coding style

See the [open issues][issues-url] for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Acknowledgments

* [DROW3](https://arxiv.org/abs/1804.02463)
* [DR-SPAAM](https://arxiv.org/abs/2004.14079)
* [ 2D_lidar_person_detection(official)](https://github.com/VisualComputingInstitute/2D_lidar_person_detection)
* [ROS 2 Humble](https://docs.ros.org/en/humble/)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

[contributors-shield]: https://img.shields.io/github/contributors/TeamSOBITS/2d_lidar_person_detection.svg?style=for-the-badge
[contributors-url]: https://github.com/TeamSOBITS/2d_lidar_person_detection/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/TeamSOBITS/2d_lidar_person_detection.svg?style=for-the-badge
[forks-url]: https://github.com/TeamSOBITS/2d_lidar_person_detection/network/members
[stars-shield]: https://img.shields.io/github/stars/TeamSOBITS/2d_lidar_person_detection.svg?style=for-the-badge
[stars-url]: https://github.com/TeamSOBITS/2d_lidar_person_detection/stargazers
[issues-shield]: https://img.shields.io/github/issues/TeamSOBITS/2d_lidar_person_detection.svg?style=for-the-badge
[issues-url]: https://github.com/TeamSOBITS/2d_lidar_person_detection/issues
[license-shield]: https://img.shields.io/github/license/TeamSOBITS/2d_lidar_person_detection.svg?style=for-the-badge
[license-url]: LICENSE
