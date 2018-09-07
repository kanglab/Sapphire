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
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State


DATA_ROOT = 'G:/Research/Drosophila/CUI/data/'


# -------
#  Main
# -------
app = dash.Dash()
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
            'Npy file :',
            html.Br(),
            html.Div([
                dcc.Dropdown(
                    id='npy-dropdown',
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
            'Imaging environment :',
            html.Div(id='imaging-env'),
            'Current npy file :',
            html.Div(id='current-npy'),
            'File name :',
            html.Div(id='manual-evals-file'),
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
        Output('npy-dropdown', 'options'),
        [Input('env-dropdown', 'value')],
        [State('data-root', 'children')])
def callback(env, data_root):
    if env is None:
        return []
    npys = [os.path.basename(i)
            for i in sorted(glob.glob(os.path.join(
                data_root, env, 'matsu_signal_data_*.npy')))]
    return [{'label': i, 'value': i} for i in npys]


if __name__ == '__main__':
    app.run_server(debug=True)
