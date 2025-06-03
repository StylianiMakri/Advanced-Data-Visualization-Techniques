

import os
import re
import json
from collections import defaultdict


def parse_trail_file(trail_path):
    steps = []
    with open(trail_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('-4'):
                continue
            parts = line.split(':')
            if len(parts) != 3:
                continue
            step, proc_id, line_no = parts
            steps.append({
                "step": int(step),
                "proc_id": int(proc_id),
                "proc_name": f"Process_{proc_id}",
                "line": int(line_no),
                "action": f"Executed line {line_no}"
            })
    return steps


def parse_pan_out(pan_path):
    """
    Parse pan.out to extract detailed assertion failures, deadlocks, invalid end states, etc.
    Returns a list of dicts with keys: type, message, step (optional), depth (optional).
    """
    errors = []
    error_pattern = re.compile(
        r'^(.*?)(assertion violated|invalid end state|deadlock)(.*)$', re.IGNORECASE
    )
    step_depth_pattern = re.compile(
        r'at depth (\d+)|step (\d+)', re.IGNORECASE
    )

    with open(pan_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            match = error_pattern.search(line)
            if match:
                err_type = match.group(2).lower()
                msg = line

                depth = None
                step_num = None
                depth_match = re.search(r'at depth (\d+)', line, re.IGNORECASE)
                if depth_match:
                    depth = int(depth_match.group(1))
                else:
                    step_match = re.search(r'step (\d+)', line, re.IGNORECASE)
                    if step_match:
                        step_num = int(step_match.group(1))

                errors.append({
                    'type': err_type,
                    'message': msg,
                    'depth': depth,
                    'step': step_num
                })
    return errors



def save_parsed_output(parsed_trail, parsed_errors, out_path="output/parsed_data.json"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    abs_out_path = os.path.join(base_dir, out_path)

    os.makedirs(os.path.dirname(abs_out_path), exist_ok=True)
    with open(abs_out_path, 'w') as f:
        json.dump({
            'trail': parsed_trail,
            'errors': parsed_errors
        }, f, indent=2)
    print(f"Saved parsed data to {abs_out_path}")

def convert_isf_to_txt(input_folder):
    for filename in os.listdir(input_folder):
        if filename.endswith('.isf'):
            isf_path = os.path.join(input_folder, filename)
            txt_filename = os.path.splitext(filename)[0] + '.txt'
            txt_path = os.path.join(input_folder, txt_filename)

            with open(isf_path, 'r', encoding='utf-8') as infile, \
                 open(txt_path, 'w', encoding='utf-8') as outfile:
                outfile.write(infile.read())

            print(f"Converted {filename} to {txt_filename}")
            return txt_path
    print("No .isf file found in the input folder.")
    return None

def parse_msc_txt(txt_path):
    with open(txt_path, 'r', encoding='utf-8') as f:
        content = f.read()

    match = re.search(r'===start Sim===(.*?)===end Sim===', content, re.DOTALL)
    if not match:
        print("No simulation block found in txt file")
        return {}, []

    sim_block = match.group(1)
    proc_names = {}
    events = []

    create_re = re.compile(r'proc\s+(\d+)\s+\([^)]+\)\s+creates proc\s+(\d+)\s+\(([^)]+)\)')
    action_re = re.compile(r'proc\s+(\d+)\s+\([^)]+\)\s+([^\[]+)\[(.+)\]')

    for line in sim_block.strip().splitlines():
        line = line.strip()
        if 'creates proc' in line:
            m = create_re.search(line)
            if m:
                src_pid = int(m.group(1))
                dst_pid = int(m.group(2))
                dst_name = m.group(3)
                proc_names[dst_pid] = dst_name
                events.append({
                    'type': 'create',
                    'from': src_pid,
                    'to': dst_pid,
                    'label': f'run {dst_name}'
                })
        else:
            m = action_re.search(line)
            if m:
                pid = int(m.group(1))
                action_raw = m.group(3).strip()
                if pid not in proc_names:
                    proc_names[pid] = f"proc_{pid}"
                events.append({
                    'type': 'action',
                    'pid': pid,
                    'label': action_raw
                })

    return proc_names, events

def save_msc_json(proc_names, events, out_path="output/msc_data.json"):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    abs_out_path = os.path.join(base_dir, out_path)
    os.makedirs(os.path.dirname(abs_out_path), exist_ok=True)
    with open(abs_out_path, 'w') as f:
        json.dump({
            "processes": proc_names,
            "events": events
        }, f, indent=2)
    print(f"Saved MSC JSON data to {abs_out_path}")



def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "data")

    trail_files = [f for f in os.listdir(data_dir) if f.endswith(".trail")]
    if not trail_files:
        raise FileNotFoundError("No .trail file found in /data")
    trail_path = os.path.join(data_dir, trail_files[0])
    
    out_files = [f for f in os.listdir(data_dir) if f.endswith(".out")]
    if not out_files:
        raise FileNotFoundError("No .out file found in /data")
    pan_path = os.path.join(data_dir, out_files[0])
    
    trail_data = parse_trail_file(trail_path)   
    error_data = parse_pan_out(pan_path)        

    txt_path = convert_isf_to_txt(data_dir)
    if txt_path:
        proc_names, events = parse_msc_txt(txt_path)
        save_msc_json(proc_names, events)
    else:
        print("No .txt file for MSC parsing.")

    save_parsed_output(trail_data, error_data)

if __name__ == '__main__':
    main()
