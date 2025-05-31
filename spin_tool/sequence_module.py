import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import defaultdict


with open("output/parsed_data.json", "r") as f:
    data = json.load(f)


trail = data["trail"]


process_timelines = defaultdict(list)
for entry in trail:
    process_timelines[entry["proc_name"]].append((entry["step"], entry["line"], entry["action"]))


processes = list(process_timelines.keys())
colors = plt.cm.get_cmap("tab10", len(processes))


fig, ax = plt.subplots(figsize=(14, 6))


for i, proc in enumerate(processes):
    timeline = process_timelines[proc]
    y = i
    for step, line, action in timeline:
        ax.broken_barh([(step, 1)], (y - 0.4, 0.8), facecolors=colors(i), edgecolor="black")
        ax.text(step + 0.05, y, f"L{line}", va="center", ha="left", fontsize=7)


ax.set_yticks(range(len(processes)))
ax.set_yticklabels(processes)
ax.set_xlabel("Step")
ax.set_title("Process Execution Timeline")
ax.grid(True, axis="x", linestyle="--", alpha=0.7)

plt.tight_layout()
plt.show()
