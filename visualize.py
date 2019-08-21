#!/usr/bin/env python3
import datetime
import json
import os
import sys
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_history(history):
    amps = [data['amps']*1000 for data in history]
    timestamps = [datetime.datetime.fromtimestamp(data['collection_time']).strftime("%Y-%m-%dT%H:%M:%S.%f") for data in history]
    amp_hours = [data['data_groups'][data['data_group_selected']]['amp_hours']*1000 for data in history]
    fig = go.Figure()
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=timestamps, y=amps, name='Amps'), secondary_y=False)
    fig.add_trace(go.Scatter(x=timestamps, y=amp_hours, name='mAh'), secondary_y=True)
    fig.update_layout(title='Device charging', xaxis_title='Time', yaxis_title='mA')
    fig.update_yaxes(rangemode="tozero", secondary_y=False)
    fig.update_yaxes(rangemode="tozero", title='mAh', secondary_y=True)
    fig.show()


def main():
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        json_file = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), 'charge.json')
    charge_history = []
    try:
        with open(json_file, 'r') as file:
            charge_history = json.load(file)
    except Exception as e:
        print(e)
    plot_history(charge_history)

if __name__ == '__main__':
    main()
