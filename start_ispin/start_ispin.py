import subprocess
import time
import os

Xming_path = r"C:\Program Files (x86)\Xming\Xming.exe" 
cygwin_shell = r"C:\cygwin64\bin\bash.exe"  

def launch_xming():
    """Launch Xming silently and minimize it to the tray."""
    try:
        print("Launching Xming silently...")
        subprocess.Popen([Xming_path, ":0", "-multiwindow", "-clipboard"])
        time.sleep(3) 
        print("Xming launched silently.")
    except Exception as e:
        print(f"Error launching Xming: {e}")

def launch_cygwin_and_run_commands():
    """Open Cygwin and run each command sequentially."""
    try:
        print("Launching Cygwin...")

        command_string = "export DISPLAY=localhost:0.0 && cd /cygdrive/c/Users/stell/Desktop/Spin-master/optional_gui && wish ispin.tcl"

        subprocess.Popen([cygwin_shell, "-c", command_string])

        print("Cygwin launched and iSpin should now be running.")

    except Exception as e:
        print(f"Error launching Cygwin: {e}")

if __name__ == "__main__":
    # Run the automation steps
    launch_xming()
    launch_cygwin_and_run_commands()