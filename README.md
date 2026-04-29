# WebDev Agent

WebDev Agent is an AI-powered coding assistant that operates as both a Command-Line Interface (CLI) and a web-accessible service. Built around the Google Gemini 2.5 Flash model, it has the ability to understand requests, formulate plans, and execute tool calls such as reading files, modifying code, listing directory contents, and executing Python scripts within a controlled workspace.

## Features

- **Autonomous Agent Loop:** Converts high-level prompts into actionable tasks with function calling capabilities.
- **Web Interface:** A React frontend that streams the agent's thought process and actions in real-time.
- **Session Memory:** Retains conversation history context across multiple interactions in a session.
- **Live Preview:** Built-in endpoints to host and preview the generated web artifacts from the agent's working directory.
- **CLI Support:** Can also be run entirely from the terminal.

## Project Structure

- `main.py`: The original CLI implementation of the agent.
- `agent/`: The core logic for the agent, containing the asynchronous generator loop (`core.py`) and tool declarations (`functions/`).
- `api/`: The FastAPI backend handling Server-Sent Events (SSE) streaming, session memory, and file previews (`main.py`).
- `frontend/`: A Vite + React frontend application that interfaces with the API backend.
- `WorkingDirectory/`: The isolated environment where the agent performs its file operations.

## Technology Stack

### Backend
- **Python 3.12+**
- **FastAPI** for API routing and streaming (SSE)
- **Uvicorn** as the ASGI server
- **Google GenAI SDK** (`gemini-2.5-flash`) for the core intelligence
- **Pydantic** for data validation
- **uv** for Python dependency management

### Frontend
- **React 19**
- **Vite** as the build tool and development server
- **TypeScript**
- **ESLint** for code quality

## Setup & Running

1. **Environment Setup:** Make sure to have Python 3.12+ and Node.js installed.
2. **API Keys:** Create a `.env` file in the root directory and add `GEMINI_API_KEY=your_api_key_here`.
3. **Run Backend:** Start the FastAPI backend with Uvicorn.
4. **Run Frontend:** Navigate to `frontend/`, run `npm install` and then `npm run dev`.
