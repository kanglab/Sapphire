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


def entire_stats(signals, coef=2):

    threshold = signals.mean() + coef * signals.std()
    thresholds = np.array([threshold] * len(signals))

    return np.expand_dims(thresholds, axis=-1)
