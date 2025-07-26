# main_launcher.py
import subprocess

# Start Flask backend (in background)
subprocess.Popen(["dist/app.exe"])

# Start Streamlit UI
subprocess.call(["streamlit", "run", "ui/streamlit_app.py"])
