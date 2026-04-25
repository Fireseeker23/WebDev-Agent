from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json, uuid, shutil, tempfile
from google.genai import types
from agent.core import run_agent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


WORKING_DIR = Path(__file__).resolve().parent.parent / "WorkingDirectory"
WORKING_DIR.mkdir(exist_ok=True)


sessions: dict[str, list[types.Content]] = {}


class ChatRequest(BaseModel):
    prompt: str
    session_id: str | None = None


@app.get("/api/preview/files")
async def list_preview_files():
    """List all files in WorkingDirectory so the frontend knows what's available."""
    files = []
    for f in WORKING_DIR.rglob("*"):
        if f.is_file():
            files.append(str(f.relative_to(WORKING_DIR)))
    return {"files": files, "has_index": (WORKING_DIR / "index.html").exists()}


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):

    sid = req.session_id or str(uuid.uuid4())


    if sid not in sessions:
        sessions[sid] = []
    history = sessions[sid]  

    async def event_generator():

        yield f"data: {json.dumps({'type': 'session_id', 'data': sid})}\n\n"

        async for event in run_agent(req.prompt, history=history):
            yield f"data: {json.dumps(event)}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no"},
    )


@app.get("/api/download")
async def download_project():
    """Zip the WorkingDirectory and return it for download."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        # Create zip archive of WORKING_DIR
        # base_name is without .zip extension, format is 'zip'
        shutil.make_archive(tmp.name, 'zip', WORKING_DIR)
        return FileResponse(
            f"{tmp.name}.zip", 
            media_type="application/x-zip-compressed", 
            filename="project.zip"
        )


@app.delete("/api/session/{session_id}")
async def clear_session(session_id: str):
    sessions.pop(session_id, None)
    return {"cleared": session_id}


app.mount("/preview", StaticFiles(directory=str(WORKING_DIR), html=True), name="preview")


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

