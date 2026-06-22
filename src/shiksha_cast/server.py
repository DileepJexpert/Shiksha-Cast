from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from threading import Thread

import yaml
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

app = FastAPI(title="Shiksha-Cast API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_build_jobs: dict[str, dict] = {}


def _ensure_chapter_dir(chapter: str) -> Path:
    d = PROJECT_ROOT / "content" / chapter
    d.mkdir(parents=True, exist_ok=True)
    return d


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
    script_data = {
        "chapter": body.get("title", chapter),
        "slides": [
            {"n": s["n"], "narration": s.get("narration", "")}
            for s in body.get("slides", [])
        ],
    }
    script_path = chapter_dir / f"{chapter}.yaml"
    with open(script_path, "w", encoding="utf-8") as f:
        yaml.dump(script_data, f, allow_unicode=True, default_flow_style=False)
    return {"status": "saved", "path": str(script_path)}


@app.post("/api/chapter/{chapter}/build")
async def start_build(chapter: str):
    if chapter in _build_jobs and _build_jobs[chapter].get("status") == "running":
        return {"status": "running", "message": "Build already in progress"}

    _build_jobs[chapter] = {"status": "running", "error": None}

    def _do_build():
        try:
            from shiksha_cast.pipeline import run_build
            result = run_build(chapter, PROJECT_ROOT)
            _build_jobs[chapter] = {
                "status": "done",
                "video_url": f"/api/chapter/{chapter}/download",
                "srt_url": f"/api/chapter/{chapter}/srt",
                "duration": result.assemble.total_duration,
                "slides": result.assemble.slide_count,
            }
        except Exception as e:
            _build_jobs[chapter] = {"status": "error", "error": str(e)}

    Thread(target=_do_build, daemon=True).start()
    return {"status": "running"}


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
