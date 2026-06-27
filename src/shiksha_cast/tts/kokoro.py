from __future__ import annotations

import atexit
import json
import logging
import subprocess
from pathlib import Path

from shiksha_cast.tts.base import TTSProvider

logger = logging.getLogger(__name__)

# Project root: src/shiksha_cast/tts/kokoro.py -> parents[3]
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_VENV_PY = _PROJECT_ROOT / ".venv-kokoro" / "Scripts" / "python.exe"
_WORKER = _PROJECT_ROOT / "scripts" / "kokoro_worker.py"


class KokoroTTSProvider(TTSProvider):
    """Kokoro-82M (Apache-2.0) — crisp, natural English TTS via a worker subprocess.

    Kokoro needs its own Python 3.11 venv (misaki/spacy have no wheels for newer
    Pythons), so we run it out-of-process over a stdin/stdout JSON protocol, just
    like Veena. It is tiny (~330 MB) and runs real-time on CPU, so it does not
    compete with the GPU. Voices: af_heart / af_bella (US female), am_michael
    (US male), bf_* / bm_* (UK), etc. The free-text Parler ``description`` is ignored.
    """

    def __init__(self, voice: str = "af_heart", device: str | None = None, speed: float = 1.0):
        self._voice = voice or "af_heart"
        self._proc: subprocess.Popen | None = None
        atexit.register(self.close)

    def set_speaker(self, voice: str) -> None:
        """Switch voice mid-session. Ignores non-Kokoro names (e.g. a leftover
        per-slide Veena voice like ``kavya``) so mixed scripts don't crash —
        Kokoro voice ids always contain an underscore (``af_heart``)."""
        if voice and "_" in voice and "/" not in voice:
            self._voice = voice

    def _ensure(self) -> None:
        if self._proc is not None and self._proc.poll() is None:
            return
        if not _VENV_PY.exists():
            raise RuntimeError(
                f"Kokoro venv not found at {_VENV_PY}. Create it with:\n"
                "  py -3.11 -m venv .venv-kokoro\n"
                "  .venv-kokoro/Scripts/python -m pip install kokoro soundfile"
            )
        logger.info("Starting Kokoro worker (loading model, ~20s first time)...")
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
        while True:
            line = self._proc.stdout.readline()
            if not line:
                raise RuntimeError("Kokoro worker exited before becoming ready")
            if line.strip() == "READY":
                break
        logger.info("Kokoro worker ready.")

    def synthesize(self, text: str, description: str, output_path: Path) -> float:
        self._ensure()
        assert self._proc is not None and self._proc.stdin and self._proc.stdout
        output_path.parent.mkdir(parents=True, exist_ok=True)
        req = json.dumps({"text": text, "voice": self._voice, "out": str(output_path)})
        self._proc.stdin.write(req + "\n")
        self._proc.stdin.flush()
        resp = self._proc.stdout.readline()
        if not resp:
            raise RuntimeError("Kokoro worker died during synthesis")
        data = json.loads(resp)
        if "error" in data:
            raise RuntimeError(f"Kokoro synthesis failed: {data['error']}")
        return float(data["duration"])

    def name(self) -> str:
        return "kokoro"

    def close(self) -> None:
        """Terminate the worker subprocess. Idempotent."""
        proc = self._proc
        if proc is None:
            return
        self._proc = None
        try:
            if proc.poll() is None:
                if proc.stdin:
                    try:
                        proc.stdin.close()
                    except Exception:
                        pass
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
        except Exception:
            pass

    def __del__(self):
        self.close()
