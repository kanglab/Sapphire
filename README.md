# Sapphire

Life-event detection algorithm and software.

![demoimage](./demoimage.png)

## Description

Dashboard application for viewing activity of drosophila and detecting life-events.

## Versions

You can find version information in [CHANGELOG.md](./CHANGELOG.md).

## Dependencies

The application requires Python 3.6.
It also needs Python modules as described bellow:

- changefinder (0.3)
- cudatoolkit (9.0)
- cudnn (7.6.0)
- dash (0.43.0)
- dash-auth (1.3.2)
- dash-core-components (0.48.0)
- dash-html-components (0.16.0)
- dash-renderer (0.24.0)
- dash-table (3.7.0)
- keras (2.2.4)
- numpy (1.16.5)
- pandas (0.25.1)
- Pillow (6.1.0)
- plotly (3.2.0)
- scipy (1.3.1)
- tensorflow-gpu (1.9.0)
- tqdm (4.32.1)

## Usage

See manual.pdf in the repository.

## Install

Clone the source codes by executing below:  

``` shell
git clone git@github.com:kanglab/DiamondsOnDash.git
```

Or download the zip file by clicking the Clone or download button in this page.

Install Python language and the dependencies according to the Dependencies section.
This application run on any OS (Windows, macOS, Linux, etc.).
Running of Sapphire is verified in Windows 7, Ubuntu 16.04/18.04, and Apple OS X 10.11 El Capitan.
We have carried out operation verification of Sapphire in all the minor version releases.

## Demo

This repository includes the directory `data_root_for_demo` for storing datasets.
Note that the directory tree under `data_root_for_demo` is regorously defined to load data appropriately.
Please put your data under the directories in `data_root_for_demo` without breaking the directory tree (renaming the directories is allowed).

After installing all the dependencies, please execute `python` command in your shell terminal to start Sapphire:

``` shell
python sapphire.py
```

And then, please open your web browser and access to `localhost:8080`.
Your browser will show Sapphire application.
If your installation is correct, you can select any parameters with the selector elements on Sapphire and explore flys' images, signals, and statistics like the [demo image](./demoimage.png).
If you can't select parameters (for example, a selector element has blank), Sapphire might raise some errors.
Please see your terminal to find erros and solve them carefully.

If your dataset has large number of frames (`original` directory has, for example, 10,000 images), Sapphire will take several seconds to show images, signals, and statistics on itself.

### Directory tree

The files/directories beggining with asterisk can be arbitrarily named, although the others should have the names as given below.

``` shell
*data_root_for_demo
├── *dataset1
│   ├── blacklist.csv
│   ├── config.json
│   ├── grouping.csv
│   ├── inference
│   │   ├── adult
│   │   │   └── *profile1
│   │   │       ├── *cf_r0.003_signals.npy
│   │   │       ├── probs
│   │   │       │   ├── 000.npz
│   │   │       │   ├── 001.npz
│   │   │       │   └── 002.npz
│   │   │       ├── probs.npz
│   │   │       └── *signals.npy
│   │   └── larva
│   │       └── *profile1
│   │           ├── probs
│   │           │   ├── 000.npz
│   │           │   ├── 001.npz
│   │           │   └── 002.npz
│   │           ├── probs.npz
│   │           └── *signals.npy
│   ├── mask.npy
│   ├── mask_params.json
│   ├── *network
│   │   ├── adult
│   │   │   ├── *profile1
│   │   │   └── *profile2
│   │   └── larva
│   │       ├── *profile1
│   │       └── *profile2
│   └── original
│       ├── 0001.jpg
│       ├── 0002.jpg
│       ├── 0003.jpg
│       ├── 0004.jpg
│       ├── 0005.jpg
│       ├── eclosion.csv
│       └── pupariation.csv
└── *dataset2
```

- `dataset1`, `dataset2`: Dataset directory.
- `blacklist.csv`: written in CSV (comma separated value) format.
- `config.json`: Configuration file for a dataset.
- `grouping.csv`: Defines groups of flies (CSV format).
- `inference`: Directory for storing results of inference by a trained neural network.
- `inference/adult` or `inference/larva`: Stores inference results for adult/larva flies.
- `inference/*/profile1`: The name of training profile indicating which trained network is used for the inference. The directory name is same as `network/*/profile1`.
- `inference/*/cf_r0.003_signals.npy`: ChangeFinder signal.
- `inference/*/probs`: Stores inference results of each fly in Numpy archive format. The number in file names indicates fly ID.
- `inference/*/probs.npz`: Numpy archive including inference results of all the flies.
- `inference/*/signals.npy`: Label diference signal.
- `mask.npy`: Definition of pixels of each fly in an original image. You can create this file with Sapphire's mask maker tab.
- `mask_params.json`: Parameters for creating the mask. You can create this file with Sapphire's mask maker tab.
- `network`: Stores neural networks trained for semantic segmentation.
- `network/adult` or `network/larva`: Stores networks for adult/larva flies.
- `network/*/profile1`: The name of training profile.
- `original`: Stores original images.

## Licence

MIT license.
