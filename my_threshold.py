# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :
# vim: set foldmethod=marker commentstring=\ \ #\ %s :
#
# Author:    Taishi Matsumura
# Created:   2018-11-03
#
# Copyright (C) 2018 Taishi Matsumura
#
import numpy as np


def minmax(signals, coef=1):

    mins = signals.min(axis=1)
    maxs = signals.max(axis=1)
    thresholds = mins + (maxs - mins) / 2
    thresholds = coef * thresholds

    return np.expand_dims(thresholds, axis=-1)


def entire_stats(signals, coef=2):

    threshold = signals.mean() + coef * signals.std()
    thresholds = np.array([threshold] * len(signals))

    return np.expand_dims(thresholds, axis=-1)


def n_times_mean(signals, coef=2):

    thresholds = coef * signals.mean(axis=1)

    return np.expand_dims(thresholds, axis=-1)


def n_times_nonzero_mean(signals, coef=2):

    signals = signals.astype(float)

    signals[signals <= 0] = np.nan

    thresholds = coef * np.nanmean(signals, axis=1)

    thresholds[np.isnan(thresholds)] = 0

    return np.expand_dims(thresholds, axis=-1)
