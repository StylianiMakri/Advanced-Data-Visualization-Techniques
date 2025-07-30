import json
import os
import networkx as nx
import plotly.graph_objs as go
import plotly.io as pio

pio.renderers.default = "browser"

parsed_data_path = os.path.join("output", "parsed_data.json")
with open(parsed_data_path, "r") as f:
    data = json.load(f)

trail_data = data["trail"]

process_names = sorted(set(step['proc_name'] for step in trail_data))
proc_to_z = {proc: i for i, proc in enumerate(process_names)}

palette = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
    "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
    "#bcbd22", "#17becf"
]
proc_color_map = {proc: palette[i % len(palette)] for i, proc in enumerate(process_names)}

G = nx.DiGraph()
for step in trail_data:
    sid = f"s{step['step']}"
    label = f"P{step['proc_id']}@{step['line']}"
    depth = step.get('depth', 0)
    G.add_node(sid, label=label, proc=step['proc_name'], step=step['step'], depth=depth)

for i in range(1, len(trail_data)):
    prev_sid = f"s{trail_data[i - 1]['step']}"
    curr_sid = f"s{trail_data[i]['step']}"
    G.add_edge(prev_sid, curr_sid)

node_traces = []
edge_traces = []

first_step = min(step['step'] for step in trail_data)
last_step = max(step['step'] for step in trail_data)

for proc in process_names:
    x, y, z = [], [], []
    text, hovertext, color, marker_size = [], [], [], []
    
    for node, attrs in G.nodes(data=True):
        if attrs['proc'] != proc:
            continue
        step = attrs['step']
        depth = attrs['depth']
        z_val = proc_to_z[proc]

        x.append(step)
        y.append(depth)
        z.append(z_val)
        hovertext.append(f"Step {step} | Proc: {proc} | Depth: {depth} | Label: {attrs['label']}")
        marker_size.append(12 if step in (first_step, last_step) else 8)
        text.append("START" if step == first_step else "END" if step == last_step else "")
        color.append(proc_color_map[proc])
    
    node_traces.append(go.Scatter3d(
        x=x, y=y, z=z,
        mode="markers+text",
        name=proc,
        marker=dict(size=marker_size, color=color),
        text=text,
        hovertext=hovertext,
        hoverinfo="text",
        textposition="top center",
        textfont=dict(size=12, color="black"),
        visible=True  # Start with all visible
    ))

edge_x, edge_y, edge_z = [], [], []
for src, dst in G.edges():
    edge_x += [G.nodes[src]['step'], G.nodes[dst]['step'], None]
    edge_y += [G.nodes[src]['depth'], G.nodes[dst]['depth'], None]
    edge_z += [proc_to_z[G.nodes[src]['proc']], proc_to_z[G.nodes[dst]['proc']], None]

edge_trace = go.Scatter3d(
    x=edge_x, y=edge_y, z=edge_z,
    mode="lines",
    line=dict(color="gray", width=2),
    hoverinfo="none",
    name="Edges",
    visible=True
)
edge_traces.append(edge_trace)

dropdown_buttons = [
    {
        "label": "All Processes",
        "method": "update",
        "args": [
            {"visible": [True] * (len(node_traces) + 1)},  # all nodes + edges
            {"title": "All Processes"}
        ]
    }
]

for i, proc in enumerate(process_names):
    visibility = [False] * (len(node_traces) + 1)
    visibility[i] = True  # show only this process' nodes
    visibility[-1] = True  # always show edges
    dropdown_buttons.append({
        "label": proc,
        "method": "update",
        "args": [
            {"visible": visibility},
            {"title": f"Process: {proc}"}
        ]
    })

fig = go.Figure(data=edge_traces + node_traces)

fig.update_layout(
    title="SPIN Trail Visualization (Step x Depth x Process)",
    scene=dict(
        xaxis=dict(title="Step"),
        yaxis=dict(title="Depth"),
        zaxis=dict(
            title="Process",
            tickvals=list(proc_to_z.values()),
            ticktext=list(proc_to_z.keys())
        )
    ),
    updatemenus=[{
        "buttons": dropdown_buttons,
        "direction": "down",
        "showactive": True,
        "x": 0.0,
        "y": 1.15,
        "xanchor": "left",
        "yanchor": "top"
    }],
    margin=dict(l=0, r=0, b=0, t=40)
)

fig.show()
