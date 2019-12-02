# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :
# vim: set foldmethod=marker commentstring=\ \ #\ %s :
#
# Author:    Taishi Matsumura
# Created:   2019-12-02
#
# Copyright (C) 2019 Taishi Matsumura
#
import os
import numpy as np
import glob
import argparse
import tqdm.tqdm
from module import *

import keras
from keras import backend as K
from keras.utils import to_categorical


def TP(y_true, y_pred):
    y_true = K.argmax(y_true, axis=-1)
    y_pred = K.argmax(y_pred, axis=-1)
    return K.sum(K.cast(K.equal(y_true * y_pred, 1), K.floatx()))


def TN(y_true, y_pred):
    y_true = K.argmax(y_true, axis=-1)
    y_pred = K.argmax(y_pred, axis=-1)
    return K.sum(K.cast(K.equal(y_true + y_pred, 0), K.floatx()))


def FP(y_true, y_pred):
    y_true = K.argmax(y_true, axis=-1)
    y_pred = K.argmax(y_pred, axis=-1)
    return K.sum(K.cast(K.less(y_true, y_pred), K.floatx()))


def FN(y_true, y_pred):
    y_true = K.argmax(y_true, axis=-1)
    y_pred = K.argmax(y_pred, axis=-1)
    return K.sum(K.cast(K.greater(y_true, y_pred), K.floatx()))


def IoU(y_true, y_pred):
    return TP(y_true, y_pred)  \
            / (FN(y_true, y_pred) + TP(y_true, y_pred) + FP(y_true, y_pred))


def get_well_imgs(img, mask, n_wells):
    well_imgs = []
    for i in range(n_wells):
        rows, clms = np.where(mask == i)
        well_imgs.append(img[min(rows):max(rows), min(clms):max(clms)])
    well_imgs = np.array(well_imgs)

    return well_imgs.reshape(
            well_imgs.shape[0], well_imgs.shape[1], well_imgs.shape[2], 1)


def inference(orgimg_path):
    # ウェル画像の切り出し
    well_images = split(orgimg_path, n_wells, mask)
    
    # (n_wells, height, width) -> (n_wells, height, width, 1)
    well_images = np.expand_dims(well_images, axis=-1)
    
    # Zeropadding
    well_images = np.array([zeropadding(well_image, (56, 56)) for well_image in well_images])

    # データの正規化
    well_images = tf_normalize(well_images)

    # Inference
    return (100 * model.predict(well_images)).astype(np.uint8)


parser = argparse.ArgumentParser(description='Inference.')
parser.add_argument('inference_dataset_path', type=str, help='Put a path to a target dataset.')
parser.add_argument('trained_network_path', type=str, help='Put a path to a trained network.')
args = parser.parse_args()

assert os.path.exists(args.inference_dataset_path), 'The given path does not exists.'
assert os.path.exists(args.trained_network_path), 'The given path does not exists.'

inference_dataset_path = args.inference_dataset_path
trained_network_path = args.trained_network_path

# 訓練済みネットワークがあるディレクトリの名前（target_dir）
target_dir = os.path.basename(os.path.dirname(trained_network_path))

# target_dir があるディレクトリの名前（morpho）
morpho = os.path.basename(os.path.dirname(os.path.dirname(trained_network_path)))



# ============
#  推論
# ============
# マスクのロード
mask = np.load(os.path.join(inference_dataset_path, 'mask.npy'))

# ウェル数のロード
with open(os.path.join(inference_dataset_path, 'mask_params.json')) as f:
    params = json.load(f)
n_wells = params['n-rows'] * params['n-clms'] * params['n-plates']

# 訓練済みネットワークのロード
model = keras.models.load_model(trained_network_path,
        custom_objects={'IoU': IoU, 'TP': TP, 'FP': FP, 'FN': FN, 'TN': TN})

# オリジナル画像のファイルパス
orgimg_paths = sorted(glob.glob(os.path.join(glob.escape(inference_dataset_path), 'original', '*.jpg')))
# orgimg_paths = orgimg_paths[:5]

probs = []
# for each frame
for orgimg_path in tqdm(orgimg_paths):
    probs.append(inference(orgimg_path))
    

# ==============
#  データの作成
# ==============
# Tranform float probs into percentage
probs = np.array(probs).reshape(len(orgimg_paths), n_wells, 56, 56, 2)

# only probs which the animal is in the pixel
probs = probs[:, :, :, :, 1]

# Wells first (wells, org_imgs, height, width)
probs = probs.transpose(1, 0, 2, 3)

# シグナルの作成
signals = (np.diff((probs >= 50).astype(np.int8), axis=1)**2).sum(-1).sum(-1).T


# ==============
#  保存
# ==============
out_dir = os.path.join(inference_dataset_path, 'inference', morpho, target_dir)
os.makedirs(os.path.join(out_dir, 'probs'), exist_ok=True)

# probs の保存
for well_idx in range(n_wells):
    np.savez_compressed(os.path.join(out_dir, 'probs', '{:03d}.npz'.format(well_idx)), probs[well_idx])

np.savez_compressed(os.path.join(out_dir, 'probs.npz'), probs)

# シグナルの保存
np.save(os.path.join(out_dir, 'signals.npy'), signals)
