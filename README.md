# LLM-Powered File System Assistant

This project is an MCP (Model-Context-Protocol) server that allows you to interact with your local file system using natural language. It's powered by the Groq LLaMA-3 language model and features a simple, chat-based web interface built with Flask.

You can ask it to find files, get details about them, read them, or even create, edit, and delete files, all through a simple conversational UI.

---

## Features

This application fulfills all the core requirements of the assignment:

* **File Search & Path Resolution**: Ask the chatbot to find files even if you only know part of the name or location (e.g., "find my report on the desktop").
* **Metadata Inspection**: Get detailed information for any file, including its full path, size, creation date, last modified date, file type, and permissions.
* **File I/O Operations**: The server provides tools for a range of file manipulations:
    * **Read**: View the contents of text-based files.
    * **Create**: Create new files with initial content.
    * **Edit**: Append content to existing files or overwrite them completely.
    * **Delete**: Safely delete files and empty folders with a confirmation step to prevent accidents.
* **LLM Orchestration**: Uses a Large Language Model to understand your commands in plain English and map them to the correct file system tool.

---

## Tech Stack

* **Backend**: Python, Flask
* **LLM API**: Groq
* **Frontend**: HTML, CSS, JavaScript (no frameworks)
* **Dependencies**: `python-dotenv`, `groq`

---

## Getting Started

There are two ways to run this application: as a standalone executable for a quick start, or from the source code for development.

### Option 1: Quick Start (Standalone .exe)

This is the easiest way to get the chatbot running without any development setup.

1.  **Download the Executable**: Go to the "Releases" section of the project's GitHub repository and download the latest `.exe` file.
2.  **Create API Key File**: In the **same folder** where you saved the `.exe`, there is a folder anmed `config`. Inside `config`, there is a file named `.env`. You can ur GROQ API-KEY there.
3.  **Add Your API Key**: Open the `.env` file with a text editor and add your Groq API key like this:
    ```
    GROQ_API_KEY='your-groq-api-key-here'
    ```
4.  **Run the Application**: Double-click the `.exe` file. A terminal window will appear, indicating that the server is running.
5.  **Open the Chat UI**: Open your web browser and navigate to **http://127.0.0.1:5000**. You can now start chatting with your file system!

### Option 2: Developer Setup (From Source Code)

Follow these instructions to run the application from the source code.

#### Prerequisites
* Python 3.8+
* Git

#### Installation Steps

1.  **Clone the Repository**:
    ```sh
    git clone [https://github.com/your-username/your-repo-name.git](https://github.com/your-username/your-repo-name.git)
    cd your-repo-name
    ```

2.  **Create a Virtual Environment** (Recommended):
    ```sh
    # For Windows
    python -m venv venv
    venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Dependencies**: A `requirements.txt` file should be included in the repository.
    ```sh
    pip install -r requirements.txt
    ```
    *(If a `requirements.txt` file is not available, you can create one with the following content and then run the command above)*:
    ```txt
    # requirements.txt
    flask
    groq
    python-dotenv
    ```

4.  **Set Up API Key**:
    * Create a folder named `config` in the root of the project directory.
    * Inside `config`, create a file named `.env`.
    * Add your Groq API key to the `.env` file:
    ```
    GROQ_API_KEY='your-groq-api-key-here'
    ```

5.  **Run the Application**:
    ```sh
    python src/app.py
    ```
    The terminal will show that the Flask server is running on `http://127.0.0.1:5000`.

6.  **Access the Chat UI**:
    Open your web browser and go to **http://127.0.0.1:5000** to start using the application.

---

## Project Structure

The source code is organized as follows to ensure a clean and maintainable structure.