# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS # Required for cross-origin requests from Streamlit

import os
import sys
# Correctly add the project root directory to the Python path.
current_dir = os.path.dirname(os.path.abspath(__file__)) # This is 'HWI-mcp-file-system-server/ui/'
project_root_dir = os.path.dirname(current_dir) # This is 'HWI-mcp-file-system-server/'
sys.path.append(project_root_dir)
# Add the directory containing client_llm.py to the Python path
# This assumes client_llm.py is in the same directory as app.py

# Import your client_llm module
# In a real scenario, this client_llm would contain your LLM orchestration logic
# and interact with your MCP_server.
try:
    from src.client_llm import MCPClient
    mcp_instance = MCPClient()
except ImportError:
    print("Error: client_llm.py not found or has issues. Please ensure it's in the same directory.")
    print("Falling back to a dummy response for demonstration.")
    # Define a dummy function if import fails, for basic functionality
def process_query_with_llm(query):
    return {"response": f"Dummy response: Received query '{query}'. (client_llm not loaded)"}


app = Flask(__name__)
CORS(app) # Enable CORS for all routes

@app.route('/')
def home():
    """
    A simple home route to confirm the Flask API is running.
    """
    return "MCP Server Flask API is running!"

@app.route('/process_query', methods=['POST'])
async def process_user_query():
    """
    Endpoint to receive natural language queries from the Streamlit frontend.
    It passes the query to the client_llm and returns the response.
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    user_query = data.get('query')

    if not user_query:
        return jsonify({"error": "Missing 'query' in request body"}), 400

    try:
        # Call your client_llm function here.
        # This function should handle the LLM orchestration and interaction
        # with your MCP_server.
        print(f"Received query from Streamlit: '{user_query}'")
        llm_response = await mcp_instance.process_query(user_query)
        print(f"Response from client_llm: {llm_response}")
        return jsonify(llm_response), 200
    except Exception as e:
        print(f"Error processing query: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

if __name__ == '__main__':
    # To run this Flask app:
    # 1. Save this code as app.py
    # 2. Save the client_llm.py code in the same directory
    # 3. Open your terminal in that directory
    # 4. Run: pip install Flask Flask-Cors
    # 5. Run: python app.py
    # This will start the Flask server, usually on http://127.0.0.1:5000/
    app.run(debug=True, port=5000)
