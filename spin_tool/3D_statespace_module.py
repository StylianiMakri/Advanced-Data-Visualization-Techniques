import json
import os
import networkx as nx
import plotly.graph_objs as go
import plotly.io as pio
import community as community_louvain  # python-louvain package


pio.renderers.default = "browser"

parsed_data_path = os.path.join("output", "parsed_data.json")
with open(parsed_data_path, "r") as f:
    data = json.load(f)

trail_data = data["trail"]

G = nx.DiGraph()
for step in trail_data:
    sid = f"s{step['step']}"
    label = f"P{step['proc_id']}@{step['line']}"
    G.add_node(sid, label=label, proc=step["proc_name"], step=step['step'])

for i in range(1, len(trail_data)):
    prev_sid = f"s{trail_data[i - 1]['step']}"
    curr_sid = f"s{trail_data[i]['step']}"
    G.add_edge(prev_sid, curr_sid, action=f"{trail_data[i - 1]['proc_name']} → {trail_data[i]['proc_name']}")

pos = nx.spring_layout(G, dim=3, seed=42)

#Louvain clustering
partition = community_louvain.best_partition(G.to_undirected())
nx.set_node_attributes(G, partition, 'cluster')


cluster_ids = set(partition.values())
palette = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
    "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
    "#bcbd22", "#17becf"
]
cluster_color_map = {cid: palette[i % len(palette)] for i, cid in enumerate(sorted(cluster_ids))}


color_start = "#0074D9" 
color_end = "#2ECC40"    

first_step = min(step['step'] for step in trail_data)
last_step = max(step['step'] for step in trail_data)

x, y, z = [], [], []
text = []       # permanent labels ("START", "END")
hovertext = []  
color = []
marker_size = []

for node, attrs in G.nodes(data=True):
    x.append(pos[node][0])
    y.append(pos[node][1])
    z.append(pos[node][2])

    step_num = attrs['step']
    label = attrs['label']
    proc = attrs['proc']
    cluster = attrs['cluster']

    base_hover = f"{node}: {label} ({proc}), Cluster: {cluster}, Step: {step_num}"

    # Start node
    if step_num == first_step:
        node_color = color_start
        size = 15
        text.append("START")
    # End node
    elif step_num == last_step:
        node_color = color_end
        size = 15
        text.append("END")
    else:
        node_color = cluster_color_map.get(cluster, "#888")
        size = 10
        text.append("")

    hovertext.append(base_hover)
    color.append(node_color)
    marker_size.append(size)

edge_x, edge_y, edge_z = [], [], []
for src, dst in G.edges():
    edge_x += [pos[src][0], pos[dst][0], None]
    edge_y += [pos[src][1], pos[dst][1], None]
    edge_z += [pos[src][2], pos[dst][2], None]

fig = go.Figure([
    go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        mode="lines",
        line=dict(color="gray", width=2),
        hoverinfo="none"
    ),
    go.Scatter3d(
        x=x, y=y, z=z,
        mode="markers+text",
        marker=dict(size=marker_size, color=color),
        text=text,
        hovertext=hovertext,
        hoverinfo="text",
        textposition="top center",
        textfont=dict(size=12, color="black"),
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
