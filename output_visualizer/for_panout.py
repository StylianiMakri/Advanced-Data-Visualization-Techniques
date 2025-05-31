import re
import os
import matplotlib.pyplot as plt
import seaborn as sns

file_path = os.path.join(os.getcwd(), "output_visualizer", "pan.txt")

# Ensure pan.txt exists
if os.path.exists(os.path.join(os.getcwd(), "output_visualizer", "pan.out")) and not os.path.exists(file_path):
    os.rename(os.path.join(os.getcwd(), "output_visualizer", "pan.out"), file_path)
    print("Renamed 'pan.out' to 'pan.txt'")

# Debugging
print(f"Looking for file: {file_path}")
print("Files in directory:", os.listdir(os.path.join(os.getcwd(), "output_visualizer")))

if not os.path.exists(file_path):
    print(f"Error: The file '{file_path}' does not exist.")
    exit(1)

def parse_spin_output(file_path):
    data = {
        "states_stored": 0,
        "transitions": 0,
        "errors": 0,
        "depth_reached": 0,
        "memory_usage": {}
    }
    
    with open(file_path, 'r') as file:
        for line in file:
            if "states, stored" in line:
                data["states_stored"] = int(re.findall(r'\d+', line)[0])
            elif "transitions" in line:
                data["transitions"] = int(re.findall(r'\d+', line)[0])
            elif "depth reached" in line:
                data["depth_reached"] = int(re.findall(r'\d+', line)[0])
            elif "errors:" in line:
                data["errors"] = int(re.findall(r'\d+', line)[0])
            elif "memory used" in line:
                match = re.findall(r'([0-9\.]+)\s+memory used for ([^\(]+)', line)
                for value, key in match:
                    data["memory_usage"][key.strip()] = float(value)
    
    return data

def visualize_data(data):
    sns.set(style="whitegrid")
    
    # Bar Chart for main statistics
    plt.figure(figsize=(8, 5))
    labels = ["States Stored", "Transitions", "Depth Reached", "Errors"]
    values = [data["states_stored"], data["transitions"], data["depth_reached"], data["errors"]]
    sns.barplot(x=labels, y=values, palette="Blues_r")
    plt.ylabel("Count")
    plt.title("SPIN Verification Summary")
    plt.show()
    
    # Pie Chart for Memory Usage
    if data["memory_usage"]:
        plt.figure(figsize=(6, 6))
        plt.pie(data["memory_usage"].values(), labels=data["memory_usage"].keys(), autopct='%1.1f%%', colors=sns.color_palette("coolwarm", len(data["memory_usage"])))
        plt.title("Memory Usage Breakdown")
        plt.show()

# Example usage
data = parse_spin_output(file_path)
visualize_data(data)