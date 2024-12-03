import pandas as pd
import re
import plotly.graph_objects as go
from datetime import datetime as dt
import zoneinfo
import os
import plotly.io as pio

TPT_REGEX = r"(\|\s+\d+\s+\|\s+\w+\s+\|\s+\d+\s+\|.*\|)"
LINK_REGEX = r"(\|\s+\d+\s+\|\s+\d+\s+\|.+\|\s+\d+\s+\|)"
IPERF_REGEX = r"(\d+\.\d+)-.+\s+(\d+)\s+"

def plot_tpt(logfile, direction="DL", outlier_control=10):
    header = [
        "UE-ID", "RB-ID", "PCELL-ID", "DL-TPT (Mb)", "UL-TPT (Mb)", 
        "DL-PKT-RX", "RLC-DL-TPT (Mb)", "RLC-UL-TPT (Mb)", 
        "MAC-DL-TPT (Mb)", "MAC-UL-TPT (Mb)", "CL-DL-TPT (Mb)", 
        "CL-UL-TPT (Mb)", "UL-PKT-TX", "NUM-SR"
    ]
    data = []
    timestamps = []

    with open(logfile, "r", errors="ignore") as file:
        text = file.readlines()

    for i, line in enumerate(text):
        match = re.search(TPT_REGEX, line)
        if match:
            result = [i.strip() for i in match.group().split("|")[1:-1]]
            data.append(result)

            time_search_window = text[max(0, i-10):i]
            for time_line in time_search_window:
                time_match = re.search(r"\(UTC (\d+)\)", time_line)
                if time_match:
                    utc_timestamp = int(time_match.group(1)) / 1000
                    timestamps.append(dt.fromtimestamp(utc_timestamp).strftime("%Y-%m-%d %H:%M:%S"))
    
    df = pd.DataFrame(data, columns=header)
    df["Timestamps"] = pd.to_datetime(timestamps, format="%Y-%m-%d %H:%M:%S")

    if outlier_control > 0:
        df["DL-TPT (Mb)"] = df["DL-TPT (Mb)"].rolling(outlier_control).median()
        df["UL-TPT (Mb)"] = df["UL-TPT (Mb)"].rolling(outlier_control).median()

    fig = go.Figure(layout={"autosize": True})
    fig.add_trace(go.Scatter(x=df["Timestamps"], y=df["DL-TPT (Mb)"], mode="lines", name="DL-TPT (Mb)"))
    fig.add_trace(go.Scatter(x=df["Timestamps"], y=df["UL-TPT (Mb)"], mode="lines", name="UL-TPT (Mb)"))

    fig.update_layout(
        title="Throughput Over Time",
        xaxis_title="Timestamps",
        yaxis_title="Throughput (Mb)",
        xaxis=dict(tickformat="%H:%M:%S", tickangle=-45, nticks=30),
    )

    return fig

def plot_link(logfile):
    header = [
        "RNTI", "CELL-ID", "DL-BLER% CW-0/1", "RI RX/UL/DL", "DL-CQI CW-0/1",
        "DL-MCS CW-0/1", "256QAM Alloc", "SMALL ALLOC", "UL-BLER-CRC% PER", 
        "UL-CQI CW-0/1", "UL-MCS CW-0/1", "C2I", "256QAM ACTV", 
        "MEAS GAP ACTIVE", "CA MODE", "BEAMID", "Connected Time(Min)"
    ]
    data = []
    timestamps = []

    with open(logfile, "r", errors="ignore") as file:
        text = file.readlines()

    for i, line in enumerate(text):
        match = re.search(LINK_REGEX, line)
        if match:
            result = [i.strip() for i in match.group().split("|")[1:-1]]
            data.append(result)

            time_search_window = text[max(0, i-10):i]
            for time_line in time_search_window:
                time_match = re.search(r"\(UTC (\d+)\)", time_line)
                if time_match:
                    utc_timestamp = int(time_match.group(1)) / 1000
                    timestamps.append(dt.fromtimestamp(utc_timestamp).strftime("%Y-%m-%d %H:%M:%S"))
    
    df = pd.DataFrame(data, columns=header)
    df["Timestamps"] = pd.to_datetime(timestamps, format="%Y-%m-%d %H:%M:%S")
    df['DL-MCS CW-0/1'] = df['DL-MCS CW-0/1'].str.split('/').str[0]
    df['UL-MCS CW-0/1'] = df['UL-MCS CW-0/1'].str.split('/').str[0]
    df['DL-BLER% CW-0/1'] = df['DL-BLER% CW-0/1'].str.split('/').str[0]
    df.to_csv("data.csv")
    #df["DL-BLER% CW-0/1"] = df["DL-BLER% CW-0/1"].rolling(10).median()
    #df["UL-BLER-CRC% PER"] = df["UL-BLER-CRC% PER"].rolling(3).median()
    fig = go.Figure()

    # Plot MCS
    fig.add_trace(go.Scatter(x=df["Timestamps"], y=df["DL-MCS CW-0/1"], mode="lines", name="DL MCS", yaxis="y1", line=dict(color="blue"), opacity=0.8))
    fig.add_trace(go.Scatter(x=df["Timestamps"], y=df["UL-MCS CW-0/1"], mode="lines", name="UL MCS", yaxis="y1", line=dict(color="darkorange"), opacity=0.8))
    # Plot BLER on secondary y-axis
    fig.add_trace(go.Scatter(x=df["Timestamps"], y=df["DL-BLER% CW-0/1"], mode="lines", name="DL BLER", yaxis="y2", line=dict(color="green"), opacity=0.8))
    fig.add_trace(go.Scatter(x=df["Timestamps"], y=df["UL-BLER-CRC% PER"], mode="lines", name="UL BLER", yaxis="y2", line=dict(color="red"), opacity=0.8))


    fig.update_layout(
        title="Link Parameters Over Time",
        xaxis=dict(title="Timestamps", tickformat="%H:%M:%S", tickangle=-45, nticks=30),
        yaxis=dict(title="MCS", range=[0, 30], side="left", type="linear", tick0=0, dtick=5),
        yaxis2=dict(title="BLER", overlaying="y", side="right", range=[0, 100], type="linear", tick0=0, dtick=10),
    )

    return fig

def plot_iperf(logfile, outlier_control=20):
    iperf_data, timestamps = [], []

    with open(logfile, "r", errors="ignore") as file:
        text = file.readlines()
    for line in text:
        match = re.search(IPERF_REGEX, line)
        if match:
            iperf_data.append(int(match.group(2)))
            timestamps.append(float(match.group(1)))

    df = pd.DataFrame({"Throughput": iperf_data, "Timestamps": timestamps})
    if outlier_control > 0:
        df["Throughput"] = df["Throughput"].rolling(outlier_control).median()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Timestamps"], y=df["Throughput"], mode="lines", name="Throughput"))

    fig.update_layout(
        title="iPerf Throughput",
        xaxis_title="Seconds",
        yaxis_title="Throughput (Mbps)",
        yaxis=dict(range=[0, 800], tickangle=-45),
        xaxis=dict(nticks=30, tickangle=-45)
    )

    return fig

def identify_log_type(logfile):
    counters = {
        "tpt": 0,
        "link": 0,
        "iperf": 0
    }
    with open(logfile, "r", errors="ignore") as file:
        text = file.readlines()
    for line in text:
        tpt_regexp = re.search(TPT_REGEX, line)
        link_regexp = re.search(LINK_REGEX, line)
        iperf_regexp = re.search(IPERF_REGEX, line)
        if tpt_regexp:
            counters["tpt"] += 1
        elif link_regexp:
            counters["link"] += 1
        elif iperf_regexp:
            counters["iperf"] += 1
    return max(counters, key=counters.get)

def process_text_file(logfile):
    logfile_path = f'uploads/{logfile}'
    log_type = identify_log_type(logfile_path)
    
    if log_type == "tpt":
        fig = plot_tpt(logfile_path, direction="DL", outlier_control=5)
    elif log_type == "link":
        fig = plot_link(logfile_path)
    elif log_type == "iperf":
        fig = plot_iperf(logfile_path, outlier_control=5)

    fig.update_layout(
        autosize=True,
        overwrite=True,
        margin=dict(l=20, r=20, t=50, b=20),
        hovermode="x unified",
        width=1200
    )
    config = {
        "displayModeBar": True,
        "responsive": True,
        "autosizable": True,
    }

    plot_html = fig.to_html(config=config, full_html=False, include_plotlyjs=False)
    return plot_html

    # Save the plot as an HTML file
    # plot_filename = 'plot.html'
    # output_path = os.path.join("plots", plot_filename)
    # fig.write_html(output_path)
    # return plot_filename

    # # Convert Plotly figure to HTML div string
    # plot_html = pio.to_html(fig, full_html=False)
    # print(plot_html)
    # return plot_html

# Usage example
# plot_tpt("./nrcli_analyzer/udp_dl_ueshow.log", direction="DL", outlier_control=5)
