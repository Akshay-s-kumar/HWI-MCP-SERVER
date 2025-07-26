# MCP File System Assistant — Demo Guide
##  Requirements
✅ Windows 10/11 (64-bit)

✅ Python 3.10 or higher installed

✅ pip install streamlit

##  How to Run
### Step 1: Download & Extract the ZIP

Includes:
main_launcher.exe       - Starts the backend (Flask)
app.exe                 - Flask backend service
streamlit_app.py        - Streamlit UI file
README.txt              - This help file
config/.env             - Environment file to set your Groq API key

### Step 2: Install Streamlit (Only once)

pip install streamlit

### Step 3: Add Your Groq API Key

1: Open the file located at: config/.env
2: Replace the placeholder value with your own API key:
GROQ_API_KEY=your-groq-key-here

### Step 4: Start the Backend
Double-click on: main_launcher.exe

### Step 5: Run the Streamlit App
In terminal or PowerShell, run:

streamlit run streamlit_app.py
This will open the UI in your browser.

### Step 6: Interact!
The app talks to a backend powered by OpenAI/Groq + Flask. Ask questions, upload files, and explore your assistant.