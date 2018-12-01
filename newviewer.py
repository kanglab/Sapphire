# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :
# vim: set foldmethod=marker commentstring=\ \ #\ %s :
#
# Author:    Taishi Matsumura
# Created:   2018-09-08
#
# Copyright (C) 2018 Taishi Matsumura
#
import io
import os
import glob
import dash
import json
import base64
import zipfile
import datetime
import PIL.Image
import dash_auth
import dash_table
import numpy as np
import pandas as pd
import scipy.signal
import my_threshold
import flask_caching
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go


DATA_ROOT = '//133.24.88.18/sdb/Research/Drosophila/data/TsukubaRIKEN/'
THETA = 50



app = dash.Dash('Sapphire')
app.css.append_css(
        {'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})
cache = flask_caching.Cache()
cache.init_app(
        app.server, config={'CACHE_TYPE': 'filesystem', 'CACHE_DIR': 'cache/'})


# ================================
#  Definition of the viewer page
# ================================
app.layout = html.Div([
    html.Header([html.H1('Sapphire', style={'margin': '10px'})]),
    dcc.Tabs(id='tabs', value='tab-1', children=[
        dcc.Tab(id='tab-1', label='Tab 1', value='tab-1', children=[
            html.Div([
                html.Div([
                    'Dataset:',
                    html.Br(),
                    html.Div([
                        dcc.Dropdown(
                            id='env-dropdown',
                            placeholder='Select a dataset...',
                            clearable=False,
                        ),
                        ],
                        style={
                            'display': 'inline-block',
                            'width': '200px',
                            'vertical-align': 'middle',
                        },
                    ),
                    dcc.RadioItems(
                        id='detect-target',
                        options=[
                            {
                                'label': 'Pupariation&Eclosion',
                                'value': 'v1',
                                'disabled': True,
                            },
                            {
                                'label': 'Death',
                                'value': 'v2',
                                'disabled': True,
                            },
                        ],
                    ),
                    'Inference Data:',
                    html.Br(),
                    html.Div([
                        dcc.Dropdown(
                            id='result-dropdown',
                            placeholder='Select a result dir...',
                            clearable=False,
                        ),
                        ],
                        style={
                            'display': 'inline-block',
                            'width': '200px',
                            'vertical-align': 'middle',
                        },
                    ),
                    html.Br(),
                    'Well Index:',
                    html.Br(),
                    html.Div([
                        dcc.Input(
                            id='well-selector',
                            type='number',
                            value=0,
                            min=0,
                            size=5,
                        ),
                        ],
                        style={
                            'display': 'inline-block',
                        },
                    ),
                    html.Br(),
                    html.Div([
                        dcc.Slider(
                            id='well-slider',
                            value=0,
                            min=0,
                            step=1,
                        ),
                        ],
                        style={
                            'display': 'inline-block',
                            'width': '200px',
                        },
                    ),
                    html.Br(),
                    'Time Step:',
                    html.Br(),
                    html.Div([
                            dcc.Input(
                                id='time-selector',
                                type='number',
                                value=0,
                                min=0,
                                size=5,
                            ),
                        ],
                        style={
                            'display': 'inline-block',
                        },
                    ),
                    html.Br(),
                    html.Div([
                        dcc.Slider(
                            id='time-slider',
                            value=0,
                            min=0,
                            step=1,
                        ),
                        ],
                        style={
                            'display': 'inline-block',
                            'width': '200px',
                        },
                    ),
                    html.Br(),

                    'Smoothing:',
                    dcc.Checklist(
                        id='filter-check',
                        options=[{'label': 'Apply', 'value': True}],
                        values=[],
                    ),
                    'Size:',
                    dcc.Input(
                        id='gaussian-size',
                        type='number',
                        value=10,
                        min=0,
                        size=5,
                    ),
                    html.Br(),
                    'Sigma:',
                    dcc.Input(
                        id='gaussian-sigma',
                        type='number',
                        value=5,
                        min=0,
                        size=5,
                        step=0.1,
                    ),
                    html.Br(),
                    dcc.Checklist(
                        id='weight-check',
                        options=[{'label': 'Signal Weight', 'value': True}],
                        values=[],
                    ),
                    ],
                    style={
                        'display': 'inline-block',
                        'margin': '10px 10px',
                    },
                ),
                html.Div([
                    dcc.Checklist(
                        id='blacklist-check',
                        options=[{
                            'label': 'Black List',
                            'value': 'checked',
                            'disabled': True,
                        }],
                        values=[],
                        style={'display': 'table'},
                    ),
                    html.Div([
                        'Original Image',
                        html.Img(
                            id='t-image',
                            style={
                                'background': '#555555',
                                'height': '80px',
                                'width': '80px',
                                'padding': '5px',
                                'display': 'block',
                            },
                        ),
                        html.Img(
                            id='t+1-image',
                            style={
                                'background': '#555555',
                                'height': '80px',
                                'width': '80px',
                                'padding': '5px',
                                'display': 'block',
                            },
                        ),
                    ], style={'display': 'table'}),
                    html.Div([
                        'Label',
                        html.Img(
                            id='t-label',
                            style={
                                'background': '#555555',
                                'height': '80px',
                                'width': '80px',
                                'padding': '5px',
                                'display': 'block',
                            },
                        ),
                        html.Img(
                            id='t+1-label',
                            style={
                                'background': '#555555',
                                'height': '80px',
                                'width': '80px',
                                'padding': '5px',
                                'display': 'block',
                            },
                        ),
                    ], style={'display': 'table'}),
                    html.Div([
                        'Probability',
                        html.Img(
                            id='t-prob',
                            style={
                                'background': '#555555',
                                'height': '80px',
                                'width': '80px',
                                'padding': '5px',
                                'display': 'block',
                            },
                        ),
                        html.Img(
                            id='t+1-prob',
                            style={
                                'background': '#555555',
                                'height': '80px',
                                'width': '80px',
                                'padding': '5px',
                                'display': 'block',
                            },
                        ),
                    ], style={'display': 'table'}),
                    html.Div(['Image at "t"'], style={'display': 'table'}),
                    html.Div(['"t+1"'], style={'display': 'table'}),
                    ],
                    style={
                        'display': 'inline-block',
                        'margin-right': '5px',
                        'margin-left': '5px',
                    },
                ),

                html.Div([
                        html.Img(
                            id='current-well',
                            style={
                                'background': '#555555',
                                'height': 'auto',
                                'width': '200px',
                                'padding': '5px',
                            },
                        ),
                    ],
                    style={
                        'display': 'inline-block',
                        'margin-left': '5px',
                    },
                ),

                html.Div([
                    'Data root :',
                    html.Div(DATA_ROOT, id='data-root'),
                    html.Br(),
                    'Imaging environment :',
                    html.Div(id='current-env'),
                    html.Br(),
                    'File name :',
                    html.Div(id='current-csv'),
                    html.Br(),
                    'Current morpho :',
                    html.Div(id='current-morpho'),
                    html.Br(),
                    'Current result :',
                    html.Div(id='current-result'),
                    ],
                    style={
                        'display': 'none',
                        'vertical-align': 'top',
                        
                    },
                ),

                html.Div([
                    dcc.Slider(
                        id='threshold-slider1',
                        value=2,
                        min=-5,
                        max=10,
                        step=.1,
                        updatemode='mouseup',
                        vertical=True,
                    )],
                    style={
                        'display': 'inline-block',
                        'height': '300px',
                        'width': '10px',
                        'padding-bottom': '50px',
                        'margin-left': '30px',

                    },
                ),
                dcc.Graph(
                    id='signal-graph',
                    style={
                        'display': 'inline-block',
                        'height': '400px',
                    },
                ),
                html.Div([
                    dcc.Slider(
                        id='threshold-slider2',
                        value=600000,
                        min=0,
                        step=1,
                        updatemode='mouseup',
                        vertical=True,
                    )],
                    style={
                        'display': 'inline-block',
                        'height': '280px',
                        'width': '10px',
                        'padding-bottom': '50px',
                    },
                ),

            ],
            ),
            html.Div([
                dcc.Graph(
                    id='summary-graph',
                    style={
                        'display': 'inline-block',
                        'height': '400px',
                        'width': '25%',
                    },
                ),
                dcc.Graph(
                    id='error-hist',
                    style={
                        'display': 'inline-block',
                        'height': '400px',
                        'width': '25%',
                    },
                ),
                dcc.Graph(
                    id='summary-graph2',
                    style={
                        'display': 'inline-block',
                        'height': '400px',
                        'width': '25%',
                    },
                ),
                dcc.Graph(
                    id='error-hist2',
                    style={
                        'display': 'inline-block',
                        'height': '400px',
                        'width': '25%',
                    },
                ),
            ]),
            html.Div(id='dummy-div'),
        ]),
        dcc.Tab(id='tab-2', label='Tab 2', value='tab-2', children=[
            html.Div(
                [
                    html.H3('Timestamp'),
                    html.Div(id='timestamp-table'),
                ],
                style={
                    'display': 'inline-block',
                    'vertical-align': 'top',
                    'margin': '20px',
                    'width': '200px',
                },
            ),
            html.Div(
                [
                    html.H3('Manual Detection'),
                    html.Div(id='manual-table'),
                ],
                style={
                    'display': 'inline-block',
                    'vertical-align': 'top',
                    'margin': '20px',
                    'width': '500px',
                },
            ),
            html.Div(
                [
                    html.H3('Auto Detection'),
                    html.Div(id='auto-table'),
                ],
                style={
                    'display': 'inline-block',
                    'vertical-align': 'top',
                    'margin': '20px',
                    'width': '500px',
                },
            ),
        ], style={'width': '1200px'}),
    ]),
    html.Div(id='hidden-timestamp', style={'display': 'none'}),

], style={'width': '1600px',},)


# =========================================
#  Smoothing signals with gaussian window
# =========================================
def my_filter(signals, size=10, sigma=5):
    
    window = scipy.signal.gaussian(size, sigma)

    signals = np.array(
            [np.convolve(signal, window, mode='same')
                for signal in signals])

    return signals


if __name__ == '__main__':
    app.run_server(debug=True)
