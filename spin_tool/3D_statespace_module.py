import json
import os
import networkx as nx
import plotly.graph_objs as go
import plotly.io as pio

# Open Plotly in the browser
pio.renderers.default = "browser"

# Load JSON trail file from output/parsed_data.json
parsed_data_path = os.path.join("output", "parsed_data.json")
with open(parsed_data_path, "r") as f:
    data = json.load(f)

trail_data = data["trail"]

# Build directed graph
G = nx.DiGraph()
for i, step in enumerate(trail_data):
    sid = f"s{step['step']}"
    label = f"P{step['proc_id']}@{step['line']}"
    G.add_node(sid, label=label, proc=step["proc_name"])

    if i > 0:
        prev_sid = f"s{trail_data[i - 1]['step']}"
        G.add_edge(prev_sid, sid, action=f"{trail_data[i - 1]['proc_name']} → {step['proc_name']}")

# Layout for 3D
pos = nx.spring_layout(G, dim=3, seed=42)
x, y, z, text, color = [], [], [], [], []
for node, attrs in G.nodes(data=True):
    x.append(pos[node][0])
    y.append(pos[node][1])
    z.append(pos[node][2])
    text.append(f"{node}: {attrs['label']} ({attrs['proc']})")
    color.append("blue")

# Edges
edge_x, edge_y, edge_z = [], [], []
for src, dst in G.edges():
    edge_x += [pos[src][0], pos[dst][0], None]
    edge_y += [pos[src][1], pos[dst][1], None]
    edge_z += [pos[src][2], pos[dst][2], None]

# Create Plotly figure
fig = go.Figure([
    go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z, mode="lines",
        line=dict(color="gray", width=2), hoverinfo="none"
    ),
    go.Scatter3d(
        x=x, y=y, z=z, mode="markers+text",
        text=text, marker=dict(size=5, color=color), hoverinfo="text"
    )
])

fig.update_layout(
    title="3D SPIN Trail State Space",
    scene=dict(
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False),
        zaxis=dict(showgrid=False)
    ),
    margin=dict(l=0, r=0, b=0, t=30)
)

fig.show()
