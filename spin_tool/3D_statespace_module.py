import json
import os
import networkx as nx
import plotly.graph_objs as go
import plotly.io as pio
import community as community_louvain

# Open Plotly in the browser
pio.renderers.default = "browser"

# Load JSON trail file from output/parsed_data.json
parsed_data_path = os.path.join("output", "parsed_data.json")
with open(parsed_data_path, "r") as f:
    data = json.load(f)

trail_data = data["trail"]

# Build directed graph
G = nx.DiGraph()
for step in trail_data:
    sid = f"s{step['step']}"
    label = f"P{step['proc_id']}@{step['line']}"
    G.add_node(sid, label=label, proc=step["proc_name"], step=step['step'])

for i in range(1, len(trail_data)):
    prev_sid = f"s{trail_data[i - 1]['step']}"
    curr_sid = f"s{trail_data[i]['step']}"
    G.add_edge(prev_sid, curr_sid, action=f"{trail_data[i - 1]['proc_name']} → {trail_data[i]['proc_name']}")

# Compute 3D layout once for all nodes
pos = nx.spring_layout(G, dim=3, seed=42)

# Community detection (Louvain clustering)
partition = community_louvain.best_partition(G.to_undirected())
nx.set_node_attributes(G, partition, 'cluster')

# Generate color palette for clusters
cluster_ids = set(partition.values())
palette = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
    "#9467bd", "#8c564b", "#e377c2", "#B819B3",
    "#bcbd22", "#17becf",  "#50411C", "#22126F", "#538548", "#1D9E9A", "#4E1011"
]
cluster_color_map = {cid: palette[i % len(palette)] for i, cid in enumerate(sorted(cluster_ids))}


process_names = set(nx.get_node_attributes(G, "proc").values())
process_palette = [
     "#636EFA", "#EF553B", "#00CC96", "#AB63FA",
     "#FFA15A", "#F3193D", "#EDF161", "#B6E880",
     "#50411C", "#22126F", "#538548", "#1D9E9A", "#4E1011", "#760DDF"
 ]
process_color_map = {pname: process_palette[i % len(process_palette)] for i, pname in enumerate(sorted(process_names))}


x, y, z, text, color = [], [], [], [], []
for node, attrs in G.nodes(data=True):
    x.append(pos[node][0])
    y.append(pos[node][1])
    z.append(pos[node][2])
    text.append(f"{node}: {attrs['label']} ({attrs['proc']}), Cluster: {attrs['cluster']}, Step: {attrs['step']}")

    # Color by cluster
    color.append(cluster_color_map.get(attrs['cluster'], "#888"))

    # To color by process instead, uncomment below and comment out the line above
    # color.append(process_color_map.get(attrs['proc'], "#888"))

# Prepare edges
edge_x, edge_y, edge_z = [], [], []
for src, dst in G.edges():
    edge_x += [pos[src][0], pos[dst][0], None]
    edge_y += [pos[src][1], pos[dst][1], None]
    edge_z += [pos[src][2], pos[dst][2], None]

# Create Plotly figure without slider
fig = go.Figure([
    go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        mode="lines",
        line=dict(color="gray", width=2),
        hoverinfo="none"
    ),
    go.Scatter3d(
        x=x, y=y, z=z,
        mode="markers",
        marker=dict(size=5, color=color),
        text=text,
        hoverinfo="text"
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
