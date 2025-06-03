import re
import os
import matplotlib.pyplot as plt
import seaborn as sns

# === Step 1: Search for .out file in /data folder (no renaming) ===

data_folder = os.path.join(os.getcwd(), "data")

# Find the first .out file
out_files = [f for f in os.listdir(data_folder) if f.endswith(".out")]
if out_files:
    out_path = os.path.join(data_folder, out_files[0])
    print(f"Using file: {out_files[0]}")
else:
    print("Error: No '.out' file found in the /data folder.")
    exit(1)

# === Step 2: Parse SPIN output ===

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
                numbers = re.findall(r'\d+', line)
                if len(numbers) >= 2:
                    data["statespace"]["states_stored"] = int(numbers[0])
                    data["statespace"]["states_visited"] = int(numbers[1])

            if "states, matched" in line:
                numbers = re.findall(r'\d+', line)
                if numbers:
                    data["statespace"]["states_matched"] = int(numbers[0])

            if "transitions" in line:
                numbers = re.findall(r'\d+', line)
                if numbers:
                    data["statespace"]["transitions"] = int(numbers[0])

            if "atomic steps" in line:
                numbers = re.findall(r'\d+', line)
                if numbers:
                    data["statespace"]["atomic_steps"] = int(numbers[0])

            if "hash conflicts" in line:
                numbers = re.findall(r'\d+', line)
                if numbers:
                    data["statespace"]["hash_conflicts"] = int(numbers[0])

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

# === Step 3: Visualization ===

def visualize_data(data):
    sns.set(style="whitegrid")

    import matplotlib.gridspec as gridspec

    fig = plt.figure(figsize=(16, 8))
    gs = gridspec.GridSpec(1, 2)  # 1 row, 2 columns

    # Bar Chart (left)
    ax1 = fig.add_subplot(gs[0, 0])
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
    sns.barplot(x=labels, y=values, palette="viridis", ax=ax1)
    ax1.set_title("SPIN Statespace Statistics")
    ax1.set_ylabel("Count")
    ax1.tick_params(axis='x', rotation=45)

    # Pie Chart (right)
    ax2 = fig.add_subplot(gs[0, 1])
    if data["memory_usage"]:
        ax2.pie(
            data["memory_usage"].values(),
            labels=data["memory_usage"].keys(),
            autopct='%1.1f%%',
            colors=sns.color_palette("coolwarm", len(data["memory_usage"]))
        )
        ax2.set_title("Memory Usage Breakdown")
    else:
        ax2.text(0.5, 0.5, "No Memory Usage Info", ha='center', va='center')
        ax2.set_title("Memory Usage Breakdown")
        ax2.axis('off')

    fig.suptitle("SPIN Verification Overview", fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.95])  # Adjust title space
    plt.show()


# === Step 4: Run ===

data = parse_spin_output(out_path)
visualize_data(data)
