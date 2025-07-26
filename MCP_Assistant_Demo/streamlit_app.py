# streamlit_app.py
import streamlit as st
import requests
import json
import os
import sys

# Disable Streamlit auto-reload when running from .exe
if getattr(sys, 'frozen', False):
    os.environ["STREAMLIT_SERVER_HEADLESS"] = "true"
    os.environ["STREAMLIT_SERVER_RUN_ON_SAVE"] = "false"
    os.environ["STREAMLIT_SERVER_ENABLE_WATCHDOG"] = "false"
    os.environ["STREAMLIT_SERVER_ENABLE_CORS"] = "false"
    os.environ["STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION"] = "false"
    os.environ["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
    os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"
    

# Configuration for your Flask API
FLASK_API_URL = "http://127.0.0.1:5000/process_query"

st.set_page_config(page_title="MCP File Agent", page_icon="📝")

st.title("🗣️ Natural Language File Agent")
st.markdown("""
Welcome to the Natural Language File Agent!
Enter your commands in natural language to interact with your local file system.
""")

user_query = st.text_input("Enter your command:", placeholder="e.g., 'Find my latest resume in downloads' or 'Rename my cover letter to COVER_LETTER and move it to desktop'")

if st.button("Execute Command"):
    if user_query:
        with st.spinner("Processing your request..."):
            try:
                payload = {"query": user_query}
                headers = {"Content-Type": "application/json"}

                response = requests.post(FLASK_API_URL, data=json.dumps(payload), headers=headers)

                # --- ADD THESE DEBUGGING LINES ---
                st.write(f"**Raw API Response Status Code:** {response.status_code}")
                st.write(f"**Raw API Response Content (text):**")
                st.code(response.text) # Display the raw text response
                st.write(f"**Attempting to parse JSON...**")
                # --- END DEBUGGING LINES ---


                if response.status_code == 200:
                    try:
                        response_data = response.json()
                        st.write(f"**Parsed JSON Data Type:** {type(response_data)}")
                        st.write(f"**Parsed JSON Data:** {response_data}")

                        st.success("Command Executed Successfully!")
                        st.write("---")
                    except json.JSONDecodeError:
                        st.error("API returned a non-JSON response despite 200 status. See raw content above.")
                        st.info("This might happen if Flask returns a plain string or HTML on success.")
                else:
                    st.error(f"Error from API: {response.status_code} - {response.text}")
            except requests.exceptions.ConnectionError:
                st.error(f"Could not connect to the Flask API at {FLASK_API_URL}. Please ensure the Flask server is running.")
                st.info("To run the Flask server, open your terminal in the directory containing `app.py` and `client_llm.py`, then run: `python ui/app.py` (from your project root).")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
    else:
        st.warning("Please enter a command to execute.")

st.markdown("---")
st.markdown("### How it works:")
st.markdown("""
1.  You enter a natural language command in the text box.
2.  The Streamlit app sends this command to the Flask API.
3.  The Flask API calls your `client_llm` (which you will implement).
4.  Your `client_llm` uses an LLM to interpret your command and orchestrate calls to your `MCP_server` tools (e.g., for file search, rename, move, read, etc.).
5.  The `client_llm` returns a natural language response, which is then sent back through the Flask API to Streamlit and displayed here.
""")