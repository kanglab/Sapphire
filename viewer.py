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
import base64
import zipfile
import PIL.Image
import dash_auth
import numpy as np
import flask_caching
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go


DATA_ROOT = '//133.24.88.18/sdb/Research/Drosophila/data/TsukubaRIKEN/'
THETA = 50


app = dash.Dash()
app.css.append_css(
        {'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})
cache = flask_caching.Cache()
cache.init_app(
        app.server, config={'CACHE_TYPE': 'filesystem', 'CACHE_DIR': 'cache/'})


# ================================
#  Definition of the viewer page
# ================================
app.layout = html.Div([
    html.Header([html.H1('Viewer', style={'margin': '0px'})]),
    html.Div([
        html.Div([
            'Imaging environment :',
            html.Br(),
            html.Div([
                dcc.Dropdown(
                    id='env-dropdown',
                    placeholder='Select imaging env...',
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
            'CSV file :',
            html.Br(),
            html.Div([
                dcc.Dropdown(
                    id='csv-dropdown',
                    placeholder='Select CSV file...',
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
            'Morpho :',
            html.Br(),
            html.Div([
                dcc.Dropdown(
                    id='morpho-dropdown',
                    placeholder='Select morpho...',
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
            'Inference result :',
            html.Br(),
            html.Div([
                dcc.Dropdown(
                    id='result-dropdown',
                    placeholder='Select result dir...',
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
            'Target to detect :',
            html.Br(),
            html.Div([
                dcc.Dropdown(
                    id='target-dropdown',
                    options=[
                        {'label': 'rise', 'value': 'rise'},
                        {'label': 'fall', 'value': 'fall'},
                    ],
                    value='rise',
                    placeholder='Detect...',
                    clearable=False,
                ),
                ],
                style={
                    'width': '100px',
                },
            ),
            'Well index :',
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
            'Time :',
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
            )
            ],
            style={
                'display': 'inline-block',
                'margin': '10px 10px',
            },
        ),
        html.Div([
            html.Div('Original image', style={'display': 'table'}),
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
                'margin': '2px 2px',
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
                'margin': '2px',
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
                'margin': '10px 10px',
            },
        ),
        dcc.Graph(
            id='signal-graph',
            style={
                'display': 'inline-block',
                'height': '400px',
                # 'width': '40%',
            },
        ),
        html.Div([
            dcc.Slider(
                id='threshold-slider',
                value=20,
                min=0,
                max=300,
                step=1,
                updatemode='mouseup',
                vertical=True,
            )],
            style={
                'display': 'inline-block',
                'height': '280px',
                'width': '10px',
                'padding-bottom': '70px',
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
    ]),
    ],
    style={
        'width': '1200px',
    },
)


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


# ==========
#  Caching
# ==========
@cache.memoize()
def store_signals(data_root, env, morpho, result):
    if env is None or morpho is None or result is None:
        return

    signals = np.load(os.path.join(
        data_root, env, 'inference', morpho, result, 'signals.npy'))

    return signals


@cache.memoize()
def store_manual_evals(data_root, env, csv):
    if env is None or csv is None:
        return

    manual_evals = np.loadtxt(
            os.path.join(data_root, env, 'original', csv),
            dtype=np.uint16,
            delimiter=',').flatten()

    return manual_evals


@cache.memoize()
def store_mask(data_root, env):
    if env is None:
        return

    return np.load(os.path.join(data_root, env, 'mask.npy'))


# ==========================================================
#  Load a mask file when selecting an imaging environment.
# ==========================================================
@app.callback(
        Output('current-env', 'children'),
        [Input('env-dropdown', 'value')],
        [State('data-root', 'children')])
def callback(env, data_root):
    store_mask(data_root, env)
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
    store_manual_evals(data_root, env, csv)
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


# ========================================================
#  Load a signal file when selecting a result directory.
# ========================================================
@app.callback(
        Output('current-result', 'children'),
        [Input('result-dropdown', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('morpho-dropdown', 'value')])
def callback(result, data_root, env, morpho):
    if env is None or morpho is None:
        return

    store_signals(data_root, env, morpho, result)
    return result


# ====================================================
#  Initialize the maximum value of the time-selector
#  after loading a signal file.
# ====================================================
@app.callback(
        Output('time-selector', 'max'),
        [Input('current-result', 'children')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('morpho-dropdown', 'value')])
def callback(result, data_root, env, morpho):
    if env is None or morpho is None:
        return

    signals = store_signals(data_root, env, morpho, result)
    return signals.shape[1] - 1


# =======================================================
#  Initialize the maximum value of the threshold-slider
#  after loading a signal file.
# =======================================================
@app.callback(
        Output('threshold-slider', 'max'),
        [Input('current-result', 'children')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('morpho-dropdown', 'value')])
def callback(result, data_root, env, morpho):
    if env is None or morpho is None:
        return

    signals = store_signals(data_root, env, morpho, result)
    return signals.max()


# =======================================================
#  Initialize the maximum value of the threshold-slider
#  after loading a signal file.
# =======================================================
@app.callback(
        Output('well-slider', 'max'),
        [Input('current-result', 'children')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('morpho-dropdown', 'value')])
def callback(result, data_root, env, morpho):
    if env is None or morpho is None:
        return

    signals = store_signals(data_root, env, morpho, result)
    return len(signals) - 1


# ====================================================
#  Initialize the maximum value of the well-selector
#  after loading a signal file.
# ====================================================
@app.callback(
        Output('well-selector', 'max'),
        [Input('current-result', 'children')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('morpho-dropdown', 'value')])
def callback(result, data_root, env, morpho):
    if env is None or morpho is None:
        return

    signals = store_signals(data_root, env, morpho, result)
    return len(signals) - 1


# ======================================================
#  Initialize the current value of the well-slider
#  after loading a signal file
#  or when clicking a data point in the summary-graph.
# ======================================================
@app.callback(
        Output('well-slider', 'value'),
        [Input('current-result', 'children'),
         Input('summary-graph', 'clickData')])
def callback(_, click_data):
    if click_data is None:
        return 20

    return click_data['points'][0]['pointNumber']


# ====================================================
#  Initialize the current value of the well-selector
#  when selecting a value on the well-slider.
# ====================================================
@app.callback(
        Output('well-selector', 'value'),
        [Input('well-slider', 'value')])
def callback(well_idx):
    return well_idx


# ====================================================
#  Initialize the current value of the time-selector
#  when clicking a data point in the signal-graph.
# ====================================================
@app.callback(
        Output('time-selector', 'value'),
        [Input('signal-graph', 'clickData')])
def callback(click_data):
    if click_data is None:
        return 0
    else:
        return click_data['points'][0]['x']


# =========================================
#  Update the figure in the signal-graph.
# =========================================
@app.callback(
        Output('signal-graph', 'figure'),
        [Input('well-selector', 'value'),
         Input('threshold-slider', 'value'),
         Input('target-dropdown', 'value'),
         Input('time-selector', 'value')],
        [State('signal-graph', 'figure'),
         State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('csv-dropdown', 'value'),
         State('morpho-dropdown', 'value'),
         State('result-dropdown', 'value')])
def callback(well_idx, threshold, rise_or_fall, time,
        figure, data_root, env, csv, morpho, result):

    # Exception handling
    if env is None or csv is None or morpho is None:
        return {'data': []}

    if len(figure['data']) == 0:
        x, y = 0, 0
    else:
        x, y = time, figure['data'][2]['y'][time]

    # Load the data
    signals = store_signals(data_root, env, morpho, result)
    manual_evals = store_manual_evals(data_root, env, csv)

    # Compute event times from signals
    if rise_or_fall == 'rise':
        auto_evals = (signals > threshold).argmax(axis=1)

    elif rise_or_fall == 'fall':
        # Scan the signal from the right hand side.
        auto_evals = (signals.shape[1]
                - (np.fliplr(signals) > threshold).argmax(axis=1))
        # If the signal was not more than the threshold.
        auto_evals[auto_evals == signals.shape[1]] = 0

    return {
            'data': [
                {
                    # Manual evaluation time (vertical line)
                    'x': [manual_evals[well_idx]] * int(signals.max()),
                    'y': list(range(256)),
                    'mode': 'lines',
                    'name': 'Manual',
                    'line': {'width': 5, 'color': '#2ca02c'},
                },
                {
                    # Auto evaluation time (vertical line)
                    'x': [auto_evals[well_idx]] * int(signals.max()),
                    'y': list(range(256)),
                    'mode': 'lines',
                    'name': 'Auto',
                    'line': {'width': 5, 'color': 'd62728'},
                },
                {
                    # Signal
                    'x': list(range(len(signals[0, :]))),
                    'y': list(signals[well_idx]),
                    'mode': 'markers+lines',
                    'marker': {'size': 5, 'color': '#1f77b4'},
                    'name': 'Signal',
                },
                {
                    # Threshold (hrizontal line)
                    'x': list(range(len(signals[0, :]))),
                    'y': [threshold]*len(signals[0, :]),
                    'mode': 'lines',
                    'name': 'Threshold',
                    'line': {'width': 5, 'color': '#ff7f0e'},
                },
                {
                    # Selected data point
                    'x': [x],
                    'y': [y],
                    'mode': 'markers',
                    'marker': {'size': 10},
                    'name': '',
                },
            ],
            'layout': {
                'title': 'Activity signal (threshold={})'.format(threshold),
                'font': {'size': 15},
                'xaxis': {
                    'title': 'Time step',
                    'tickfont': {'size': 15},
                },
                'yaxis': {
                    'title': 'Signal intensity',
                    'tickfont': {'size': 15},
                },
                'showlegend': False,
                'hovermode': 'closest',
                'margin': go.Margin(l=50, r=0, b=50, t=50, pad=0),
            },
        }


# ==========================================
#  Update the figure in the summary-graph.
# ==========================================
@app.callback(
        Output('summary-graph', 'figure'),
        [Input('threshold-slider', 'value'),
         Input('well-selector', 'value'),
         Input('target-dropdown', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('csv-dropdown', 'value'),
         State('morpho-dropdown', 'value'),
         State('result-dropdown', 'value')])
def callback(threshold, well_idx, rise_or_fall, data_root,
        env, csv, morpho, result):

    # Exception handling
    if env is None or csv is None or morpho is None:
        return {'data': []}

    # Load the data
    signals = store_signals(data_root, env, morpho, result)
    manual_evals = store_manual_evals(data_root, env, csv)

    # Compute event times from signals
    if rise_or_fall == 'rise':
        auto_evals = (signals > threshold).argmax(axis=1)

    elif rise_or_fall == 'fall':
        # Scan the signal from the right hand side.
        auto_evals = (signals.shape[1]
                - (np.fliplr(signals) > threshold).argmax(axis=1))
        # If the signal was not more than the threshold.
        auto_evals[auto_evals == signals.shape[1]] = 0

    return {
            'data': [
                {
                    'x': list(auto_evals),
                    'y': list(manual_evals),
                    'mode': 'markers',
                    'marker': {'size': 5},
                    'name': 'Well',
                },
                {
                    'x': [0, len(signals[0, :])],
                    'y': [0, len(signals[0, :])],
                    'mode': 'lines',
                    'name': 'Auto = Manual',
                },
                {
                    'x': [auto_evals[well_idx]],
                    'y': [manual_evals[well_idx]],
                    'mode': 'markers',
                    'marker': {'size': 10},
                    'name': 'Selected well',
                },
            ],
            'layout': {
                'title': 'Auto vs Manual',
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
                'margin': go.Margin(l=50, r=0, b=50, t=50, pad=0),
            },
        }


# =======================================
#  Update the figure in the error-hist.
# =======================================
@app.callback(
        Output('error-hist', 'figure'),
        [Input('threshold-slider', 'value'),
         Input('well-selector', 'value'),
         Input('target-dropdown', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('csv-dropdown', 'value'),
         State('morpho-dropdown', 'value'),
         State('result-dropdown', 'value')])
def callback(threshold, well_idx, rise_or_fall, data_root,
        env, csv, morpho, result):

    # Exception handling
    if env is None or csv is None or morpho is None:
        return {'data': []}

    # Load the data
    signals = store_signals(data_root, env, morpho, result)
    manual_evals = store_manual_evals(data_root, env, csv)

    # Compute event times from signals
    if rise_or_fall == 'rise':
        auto_evals = (signals > threshold).argmax(axis=1)

    elif rise_or_fall == 'fall':
        # Scan the signal from the right hand side.
        auto_evals = (signals.shape[1]
                - (np.fliplr(signals) > threshold).argmax(axis=1))
        # If the signal was not more than the threshold.
        auto_evals[auto_evals == signals.shape[1]] = 0

    # Calculate how many frames auto-evaluation is far from manual's one
    errors = auto_evals - manual_evals
    ns, bins = np.histogram(errors, 1000)

    # Calculate the root mean square
    rms = np.sqrt((errors**2).sum() / len(errors))

    return {
            'data': [
                {
                    'x': list(bins[1:]),
                    'y': list(ns),
                    'mode': 'markers',
                    'type': 'bar',
                    'marker': {'size': 5},
                },
                {
                    'x': [-10, 10],
                    'y': [ns.max(), ns.max()],
                    'mode': 'lines',
                    'fill': 'tozeroy',
                },
            ],
            'layout': {
                'title': 'Error histogram (RMS={})'.format(int(rms)),
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
                'margin': go.Margin(l=50, r=0, b=50, t=50, pad=0),
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
    mask = store_mask(data_root, env)

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
    mask = store_mask(data_root, env)

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

    # Load a zip file storing label images
    # and get a label image
    zipfile_path = os.path.join(
            data_root, env, 'inference', morpho, result, 'labels',
            '{:03d}.zip'.format(well_idx))
    with zipfile.ZipFile(zipfile_path, 'r') as labels_zip:
        filenames = sorted(
                [info.filename for info in labels_zip.infolist()])
        with labels_zip.open(filenames[time]) as label_file:
            label_image = PIL.Image.open(label_file)

    # Buffer the well image as byte stream
    buf = io.BytesIO()
    label_image.save(buf, format='PNG')

    return 'data:image/png;base64,{}'.format(
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

    # Load a zip file storing label images
    # and get a label image
    zipfile_path = os.path.join(
            data_root, env, 'inference', morpho, result, 'labels',
            '{:03d}.zip'.format(well_idx))
    with zipfile.ZipFile(zipfile_path, 'r') as labels_zip:
        filenames = sorted(
                [info.filename for info in labels_zip.infolist()])
        with labels_zip.open(filenames[time+1]) as label_file:
            label_image = PIL.Image.open(label_file)

    # Buffer the well image as byte stream
    buf = io.BytesIO()
    label_image.save(buf, format='PNG')

    return 'data:image/png;base64,{}'.format(
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

    # Load a zip file storing prob images
    # and get a prob image
    zipfile_path = os.path.join(
            data_root, env, 'inference', morpho, result, 'probs',
            '{:03d}.zip'.format(well_idx))
    with zipfile.ZipFile(zipfile_path, 'r') as probs_zip:
        filenames = sorted(
                [info.filename for info in probs_zip.infolist()])
        with probs_zip.open(filenames[time]) as prob_file:
            prob_image = PIL.Image.open(prob_file)

    # Buffer the well image as byte stream
    buf = io.BytesIO()
    prob_image.save(buf, format='PNG')

    return 'data:image/png;base64,{}'.format(
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

    # Load a zip file storing prob images
    # and get a prob image
    zipfile_path = os.path.join(
            data_root, env, 'inference', morpho, result, 'probs',
            '{:03d}.zip'.format(well_idx))
    with zipfile.ZipFile(zipfile_path, 'r') as probs_zip:
        filenames = sorted(
                [info.filename for info in probs_zip.infolist()])
        with probs_zip.open(filenames[time+1]) as prob_file:
            prob_image = PIL.Image.open(prob_file)

    # Buffer the well image as byte stream
    buf = io.BytesIO()
    prob_image.save(buf, format='PNG')

    return 'data:image/png;base64,{}'.format(
            base64.b64encode(buf.getvalue()).decode('utf-8'))


if __name__ == '__main__':
    app.run_server(debug=True)
