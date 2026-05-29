<a name="readme-top"></a>

[EN](README.md) | [JA](README_ja.md)

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
    <li><a href="#マイルストーン">マイルストーン</a></li>
    <li><a href="#参考文献">参考文献</a></li>
  </ol>
</details>

## 概要

本リポジトリには，足首や膝の高さに取り付けた2D LiDARを使ったリアルタイム人物検出器DROW3 ([arXiv](https://arxiv.org/abs/1804.02463)) とDR-SPAAM ([arXiv](https://arxiv.org/abs/2004.14079)) が実装されている．
また，*Self-Supervised Person Detection in 2D Range Data using a Calibrated Camera* ([arXiv](https://arxiv.org/abs/2012.08890))の実験も含まれている．

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

## 環境構築

ここで，本レポジトリのセットアップ方法について説明します．

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>

### 環境条件

まず，以下の環境を整えてから，次のインストール段階に進んでください．

| System  | Version |
| ------------- | ------------- |
| Ubuntu | 24.04 (Noble Numbat) |
| ROS 2 | Jazzy Jalisco |
| Python | 3.8 |
| PyTorch | 2.2.1 (Tested) |

> [!NOTE]
> `Ubuntu`や`ROS`のインストール方法に関しては，[SOBITS Manual](https://github.com/TeamSOBITS/sobits_manual#%E9%96%8B%E7%99%BA%E7%92%B0%E5%A2%83%E3%81%AB%E3%81%A4%E3%81%84%E3%81%A6)に参照してください．

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>

### インストール方法

1. ROSの`src`フォルダに移動します．
   ```sh
   $ cd ~/colcon_ws/src/
   ```
2. 本レポジトリをcloneします．
   ```sh
   $ git clone -b humble-devel https://github.com/TeamSOBITS/2d_lidar_person_detection
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
   $ cd ~/colcon_ws
   $ colcon build --symlink-install
   $ source ~/colcon_ws/install/setup.sh
   ```

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>

## 実行・操作方法

1. [dr_spaam_param.yaml](dr_spaam_ros/config/dr_spaam_param.yaml)のパラメータを設定します．
    ```yaml
    weight_file: "ckpt_jrdb_ann_ft_dr_spaam_e20.pth" # Name of the weight file
    detector_model: "DR-SPAAM"                # DROW3 または DR-SPAAM
    use_gpu: True                             # GPU を使う場合は True
    conf_thresh: 0.9                          # 検出信頼度のしきい値
    stride: 1                                 # scan の間引き幅
    panoramic_scan: false                     # 360 度 LiDAR の場合は true
    queue_size: 1
    ```
2. 必要に応じて launch 引数を指定してノードを起動します．
    ```sh
    $ ros2 launch dr_spaam_ros dr_spaam_ros.launch.py
    ```
3. 起動時に lifecycle を自動遷移させない場合は，`auto_configure` / `auto_activate` を指定します．
    ```sh
    $ ros2 launch dr_spaam_ros dr_spaam_ros.launch.py auto_configure:=False auto_activate:=False
    ```
4. 手動で lifecycle を遷移させる場合は，以下を実行します．
    ```sh
    $ ros2 lifecycle set /dr_spaam_ros configure
    $ ros2 lifecycle set /dr_spaam_ros activate
    ```
5. scan topic が namespace 付きの場合は，明示的に指定します．
    ```sh
    $ ros2 launch dr_spaam_ros dr_spaam_ros.launch.py scan_topic_name:=/sobit_home/lidar_scan
    ```

### Lifecycle と QoS に関する注意

- `dr_spaam_ros` は lifecycle node として動作します．
- `configure` で Detector と Publisher を生成し，`activate` で `LaserScan` の Subscriber を生成します．
- `LaserScan` は `qos_profile_sensor_data` (`BEST_EFFORT`) で購読します．
- そのため，多くの ROS 2 LiDAR ドライバと QoS 互換を保てます．

Publisher 側の QoS を確認したい場合:
```sh
$ ros2 topic info /scan --verbose
```

### 主な launch 引数

| 引数 | 説明 | デフォルト |
| --- | --- | --- |
| `param_file` | パラメータ YAML のパス | `dr_spaam_ros/config/dr_spaam_param.yaml` |
| `scan_topic_name` | 入力 `LaserScan` topic | `/scan` |
| `namespace` | ノード namespace | `""` |
| `auto_configure` | 起動時に configure する | `True` |
| `auto_activate` | 起動時に activate する | `True` |

### 主な ROS パラメータ

| パラメータ | 説明 | デフォルト |
| --- | --- | --- |
| `weight_file` | `weights/` 以下の重みファイル名 | `ckpt_jrdb_ann_ft_dr_spaam_e20.pth` |
| `detector_model` | `DROW3` または `DR-SPAAM` | `DR-SPAAM` |
| `use_gpu` | GPU 推論を使うか | `False` |
| `conf_thresh` | 検出信頼度のしきい値 | `0.9` |
| `stride` | scan の間引き幅 | `1` |
| `panoramic_scan` | 360 度 scan かどうか | `False` |
| `scan_topic_name` | 入力 `LaserScan` topic 名 | `/scan` |

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>

### Subscribers & Publishers

- Subscribers:

| トピック名 | 型 | 意味 |
| --- | --- | --- |
| `/scan` または `scan_topic_name` で指定した topic | sensor_msgs/LaserScan | LiDARのスキャン情報 |

- Publishers:

| トピック名 | 型 | 意味 |
| --- | --- | --- |
| /dr_spaam_ros/dr_spaam_detections | geometry_msgs/PoseArray   | 人物検出結果 |
| /dr_spaam_ros/dr_spaam_rviz       | visualization_msgs/Marker | RViz上の結果の可視化 |

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>

### Lifecycle Control

人物検出の有効化 / 無効化は service ではなく lifecycle で行います．

```sh
$ ros2 lifecycle set /dr_spaam_ros deactivate
$ ros2 lifecycle set /dr_spaam_ros activate
```

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>

## マイルストーン

- [○] lifecycle node への対応
- [○] OSS
    - [○] ドキュメンテーションの充実
    - [○] コーディングスタイルの統一

現時点のバッグや新規機能の依頼を確認するために[Issueページ][issues-url] をご覧ください．

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>

## 参考文献

* [DROW3](https://arxiv.org/abs/1804.02463)
* [DR-SPAAM](https://arxiv.org/abs/2004.14079)
* [ 2D_lidar_person_detection(official)](https://github.com/VisualComputingInstitute/2D_lidar_person_detection)
* [ROS 2 Humble](https://docs.ros.org/en/humble/)

<p align="right">(<a href="#readme-top">上に戻る</a>)</p>

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
