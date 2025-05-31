import re
import os
import matplotlib.pyplot as plt
import seaborn as sns

file_path = os.path.join(os.getcwd(), "output_visualizer", "pan.txt")

if os.path.exists(os.path.join(os.getcwd(), "output_visualizer", "pan.out")) and not os.path.exists(file_path):
    os.rename(os.path.join(os.getcwd(), "output_visualizer", "pan.out"), file_path)
    print("Renamed 'pan.out' to 'pan.txt'")

if not os.path.exists(file_path):
    print(f"Error: The file '{file_path}' does not exist.")
    exit(1)

def parse_spin_output(file_path):
    data = {
        "compilation_flags": [],
        "settings": [],
        "checks": {},
        "statespace": {
            "state_vector_size": 0,
            "depth_reached": 0,
            "states_stored": 0,
            "states_visited": 0,
            "states_matched": 0,
            "transitions": 0,
            "atomic_steps": 0,
            "hash_conflicts": 0
        },
        "memory_usage": {},
        "unreached": [],
        "elapsed_time": 0.0,
        "errors": 0,
        "final_status": ""
    }

    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith('spin -a') or 'gcc' in line or './pan' in line:
                data["compilation_flags"].append(line.strip())

            if 'Partial Order Reduction' in line:
                data["settings"].append("Partial Order Reduction enabled")

            if 'never claim' in line:
                data["checks"]["never_claim"] = '+' in line
            if 'assertion violations' in line:
                data["checks"]["assertion_violations"] = '+' in line
            if 'non-progress cycles' in line:
                data["checks"]["non_progress_cycles"] = '+' in line
            if 'invalid end states' in line:
                data["checks"]["invalid_end_states"] = '+' in line

            if "State-vector" in line:
                match = re.search(r'State-vector (\d+) byte, depth reached (\d+), errors: (\d+)', line)
                if match:
                    data["statespace"]["state_vector_size"] = int(match.group(1))
                    data["statespace"]["depth_reached"] = int(match.group(2))
                    data["errors"] = int(match.group(3))
            if "states, stored" in line:
                data["statespace"]["states_stored"] = int(re.findall(r'\d+', line)[0])
                data["statespace"]["states_visited"] = int(re.findall(r'\d+', line)[1])
            if "states, matched" in line:
                data["statespace"]["states_matched"] = int(re.findall(r'\d+', line)[0])
            if "transitions" in line:
                data["statespace"]["transitions"] = int(re.findall(r'\d+', line)[0])
            if "atomic steps" in line:
                data["statespace"]["atomic_steps"] = int(re.findall(r'\d+', line)[0])
            if "hash conflicts" in line:
                data["statespace"]["hash_conflicts"] = int(re.findall(r'\d+', line)[0])

            if "memory used" in line or "memory usage" in line:
                match = re.findall(r'([0-9\.]+)\s+memory used for ([^\(]+)', line)
                for value, key in match:
                    data["memory_usage"][key.strip()] = float(value)

            if "unreached in proctype" in line or "unreached in init" in line:
                data["unreached"].append(line.strip())

            if "elapsed time" in line:
                match = re.search(r'elapsed time ([\d\.]+) seconds', line)
                if match:
                    data["elapsed_time"] = float(match.group(1))

            if "No errors found" in line or "errors found" in line:
                data["final_status"] = line.strip()

    return data

def visualize_data(data):
    sns.set(style="whitegrid")

    plt.figure(figsize=(10, 6))
    labels = ["States Stored", "States Visited", "States Matched", "Transitions", "Depth Reached", "Errors", "Hash Conflicts"]
    values = [
        data["statespace"]["states_stored"],
        data["statespace"]["states_visited"],
        data["statespace"]["states_matched"],
        data["statespace"]["transitions"],
        data["statespace"]["depth_reached"],
        data["errors"],
        data["statespace"]["hash_conflicts"]
    ]
    sns.barplot(x=labels, y=values, palette="viridis")
    plt.xticks(rotation=45)
    plt.ylabel("Count")
    plt.title("SPIN Verification - Statespace Statistics")
    plt.tight_layout()
    plt.show()

    if data["memory_usage"]:
        plt.figure(figsize=(6, 6))
        plt.pie(data["memory_usage"].values(), labels=data["memory_usage"].keys(), autopct='%1.1f%%', colors=sns.color_palette("coolwarm", len(data["memory_usage"])))
        plt.title("Memory Usage Breakdown")
        plt.show()

    fig, ax = plt.subplots(figsize=(12, 8))
    ax.axis('off')  # Hide axes

    text_content = ""

    text_content += "Compilation Commands:\n"
    for cmd in data["compilation_flags"]:
        text_content += f"  - {cmd}\n"

    text_content += "\nSPIN Settings Used:\n"
    for setting in data["settings"]:
        text_content += f"  - {setting}\n"

    text_content += "\nVerification Checks:\n"
    for check, passed in data["checks"].items():
        result = "Passed" if passed else "Failed"
        text_content += f"  - {check}: {result}\n"

    text_content += "\nUnreached Code Sections:\n"
    for unreachable in data["unreached"]:
        text_content += f"  - {unreachable}\n"

    text_content += f"\nElapsed Time: {data['elapsed_time']} seconds\n"
    text_content += f"Final Status: {data['final_status']}\n"

    plt.text(0.01, 0.99, text_content, fontsize=12, va='top', ha='left', family='monospace')
    plt.title("SPIN Detailed Verification Report", fontsize=16)
    plt.tight_layout()
    plt.show()

data = parse_spin_output(file_path)
visualize_data(data)
