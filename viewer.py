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
                    html.Br(),
                    'Manual Detection File (CSV):',
                    html.Br(),
                    html.Div([
                        dcc.Dropdown(
                            id='csv-dropdown',
                            placeholder='Select a CSV file...',
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
                    'Target Morphology:',
                    html.Br(),
                    html.Div([
                        dcc.Dropdown(
                            id='morpho-dropdown',
                            placeholder='Select a morpho...',
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
                    'Thresholding:',
                    html.Br(),
                    dcc.RadioItems(
                        id='rise-or-fall',
                        options=[
                            {'label': 'Rising Up', 'value': 'rise'},
                            {'label': 'Falling Down', 'value': 'fall'},
                        ],
                        value='rise',
                    ),
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
                            # 'margin-left': '20px',
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
                    'Sigma:',
                    dcc.Input(
                        id='gaussian-sigma',
                        type='number',
                        value=5,
                        min=0,
                        size=5,
                        step=0.1,
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
                    html.Div('Original Image', style={'display': 'table'}),
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
                    html.Div('Label', style={'display': 'table'}),
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
                    html.Div('Probability', style={'display': 'table'}),
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
                    html.Div(['Image at "t"'], style={'display': 'table'}),
                    ],
                    style={
                        'display': 'inline-block',
                        'margin-right': '5px',
                        'margin-left': '5px',
                    },
                ),
                html.Div([
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
                    html.Div('Label', style={'display': 'table'}),
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
                    html.Div('Probability', style={'display': 'table'}),
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
                        # 'display': 'inline-block',
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
                        #'width': '60%',
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
#  Initialize csv-dropdown when selecting an imaging environment.
# =================================================================
@app.callback(
        Output('csv-dropdown', 'options'),
        [Input('env-dropdown', 'value')],
        [State('data-root', 'children')])
def callback(env, data_root):
    if env is None:
        return []

    csvs = [os.path.basename(i)
            for i in sorted(glob.glob(os.path.join(
                data_root, env, 'original', '*.csv')))]

    return [{'label': i, 'value': i} for i in csvs]


# ======================================
#  Load a blacklist file and check it.
# ======================================
@app.callback(
        Output('blacklist-check', 'values'),
        [Input('well-selector', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value')])
def callback(well_idx, data_root, env):
    if well_idx is None or env is None:
        return []
    
    if not os.path.exists(os.path.join(data_root, env, 'blacklist.csv')):
        return []

    blacklist = np.loadtxt(
            os.path.join(data_root, env, 'blacklist.csv'),
            dtype=np.uint16, delimiter=',').flatten() == 1

    if blacklist[well_idx]:
        return 'checked'

    else:
        return []


# ===================================================================
#  Initialize morpho-dropdown when selecting an imaging environment.
# ===================================================================
@app.callback(
        Output('morpho-dropdown', 'options'),
        [Input('env-dropdown', 'value')],
        [State('data-root', 'children')])
def callback(env, data_root):
    if env is None:
        return []

    npys = [os.path.basename(i)
            for i in sorted(glob.glob(os.path.join(
                data_root, env, 'inference', '*'))) if os.path.isdir(i)]

    return [{'label': i, 'value': i} for i in npys]


# ======================================================
#  Initialize result-dropdown when selecting a morpho.
# ======================================================
@app.callback(
        Output('result-dropdown', 'options'),
        [Input('morpho-dropdown', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value')])
def callback(morpho, data_root, env):
    if env is None:
        return []

    results = [os.path.basename(i)
            for i in sorted(glob.glob(os.path.join(
                data_root, env, 'inference', morpho, '*'))) if os.path.isdir(i)]

    return [{'label': i, 'value': i} for i in results]


# =======================================================================
#  Store image file names and their timestamps as json in a hidden div.
# =======================================================================
@app.callback(
        Output('hidden-timestamp', 'children'),
        [Input('env-dropdown', 'value')],
        [State('data-root', 'children')])
def callback(env, data_root):

    # Guard
    if env is None:
        return

    # Load an original image
    orgimg_paths = sorted(glob.glob(
            os.path.join(data_root, env, 'original', '*.jpg')))

    return pd.DataFrame([[
            os.path.basename(orgimg_path),
            datetime.datetime.fromtimestamp(os.stat(orgimg_path).st_mtime) \
                    .strftime('%Y-%m-%d %H:%M:%S')]
            for orgimg_path in orgimg_paths],
            columns=['frame', 'create time']).T.to_json()


# ======================================================================
#  Load a luminance signal file when selecting an imaging environment.
# ======================================================================
@app.callback(
        Output('dummy-div','children'),
        [Input('env-dropdown', 'value')],
        [State('data-root', 'children')])
def callback(env, data_root):
    return ''


# ==========================================================
#  Load a mask file when selecting an imaging environment.
# ==========================================================
@app.callback(
        Output('current-env', 'children'),
        [Input('env-dropdown', 'value')],
        [State('data-root', 'children')])
def callback(env, data_root):
    return env


# ======================================
#  Load a csv file when selecting csv.
# ======================================
@app.callback(
        Output('current-csv', 'children'),
        [Input('csv-dropdown', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value')])
def callback(csv, data_root, env):
    return csv


# =========================================================
#  Initialize the current-morpho when selecting a morpho.
# =========================================================
@app.callback(
        Output('current-morpho', 'children'),
        [Input('morpho-dropdown', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value')])
def callback(morpho, data_root, env):
    if env is None or morpho is None:
        return
    return morpho


# =================================
#  Initialize the current-result.
# =================================
@app.callback(
        Output('current-result', 'children'),
        [Input('result-dropdown', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('morpho-dropdown', 'value')])
def callback(result, data_root, env, morpho):
    if env is None or morpho is None:
        return

    return result


# ========================================================
#  Initialize the maximum value of the threshold-slider2
#  after loading a signal file.
# ========================================================
@app.callback(
        Output('threshold-slider2', 'max'),
        [Input('current-result', 'children')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('morpho-dropdown', 'value')])
def callback(result, data_root, env, morpho):
    if env is None or morpho is None:
        return

    if not os.path.exists(os.path.join(
            data_root, env, 'luminance_signals.npy')):
        return

    return np.load(
            os.path.join(data_root, env, 'luminance_signals.npy')).max()


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
         Input('current-result', 'children')],
        [State('well-slider', 'value')])
def callback(_, click_data, result, well_idx):
    if click_data is None or result is None:
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
         Input('current-result', 'children'),
         Input('summary-graph', 'clickData')],
        [State('time-slider', 'value')])
def callback(_, result, click_data, time):
    if click_data is None or result is None:
        return time

    return click_data['points'][0]['x']


# =========================================
#  Update the figure in the signal-graph.
# =========================================
@app.callback(
        Output('signal-graph', 'figure'),
        [Input('well-selector', 'value'),
         Input('threshold-slider1', 'value'),
         Input('threshold-slider2', 'value'),
         Input('rise-or-fall', 'value'),
         Input('time-selector', 'value'),
         Input('filter-check', 'values'),
         Input('gaussian-sigma', 'value')],
        [State('signal-graph', 'figure'),
         State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('csv-dropdown', 'value'),
         State('morpho-dropdown', 'value'),
         State('result-dropdown', 'value')])
def callback(well_idx, coef, threshold2, positive_or_negative, time, checks,
        sigma, figure, data_root, env, csv, morpho, result):

    # Guard
    if env is None or morpho is None:
        return {'data': []}

    if not os.path.exists(os.path.join(
            data_root, env, 'inference', morpho, result, 'signals.npy')):
        return {'data': []}

    if not os.path.exists(os.path.join(
            data_root, env, 'luminance_signals.npy')):
        return {'data': []}

    if len(figure['data']) == 0:
        x, y = 0, 0
    else:
        x, y = time, figure['data'][3]['y'][time]

    # Load the data
    signals = np.load(os.path.join(
            data_root, env, 'inference', morpho, result, 'signals.npy'))
    luminance_signals = np.load(
            os.path.join(data_root, env, 'luminance_signals.npy')).T

    # Smooth the signals
    if len(checks) != 0:
        signals = my_filter(signals, sigma=sigma)
        luminance_signals = my_filter(luminance_signals, sigma=sigma)

    # Compute thresholds
    threshold = my_threshold.entire_stats(signals, coef=coef)

    # Compute event times from signals
    if positive_or_negative == 'rise':

        auto_evals = (signals > threshold).argmax(axis=1)
        auto_evals2 = (luminance_signals > threshold2).argmax(axis=1)

    elif positive_or_negative == 'fall':

        # Scan the signal from the right hand side.
        auto_evals = (signals.shape[1]
                - (np.fliplr(signals) > threshold).argmax(axis=1))

        # If the signal was not more than the threshold.
        auto_evals[auto_evals == signals.shape[1]] = 0

        # Scan the signal from the right hand side.
        auto_evals2 = (luminance_signals.shape[1]
                - (np.fliplr(luminance_signals) > threshold2).argmax(axis=1))

        # If the signal was not more than the threshold.
        auto_evals2[auto_evals2 == luminance_signals.shape[1]] = 0

    # Load a manual data and prepare data to be drawn
    # If a manual data exists, draw it
    if csv is None:
        manual_data = [{'x': [], 'y': []}]

    else:
        manual_evals = np.loadtxt(
                os.path.join(data_root, env, 'original', csv),
                dtype=np.uint16, delimiter=',').flatten()

        manual_data = [
                {
                    # Manual evaluation time (vertical line)
                    'x': [manual_evals[well_idx], manual_evals[well_idx]],
                    'y': [0, signals.max()],
                    'mode': 'lines',
                    'name': 'Manual',
                    'line': {'width': 5, 'color': '#ffa500'},
                    'yaxis': 'y2',
                }
            ]

    return {
            'data': manual_data + [
                {
                    # Auto evaluation time (vertical line)
                    'x': [auto_evals[well_idx], auto_evals[well_idx]],
                    'y': [0, signals.max()],            
                    'name': 'Auto',
                    'mode':'lines',
                    'line': {'width':4,'color': '#4169e1','dash':'dot'},
                    'yaxis': 'y2',
                },
                {
                    # Auto evaluation time (vertical line)
                    'x': [auto_evals2[well_idx], auto_evals2[well_idx]],
                    'y': [0, luminance_signals.max()],
                    'mode': 'lines',
                    'name': 'Auto',
                    'line': {'width':4,'color': '#20b2aa','dash':'dot'},
                    
                },
                {
                    # Signal
                    'x': list(range(len(signals[0, :]))),
                    'y': list(signals[well_idx]),
                    'mode': 'lines',
                    'marker': {'color': '#4169e1'},
                    'name': 'Signal',
                    'opacity':1.0,
                    'yaxis': 'y2',
                },
                {
                    # Luminance signal
                    'x': list(range(luminance_signals.shape[1])),
                    'y': list(luminance_signals[well_idx,:]),
                    'mode': 'lines',
                    'line': {'color': '#20b2aa'},
                    'name': 'Luminance Signal',
                    'opacity': 1.0,
                },
                {
                    # Threshold (horizontal line)
                    'x': [0, len(signals[0, :])],
                    'y': [threshold[well_idx, 0], threshold[well_idx, 0]],
                    'mode': 'lines',
                    'name': 'Threshold',
                    'line': {'width': 2, 'color': '#4169e1'},
                    'yaxis': 'y2',
                },
                {
                    # Threshold2 (horizontal line)
                    'x': [0, len(signals[0, :])],
                    'y': [threshold2, threshold2],
                    'mode': 'lines',
                    'name': 'Threshold2',
                    'line': {'width': 2, 'color': '#20b2aa'},
                    
                },

                {
                    # Selected data point
                    'x': [x],
                    'y': [y],
                    'mode': 'markers',
                    'marker': {'size': 10, 'color': '#ff0000'},
                    'name': '',
                    'yaxis': 'y2',
                },
            ],
            'layout': {
                    'title': 'Threshold: {:.1f}={:.1f}{:+.1f}*{:.1f} (blue), {:.1f} (green)'.format(
                        threshold[well_idx, 0],
                        signals.mean(),
                        coef,
                        signals.std(),
                        threshold2
                    ),
                    'font': {'size': 15},
                    'xaxis': {
                        'title': 'Time step',
                        'tickfont': {'size': 15},
                    },
                    'yaxis2': {
                        'title': 'Diff. of ROI',
                        'tickfont': {'size': 15},
                        'overlaying':'y',
                        'range':[0, signals.max()],
                        },
                    'yaxis1': {
                        'title':'Diff. of Luminance',
                        'tickfont': {'size': 15},
                        'side':'right',
                        'range':[0, luminance_signals.max()],
                },
                'showlegend': False,
                'hovermode': 'closest',
                'margin': go.layout.Margin(l=50, r=70, b=50, t=50, pad=0),
            },
        }


# ==========================================
#  Update the figure in the summary-graph.
# ==========================================
@app.callback(
        Output('summary-graph', 'figure'),
        [Input('threshold-slider1', 'value'),
         Input('well-selector', 'value'),
         Input('rise-or-fall', 'value'),
         Input('filter-check', 'values'),
         Input('gaussian-sigma', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('csv-dropdown', 'value'),
         State('morpho-dropdown', 'value'),
         State('result-dropdown', 'value')])
def callback(coef, well_idx, positive_or_negative, checks, sigma, data_root,
        env, csv, morpho, result):

    # Guard
    if env is None or csv is None or morpho is None:
        return {'data': []}
    if not os.path.exists(os.path.join(
            data_root, env, 'inference', morpho, result, 'signals.npy')):
        return {'data': []}

    # Load a mask params
    with open(os.path.join(data_root, env, 'mask_params.json')) as f:
        params = json.load(f)
    
    # Load a blacklist
    if os.path.exists(os.path.join(data_root, env, 'blacklist.csv')):

        blacklist = np.loadtxt(
                os.path.join(data_root, env, 'blacklist.csv'),
                dtype=np.uint16, delimiter=',').flatten() == 1

    else:
        blacklist = np.zeros(
                (params['n-rows']*params['n-plates'], params['n-clms'])) \
                        .flatten() == 1

    # Make a whitelist
    whitelist = np.logical_not(blacklist)

    # Load the data
    signals = np.load(os.path.join(
            data_root, env, 'inference', morpho, result, 'signals.npy'))
    manual_evals = np.loadtxt(
            os.path.join(data_root, env, 'original', csv),
            dtype=np.uint16, delimiter=',').flatten()

    # Smooth the signals
    if len(checks) != 0:
        signals = my_filter(signals, sigma=sigma)

    # Compute thresholds
    threshold = my_threshold.entire_stats(signals, coef=coef)

    # Compute event times from signals
    if positive_or_negative == 'rise':
        auto_evals = (signals > threshold).argmax(axis=1)

    elif positive_or_negative == 'fall':
        # Scan the signal from the right hand side.
        auto_evals = (signals.shape[1]
                - (np.fliplr(signals) > threshold).argmax(axis=1))
        # If the signal was not more than the threshold.
        auto_evals[auto_evals == signals.shape[1]] = 0

    # Calculate how many frames auto-evaluation is far from manual's one
    errors = auto_evals[whitelist] - manual_evals[whitelist]

    # Calculate the root mean square
    rms = np.sqrt((errors**2).sum() / len(errors))

    return {
            'data': [
                {
                    'x': [
                        round(0.05 * len(signals[0, :])),
                        len(signals[0, :])
                    ],
                    'y': [
                        0,
                        len(signals[0, :])-round(0.05 * len(signals[0, :]))
                    ],
                    'mode': 'lines',
                    'fill': None,
                    'line': {'width': .1, 'color': '#43d86b'},
                    'name': 'Lower bound',
                },
                {
                    'x': [
                        -round(0.05 * len(signals[0, :])),
                        len(signals[0, :])
                    ],
                    'y': [
                        0,
                        len(signals[0, :])+round(0.05 * len(signals[0, :]))
                    ],
                    'mode': 'lines',
                    'fill': 'tonexty',
                    'line': {'width': .1, 'color': '#43d86b'},
                    'name': 'Upper bound',
                },
                {
                    'x': [0, len(signals[0, :])],
                    'y': [0, len(signals[0, :])],
                    'mode': 'lines',
                    'line': {'width': .5, 'color': '#000000'},
                    'name': 'Auto = Manual',
                },
                {
                    'x': list(auto_evals[blacklist]),
                    'y': list(manual_evals[blacklist]),
                    'text': [str(i) for i in np.where(blacklist)[0]],
                    'mode': 'markers',
                    'marker': {'size': 4, 'color': '#000000'},
                    'name': 'Well in Blacklist',
                },
                {
                    'x': list(auto_evals[whitelist]),
                    'y': list(manual_evals[whitelist]),
                    'text': [str(i) for i in np.where(whitelist)[0]],
                    'mode': 'markers',
                    'marker': {'size': 4, 'color': '#1f77b4'},
                    'name': 'Well in Whitelist',
                },
                {
                    'x': [auto_evals[well_idx]],
                    'y': [manual_evals[well_idx]],
                    'text': str(well_idx),
                    'mode': 'markers',
                    'marker': {'size': 10, 'color': '#ff0000'},
                    'name': 'Selected well',
                },
            ],
            'layout': {
                'title': 'RMS: {:.1f}'.format(rms),
                'font': {'size': 15},
                'xaxis': {
                    'title': 'Auto',
                    'tickfont': {'size': 15},
                },
                'yaxis': {
                    'title': 'Manual',
                    'tickfont': {'size': 15},
                },
                'showlegend': False,
                'hovermode': 'closest',
                'margin': go.layout.Margin(l=50, r=0, b=50, t=50, pad=0),
            },
        }

# ===========================================
#  Update the figure in the summary-graph2.
# ===========================================
@app.callback(
        Output('summary-graph2', 'figure'),
        [Input('threshold-slider2', 'value'),
         Input('well-selector', 'value'),
         Input('rise-or-fall', 'value'),
         Input('filter-check', 'values'),
         Input('gaussian-sigma', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('csv-dropdown', 'value'),
         State('morpho-dropdown', 'value'),
         State('result-dropdown', 'value')])
def callback(threshold, well_idx, positive_or_negative, checks, sigma,
        data_root, env, csv, morpho, result):

    # Guard
    if env is None or csv is None or morpho is None:
        return {'data': []}
    if not os.path.exists(os.path.join(
            data_root, env, 'luminance_signals.npy')):
        return {'data': []}

    # Load a mask params
    with open(os.path.join(data_root, env, 'mask_params.json')) as f:
        params = json.load(f)
    
    # Load a blacklist
    if os.path.exists(os.path.join(data_root, env, 'blacklist.csv')):

        blacklist = np.loadtxt(
                os.path.join(data_root, env, 'blacklist.csv'),
                dtype=np.uint16, delimiter=',').flatten() == 1

    else:
        blacklist = np.zeros(
                (params['n-rows']*params['n-plates'], params['n-clms'])) \
                        .flatten() == 1

    # Make a whitelist
    whitelist = np.logical_not(blacklist)

    # Load the data
    signals = np.load(
            os.path.join(data_root, env, 'luminance_signals.npy')).T
    manual_evals = np.loadtxt(
            os.path.join(data_root, env, 'original', csv),
            dtype=np.uint16, delimiter=',').flatten()

    # Smooth the signals
    if len(checks) != 0:
        signals = my_filter(signals, sigma=sigma)

    # Compute event times from signals
    if positive_or_negative == 'rise':
        auto_evals = (signals > threshold).argmax(axis=1)

    elif positive_or_negative == 'fall':
        # Scan the signal from the right hand side.
        auto_evals = (signals.shape[1]
                - (np.fliplr(signals) > threshold).argmax(axis=1))
        # If the signal was not more than the threshold.
        auto_evals[auto_evals == signals.shape[1]] = 0

    # Calculate how many frames auto-evaluation is far from manual's one
    errors = auto_evals[whitelist] - manual_evals[whitelist]

    # Calculate the root mean square
    rms = np.sqrt((errors**2).sum() / len(errors))

    return {
            'data': [
                {
                    'x': [
                        round(0.05 * len(signals[0, :])),
                        len(signals[0, :])
                    ],
                    'y': [
                        0,
                        len(signals[0, :])-round(0.05 * len(signals[0, :]))
                    ],
                    'mode': 'lines',
                    'fill': None,
                    'line': {'width': .1, 'color': '#43d86b'},
                    'name': 'Lower bound',
                },
                {
                    'x': [
                        -round(0.05 * len(signals[0, :])),
                        len(signals[0, :])
                    ],
                    'y': [
                        0,
                        len(signals[0, :])+round(0.05 * len(signals[0, :]))
                    ],
                    'mode': 'lines',
                    'fill': 'tonexty',
                    'line': {'width': .1, 'color': '#43d86b'},
                    'name': 'Upper bound',
                },
                {
                    'x': [0, len(signals[0,:])],
                    'y': [0, len(signals[0,:])],
                    'mode': 'lines',
                    'line': {'width': .5, 'color': '#000000'},
                    'name': 'Auto = Manual',
                },
                {
                    'x': list(auto_evals[blacklist]),
                    'y': list(manual_evals[blacklist]),
                    'text': [str(i) for i in np.where(blacklist)[0]],
                    'mode': 'markers',
                    'marker': {'size': 4, 'color': '#000000'},
                    'name': 'Well in Blacklist',
                },
                {
                    'x': list(auto_evals[whitelist]),
                    'y': list(manual_evals[whitelist]),
                    'text': [str(i) for i in np.where(whitelist)[0]],
                    'mode': 'markers',
                    'marker': {'size': 4, 'color': '#20b2aa'},
                    'name': 'Well in Whitelist',
                },
                {
                    'x': [auto_evals[well_idx]],
                    'y': [manual_evals[well_idx]],
                    'mode': 'markers',
                    'marker': {'size': 10, 'color': '#ff0000'},
                    'name': 'Selected well',
                },
            ],
            'layout': {
                'title': 'RMS: {:.1f}'.format(rms),
                'font': {'size': 15},
                'xaxis': {
                    'title': 'Auto',
                    'tickfont': {'size': 15},
                },
                'yaxis': {
                    'title': 'Manual',
                    'tickfont': {'size': 15},
                },
                'showlegend': False,
                'hovermode': 'closest',
                'margin': go.layout.Margin(l=50, r=0, b=50, t=50, pad=0),
            },
        }


# =======================================
#  Update the figure in the error-hist.
# =======================================
@app.callback(
        Output('error-hist', 'figure'),
        [Input('threshold-slider1', 'value'),
         Input('well-selector', 'value'),
         Input('rise-or-fall', 'value'),
         Input('filter-check', 'values'),
         Input('gaussian-sigma', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('csv-dropdown', 'value'),
         State('morpho-dropdown', 'value'),
         State('result-dropdown', 'value')])
def callback(coef, well_idx, positive_or_negative, checks, sigma, data_root,
        env, csv, morpho, result):

    # Guard
    if env is None or csv is None or morpho is None:
        return {'data': []}
    if not os.path.exists(os.path.join(
            data_root, env, 'inference', morpho, result, 'signals.npy')):
        return {'data': []}

    # Load a mask params
    with open(os.path.join(data_root, env, 'mask_params.json')) as f:
        params = json.load(f)
    
    # Load a blacklist
    if os.path.exists(os.path.join(data_root, env, 'blacklist.csv')):

        whitelist = np.loadtxt(
                os.path.join(data_root, env, 'blacklist.csv'),
                dtype=np.uint16, delimiter=',').flatten() == 0

    else:
        whitelist = np.zeros(
                (params['n-rows']*params['n-plates'], params['n-clms'])) \
                        .flatten() == 0

    # Load the data
    signals = np.load(os.path.join(
            data_root, env, 'inference', morpho, result, 'signals.npy'))
    manual_evals = np.loadtxt(
            os.path.join(data_root, env, 'original', csv),
            dtype=np.uint16, delimiter=',').flatten()

    # Smooth the signals
    if len(checks) != 0:
        signals = my_filter(signals, sigma=sigma)

    # Compute thresholds
    threshold = my_threshold.entire_stats(signals, coef=coef)

    # Compute event times from signals
    if positive_or_negative == 'rise':
        auto_evals = (signals > threshold).argmax(axis=1)

    elif positive_or_negative == 'fall':
        # Scan the signal from the right hand side.
        auto_evals = (signals.shape[1]
                - (np.fliplr(signals) > threshold).argmax(axis=1))
        # If the signal was not more than the threshold.
        auto_evals[auto_evals == signals.shape[1]] = 0

    # Calculate how many frames auto-evaluation is far from manual's one
    errors = auto_evals[whitelist == 1] - manual_evals[whitelist == 1]
    ns, bins = np.histogram(errors, 1000)

    # Calculate the number of inconsistent wells
    tmp = np.bincount(abs(errors))
    n_consist_5percent = tmp[:round(0.05 * signals.shape[1])].sum()
    n_consist_1percent = tmp[:round(0.01 * signals.shape[1])].sum()
    n_consist_10frames = tmp[:11].sum()

    return {
            'data': [
                {
                    'x': [
                        -round(0.05 * signals.shape[1]),
                        round(0.05 * signals.shape[1])
                    ],
                    'y': [ns.max(), ns.max()],
                    'mode': 'lines',
                    'fill': 'tozeroy',
                    'line': {'width': 0, 'color': '#43d86b'},
                },
                {
                    'x': list(bins[1:]),
                    'y': list(ns),
                    'mode': 'markers',
                    'type': 'bar',
                    'marker': {'size': 5, 'color': '#1f77b4'},
                },
            ],
            'layout': {
                'title': 'Error histogram',
                'annotations': [
                    {
                        'x': 0.9 * signals.shape[1],
                        'y': 1.0 * ns.max(),
                        'text': '#frames: consistency',
                        'showarrow': False,
                        'xanchor': 'right',
                    },
                    {
                        'x': 0.9 * signals.shape[1],
                        'y': 0.9 * ns.max(),
                        'text': '{} (5%): {:.1f}% ({}/{})'.format(
                            round(0.05 * signals.shape[1]),
                            100 * n_consist_5percent / len(manual_evals),
                            n_consist_5percent,
                            len(manual_evals)),
                        'showarrow': False,
                        'xanchor': 'right',
                    },
                    {
                        'x': 0.9 * signals.shape[1],
                        'y': 0.8 * ns.max(),
                        'text': '{} (1%): {:.1f}% ({}/{})'.format(
                            round(0.01 * signals.shape[1]),
                            100 * n_consist_1percent / len(manual_evals),
                            n_consist_1percent,
                            len(manual_evals)),
                        'showarrow': False,
                        'xanchor': 'right',
                    },
                    {
                        'x': 0.9 * signals.shape[1],
                        'y': 0.7 * ns.max(),
                        'text': '10: {:.1f}% ({}/{})'.format(
                            100 * n_consist_10frames / len(manual_evals),
                            n_consist_10frames,
                            len(manual_evals)),
                        'showarrow': False,
                        'xanchor': 'right',
                    },
                ],
                'font': {'size': 15},
                'xaxis': {
                    'title': 'auto - manual',
                    'range': [-len(signals.T), len(signals.T)],
                    'tickfont': {'size': 15},
                },
                'yaxis': {
                    'title': 'Count',
                    'tickfont': {'size': 15},
                },
                'showlegend': False,
                'hovermode': 'closest',
                'margin': go.layout.Margin(l=50, r=0, b=50, t=50, pad=0),
            },
        }


# ==================================================
#  Update the figure in the error-hist.(Luminance)
# ==================================================
@app.callback(
        Output('error-hist2', 'figure'),
        [Input('threshold-slider2', 'value'),
         Input('well-selector', 'value'),
         Input('rise-or-fall', 'value'),
         Input('filter-check', 'values'),
         Input('gaussian-sigma', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('csv-dropdown', 'value'),
         State('morpho-dropdown', 'value'),
         State('result-dropdown', 'value')])
def callback(threshold, well_idx, positive_or_negative, checks, sigma,
        data_root, env, csv, morpho, result):

    # Guard
    if env is None or csv is None or morpho is None:
        return {'data': []}
    if not os.path.exists(os.path.join(
            data_root, env, 'luminance_signals.npy')):
        return {'data': []}

    # Load a mask params
    with open(os.path.join(data_root, env, 'mask_params.json')) as f:
        params = json.load(f)
    
    # Load a blacklist
    if os.path.exists(os.path.join(data_root, env, 'blacklist.csv')):

        whitelist = np.loadtxt(
                os.path.join(data_root, env, 'blacklist.csv'),
                dtype=np.uint16, delimiter=',').flatten() == 0

    else:
        whitelist = np.zeros(
                (params['n-rows']*params['n-plates'], params['n-clms'])) \
                        .flatten() == 0

    # Load the data
    signals = np.load(
            os.path.join(data_root, env, 'luminance_signals.npy')).T
    manual_evals = np.loadtxt(
            os.path.join(data_root, env, 'original', csv),
            dtype=np.uint16, delimiter=',').flatten()

    # Smooth the signals
    if len(checks) != 0:
        signals = my_filter(signals, sigma=sigma)

    # Compute event times from signals
    if positive_or_negative == 'rise':
        auto_evals = (signals > threshold).argmax(axis=1)

    elif positive_or_negative == 'fall':
        # Scan the signal from the right hand side.
        auto_evals = (signals.shape[1]
                - (np.fliplr(signals) > threshold).argmax(axis=1))
        # If the signal was not more than the threshold.
        auto_evals[auto_evals == signals.shape[1]] = 0

    # Calculate how many frames auto-evaluation is far from manual's one
    errors = auto_evals[whitelist == 1] - manual_evals[whitelist == 1]
    ns, bins = np.histogram(errors, 1000)

    # Calculate the number of inconsistent wells
    tmp = np.bincount(abs(errors))
    n_consist_5percent = tmp[:round(0.05 * signals.shape[1])].sum()
    n_consist_1percent = tmp[:round(0.01 * signals.shape[1])].sum()
    n_consist_10frames = tmp[:11].sum()

    return {
            'data': [
                {
                    'x': [
                        -round(0.05 * signals.shape[1]),
                        round(0.05 * signals.shape[1])
                    ],
                    'y': [ns.max(), ns.max()],
                    'mode': 'lines',
                    'fill': 'tozeroy',
                    'line': {'width': 0, 'color': '#43d86b'},
                },
                {
                    'x': list(bins[1:]),
                    'y': list(ns),
                    'mode': 'markers',
                    'type': 'bar',
                    'marker': {'size': 5, 'color': '#20b2aa'},
                },
            ],
            'layout': {
                'annotations': [
                    {
                        'x': 0.9 * signals.shape[1],
                        'y': 1.0 * ns.max(),
                        'text': '#frames: consistency',
                        'showarrow': False,
                        'xanchor': 'right',
                    },
                    {
                        'x': 0.9 * signals.shape[1],
                        'y': 0.9 * ns.max(),
                        'text': '{} (5%): {:.1f}% ({}/{})'.format(
                            round(0.05 * signals.shape[1]),
                            100 * n_consist_5percent / len(manual_evals),
                            n_consist_5percent,
                            len(manual_evals)),
                        'showarrow': False,
                        'xanchor': 'right',
                    },
                    {
                        'x': 0.9 * signals.shape[1],
                        'y': 0.8 * ns.max(),
                        'text': '{} (1%): {:.1f}% ({}/{})'.format(
                            round(0.01 * signals.shape[1]),
                            100 * n_consist_1percent / len(manual_evals),
                            n_consist_1percent,
                            len(manual_evals)),
                        'showarrow': False,
                        'xanchor': 'right',
                    },
                    {
                        'x': 0.9 * signals.shape[1],
                        'y': 0.7 * ns.max(),
                        'text': '10: {:.1f}% ({}/{})'.format(
                            100 * n_consist_10frames / len(manual_evals),
                            n_consist_10frames,
                            len(manual_evals)),
                        'showarrow': False,
                        'xanchor': 'right',
                    },
                ],
                'font': {'size': 15},
                'xaxis': {
                    'title': 'auto - manual',
                    'range': [-len(signals.T), len(signals.T)],
                    'tickfont': {'size': 15},
                },
                'yaxis': {
                    'title': 'Count',
                    'tickfont': {'size': 15},
                },
                'showlegend': False,
                'hovermode': 'closest',
                'margin': go.layout.Margin(l=50, r=0, b=50, t=50, pad=0),
            },
        }


# ======================
#  Update the t-image.
# ======================
@app.callback(
        Output('t-image', 'src'),
        [Input('time-selector', 'value'),
         Input('well-selector', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value')])
def callback(time, well_idx, data_root, env):

    # Exception handling
    if env is None:
        return ''

    # Load the mask
    mask = np.load(os.path.join(data_root, env, 'mask.npy'))

    # Load an original image
    orgimg_paths = sorted(glob.glob(
            os.path.join(data_root, env, 'original', '*.jpg')))
    org_img = np.array(
            PIL.Image.open(orgimg_paths[time]).convert('L'), dtype=np.uint8)

    # Cut out an well image from the original image
    r, c = np.where(mask == well_idx)
    org_img = org_img[r.min():r.max(), c.min():c.max()]
    org_img = PIL.Image.fromarray(org_img)

    # Buffer the well image as byte stream
    buf = io.BytesIO()
    org_img.save(buf, format='JPEG')

    return 'data:image/jpeg;base64,{}'.format(
            base64.b64encode(buf.getvalue()).decode('utf-8'))


# ========================
#  Update the t+1-image.
# ========================
@app.callback(
        Output('t+1-image', 'src'),
        [Input('time-selector', 'value'),
         Input('well-selector', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value')])
def callback(time, well_idx, data_root, env):

    # Exception handling
    if env is None:
        return ''

    # Load the mask
    mask = np.load(os.path.join(data_root, env, 'mask.npy'))

    # Load an original image
    orgimg_paths = sorted(glob.glob(
            os.path.join(data_root, env, 'original', '*.jpg')))
    org_img = np.array(
            PIL.Image.open(orgimg_paths[time+1]).convert('L'), dtype=np.uint8)

    # Cut out an well image from the original image
    r, c = np.where(mask == well_idx)
    org_img = org_img[r.min():r.max(), c.min():c.max()]
    org_img = PIL.Image.fromarray(org_img)

    # Buffer the well image as byte stream
    buf = io.BytesIO()
    org_img.save(buf, format='JPEG')

    return 'data:image/jpeg;base64,{}'.format(
            base64.b64encode(buf.getvalue()).decode('utf-8'))


# ======================
#  Update the t-label.
# ======================
@app.callback(
        Output('t-label', 'src'),
        [Input('time-selector', 'value'),
         Input('well-selector', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('current-morpho', 'children'),
         State('current-result', 'children')])
def callback(time, well_idx, data_root, env, morpho, result):

    # Exception handling
    if env is None or morpho is None or result is None:
        return ''

    # Load a npz file storing prob images
    # and get a prob image
    npzfile_path = os.path.join(
            data_root, env, 'inference', morpho, result, 'probs',
            '{:03d}.npz'.format(well_idx))
    npz = np.load(npzfile_path)
    probs = npz['arr_0'].astype(np.int32)
    prob = (probs[time] > THETA) * 255
    prob = prob.astype(np.uint8)
    label_image = PIL.Image.fromarray(prob).convert('L')

    # Buffer the well image as byte stream
    buf = io.BytesIO()
    label_image.save(buf, format='JPEG')

    return 'data:image/jpeg;base64,{}'.format(
            base64.b64encode(buf.getvalue()).decode('utf-8'))


# ========================
#  Update the t+1-label.
# ========================
@app.callback(
        Output('t+1-label', 'src'),
        [Input('time-selector', 'value'),
         Input('well-selector', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('current-morpho', 'children'),
         State('current-result', 'children')])
def callback(time, well_idx, data_root, env, morpho, result):

    # Exception handling
    if env is None or morpho is None or result is None:
        return ''

    # Load a npz file storing prob images
    # and get a prob image
    npzfile_path = os.path.join(
            data_root, env, 'inference', morpho, result, 'probs',
            '{:03d}.npz'.format(well_idx))
    npz = np.load(npzfile_path)
    probs = npz['arr_0'].astype(np.int32)
    prob = (probs[time+1] > THETA) * 255
    prob = prob.astype(np.uint8)
    label_image = PIL.Image.fromarray(prob).convert('L')

    # Buffer the well image as byte stream
    buf = io.BytesIO()
    label_image.save(buf, format='JPEG')

    return 'data:image/jpeg;base64,{}'.format(
            base64.b64encode(buf.getvalue()).decode('utf-8'))


# ======================
#  Update the t-prob.
# ======================
@app.callback(
        Output('t-prob', 'src'),
        [Input('time-selector', 'value'),
         Input('well-selector', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('current-morpho', 'children'),
         State('current-result', 'children')])
def callback(time, well_idx, data_root, env, morpho, result):

    # Exception handling
    if env is None or morpho is None or result is None:
        return ''

    # Load a npz file storing prob images
    # and get a prob image
    npzfile_path = os.path.join(
            data_root, env, 'inference', morpho, result, 'probs',
            '{:03d}.npz'.format(well_idx))
    npz = np.load(npzfile_path)
    probs = npz['arr_0'].astype(np.int32)
    prob_image = PIL.Image.fromarray(probs[time] / 100 * 255).convert('L')

    # Buffer the well image as byte stream
    buf = io.BytesIO()
    prob_image.save(buf, format='JPEG')

    return 'data:image/jpeg;base64,{}'.format(
            base64.b64encode(buf.getvalue()).decode('utf-8'))


# ========================
#  Update the t+1-prob.
# ========================
@app.callback(
        Output('t+1-prob', 'src'),
        [Input('time-selector', 'value'),
         Input('well-selector', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('current-morpho', 'children'),
         State('current-result', 'children')])
def callback(time, well_idx, data_root, env, morpho, result):

    # Exception handling
    if env is None or morpho is None or result is None:
        return ''

    # Load a npz file storing prob images
    # and get a prob image
    npzfile_path = os.path.join(
            data_root, env, 'inference', morpho, result, 'probs',
            '{:03d}.npz'.format(well_idx))
    npz = np.load(npzfile_path)
    probs = npz['arr_0'].astype(np.int32)
    prob_image = PIL.Image.fromarray(probs[time+1] / 100 * 255).convert('L')

    # Buffer the well image as byte stream
    buf = io.BytesIO()
    prob_image.save(buf, format='JPEG')

    return 'data:image/jpeg;base64,{}'.format(
            base64.b64encode(buf.getvalue()).decode('utf-8'))


# ===========================
#  Update the current-well.
# ===========================
@app.callback(
        Output('current-well', 'src'),
        [Input('time-selector', 'value'),
         Input('well-selector', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('current-morpho', 'children'),
         State('current-result', 'children')])
def callback(time, well_idx, data_root, env, morpho, result):

    # Exception handling
    if env is None or morpho is None or result is None:
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


# ======================================================
#  Toggle validation or invalidation of gaussian-sigma
# ======================================================
@app.callback(
        Output('gaussian-sigma', 'disabled'),
        [Input('filter-check', 'values')])
def callback(checks):

    if len(checks) == 0:
        return True

    else:
        return False


# ======================================================
#  Timestamp table
# ======================================================
@app.callback(
        Output('timestamp-table', 'children'),
        [Input('tabs', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('hidden-timestamp', 'children')])
def callback(tab_name, data_root, env, timestamps):

    # Guard
    if data_root is None:
        return
    if env is None:
        return
    if tab_name != 'tab-2':
        return

    data = list(json.loads(timestamps).values())
    time_to_csv = 'data:text/csv;charset=utf-8,' \
            + pd.DataFrame(data).to_csv(index=False)


    return [
            dash_table.DataTable(
                columns=[
                    {'id': 'frame', 'name': 'frame'},
                    {'id': 'create time', 'name': 'create time'}],
                data=data,
                n_fixed_rows=1,
                style_table={'width': '100%'},
                pagination_mode=False,
            ),
            html.Br(),
            html.A(
                'Download Time Stamp',
                id='download-link',
                download='Timestamp({}).csv'.format(env[0:20]),
                href=time_to_csv,
                target="_blank"
            ),
        ]


# ======================================================
#  Manual table
# ======================================================
@app.callback(
        Output('manual-table', 'children'),
        [Input('tabs', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('csv-dropdown', 'value'),
         State('morpho-dropdown', 'value'),
         State('result-dropdown', 'value'),
         State('rise-or-fall', 'value'),
         State('threshold-slider1', 'value'),
         State('gaussian-sigma', 'value'),
         State('filter-check', 'values')])
def callback(
        tab_name, data_root, env, csv, morpho, result, rise_fall,
        coef, sigma, checks):

    # Guard
    if data_root is None:
        return
    if env is None:
        return
    if csv is None:
        return 'Not available.'
    if tab_name != 'tab-2':
        return

    # Load a mask params
    with open(os.path.join(data_root, env, 'mask_params.json')) as f:
        params = json.load(f)

    # Load a manual data
    manual_evals = np.loadtxt(
            os.path.join(data_root, env, 'original', csv),
            dtype=np.uint16, delimiter=',').flatten()

    manual_evals = manual_evals.reshape(
            params['n-rows']*params['n-plates'], params['n-clms'])

    manual_to_csv = \
              'data:text/csv;charset=utf-8,' \
            + 'Dataset,{}\nMorphology,{}\n'.format(env, morpho) \
            + 'Inference Data,{}\n'.format(result) \
            + 'Thresholding,{}\n'.format(rise_fall) \
            + 'Event Timing\n' \
            + pd.DataFrame(manual_evals).to_csv(
                    index=False, encoding='utf-8', header=False)

    style = [{
            'if': {
                'column_id': '{}'.format(clm),
                'filter': 'num({2}) > {0} && {1} >= num({3})'.format(
                        clm, clm, int(t)+100, int(t)),
            },
            'backgroundColor': '#{:02X}{:02X}00'.format(int(c), int(c)),
            'color': 'black',
        }
        for clm in range(params['n-clms'])
        for t, c in zip(
            range(0, manual_evals.max(), 100),
            np.linspace(0, 255, len(range(0, manual_evals.max(), 100))))
    ]

    return [
            dash_table.DataTable(
                columns=[{'name': str(clm), 'id': str(clm)}
                        for clm in range(params['n-clms'])],
                data=pd.DataFrame(manual_evals).to_dict('rows'),
                style_data_conditional=style,
                style_table={'width': '100%'}
            ),
            html.Br(),
            html.A(
                'Download Manual Data',
                id='download-link',
                download='Manual_Detection.csv',
                href=manual_to_csv,
                target="_blank"
            ),
        ]


# ======================================================
#  Auto table
# ======================================================
@app.callback(
        Output('auto-table', 'children'),
        [Input('tabs', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('csv-dropdown', 'value'),
         State('morpho-dropdown', 'value'),
         State('result-dropdown', 'value'),
         State('rise-or-fall', 'value'),
         State('threshold-slider1', 'value'),
         State('gaussian-sigma', 'value'),
         State('filter-check', 'values')])
def callback(
        tab_name, data_root, env, csv, morpho, result, rise_fall,
        coef, sigma, checks):

    # Guard
    if data_root is None:
        return
    if env is None:
        return
    if csv is None:
        return 'Not available.'
    if tab_name != 'tab-2':
        return
    if morpho is None or result is None:
        return

    # Load a mask params
    with open(os.path.join(data_root, env, 'mask_params.json')) as f:
        params = json.load(f)

    signals = np.load(os.path.join(
            data_root, env, 'inference', morpho, result, 'signals.npy'))

    # Smooth the signals
    if len(checks) != 0:
        signals = my_filter(signals, sigma=sigma)

    # Compute thresholds
    threshold = my_threshold.entire_stats(signals, coef=coef)

    # Compute event times from signals
    if rise_fall == 'rise':
        auto_evals = (signals > threshold).argmax(axis=1)

    elif rise_fall == 'fall':
        # Scan the signal from the right hand side.
        auto_evals = (signals.shape[1]
                - (np.fliplr(signals) > threshold).argmax(axis=1))
        # If the signal was not more than the threshold.
        auto_evals[auto_evals == signals.shape[1]] = 0

    auto_evals = auto_evals.reshape(
            params['n-rows']*params['n-plates'], params['n-clms'])

    auto_to_csv = \
              'data:text/csv;charset=utf-8,' \
            + 'Dataset,{}\nMorphology,{}\n'.format(env, morpho) \
            + 'Inference Data,{}\n'.format(result) \
            + 'Thresholding,{}\n'.format(rise_fall) \
            + 'Threshold Value,{}\n'.format(threshold[0, 0]) \
            + '(Threshold Value = mean + coef * std)\n' \
            + 'Mean (mean),{}\n'.format(signals.mean()) \
            + 'Coefficient (coef),{}\n'.format(coef) \
            + 'Standard Deviation (std),{}\n'.format(signals.std()) \
            + 'Smoothing Sigma,{}\nEvent Timing\n'.format(sigma) \
            + pd.DataFrame(auto_evals).to_csv(
                    index=False, encoding='utf-8', header=False),

    style = [{
            'if': {
                'column_id': '{}'.format(clm),
                'filter': 'num({2}) > {0} && {1} >= num({3})'.format(
                        clm, clm, int(t)+100, int(t)),
            },
            'backgroundColor': '#{:02X}{:02X}00'.format(int(c), int(c)),
            'color': 'black',
        }
        for clm in range(params['n-clms'])
        for t, c in zip(
            range(0, auto_evals.max(), 100),
            np.linspace(0, 255, len(range(0, auto_evals.max(), 100))))
    ]

    return [
            dash_table.DataTable(
                columns=[{'name': str(clm), 'id': str(clm)}
                        for clm in range(params['n-clms'])],
                data=pd.DataFrame(auto_evals).to_dict('rows'),
                style_data_conditional=style,
                style_table={'width': '100%'}
            ),
            html.Br(),
            html.A(
                'Download Auto Data',
                id='download-link',
                download='Auto_Detection.csv',
                href=auto_to_csv,
                target="_blank"
            ),
        ]


# =========================================
#  Smoothing signals with gaussian window
# =========================================
def my_filter(signals, sigma=5):
    
    window = scipy.signal.gaussian(10, sigma)

    signals = np.array(
            [np.convolve(signal, window, mode='same')
                for signal in signals])

    return signals


if __name__ == '__main__':
    app.run_server(debug=True)
