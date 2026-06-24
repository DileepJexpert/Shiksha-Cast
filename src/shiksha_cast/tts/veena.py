from __future__ import annotations

import json
import logging
import subprocess
import sys
from pathlib import Path

from shiksha_cast.tts.base import TTSProvider

logger = logging.getLogger(__name__)

# Project root: src/shiksha_cast/tts/veena.py -> parents[3]
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_VENV_PY = _PROJECT_ROOT / ".venv-veena" / "Scripts" / "python.exe"
_WORKER = _PROJECT_ROOT / "scripts" / "veena_worker.py"


class VeenaTTSProvider(TTSProvider):
    """Veena-TTS (Apache-2.0, 3B, Hindi-English) via a persistent worker subprocess.

    Veena needs its own venv (snac + bitsandbytes, conflicting transformers), so we
    run it out-of-process: the worker loads the model once and synthesizes each slide
    over a stdin/stdout JSON protocol. Built-in voices: kavya, agastya, maitri, vinaya.
    """

    def __init__(self, speaker: str = "kavya"):
        self._speaker = speaker or "kavya"
        self._proc: subprocess.Popen | None = None

    def set_speaker(self, speaker: str) -> None:
        """Switch voice mid-session; the worker reads the speaker per request."""
        if speaker:
            self._speaker = speaker

    def _ensure(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            return
        if not _VENV_PY.exists():
            raise RuntimeError(
                f"Veena venv not found at {_VENV_PY}. Create it with:\n"
                "  python -m venv .venv-veena --system-site-packages\n"
                "  .venv-veena/Scripts/python -m pip install snac bitsandbytes accelerate"
            )
        logger.info("Starting Veena worker (loading model, ~1-2 min first time)...")
        self._proc = subprocess.Popen(
            [str(_VENV_PY), str(_WORKER)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,  # let model-load/progress go to the console/log
            cwd=str(_PROJECT_ROOT),
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        # Block until the worker signals it has loaded the model.
        while True:
            line = self._proc.stdout.readline()
            if not line:
                raise RuntimeError("Veena worker exited before becoming ready")
            if line.strip() == "READY":
                break
        logger.info("Veena worker ready.")

    def synthesize(self, text: str, description: str, output_path: Path) -> float:
        self._ensure()
        assert self._proc is not None and self._proc.stdin and self._proc.stdout
        output_path.parent.mkdir(parents=True, exist_ok=True)
        req = json.dumps({"text": text, "speaker": self._speaker, "out": str(output_path)})
        self._proc.stdin.write(req + "\n")
        self._proc.stdin.flush()
        resp = self._proc.stdout.readline()
        if not resp:
            raise RuntimeError("Veena worker died during synthesis")
        data = json.loads(resp)
        if "error" in data:
            raise RuntimeError(f"Veena synthesis failed: {data['error']}")
        return float(data["duration"])

    def name(self) -> str:
        return "veena"

    def __del__(self):
        try:
            if self._proc and self._proc.poll() is None:
                self._proc.stdin.close()
                self._proc.terminate()
        except Exception:
            pass
