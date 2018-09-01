# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8 :
# vim: set foldmethod=marker commentstring=\ \ #\ %s :
#
# Author:    Taishi Matsumura
# Created:   2018-08-29
#
# Copyright (C) 2018 Taishi Matsumura
#
import io
import os
import glob
import dash
import base64
import PIL.Image
import dash_auth
import numpy as np
import scipy.ndimage
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State


def centroid(binary_img):
    rows, clms = np.where(binary_img)
    cent = rows.sum() / rows.shape[0], clms.sum() / clms.shape[0]
    if np.isnan(cent[0]):
        return (binary_img.shape[0]/2, binary_img.shape[1]/2)
    else:
        return cent


# -------------------
#  Global variables
# -------------------
# Keep this out of source code repository - save in a file or a database
VALID_USERNAME_PASSWORD_PAIRS = [
    ['matsu', 'dash1m0'],
    ['kang', 'dash3360'],
]

data_root = 'G:/Research/Drosophila/CUI/data/'
imaging_env = '171013.15.50.w1118.starvation.96well.3plates.740D-3'
imaging_env = 'allevents'

manual_evals_file = 'eclosion.csv'
manual_evals_file = '171013.csv'
manual_evals_file = 'pupariation.csv'

theta = 50
labels = None
signals = None
manual_evals = np.loadtxt(
        os.path.join(data_root, imaging_env, 'original', manual_evals_file),
        dtype=np.uint16,
        delimiter=',').flatten()
mask = np.load(
        os.path.join(data_root, imaging_env, 'mask.npy'))

# -------
#  Main
# -------
app = dash.Dash()
auth = dash_auth.BasicAuth(app, VALID_USERNAME_PASSWORD_PAIRS)
'''
If you don't want to use CDN, set to True

app.css.config.serve_locally = True
app.scripts.config.serve_locally = True
'''
app.scripts.config.serve_locally = False
app.css.config.serve_locally = False
app.css.append_css(
        {'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})

app.layout = html.Div([
    html.Header([html.H1('Viewer')]),
    html.Div([
        html.Div([
            html.Div(['Image at "t"'], style={'display': 'table'}),
            html.Img(
                id='t-image',
                style={
                    'background': '#555555',
                    'height': '120px',
                    'width': '120px',
                    'padding': '5px',
                    'display': 'block',
                },
            ),
            html.Img(
                id='t-label',
                style={
                    'background': '#555555',
                    'height': '120px',
                    'width': '120px',
                    'padding': '5px',
                    'display': 'block',
                },
            ),
            ],
            style={
                'display': 'inline-block',
                'margin': '10px 10px',
            },
        ),
        html.Div([
            html.Div(['"t+1"'], style={'display': 'table'}),
            html.Img(
                id='t+1-image',
                style={
                    'background': '#555555',
                    'height': '120px',
                    'width': '120px',
                    'padding': '5px',
                    'display': 'block',
                },
            ),
            html.Img(
                id='t+1-label',
                style={
                    'background': '#555555',
                    'height': '120px',
                    'width': '120px',
                    'padding': '5px',
                    'display': 'block',
                },
            ),
            ],
            style={
                'display': 'inline-block',
                'margin': '10px',
            },
        ),
        html.Div([
            'Npy file :',
            html.Br(),
            html.Div([
                dcc.Dropdown(
                    id='dropdown1',
                    options=[
                        {
                            'label': 'matsu_signal_data_larva.npy',
                            'value': 'matsu_signal_data_larva.npy',
                        },
                        {
                            'label': 'matsu_signal_data_adult.npy',
                            'value': 'matsu_signal_data_adult.npy',
                        },
                    ],
                    value='matsu_signal_data_larva.npy',
                    placeholder='Select npy file...',
                    clearable=False,
                ),
                ],
                style={
                    'display': 'inline-block',
                    'width': '300px',
                    'vertical-align': 'middle',
                },
            ),
            html.Div([
                html.Button(
                    'Load',
                    id='button',
                ),
                ],
                style={
                    'display': 'inline-block',
                },
            ),
            html.Br(),
            html.Br(),
            'Target to detect :',
            html.Br(),
            html.Div([
                dcc.Dropdown(
                    id='dropdown2',
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
            html.Br(),
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
                style={'display': 'inline-block'},
            ),
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
                    'width': '300px',
                    'margin-left': '20px',
                },
            ),
            html.Br(),
            html.Br(),
            'Time :',
            html.Br(),
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
                'margin': '10px 10px',
            },
        ),
        html.Div([
            html.Div(['Current npy file : '], id='current-npy'),
            'Data root : {}'.format(data_root),
            html.Br(),
            'Imaging environment : {}'.format(imaging_env),
            html.Br(),
            'File name : {}'.format(manual_evals_file),
            html.Br(),
            ],
            style={
                'display': 'inline-block',
                'vertical-align': 'top',
                'margin': '10px 10px',
            },
        ),
        ],
    ),
    html.Div([
        dcc.Graph(
            id='signal-graph',
            style={
                'display': 'inline-block',
                'height': '500px',
                'width': '60%',
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
                'height': '300px',
                'width': '5%',
                'padding-bottom': '100px',
            },
        ),
        dcc.Graph(
            id='summary-graph',
            style={
                'display': 'inline-block',
                'height': '500px',
                'width': '35%',
            },
        ),
    ]),
    ],
    style={
        'width': '1200px',
    },
)


# ------------
#  Callbacks
# ------------
@app.callback(
        Output('time-selector', 'value'),
        [Input('signal-graph', 'clickData')])
def callback(click_data):
    if click_data is None:
        return 0
    else:
        return click_data['points'][0]['x']


@app.callback(
        Output('time-selector', 'max'),
        [Input('current-npy', 'children')])
def callback(_):
    return signals.shape[1] - 1


@app.callback(
        Output('well-slider', 'max'),
        [Input('current-npy', 'children')])
def callback(_):
    return len(labels) - 1


@app.callback(
        Output('well-selector', 'max'),
        [Input('current-npy', 'children')])
def callback(_):
    return len(labels) - 1


@app.callback(
        Output('threshold-slider', 'max'),
        [Input('current-npy', 'children')])
def callback(_):
    return signals.max()


@app.callback(
        Output('current-npy', 'children'),
        [Input('button', 'n_clicks')],
        [State('dropdown1', 'value')])
def callback(n_clicks, larva_or_adult):
    global labels, signals
    labels = np.load(os.path.join(
            data_root,
            imaging_env,
            larva_or_adult)) >= theta
    signals = (np.diff(labels.astype(np.int8), axis=1)**2).sum(-1).sum(-1)

    '''
    # Euclidean
    n_wells, n_times, height, width = labels.shape
    temp = np.array([scipy.ndimage.binary_erosion(label, structure=np.ones((3, 3)), iterations=1) for label in labels.reshape(-1, height, width)]).astype(labels.dtype).reshape(*labels.shape)
    centroids = np.array(list(map(centroid, temp.reshape(-1, height, width))))
    centroids = centroids.reshape(n_wells, n_times, 2)
    signals = np.sqrt((np.diff(centroids, axis=1)**2).sum(-1))
    '''
    return 'Current npy file : {}'.format(larva_or_adult)


@app.callback(
        Output('well-slider', 'value'),
        [Input('summary-graph', 'clickData'),
         Input('current-npy', 'children')])
def callback(click_data, _):
    if click_data is None:
        return 0
    return click_data['points'][0]['pointNumber']


@app.callback(
        Output('summary-graph', 'figure'),
        [Input('threshold-slider', 'value'),
         Input('well-selector', 'value'),
         Input('dropdown2', 'value')])
def callback(threshold, well_idx, rise_or_fall):
    if rise_or_fall == 'rise':
        auto_evals = (signals > threshold).argmax(axis=1)
    elif rise_or_fall == 'fall':
        # Scan the signal from the right hand side.
        auto_evals = signals.shape[1] - (np.fliplr(signals) > threshold).argmax(axis=1)
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
                'xaxis': {
                    'title': 'Auto',
                },
                'yaxis': {
                    'title': 'Manual',
                },
                'hovermode': 'closest',
            },
        }


@app.callback(
        Output('well-selector', 'value'),
        [Input('well-slider', 'value')])
def callback(well_idx):
    return well_idx


@app.callback(
        Output('signal-graph', 'figure'),
        [Input('well-selector', 'value'),
         Input('threshold-slider', 'value'),
         Input('dropdown2', 'value'),
         Input('time-selector', 'value')],
        [State('signal-graph', 'figure')])
def callback(well_idx, threshold, rise_or_fall, time, figure):
    if figure is None:
        x, y = 0, 0
    else:
        x, y = time, figure['data'][0]['y'][time]
    if rise_or_fall == 'rise':
        auto_evals = (signals > threshold).argmax(axis=1)
    elif rise_or_fall == 'fall':
        auto_evals = signals.shape[1] - (np.fliplr(signals) > threshold).argmax(axis=1)
    return {
            'data': [
                {
                    # Signal
                    'x': list(range(len(signals[0, :]))),
                    'y': list(signals[well_idx]),
                    'mode': 'markers+lines',
                    'marker': {'size': 5},
                    'name': 'Signal',
                },
                {
                    # Threshold (hrizontal line)
                    'x': list(range(len(signals[0, :]))),
                    'y': [threshold]*len(signals[0, :]),
                    'mode': 'lines',
                    'name': 'Threshold',
                },
                {
                    # Manual evaluation time (vertical line)
                    'x': [manual_evals[well_idx]] * int(signals.max()),
                    'y': list(range(256)),
                    'mode': 'lines',
                    'name': 'Manual',
                },
                {
                    # Auto evaluation time (vertical line)
                    'x': [auto_evals[well_idx]] * int(signals.max()),
                    'y': list(range(256)),
                    'mode': 'lines',
                    'name': 'Auto',
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
                'title': '',
                'xaxis': {
                    'title': 'Time step',
                },
                'yaxis': {
                    'title': 'Signal',
                },
                'showlegend': False,
                'hovermode': 'closest',
            },
        }


@app.callback(
        Output('t-image', 'src'),
        [Input('time-selector', 'value'),
         Input('well-selector', 'value')])
def callback(time, well_idx):
    orgimg_paths = sorted(glob.glob(
            os.path.join(data_root, imaging_env, 'original', '*.jpg')))
    org_img = np.array(
            PIL.Image.open(orgimg_paths[time]).convert('L'), dtype=np.uint8)
    r, c = np.where(mask == well_idx)
    org_img = org_img[r.min():r.max(), c.min():c.max()]
    org_img = PIL.Image.fromarray(org_img)
    buf = io.BytesIO()
    org_img.save(buf, format='JPEG')
    return 'data:image/jpeg;base64,{}'.format(
            base64.b64encode(buf.getvalue()).decode('utf-8'))


@app.callback(
        Output('t-label', 'src'),
        [Input('time-selector', 'value'),
         Input('well-selector', 'value')])
def callback(time, well_idx):
    buf = io.BytesIO()
    PIL.Image.fromarray(
            (255 * labels[well_idx, time, :, :]).astype(np.uint8)).save(buf, format='PNG')
    return 'data:image/png;base64,{}'.format(
            base64.b64encode(buf.getvalue()).decode('utf-8'))


@app.callback(
        Output('t+1-image', 'src'),
        [Input('time-selector', 'value'),
         Input('well-selector', 'value')])
def callback(time, well_idx):
    orgimg_paths = sorted(glob.glob(
            os.path.join(data_root, imaging_env, 'original', '*.jpg')))
    org_img = np.array(
            PIL.Image.open(orgimg_paths[time+1]).convert('L'), dtype=np.uint8)
    r, c = np.where(mask == well_idx)
    org_img = org_img[r.min():r.max(), c.min():c.max()]
    org_img = PIL.Image.fromarray(org_img)
    buf = io.BytesIO()
    org_img.save(buf, format='JPEG')
    return 'data:image/jpeg;base64,{}'.format(
            base64.b64encode(buf.getvalue()).decode('utf-8'))


@app.callback(
        Output('t+1-label', 'src'),
        [Input('time-selector', 'value'),
         Input('well-selector', 'value')])
def callback(time, well_idx):
    buf = io.BytesIO()
    PIL.Image.fromarray(
            (255 * labels[well_idx, time+1, :, :]).astype(np.uint8)).save(buf, format='PNG')
    return 'data:image/png;base64,{}'.format(
            base64.b64encode(buf.getvalue()).decode('utf-8'))


if __name__ == '__main__':
    app.run_server(debug=True)
