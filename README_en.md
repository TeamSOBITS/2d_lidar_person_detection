<a name="readme-top"></a>

[JA](README.md) | [EN](README_en.md)

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
    <!-- <li><a href="#contributing">Contributing</a></li> -->
    <!-- <li><a href="#license">License</a></li> -->
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- INTRODUCTION -->
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


<!-- GETTING STARTED -->
## Getting Started

This section describes how to set up this repository.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


### Prerequisites

First, please set up the following environment before proceeding to the next installation stage.

| System  | Version |
| --- | --- |
| Ubuntu  | 20.04 (Focal Fossa) |
| ROS     | Noetic Ninjemys |
| Python  | 3.8 |
| PyTorch | 2.2.1 (Tested) |

> [!NOTE]
> If you need to install `Ubuntu` or `ROS`, please check our [SOBITS Manual](https://github.com/TeamSOBITS/sobits_manual#%E9%96%8B%E7%99%BA%E7%92%B0%E5%A2%83%E3%81%AB%E3%81%A4%E3%81%84%E3%81%A6).

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>


### Installation

1. Go to the `src` folder of ROS.
   ```sh
   $ roscd
   # Or just use "cd ~/catkin_ws/" and change directory.
   $ cd src/
   ```
2. Clone this repository.
   ```sh
   $ git clone https://github.com/TeamSOBITS/2d_lidar_person_detection
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
   $ roscd
   # Or just use "cd ~/catkin_ws/" and change directory.
   $ catkin_make
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- LAUNCH AND USAGE EXAMPLES -->
## Launch and Usage

1. Set the parameters inside [dr_spaam_ros.yaml](dr_spaam_ros/config/dr_spaam_ros.yaml).
    ```yaml
    weight_file: "ckpt_jrdb_ann_ft_dr_spaam_e20.pth" # Name of the weight file
    detector_model: "DR-SPAAM"  # Set model name: DROW3 or DR-SPAAM
    use_gpu: True     # Set to True to use GPU
    conf_thresh: 0.5  # Set confidence threshold
    stride: 1         # Downsample scans for faster inference
    panoramic_scan: False  # Set to True if the scan covers 360 degree
    detect_mode: True # Set detection mode when launching
    ```
2. Set the parameters inside [topics.yaml](dr_spaam_ros/config/topics.yaml).
    ```yaml
    publisher:
        detections:
            topic: /dr_spaam_detections
            queue_size: 1
            latch: false

        rviz:
            topic: /dr_spaam_rviz
            queue_size: 1
            latch: false

    subscriber:
        scan:
            topic: /scan
            queue_size: 1
    ```
3. Execute the launch file [dr_spaam_ros.launch](dr_spaam_ros/launch/dr_spaam_ros.launch).
   ```sh
   $ roslaunch dr_spaam_ros dr_spaam_ros.launch
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>


### Subscribers & Publishers

- Subscribers:

| Topic | Type | Meaning |
| --- | --- | --- |
| /scan | sensor_msgs/LaserScan | LiDAR scan data |

- Publishers:

| Topic | Type | Meaning |
| --- | --- | --- |
| /dr_spaam_ros/dr_spaam_detections | geometry_msgs/PoseArray   | 3D position detection result array | 
| /dr_spaam_ros/dr_spaam_rviz       | visualization_msgs/Marker | Result Visualization over RViz |

<p align="right">(<a href="#readme-top">back to top</a>)</p>


### Services

| Service | Type | Meaning |
| --- | --- | --- |
| /dr_spaam_ros/run_ctrl | sobits_msgs/RunCtrl | 3D position detection toogle (ON:`true`, OFF:`false`) |

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- MILESTONE -->
## Milestone
- [x] Implement service (turn on/off detection)
- [x] OSS
    - [x] Improved documentation
    - [x] Unified coding style

See the [open issues][issues-url] for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- CONTRIBUTING -->
<!-- ## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p> -->


<!-- LICENSE -->
<!-- ## License

Distributed under the MIT License. See `LICENSE.txt` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p> -->


<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [DROW3](https://arxiv.org/abs/1804.02463)
* [DR-SPAAM](https://arxiv.org/abs/2004.14079)
* [ 2D_lidar_person_detection(official)](https://github.com/VisualComputingInstitute/2D_lidar_person_detection)
* [ROS Noetic](http://wiki.ros.org/noetic)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
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