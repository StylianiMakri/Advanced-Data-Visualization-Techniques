import re
import json
import matplotlib.pyplot as plt
from collections import defaultdict

# === 1. Load and parse pan.out ===
def parse_pan_out(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    result = {
        "errors": "errors: 0" not in content,
        "details": content.strip()
    }
    return result

# === 2. Parse trail.txt into structured steps ===
def parse_trail(filepath):
    steps = []
    with open(filepath, 'r') as f:
        for line in f:
            match = re.search(r'proc (\d+) \((.*?)\):line (\d+) "(.*?)"', line)
            if match:
                proc_id, proc_name, line_no, action = match.groups()
                steps.append({
                    "proc_id": int(proc_id),
                    "proc_name": proc_name,
                    "line_no": int(line_no),
                    "action": action
                })
    return steps

# === 3. Visualize the sequence of actions ===
def plot_action_sequence(steps):
    proc_actions = defaultdict(list)
    for i, step in enumerate(steps):
        proc_actions[step["proc_name"]].append((i, step["action"]))
    
    plt.figure(figsize=(12, 6))
    for idx, (proc, actions) in enumerate(proc_actions.items()):
        x = [a[0] for a in actions]
        y = [idx]*len(actions)
        labels = [a[1] for a in actions]
        plt.scatter(x, y, label=proc)
        for xi, yi, lbl in zip(x, y, labels):
            plt.text(xi, yi + 0.1, lbl, rotation=45, fontsize=8)
    
    plt.yticks(range(len(proc_actions)), list(proc_actions.keys()))
    plt.xlabel("Step")
    plt.title("Process Action Sequence from trail.txt")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# === Entry point for user ===
def main(pan_path, trail_path):
    print("=== PAN.OUT RESULTS ===")
    pan_results = parse_pan_out(pan_path)
    print(json.dumps(pan_results, indent=2))
    
    print("\n=== TRAIL STEPS ===")
    steps = parse_trail(trail_path)
    for step in steps[:10]:  # Show first 10 for brevity
        print(step)
    
    print("\n=== PLOTTING TRACE ===")
    plot_action_sequence(steps)

# Example usage:
# main("pan.out", "trail.txt")
