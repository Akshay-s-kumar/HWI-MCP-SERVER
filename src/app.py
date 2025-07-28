import os
import asyncio
from flask import Flask, request, jsonify, render_template
import sys 
import asyncio
from client_llm import MCPClient
import traceback
import nest_asyncio
nest_asyncio.apply()
# Add this helper function below the imports
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- Initialization ---
app = Flask(__name__, template_folder=resource_path('ui')) 

# Create a single, shared instance of the chatbot
# This is important for performance and for state management (like delete confirmations)
chatbot_instance = MCPClient()

# --- Routes ---

@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
async def chat():
    """Handles chat messages from the UI."""
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({'response': 'Error: No message provided.'}), 400

    # Because our chatbot methods are async, we need to run them in an event loop.
    # Flask doesn't support async routes by default in a simple way,
    # so asyncio.run() is a straightforward solution for this use case.
    
    try:
        await chatbot_instance.connect_to_server(".\src\mcp_server.py")
        response_text = await chatbot_instance.process_query(user_message)
        return jsonify({'response': response_text})
    except Exception as e:
        traceback.print_exc()  # Print the traceback to the console for debugging
        # Log the error to a file or monitoring system in production
        print(f"Error during chat handling: {e}")
        
        return jsonify({'response': f'An internal error occurred: {e}'}), 500

if __name__ == '__main__':
    # Note: For production, use a proper WSGI server like Gunicorn or Waitress
    app.run(debug=True, port=5000, threaded=False)
    