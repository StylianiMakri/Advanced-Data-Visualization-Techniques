import re
import json
import os

def extract_simulation_block(file_path):
    with open(file_path, 'r') as f:
        lines = f.readlines()

    sim_start = None
    sim_end = None
    for i, line in enumerate(lines):
        if '===start Sim===' in line:
            sim_start = i + 1
        elif '===end Sim===' in line:
            sim_end = i
            break

    if sim_start is None or sim_end is None:
        raise ValueError("Simulation block not found.")

    return lines[sim_start:sim_end]

def parse_simulation_events(sim_lines, channel_map={'f': '2', 'you': '4'}):
    proc_counters = {}
    events = []

    for line in sim_lines:
        line = line.strip()

        match = re.search(
            r'proc\s+(\d+)\s+\(([^)]+)\).*?\[([a-zA-Z_]+)([!?])([^,\]\s]+),?\s*([^\]]*)\]', 
            line
        )
        if not match:
            continue

        proc_id = int(match.group(1))
        proc_full = match.group(2)
        chan_name = match.group(3)
        direction = match.group(4)  # ! or ?
        label = match.group(5)
        value = match.group(6).strip()

        base_name = proc_full.split(':')[0].strip()
        if base_name == 'init':
            proc_label = 'init'
        elif base_name == 'calc':
            if proc_id not in proc_counters:
                proc_counters[proc_id] = len(proc_counters) + 1
            proc_label = f"calc[{proc_counters[proc_id]}]"
        else:
            proc_label = base_name

        chan_id = channel_map.get(chan_name, chan_name)
        
        label_full = f"{chan_id}{direction}{label}"
        if value:
            label_full += f",{value}"

        events.append((proc_label, label_full))

    return events

def save_sim_data(events, output_path="output/sim_data.json"):
    sim_dict = [{"process": proc, "action": action} for proc, action in events]
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(sim_dict, f, indent=2)

def process_single_txt_in_data(channel_map={'f': '2', 'you': '4'}):
    data_dir = "data"

    txt_files = [f for f in os.listdir(data_dir) if f.endswith(".txt")]
    if len(txt_files) != 1:
        raise ValueError(f"Expected exactly one .txt file in /data/, found {len(txt_files)}")

    filename = txt_files[0]
    input_path = os.path.join(data_dir, filename)

    sim_lines = extract_simulation_block(input_path)
    events = parse_simulation_events(sim_lines, channel_map)
    save_sim_data(events)

if __name__ == "__main__":
    process_single_txt_in_data()
