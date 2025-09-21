#SPIN Visualizer Tool - Advanced Data Visualization and Explanation Techniques on Design and Verification Tools

My diploma thesis, focused on visualising SPIN model checker outputs, turning raw output files (.out, .trail, .isf) into interactive and understandable visualizations.

##Project Overview 
SPIN Visualizer is a desktop GUI application that transforms SPIN outputs into interactive, visual representations.  
It allows users to quickly identify errors such as assertions, deadlocks, unmatched communications, and never claim violations.The tool bridges the gap between raw SPIN outputs and intuitive analysis by providing execution tables linking steps to PROMELA code, chronological timelines of process execution, interactive 3D state space graphs and easy to understand explanations of why a simulation failed.

##Features

###**Users can:**

-Load SPIN output files and parse them into JSON
-View execution steps in a table with code line references
-Explore chronological timelines of processes
-Visualize the 3D state space of the simulation
-Understand errors through the Why It Failed module
-Get a quick overview of verification results with the Overview module

###**Usage**: 
- **File Parsing** : Supports `.out`, `.trail`, `.pml`, and `.isf` files. Extracts execution steps, process IDs, model line numbers, actions, and critical information such as assertions, deadlocks, invalid end states, execution depth, and memory usage. Converts all parsed data into `parsed_data.json`, creating a flexible bridge between the parser and visualization modules.
- **Visualizer Module**:  
  - Presents execution in a detailed table with step number, process, code line, action performed, and the corresponding PML code.  
  - Users can search, filter, and export data to Excel (`.xlsx`) or HTML.  
  - Highlights errors detected during SPIN analysis, providing quick access to assertion violations, deadlocks, and unmatched communications.
- **Timeline Module**:  
  - Displays a chronological execution timeline with each process as a separate row.  
  - Marks steps in order, making it easier to detect bottlenecks and interactions between processes.
- **3D State Graph Module**:  
  - Generates a 3D visualization of the execution state space using NetworkX and Plotly.  
  - Nodes represent execution steps, edges represent transitions, allowing interactive exploration of the system behavior.
- **Why It Failed Module**:  
  - Provides a clear timeline of transitions with explanatory messages for assertions, deadlocks, unmatched communications, or never claim violations.  
  - Displays the full simulation trace for in-depth investigation of each step.
- **Overview Module**:  
  - Summarizes SPIN verification results, including compilation commands, verification settings, state space information, and resource usage.  
  - Offers customizable views and clear visual charts for quick understanding of verification outcomes.
- **User Dashboard & Profile Management**:  
  - Centralized dashboard for file selection, clearing data, and running modules.  
  - Allows creation, deletion and loading of "model profiles" containing sets of SPIN files for quick analysis. 
  - Fully supports selection, uploading, clearing, and saving of input and created files.  




