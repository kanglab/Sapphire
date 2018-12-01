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
                            id='larva-dropdown',
                            placeholder='Select a larva data...',
                            clearable=False,
                        ),
                        dcc.Dropdown(
                            id='adult-dropdown',
                            placeholder='Select a adult data...',
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

                    html.Div(id='org-image', style={'display': 'table'}),

                    html.Div(id='label-and-prob', style={'display': 'table'}),

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


# =================================================
#  Initialize env-dropdown when opening the page.
# =================================================
@app.callback(
        Output('env-dropdown', 'options'),
        [Input('data-root', 'children')])
def callback(data_root):

    imaging_envs = [os.path.basename(i)
            for i in sorted(glob.glob(os.path.join(data_root, '*')))]

    return [{'label': i, 'value': i} for i in imaging_envs]


# =================================================================
#  Initialize detect-target.
# =================================================================
@app.callback(
        Output('detect-target', 'value'),
        [Input('env-dropdown', 'value')],
        [State('data-root', 'children')])
def callback(env, data_root):
    # Guard
    if env is None:
        print(1)
        return
    if not os.path.exists(os.path.join(data_root, env, 'config.json')):
        print(2)
        return

    with open(os.path.join(data_root, env, 'config.json')) as f:
        config = json.load(f)

    if config['detect'] == 'pupa&eclo':
        print(3)
        return 'v1'
    elif config['detect'] == 'death':
        print(4)
        return 'v2'
    else:
        print(5)
        return


# ======================================================
#  Initialize larva-dropdown.
# ======================================================
@app.callback(
        Output('larva-dropdown', 'disabled'),
        [Input('detect-target', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value')])
def callback(detect, data_root, env):
    if env is None:
        return

    if detect == 'v1':

        return False

    elif detect == 'v2':

        return True


@app.callback(
        Output('larva-dropdown', 'options'),
        [Input('detect-target', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value')])
def callback(detect, data_root, env):
    if env is None:
        return []

    if detect == 'v1':

        results = [os.path.basename(i)
                for i in sorted(glob.glob(os.path.join(
                    data_root, env, 'inference', 'larva', '*')))
                if os.path.isdir(i)]

        return [{'label': i, 'value': i} for i in results]

    elif detect == 'v2':

        return []


@app.callback(
        Output('larva-dropdown', 'value'),
        [Input('larva-dropdown', 'options')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value')])
def callback(_, data_root, env):
    if env is None:
        return None

    return None


# ======================================================
#  Initialize adult-dropdown.
# ======================================================
@app.callback(
        Output('adult-dropdown', 'options'),
        [Input('detect-target', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value')])
def callback(detect, data_root, env):
    if env is None:
        return []

    results = [os.path.basename(i)
            for i in sorted(glob.glob(os.path.join(
                data_root, env, 'inference', 'adult', '*')))
            if os.path.isdir(i)]

    return [{'label': i, 'value': i} for i in results]


@app.callback(
        Output('adult-dropdown', 'value'),
        [Input('adult-dropdown', 'options')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value')])
def callback(_, data_root, env):
    if env is None:
        return None

    return None


# =====================================================
#  Initialize the maximum value of the well-selector.
# =====================================================
@app.callback(
        Output('well-selector', 'max'),
        [Input('env-dropdown', 'value')],
        [State('data-root', 'children')])
def callback(env, data_root):
    if env is None or data_root is None:
        return

    with open(os.path.join(data_root, env, 'mask_params.json')) as f:
        params = json.load(f)

    return params['n-rows'] * params['n-plates'] * params['n-clms'] - 1
        

# ====================================================
#  Initialize the current value of the well-selector
#  when selecting a value on the well-slider.
# ====================================================
@app.callback(
        Output('well-selector', 'value'),
        [Input('well-slider', 'value')])
def callback(well_idx):
    return well_idx


# ===================================================
#  Initialize the maximum value of the well-slider.
# ===================================================
@app.callback(
        Output('well-slider', 'max'),
        [Input('env-dropdown', 'value')],
        [State('data-root', 'children')])
def callback(env, data_root):
    if env is None or data_root is None:
        return

    with open(os.path.join(data_root, env, 'mask_params.json')) as f:
        params = json.load(f)

    return params['n-rows'] * params['n-plates'] * params['n-clms'] - 1


# =======================================================
#  Initialize the current value of the well-slider
#  when selecting a dataset
#  or when clicking a data point in the summary-graph
#  or when selecting a result directory to draw graphs.
# =======================================================
@app.callback(
        Output('well-slider', 'value'),
        [Input('env-dropdown', 'value'),
         Input('summary-graph', 'clickData'),
         Input('larva-dropdown', 'value'),
         Input('adult-dropdown', 'value')],
        [State('well-slider', 'value')])
def callback(_, click_data, larva_data, adult_data, well_idx):
    if click_data is None:
        return well_idx

    return int(click_data['points'][0]['text'])


# =====================================================
#  Initialize the maximum value of the time-selector.
# =====================================================
@app.callback(
        Output('time-selector', 'max'),
        [Input('env-dropdown', 'value')],
        [State('data-root', 'children')])
def callback(env, data_root):
    if env is None:
        return

    return len(glob.glob(
            os.path.join(data_root, env, 'original', '*.jpg'))) - 2


# ====================================================
#  Initialize the current value of the time-selector
#  when selecting a value on the time-slider.
# ====================================================
@app.callback(
        Output('time-selector', 'value'),
        [Input('time-slider', 'value')])
def callback(timestep):
    return timestep


# ===================================================
#  Initialize the maximum value of the time-slider.
# ===================================================
@app.callback(
        Output('time-slider', 'max'),
        [Input('env-dropdown', 'value')],
        [State('data-root', 'children')])
def callback(env, data_root):
    if env is None:
        return 100

    return len(glob.glob(
            os.path.join(data_root, env, 'original', '*.jpg'))) - 2


# ======================================================
#  Initialize the current value of the time-slider
#  when selecting a dataset
#  or when clicking a data point in the summary-graph.
# ======================================================
@app.callback(
        Output('time-slider', 'value'),
        [Input('env-dropdown', 'value'),
         Input('larva-dropdown', 'value'),
         Input('adult-dropdown', 'value'),
         Input('summary-graph', 'clickData')],
        [State('time-slider', 'value')])
def callback(_, larva_data, adult_data, click_data, time):
    if click_data is None:
        return time

    return click_data['points'][0]['x']


# ========================
#  Update the org-image.
# ========================
@app.callback(
        Output('org-image', 'children'),
        [Input('time-selector', 'value'),
         Input('well-selector', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value')])
def callback(time, well_idx, data_root, env):

    # Exception handling
    if env is None:
        return

    # Load the mask
    mask = np.load(os.path.join(data_root, env, 'mask.npy'))

    # Load an original image
    orgimg_paths = sorted(glob.glob(
            os.path.join(data_root, env, 'original', '*.jpg')))
    orgimg1 = np.array(
            PIL.Image.open(orgimg_paths[time]).convert('L'), dtype=np.uint8)
    orgimg2 = np.array(
            PIL.Image.open(orgimg_paths[time+1]).convert('L'), dtype=np.uint8)

    # Cut out an well image from the original image
    r, c = np.where(mask == well_idx)
    orgimg1 = orgimg1[r.min():r.max(), c.min():c.max()]
    orgimg2 = orgimg2[r.min():r.max(), c.min():c.max()]
    orgimg1 = PIL.Image.fromarray(orgimg1)
    orgimg2 = PIL.Image.fromarray(orgimg2)

    # Buffer the well image as byte stream
    buf1 = io.BytesIO()
    buf2 = io.BytesIO()
    orgimg1.save(buf1, format='JPEG')
    orgimg2.save(buf2, format='JPEG')

    return [
            html.Div('Original Image'),
            html.Img(
                src='data:image/jpeg;base64,{}'.format(
                        base64.b64encode(buf1.getvalue()).decode('utf-8')),
                style={
                    'background': '#555555',
                    'height': '80px',
                    'width': '80px',
                    'padding': '5px',
                    'display': 'inline-block',
                },
            ),
            html.Img(
                src='data:image/jpeg;base64,{}'.format(
                        base64.b64encode(buf2.getvalue()).decode('utf-8')),
                style={
                    'background': '#555555',
                    'height': '80px',
                    'width': '80px',
                    'padding': '5px',
                    'display': 'inline-block',
                },
            ),
        ]


# =============================
#  Update the label-and-prob.
# =============================
@app.callback(
        Output('label-and-prob', 'children'),
        [Input('time-selector', 'value'),
         Input('well-selector', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('detect-target', 'value'),
         State('larva-dropdown', 'value'),
         State('adult-dropdown', 'value')])
def callback(time, well_idx, data_root, env, detect, larva_data, adult_data):
    # Guard
    if env is None or adult_data is None:
        return

    data = []

    if detect == 'v1':

        # Load a npz file storing prob images
        # and get a prob image
        larva_probs = np.load(os.path.join(
                data_root, env, 'inference', 'larva', larva_data, 'probs',
                '{:03d}.npz'.format(well_idx)))['arr_0'].astype(np.int32)
        adult_probs = np.load(os.path.join(
                data_root, env, 'inference', 'adult', adult_data, 'probs',
                '{:03d}.npz'.format(well_idx)))['arr_0'].astype(np.int32)

        larva_prob_img1 = PIL.Image.fromarray(
                larva_probs[time] / 100 * 255).convert('L')
        larva_prob_img2 = PIL.Image.fromarray(
                larva_probs[time+1] / 100 * 255).convert('L')
        adult_prob_img1 = PIL.Image.fromarray(
                adult_probs[time] / 100 * 255).convert('L')
        adult_prob_img2 = PIL.Image.fromarray(
                adult_probs[time+1] / 100 * 255).convert('L')

        larva_label_img1 = PIL.Image.fromarray(
                ((larva_probs[time] > THETA) * 255).astype(np.uint8)).convert('L')
        larva_label_img2 = PIL.Image.fromarray(
                ((larva_probs[time+1] > THETA) * 255).astype(np.uint8)).convert('L')
        adult_label_img1 = PIL.Image.fromarray(
                ((adult_probs[time] > THETA) * 255).astype(np.uint8)).convert('L')
        adult_label_img2 = PIL.Image.fromarray(
                ((adult_probs[time+1] > THETA) * 255).astype(np.uint8)).convert('L')

        # Buffer the well image as byte stream
        larva_prob_buf1 = io.BytesIO()
        larva_prob_buf2 = io.BytesIO()
        larva_label_buf1 = io.BytesIO()
        larva_label_buf2 = io.BytesIO()
        larva_prob_img1.save(larva_prob_buf1, format='JPEG')
        larva_prob_img2.save(larva_prob_buf2, format='JPEG')
        larva_label_img1.save(larva_label_buf1, format='JPEG')
        larva_label_img2.save(larva_label_buf2, format='JPEG')

        adult_prob_buf1 = io.BytesIO()
        adult_prob_buf2 = io.BytesIO()
        adult_label_buf1 = io.BytesIO()
        adult_label_buf2 = io.BytesIO()
        adult_prob_img1.save(adult_prob_buf1, format='JPEG')
        adult_prob_img2.save(adult_prob_buf2, format='JPEG')
        adult_label_img1.save(adult_label_buf1, format='JPEG')
        adult_label_img2.save(adult_label_buf2, format='JPEG')

        data = data + [
            html.Div('Larva'),
            html.Div([
                html.Img(
                    src='data:image/jpeg;base64,{}'.format(
                            base64.b64encode(
                                larva_label_buf1.getvalue()).decode('utf-8')),
                    style={
                        'background': '#555555',
                        'height': '80px',
                        'width': '80px',
                        'padding': '5px',
                        'display': 'inline-block',
                    },
                ),
                html.Img(
                    src='data:image/jpeg;base64,{}'.format(
                            base64.b64encode(
                                larva_label_buf2.getvalue()).decode('utf-8')),
                    style={
                        'background': '#555555',
                        'height': '80px',
                        'width': '80px',
                        'padding': '5px',
                        'display': 'inline-block',
                    },
                ),
            ]),
            html.Div([
                html.Img(
                    src='data:image/jpeg;base64,{}'.format(
                            base64.b64encode(
                                larva_prob_buf1.getvalue()).decode('utf-8')),
                    style={
                        'background': '#555555',
                        'height': '80px',
                        'width': '80px',
                        'padding': '5px',
                        'display': 'inline-block',
                    },
                ),
                html.Img(
                    src='data:image/jpeg;base64,{}'.format(
                            base64.b64encode(
                                larva_prob_buf2.getvalue()).decode('utf-8')),
                    style={
                        'background': '#555555',
                        'height': '80px',
                        'width': '80px',
                        'padding': '5px',
                        'display': 'inline-block',
                    },
                ),
            ]),
            ]

    # Load a npz file storing prob images
    # and get a prob image
    adult_probs = np.load(os.path.join(
            data_root, env, 'inference', 'adult', adult_data, 'probs',
            '{:03d}.npz'.format(well_idx)))['arr_0'].astype(np.int32)

    adult_prob_img1 = PIL.Image.fromarray(
            adult_probs[time] / 100 * 255).convert('L')
    adult_prob_img2 = PIL.Image.fromarray(
            adult_probs[time+1] / 100 * 255).convert('L')

    adult_label_img1 = PIL.Image.fromarray(
            ((adult_probs[time] > THETA) * 255).astype(np.uint8)).convert('L')
    adult_label_img2 = PIL.Image.fromarray(
            ((adult_probs[time+1] > THETA) * 255).astype(np.uint8)).convert('L')

    # Buffer the well image as byte stream
    adult_prob_buf1 = io.BytesIO()
    adult_prob_buf2 = io.BytesIO()
    adult_label_buf1 = io.BytesIO()
    adult_label_buf2 = io.BytesIO()
    adult_prob_img1.save(adult_prob_buf1, format='JPEG')
    adult_prob_img2.save(adult_prob_buf2, format='JPEG')
    adult_label_img1.save(adult_label_buf1, format='JPEG')
    adult_label_img2.save(adult_label_buf2, format='JPEG')

    return data + [
            html.Div('Adult'),
            html.Div([
                html.Img(
                    src='data:image/jpeg;base64,{}'.format(
                            base64.b64encode(
                                adult_label_buf1.getvalue()).decode('utf-8')),
                    style={
                        'background': '#555555',
                        'height': '80px',
                        'width': '80px',
                        'padding': '5px',
                        'display': 'inline-block',
                    },
                ),
                html.Img(
                    src='data:image/jpeg;base64,{}'.format(
                            base64.b64encode(
                                adult_label_buf2.getvalue()).decode('utf-8')),
                    style={
                        'background': '#555555',
                        'height': '80px',
                        'width': '80px',
                        'padding': '5px',
                        'display': 'inline-block',
                    },
                ),
            ]),
            html.Div([
                html.Img(
                    src='data:image/jpeg;base64,{}'.format(
                            base64.b64encode(
                                adult_prob_buf1.getvalue()).decode('utf-8')),
                    style={
                        'background': '#555555',
                        'height': '80px',
                        'width': '80px',
                        'padding': '5px',
                        'display': 'inline-block',
                    },
                ),
                html.Img(
                    src='data:image/jpeg;base64,{}'.format(
                            base64.b64encode(
                                adult_prob_buf2.getvalue()).decode('utf-8')),
                    style={
                        'background': '#555555',
                        'height': '80px',
                        'width': '80px',
                        'padding': '5px',
                        'display': 'inline-block',
                    },
                ),
            ]),
            html.Div('Image at "t"',
                    style={'display': 'inline-block', 'margin-right': '25px'}),
            html.Div('"t+1"', style={'display': 'inline-block'}),
        ]


# ===========================
#  Update the current-well.
# ===========================
@app.callback(
        Output('current-well', 'src'),
        [Input('time-selector', 'value'),
         Input('well-selector', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value')])
def callback(time, well_idx, data_root, env):
    # Guard
    if env is None:
        return ''

    # Load the mask
    mask = np.load(os.path.join(data_root, env, 'mask.npy'))

    # Load an original image
    orgimg_paths = sorted(glob.glob(
            os.path.join(data_root, env, 'original', '*.jpg')))
    org_img = np.array(
            PIL.Image.open(orgimg_paths[time]).convert('RGB'), dtype=np.uint8)

    r, c = np.where(mask == well_idx)
    org_img[r.min():r.max(), c.min():c.max(), [0, ]] = 255
    org_img[r.min():r.max(), c.min():c.max(), [1, 2]] = 0
    org_img = PIL.Image.fromarray(org_img).convert('RGB')

    # Buffer the well image as byte stream
    buf = io.BytesIO()
    org_img.save(buf, format='JPEG')

    return 'data:image/jpeg;base64,{}'.format(
            base64.b64encode(buf.getvalue()).decode('utf-8'))


# =========================================
#  Update the figure in the signal-graph.
# =========================================
@app.callback(
        Output('signal-graph', 'figure'),
        [Input('well-selector', 'value'),
         Input('threshold-slider1', 'value'),
         Input('time-selector', 'value'),
         Input('weight-check', 'values'),
         Input('filter-check', 'values'),
         Input('gaussian-size', 'value'),
         Input('gaussian-sigma', 'value')],
        [State('signal-graph', 'figure'),
         State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('detect-target', 'value'),
         State('larva-dropdown', 'value'),
         State('adult-dropdown', 'value')])
def callback(well_idx, coef, time, weight, checks, size, sigma,
        figure, data_root, env, detect, larva, adult):
    # Guard
    if env is None:
        return {'data': []}

    if len(figure['data']) == 0:
        x, y = 0, 0
    else:
        x, y = time, figure['data'][3]['y'][time]

    larva_data = []
    adult_data = []
    manual_data = []
    common_data = []

    if detect == 'v1':

        # Load the data
        larva_diffs = np.load(os.path.join(
                data_root, env, 'inference',
                'larva', larva, 'signals.npy')).T

        # Compute thresholds
        threshold = my_threshold.entire_stats(larva_diffs, coef=coef)

        # Scan the signal from the right hand side.
        auto_evals = (larva_diffs.shape[1]
                - (np.fliplr(larva_diffs) > threshold).argmax(axis=1))

        # If the signal was not more than the threshold.
        auto_evals[auto_evals == larva_diffs.shape[1]] = 0

        if os.path.exists(
                os.path.join(data_root, env, 'original', 'pupariation.csv')):

            manual_evals = np.loadtxt(
                    os.path.join(
                        data_root, env, 'original', 'pupariation.csv'),
                    dtype=np.uint16, delimiter=',').flatten()

            manual_data = [
                {
                    # Manual evaluation time (vertical line)
                    'x': [manual_evals[well_idx], manual_evals[well_idx]],
                    'y': [0, larva_diffs.max()],
                    'mode': 'lines',
                    'name': 'Manual',
                    'line': {'width': 5, 'color': '#4169e1'},
                    'yaxis': 'y2',
                },
            ]

        larva_data = manual_data + [
                {
                    # Signal
                    'x': list(range(len(larva_diffs[0, :]))),
                    'y': list(larva_diffs[well_idx]),
                    'mode': 'lines',
                    'marker': {'color': '#4169e1'},
                    'name': 'Signal',
                    'opacity':1.0,
                    'yaxis': 'y2',
                },
                {
                    # Threshold (horizontal line)
                    'x': [0, len(larva_diffs[0, :])],
                    'y': [threshold[well_idx, 0], threshold[well_idx, 0]],
                    'mode': 'lines',
                    'name': 'Threshold',
                    'line': {'width': 2, 'color': '#4169e1'},
                    'yaxis': 'y2',
                },
                {
                    # Auto evaluation time (vertical line)
                    'x': [auto_evals[well_idx], auto_evals[well_idx]],
                    'y': [0, larva_diffs.max()],            
                    'name': 'Auto',
                    'mode':'lines',
                    'line': {'width': 4, 'color': '#4169e1', 'dash': 'dot'},
                    'yaxis': 'y2',
                },
            ]

    # Load the data
    adult_diffs = np.load(os.path.join(
            data_root, env, 'inference',
            'adult', adult, 'signals.npy')).T

    # Compute thresholds
    threshold = my_threshold.entire_stats(adult_diffs, coef=coef)

    auto_evals = (adult_diffs > threshold).argmax(axis=1)

    if os.path.exists(
            os.path.join(data_root, env, 'original', 'pupariation.csv')):

        manual_evals = np.loadtxt(
                os.path.join(
                    data_root, env, 'original', 'pupariation.csv'),
                dtype=np.uint16, delimiter=',').flatten()

        manual_data = [
            {
                # Manual evaluation time (vertical line)
                'x': [manual_evals[well_idx], manual_evals[well_idx]],
                'y': [0, adult_diffs.max()],
                'mode': 'lines',
                'name': 'Manual',
                'line': {'width': 5, 'color': '#20b2aa'},
            },
        ]

    adult_data = manual_data + [
            {
                # Signal
                'x': list(range(len(adult_diffs[0, :]))),
                'y': list(adult_diffs[well_idx]),
                'mode': 'lines',
                'marker': {'color': '#20b2aa'},
                'name': 'Signal',
                'opacity':1.0,
            },
            {
                # Threshold (horizontal line)
                'x': [0, len(adult_diffs[0, :])],
                'y': [threshold[well_idx, 0], threshold[well_idx, 0]],
                'mode': 'lines',
                'name': 'Threshold',
                'line': {'width': 2, 'color': '#20b2aa'},
            },
            {
                # Auto evaluation time (vertical line)
                'x': [auto_evals[well_idx], auto_evals[well_idx]],
                'y': [0, adult_diffs.max()],            
                'name': 'Auto',
                'mode':'lines',
                'line': {'width': 4, 'color': '#20b2aa', 'dash': 'dot'},
            },
        ]

    common_data = [
            {
                # Selected data point
                'x': [x],
                'y': [y],
                'mode': 'markers',
                'marker': {'size': 10, 'color': '#ff0000'},
                'name': '',
                'yaxis': 'y2',
            },
        ]

    data = larva_data + adult_data + common_data

    return {
            'data': data,
            'layout': {
                    'title':
                        'Threshold: {:.1f}'.format(threshold[well_idx, 0]) +  \
                         '={:.1f}'.format(larva_diffs.mean()) +  \
                         '{:+.1f}'.format(coef) +  \
                         '*{:.1f}'.format(larva_diffs.std()),
                    'font': {'size': 15},
                    'xaxis': {
                        'title': 'Time step',
                        'tickfont': {'size': 15},
                    },
                    'yaxis2': {
                        'title': 'Diff. of ROI',
                        'tickfont': {'size': 15},
                        'overlaying':'y',
                        'range':[0, larva_diffs.max()],
                    },
                    'yaxis1': {
                        'title':'Diff. of Luminance',
                        'tickfont': {'size': 15},
                        'side':'right',
                        'range':[0, adult_diffs.max()],
                    },
                'showlegend': False,
                'hovermode': 'closest',
                'margin': go.layout.Margin(l=50, r=70, b=50, t=50, pad=0),
            },
        }


if __name__ == '__main__':
    app.run_server(debug=True)
