<a name="readme-top"></a>

[JA](README.md) | [EN](README_en.md)

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![License][license-shield]][license-url]

# Person Detection in 2D Range Data

<!-- 目次 -->
<details>
  <summary>目次</summary>
  <ol>
    <li>
      <a href="#概要">概要</a>
    </li>
    <li>
      <a href="#環境構築">環境構築</a>
      <ul>
        <li><a href="#環境条件">環境条件</a></li>
        <li><a href="#インストール方法">インストール方法</a></li>
      </ul>
    </li>
    <li>
    　<a href="#実行操作方法">実行・操作方法</a>
      <ul>
        <li><a href="#subscribers--publishers">Subscribers & Publishers</a></li>
      </ul>
    </li>
    <li>
    <li><a href="#マイルストーン">マイルストーン</a></li>
    <!-- <li><a href="#contributing">Contributing</a></li> -->
    <!-- <li><a href="#license">License</a></li> -->
    <li><a href="#参考文献">参考文献</a></li>
  </ol>
</details>



<!-- レポジトリの概要 -->
## 概要

This repository implements DROW3 ([arXiv](https://arxiv.org/abs/1804.02463)) and DR-SPAAM ([arXiv](https://arxiv.org/abs/2004.14079)), real-time person detectors using 2D LiDARs mounted at ankle or knee height.
Also included are experiments from *Self-Supervised Person Detection in 2D Range Data using a Calibrated Camera* ([arXiv](https://arxiv.org/abs/2012.08890)).

<details>
<summary>重みファイル一覧</summary>

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

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>


<!-- セットアップ -->
## セットアップ

ここで，本レポジトリのセットアップ方法について説明します．

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>


### 環境条件

まず，以下の環境を整えてから，次のインストール段階に進んでください．

| System  | Version |
| ------------- | ------------- |
| Ubuntu | 20.04 (Focal Fossa) |
| ROS | Noetic Ninjemys |
| Python | 3.8 |
| PyTorch | 2.2.1 (Tested) |

> [!NOTE]
> `Ubuntu`や`ROS`のインストール方法に関しては，[SOBITS Manual](https://github.com/TeamSOBITS/sobits_manual#%E9%96%8B%E7%99%BA%E7%92%B0%E5%A2%83%E3%81%AB%E3%81%A4%E3%81%84%E3%81%A6)に参照してください．

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>


### インストール方法

1. ROSの`src`フォルダに移動します．
   ```sh
   $ roscd
   # もしくは，"cd ~/catkin_ws/"へ移動．
   $ cd src/
   ```
2. 本レポジトリをcloneします．
   ```sh
   $ git clone https://github.com/TeamSOBITS/2d_lidar_person_detection
   ```
3. レポジトリの中へ移動します．
   ```sh
   $ cd 2d_lidar_person_detection/
   ```
4. 依存パッケージをインストールします．
   ```sh
   $ bash install.sh
   ```
5. パッケージをコンパイルします．
   ```sh
   $ roscd
   # もしくは，"cd ~/catkin_ws/"へ移動．
   $ catkin_make
   ```

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>


<!-- 実行・操作方法 -->
## 実行・操作方法

1. [dr_spaam_ros.yaml](dr_spaam_ros/config/dr_spaam_ros.yaml)のパラメータを設定する．
    ```yaml
    weight_file: "ckpt_jrdb_ann_ft_dr_spaam_e20.pth" # Name of the weight file
    detector_model: "DR-SPAAM"  # Set model name: DROW3 or DR-SPAAM
    use_gpu: True     # Set to True to use GPU
    conf_thresh: 0.5  # Set confidence threshold
    stride: 1         # Downsample scans for faster inference
    panoramic_scan: False  # Set to True if the scan covers 360 degree
    detect_mode: True # Set detection mode when launching
    ```
2. [topics.yaml](dr_spaam_ros/config/topics.yaml)のパラメータを設定する．
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
3. [dr_spaam_ros.launch](dr_spaam_ros/launch/dr_spaam_ros.launch)というlaunchファイルを実行します．
    ```sh
   $ roslaunch dr_spaam_ros dr_spaam_ros.launch
    ```

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>


### Subscribers & Publishers

- Subscribers:

| トピック名 | 型 | 意味 |
| --- | --- | --- |
| /scan | sensor_msgs/LaserScan | LiDARのスキャン情報 |

- Publishers:

| トピック名 | 型 | 意味 |
| --- | --- | --- |
| /dr_spaam_ros/dr_spaam_detections | geometry_msgs/PoseArray   | 3次元位置検出結果の配列 | 
| /dr_spaam_ros/dr_spaam_rviz       | visualization_msgs/Marker | RViz上の結果の可視化 |

<p align="right">(<a href="#readme-top">back to top</a>)</p>


### Services

| サービス名 | 型 | 意味 |
| --- | --- | --- |
| /dr_spaam_ros/run_ctrl | sobits_msgs/RunCtrl | 3次元位置検出の切り替え (ON:`true`, OFF:`false`) |

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- マイルストーン -->
## マイルストーン

- [x] 検出機能のサービス化
- [x] OSS
    - [x] ドキュメンテーションの充実
    - [x] コーディングスタイルの統一

現時点のバッグや新規機能の依頼を確認するために[Issueページ][issues-url] をご覧ください．

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>


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

<p align="right">(<a href="#readme-top">上に戻る</a>)</p> -->


<!-- LICENSE -->
<!-- ## License

Distributed under the MIT License. See `LICENSE.txt` for more NOTErmation.

<p align="right">(<a href="#readme-top">上に戻る</a>)</p> -->


<!-- 参考文献 -->
## 参考文献

* [DROW3](https://arxiv.org/abs/1804.02463)
* [DR-SPAAM](https://arxiv.org/abs/2004.14079)
* [ 2D_lidar_person_detection(official)](https://github.com/VisualComputingInstitute/2D_lidar_person_detection)
* [ROS Noetic](http://wiki.ros.org/noetic)

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>



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