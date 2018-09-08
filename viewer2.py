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
import PIL.Image
import dash_auth
import numpy as np
import scipy.ndimage
import flask_caching
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State


DATA_ROOT = 'G:/Research/Drosophila/CUI/data/'
THETA = 50


# -------
#  Main
# -------
app = dash.Dash()
app.css.append_css(
        {'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})
cache = flask_caching.Cache()
cache.init_app(
        app.server, config={'CACHE_TYPE': 'filesystem', 'CACHE_DIR': 'cache/'})

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
                    'width': '300px',
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
                    'width': '300px',
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


@app.callback(
        Output('env-dropdown', 'options'),
        [Input('data-root', 'children')])
def callback(data_root):
    imaging_envs = [os.path.basename(i)
            for i in sorted(glob.glob(os.path.join(data_root, '*')))]

    return [{'label': i, 'value': i} for i in imaging_envs]


'''
@app.callback(
        Output('env-dropdown', 'value'),
        [Input('env-dropdown', 'options')])
def callback(envs):
    return envs[-1]['value']
'''


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


@cache.memoize()
def store_signals(data_root, env, morpho):
    if env is None:
        return

    signals = np.load(os.path.join(
        data_root, env, 'inference', morpho, 'signals.npy'))

    return signals


@cache.memoize()
def store_manual_evals(data_root, env, morpho):
    if env is None:
        return

    manual_evals = np.loadtxt(
            os.path.join(data_root, env, 'original', morpho),
            dtype=np.uint16,
            delimiter=',').flatten()

    return manual_evals


@cache.memoize()
def store_mask(data_root, env):
    if env is None:
        return

    return np.load(os.path.join(data_root, env, 'mask.npy'))



@app.callback(
        Output('current-morpho', 'children'),
        [Input('button', 'n_clicks')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('csv-dropdown', 'value'),
         State('morpho-dropdown', 'value')])
def callback(n_clicks, data_root, env, csv, morpho):
    print('[1] callback : button')
    if n_clicks is None:
        return ''

    print('[2] callback : button')
    store_signals(data_root, env, morpho)
    store_manual_evals(data_root, env, csv)
    store_mask(data_root, env)
    print('[3] callback : button')
    return morpho


@app.callback(
        Output('current-env', 'children'),
        [Input('current-morpho', 'children')],
        [State('env-dropdown', 'value')])
def callback(_, env):
    return env


@app.callback(
        Output('current-csv', 'children'),
        [Input('current-morpho', 'children')],
        [State('csv-dropdown', 'value')])
def callback(_, csv):
    return csv


@app.callback(
        Output('time-selector', 'max'),
        [Input('current-morpho', 'children')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('morpho-dropdown', 'value')])
def callback(_, data_root, env, morpho):
    print('[1] callback : time-selector max')
    if env is None:
        return

    signals = store_signals(data_root, env, morpho)
    return signals.shape[1] - 1


@app.callback(
        Output('threshold-slider', 'max'),
        [Input('current-morpho', 'children')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('morpho-dropdown', 'value')])
def callback(_, data_root, env, morpho):
    print('[1] callback : threshold-slider max')
    if env is None:
        return

    signals = store_signals(data_root, env, morpho)
    return signals.max()


@app.callback(
        Output('well-slider', 'max'),
        [Input('current-morpho', 'children')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('morpho-dropdown', 'value')])
def callback(_, data_root, env, morpho):
    print('[1] callback : well-slider max')
    if env is None:
        return

    signals = store_signals(data_root, env, morpho)
    return len(signals) - 1


@app.callback(
        Output('well-selector', 'max'),
        [Input('current-morpho', 'children')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('morpho-dropdown', 'value')])
def callback(_, data_root, env, morpho):
    print('[1] callback : well-selector max')
    if env is None:
        return

    signals = store_signals(data_root, env, morpho)
    return len(signals) - 1


@app.callback(
        Output('well-slider', 'value'),
        [Input('summary-graph', 'clickData'),
         Input('current-morpho', 'children')])
def callback(click_data, _):
    print('[1] callback : well-slider value')
    if click_data is None:
        return 20

    return click_data['points'][0]['pointNumber']


@app.callback(
        Output('well-selector', 'value'),
        [Input('well-slider', 'value')])
def callback(well_idx):
    print('[1] callback : well-selector value')
    return well_idx


@app.callback(
        Output('time-selector', 'value'),
        [Input('signal-graph', 'clickData')])
def callback(click_data):
    if click_data is None:
        return 0
    else:
        return click_data['points'][0]['x']


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
         State('morpho-dropdown', 'value')])
def callback(well_idx, threshold, rise_or_fall, time,
        figure, data_root, env, csv, morpho):
    if env is None:
        return {'data': []}

    if len(figure['data']) == 0:
        x, y = 0, 0
    else:
        x, y = time, figure['data'][0]['y'][time]

    signals = store_signals(data_root, env, morpho)
    manual_evals = store_manual_evals(data_root, env, csv)

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
        Output('summary-graph', 'figure'),
        [Input('threshold-slider', 'value'),
         Input('well-selector', 'value'),
         Input('target-dropdown', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('csv-dropdown', 'value'),
         State('morpho-dropdown', 'value')])
def callback(threshold, well_idx, rise_or_fall, data_root, env, csv, morpho):
    print('[1] callback : summary-graph')
    if env is None:
        return {'data': []}
    print('[2] callback : summary-graph')

    signals = store_signals(data_root, env, morpho)
    manual_evals = store_manual_evals(data_root, env, csv)

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
        Output('t-image', 'src'),
        [Input('time-selector', 'value'),
         Input('well-selector', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value')])
def callback(time, well_idx, data_root, env):
    if env is None:
        return ''

    mask = store_mask(data_root, env)
    orgimg_paths = sorted(glob.glob(
            os.path.join(data_root, env, 'original', '*.jpg')))
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
        Output('t+1-image', 'src'),
        [Input('time-selector', 'value'),
         Input('well-selector', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value')])
def callback(time, well_idx, data_root, env):
    if env is None:
        return ''

    mask = store_mask(data_root, env)
    orgimg_paths = sorted(glob.glob(
            os.path.join(data_root, env, 'original', '*.jpg')))
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
        Output('t-label', 'src'),
        [Input('time-selector', 'value'),
         Input('well-selector', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('current-morpho', 'children')])
def callback(time, well_idx, data_root, env, morpho):
    if env is None:
        return ''

    buf = io.BytesIO()
    PIL.Image.open(os.path.join(
            data_root, env, 'inference', morpho,
            '{:03d}'.format(well_idx),
            '{:04d}.png'.format(time+1))).save(buf, format='PNG')
    return 'data:image/png;base64,{}'.format(
            base64.b64encode(buf.getvalue()).decode('utf-8'))


@app.callback(
        Output('t+1-label', 'src'),
        [Input('time-selector', 'value'),
         Input('well-selector', 'value')],
        [State('data-root', 'children'),
         State('env-dropdown', 'value'),
         State('current-morpho', 'children')])
def callback(time, well_idx, data_root, env, morpho):
    if env is None:
        return ''

    buf = io.BytesIO()
    PIL.Image.open(os.path.join(
            data_root, env, 'inference', morpho,
            '{:03d}'.format(well_idx),
            '{:04d}.png'.format(time+2))).save(buf, format='PNG')
    return 'data:image/png;base64,{}'.format(
            base64.b64encode(buf.getvalue()).decode('utf-8'))


if __name__ == '__main__':
    app.run_server(debug=True)
