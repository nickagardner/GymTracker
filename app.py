import pytz
import datetime
import pandas as pd

import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

from plot_utilities import query_db, get_daily, get_weekly
from constants import TIMEZONE, FORMAT_PRED_NAMES, FORMAT_VALUE_NAMES, VALUE_COLORS, PRED_COLORS

today = datetime.datetime.now()
tz = pytz.timezone('UTC')
today = tz.localize(today).astimezone(pytz.timezone(TIMEZONE))

df, pred_df = query_db(TIMEZONE)

app = Dash(__name__)

server = app.server

app.layout = html.Div([
    html.Div([
        dcc.Dropdown(['Daily', 'Weekly'], 'Daily', id='view_dropdown',
                     style={'height': '48px', 'width': '132px'}),
        dcc.DatePickerSingle(month_format='MMMM Y', placeholder='MMMM Y',
                             date=today, id='date_selector'),
    ], style={'display': 'flex'}),
    dcc.Graph(id="graph")
])

funcs = [get_daily, get_weekly]
yaxis_titles = ["Number of Occupants", "12-Hour Average Number of Occupants"]


@app.callback(
    Output("graph", "figure"),
    Input('view_dropdown', 'value'),
    Input('date_selector', 'date')
)
def update_graph(view, now):
    """
    Updates graph based on input from user
    Args:
        view: Which view to use: daily or weekly
        now: What day to focus on (from calendar widget)

    Returns:
        Figure to render
    """
    fig = go.Figure()
    view_idx = 0 if view == "Daily" else 1
    now = pd.Timestamp(now)
    try:
        tz = pytz.timezone(TIMEZONE)
        now = tz.localize(now)
    except:
        # timezone already localized
        pass
    if now.date() == today.date():
        now = today

    df_subset, pred_df_subset, begin, end = funcs[view_idx](df, pred_df, TIMEZONE, now)
    for col_idx, column in enumerate(df_subset.columns[1:]):
        fig.add_trace(go.Scatter(x=df_subset["date"], y=df_subset[column],
                                 mode='lines+markers',
                                 name=FORMAT_VALUE_NAMES[col_idx],
                                 line=dict(color=VALUE_COLORS[col_idx])))

    if len(pred_df_subset) > 0:
        for col_idx, column in enumerate(df_subset.columns[1:]):
            try:
                last_val = df_subset.iloc[-1]
                pred_df_temp = pred_df_subset[pred_df_subset['date'] > last_val.date]
                final_df = pd.concat([last_val, pred_df_temp]).reset_index(drop=True)
            except:
                # no historical datapoint to connect to
                final_df = pred_df_subset
            fig.add_trace(go.Scatter(x=final_df["date"], y=final_df[column],
                                     mode='lines+markers',
                                     name=FORMAT_PRED_NAMES[col_idx],
                                     line=dict(color=PRED_COLORS[col_idx])))
    fig.update_xaxes(range=[begin, end])
    fig.update_layout(title="RIT Recreation Facility Occupancy", xaxis_title="Datetime",
                      yaxis_title=yaxis_titles[view_idx], legend_title="Facility Name")
    return fig


if __name__ == '__main__':
    app.run_server(debug=True)