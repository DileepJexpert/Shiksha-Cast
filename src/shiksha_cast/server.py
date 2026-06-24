from __future__ import annotations

import io
import logging
import shutil
import sys
import uuid
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from typing import Any

import yaml
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.responses import StreamingResponse

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

AVAILABLE_MODELS = [
    {
        "id": "ai4bharat/indic-parler-tts",
        "name": "Indic Parler-TTS",
        "category": "Hindi",
        "description": "Best quality for Hindi & Hinglish narration. Requires free HuggingFace approval.",
        "size": "3.7 GB",
        "gated": True,
    },
    {
        "id": "parler-tts/parler-tts-mini-v1",
        "name": "Parler-TTS Mini v1",
        "category": "Multilingual",
        "description": "Multilingual model, no approval needed. Good for English + mixed content.",
        "size": "2.2 GB",
        "gated": False,
    },
    {
        "id": "parler-tts/parler-tts-large-v1",
        "name": "Parler-TTS Large v1",
        "category": "Multilingual",
        "description": "Higher quality multilingual model. No approval needed, larger download.",
        "size": "4.6 GB",
        "gated": False,
    },
    {
        "id": "veena:kavya",
        "name": "Veena — Kavya (Hinglish, female)",
        "category": "Hinglish",
        "description": "Best-quality Hindi-English code-switching (MOS 4.2). 4-bit, fits 8GB. Apache-2.0. Needs the .venv-veena environment.",
        "size": "3B (4-bit ~2 GB)",
        "gated": False,
    },
    {
        "id": "veena:maitri",
        "name": "Veena — Maitri (Hinglish, female)",
        "category": "Hinglish",
        "description": "Veena alternate female voice. Hindi-English code-switching, 4-bit, fits 8GB.",
        "size": "3B (4-bit ~2 GB)",
        "gated": False,
    },
    {
        "id": "veena:agastya",
        "name": "Veena — Agastya (Hinglish, male)",
        "category": "Hinglish",
        "description": "Veena male voice. Hindi-English code-switching, 4-bit, fits 8GB.",
        "size": "3B (4-bit ~2 GB)",
        "gated": False,
    },
    {
        "id": "veena:vinaya",
        "name": "Veena — Vinaya (Hinglish, male)",
        "category": "Hinglish",
        "description": "Veena alternate male voice. Hindi-English code-switching, 4-bit, fits 8GB.",
        "size": "3B (4-bit ~2 GB)",
        "gated": False,
    },
    {
        "id": "kokoro",
        "name": "Kokoro-82M (clearest)",
        "category": "English",
        "description": "Crisp, natural English narration. Tiny (~330 MB), fast, low VRAM. Best audio clarity and no OOM on 8 GB GPUs.",
        "size": "330 MB",
        "gated": False,
    },
    {
        "id": "stub",
        "name": "Test Tone (No GPU)",
        "category": "Test",
        "description": "Silent placeholder with a short blip. No download needed, for testing pipeline only.",
        "size": "0 MB",
        "gated": False,
    },
]

app = FastAPI(title="Shiksha-Cast API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_build_jobs: dict[str, dict] = {}
_build_logs: dict[str, Queue] = {}


class _LogCapture(logging.Handler):
    """Sends log records to a per-chapter SSE queue."""

    def __init__(self, queue: Queue):
        super().__init__()
        self._q = queue

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._q.put_nowait(self.format(record))
        except Exception:
            pass


class _StreamCapture(io.TextIOBase):
    """Captures writes to stdout/stderr and puts them in the log queue."""

    def __init__(self, queue: Queue, original: Any):
        self._q = queue
        self._original = original

    def write(self, s: str) -> int:
        if self._original:
            self._original.write(s)
        text = s.strip()
        if text:
            for line in text.split("\n"):
                line = line.strip()
                if line:
                    try:
                        self._q.put_nowait(line)
                    except Exception:
                        pass
        return len(s)

    def flush(self) -> None:
        if self._original:
            self._original.flush()


def _ensure_chapter_dir(chapter: str) -> Path:
    d = PROJECT_ROOT / "content" / chapter
    d.mkdir(parents=True, exist_ok=True)
    return d


def _push_log(chapter: str, msg: str) -> None:
    q = _build_logs.get(chapter)
    if q:
        try:
            q.put_nowait(msg)
        except Exception:
            pass


def _find_script_path(chapter_dir: Path) -> Path | None:
    """Find script YAML in a chapter dir: script.yaml > {name}.yaml > any .yaml."""
    for candidate in [chapter_dir / "script.yaml", chapter_dir / f"{chapter_dir.name}.yaml"]:
        if candidate.exists():
            return candidate
    yamls = list(chapter_dir.glob("*.yaml"))
    return yamls[0] if yamls else None


@app.get("/api/chapters")
async def list_chapters():
    content_dir = PROJECT_ROOT / "content"
    chapters = []
    if content_dir.is_dir():
        for d in sorted(content_dir.iterdir()):
            if not d.is_dir() or d.name.startswith((".","_")):
                continue
            ch_id = d.name
            script_path = _find_script_path(d)
            if not script_path:
                continue

            info: dict[str, Any] = {"id": ch_id, "has_pdf": False, "has_script": True, "has_video": False, "slide_count": 0}

            info["has_pdf"] = any(d.glob("*.pdf"))

            try:
                with open(script_path, encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                info["title"] = data.get("chapter", ch_id)
                info["slide_count"] = len(data.get("slides", []))
            except Exception:
                info["title"] = ch_id

            slides_dir = PROJECT_ROOT / "build" / ch_id / "slides"
            if slides_dir.is_dir():
                pngs = list(slides_dir.glob("slide_*.png"))
                if pngs:
                    info["slide_count"] = max(info["slide_count"], len(pngs))

            video = PROJECT_ROOT / "dist" / f"{ch_id}.mp4"
            info["has_video"] = video.exists()

            job = _build_jobs.get(ch_id, {})
            info["build_status"] = job.get("status", "idle")

            chapters.append(info)
    return {"chapters": chapters}


@app.get("/api/chapter/{chapter}/script")
async def get_script(chapter: str):
    chapter_dir = PROJECT_ROOT / "content" / chapter
    script_path = _find_script_path(chapter_dir)
    if not script_path:
        return JSONResponse({"error": "Script not found"}, status_code=404)
    with open(script_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


@app.post("/api/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    chapter: str = Form(default=""),
):
    if not chapter:
        chapter = f"ch{uuid.uuid4().hex[:4]}"

    chapter_dir = _ensure_chapter_dir(chapter)
    pdf_path = chapter_dir / f"{chapter}.pdf"
    with open(pdf_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    from shiksha_cast.render import render_chapter

    result = render_chapter(chapter, PROJECT_ROOT)

    slides = []
    for i, p in enumerate(result.slide_paths):
        slides.append({
            "n": i + 1,
            "image_url": f"/api/slides/{chapter}/{p.name}",
        })

    return {"chapter": chapter, "slides": slides, "total": len(slides)}


@app.post("/api/upload-slides")
async def upload_slides(
    files: list[UploadFile] = File(...),
    chapter: str = Form(default=""),
):
    if not chapter:
        chapter = f"ch{uuid.uuid4().hex[:4]}"

    build_dir = PROJECT_ROOT / "build" / chapter / "slides"
    build_dir.mkdir(parents=True, exist_ok=True)
    _ensure_chapter_dir(chapter)

    slides = []
    for i, f in enumerate(sorted(files, key=lambda x: x.filename or ""), start=1):
        dest = build_dir / f"slide_{i:03d}.png"
        with open(dest, "wb") as out:
            shutil.copyfileobj(f.file, out)
        slides.append({
            "n": i,
            "image_url": f"/api/slides/{chapter}/{dest.name}",
        })

    return {"chapter": chapter, "slides": slides, "total": len(slides)}


@app.get("/api/slides/{chapter}/{filename}")
async def get_slide(chapter: str, filename: str):
    path = PROJECT_ROOT / "build" / chapter / "slides" / filename
    if not path.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(path, media_type="image/png")


@app.put("/api/chapter/{chapter}/script")
async def save_script(chapter: str, body: dict):
    chapter_dir = _ensure_chapter_dir(chapter)
    slides = []
    for s in body.get("slides", []):
        slide = {"n": s["n"], "narration": s.get("narration", "")}
        if s.get("visual_prompt"):
            slide["visual_prompt"] = s["visual_prompt"]
        if s.get("voice_description"):
            slide["voice_description"] = s["voice_description"]
        if s.get("voice"):
            slide["voice"] = s["voice"]
        slides.append(slide)
    script_data = {
        "chapter": body.get("title", chapter),
        "slides": slides,
    }
    script_path = chapter_dir / "script.yaml"
    with open(script_path, "w", encoding="utf-8") as f:
        yaml.dump(script_data, f, allow_unicode=True, default_flow_style=False)
    return {"status": "saved", "path": str(script_path)}


@app.post("/api/chapter/{chapter}/build")
async def start_build(chapter: str, body: dict | None = None):
    if chapter in _build_jobs and _build_jobs[chapter].get("status") == "running":
        return {"status": "running", "message": "Build already in progress"}

    use_ai = (body or {}).get("ai_mode", False)
    force = (body or {}).get("force", False)

    log_q: Queue = Queue(maxsize=5000)
    _build_logs[chapter] = log_q
    _build_jobs[chapter] = {"status": "running", "stage": "starting", "error": None, "progress": 0}

    def _do_build():
        handler = _LogCapture(log_q)
        handler.setFormatter(logging.Formatter("%(message)s"))
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)

        stdout_cap = _StreamCapture(log_q, sys.stdout)
        stderr_cap = _StreamCapture(log_q, sys.stderr)
        old_stdout, old_stderr = sys.stdout, sys.stderr

        try:
            sys.stdout = stdout_cap  # type: ignore[assignment]
            sys.stderr = stderr_cap  # type: ignore[assignment]

            _push_log(chapter, f"[BUILD] Starting {'AI' if use_ai else 'standard'} build for {chapter}")

            if use_ai:
                from shiksha_cast.pipeline import run_ai_build

                _build_jobs[chapter]["stage"] = "visuals"
                _push_log(chapter, "[STAGE] Generating AI visuals...")
                _build_jobs[chapter]["progress"] = 10

                result = run_ai_build(chapter, PROJECT_ROOT, force=force)
            else:
                from shiksha_cast.pipeline import run_build

                _build_jobs[chapter]["stage"] = "render"
                _push_log(chapter, "[STAGE] Rendering PDF slides to PNG...")
                _build_jobs[chapter]["progress"] = 10

                result = run_build(chapter, PROJECT_ROOT, force=force)

            _build_jobs[chapter] = {
                "status": "done",
                "stage": "complete",
                "progress": 100,
                "video_url": f"/api/chapter/{chapter}/download",
                "srt_url": f"/api/chapter/{chapter}/srt",
                "duration": result.assemble.total_duration,
                "slides": result.assemble.slide_count,
            }
            _push_log(chapter, f"[DONE] Build complete! {result.assemble.slide_count} slides, {result.assemble.total_duration:.1f}s video")
            _push_log(chapter, "[END]")

        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            _build_jobs[chapter] = {"status": "error", "stage": "failed", "progress": 0, "error": str(e)}
            _push_log(chapter, f"[ERROR] {e}")
            _push_log(chapter, tb)
            _push_log(chapter, "[END]")
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            root_logger.removeHandler(handler)

    Thread(target=_do_build, daemon=True).start()
    return {"status": "running"}


@app.get("/api/chapter/{chapter}/logs")
async def stream_logs(chapter: str):
    """SSE endpoint - streams build logs in real time."""
    q = _build_logs.get(chapter)
    if not q:
        job = _build_jobs.get(chapter, {})
        if job.get("status") == "error":
            async def error_stream():
                yield f"data: [ERROR] {job.get('error', 'Unknown error')}\n\n"
                yield "data: [END]\n\n"
            return StreamingResponse(error_stream(), media_type="text/event-stream")
        async def empty_stream():
            yield "data: No active build for this chapter.\n\n"
            yield "data: [END]\n\n"
        return StreamingResponse(empty_stream(), media_type="text/event-stream")

    async def event_generator():
        yield "data: [CONNECTED] Log stream connected\n\n"
        while True:
            try:
                msg = q.get(timeout=1.0)
                yield f"data: {msg}\n\n"
                if msg == "[END]":
                    break
            except Empty:
                yield ": keepalive\n\n"
                job = _build_jobs.get(chapter, {})
                if job.get("status") in ("done", "error"):
                    if q.empty():
                        break

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/chapter/{chapter}/status")
async def build_status(chapter: str):
    job = _build_jobs.get(chapter)
    if not job:
        video = PROJECT_ROOT / "dist" / f"{chapter}.mp4"
        if video.exists():
            return {"status": "done", "video_url": f"/api/chapter/{chapter}/download"}
        return {"status": "idle"}
    return job


@app.get("/api/chapter/{chapter}/download")
async def download_video(chapter: str):
    path = PROJECT_ROOT / "dist" / f"{chapter}.mp4"
    if not path.exists():
        return JSONResponse({"error": "Video not found. Run build first."}, status_code=404)
    return FileResponse(path, media_type="video/mp4", filename=f"{chapter}.mp4")


@app.get("/api/chapter/{chapter}/srt")
async def download_srt(chapter: str):
    path = PROJECT_ROOT / "dist" / f"{chapter}.srt"
    if not path.exists():
        return JSONResponse({"error": "SRT not found."}, status_code=404)
    return FileResponse(path, media_type="text/plain", filename=f"{chapter}.srt")


@app.get("/api/models")
async def list_models():
    from shiksha_cast.config import load_channel_config

    cfg = load_channel_config(PROJECT_ROOT)
    current_model = cfg.voice.model
    if cfg.voice.provider == "stub":
        current_model = "stub"
    elif cfg.voice.provider == "kokoro":
        current_model = "kokoro"
    elif cfg.voice.provider == "veena":
        current_model = f"veena:{cfg.voice.model}"
    return {"models": AVAILABLE_MODELS, "current": current_model}


@app.put("/api/config/voice-model")
async def set_voice_model(body: dict):
    model_id = body.get("model")
    if not model_id:
        return JSONResponse({"error": "model is required"}, status_code=400)

    valid_ids = {m["id"] for m in AVAILABLE_MODELS}
    if model_id not in valid_ids:
        return JSONResponse({"error": f"Unknown model: {model_id}"}, status_code=400)

    config_path = PROJECT_ROOT / "config" / "channel.yaml"
    with open(config_path, encoding="utf-8") as f:
        cfg_data = yaml.safe_load(f) or {}

    if "voice" not in cfg_data:
        cfg_data["voice"] = {}

    if model_id == "stub":
        cfg_data["voice"]["provider"] = "stub"
    elif model_id == "kokoro" or model_id.startswith("kokoro:"):
        cfg_data["voice"]["provider"] = "kokoro"
        # "kokoro:af_bella" picks a specific voice; bare "kokoro" uses the default.
        cfg_data["voice"]["model"] = model_id.split(":", 1)[1] if ":" in model_id else "af_heart"
    elif model_id == "veena" or model_id.startswith("veena:"):
        cfg_data["voice"]["provider"] = "veena"
        # "veena:kavya" picks a speaker; bare "veena" uses the default.
        cfg_data["voice"]["model"] = model_id.split(":", 1)[1] if ":" in model_id else "kavya"
    else:
        cfg_data["voice"]["provider"] = "parler"
        cfg_data["voice"]["model"] = model_id

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(cfg_data, f, allow_unicode=True, default_flow_style=False)

    return {"status": "updated", "model": model_id}
