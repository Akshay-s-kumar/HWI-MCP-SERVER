import subprocess

# Start only the Flask backend (app.py is compiled to app.exe)
subprocess.Popen(["app.exe"])

print("MCP Backend started successfully.")
print("Now open a new terminal and run:")
print("streamlit run streamlit_app.py")
