"""Generate a 9:16 vertical YouTube Short (~45s) from a finished episode video.

Takes the first SECONDS of dist/<ep>.mp4, converts 16:9 -> 1080x1920 with a
blurred background, and burns in the captions (dist/<ep>.srt) large at the
bottom. Great for channel discovery.

Usage:
  python scripts/make_short.py s06-yawning [seconds]
  python scripts/make_short.py --all [seconds]     # every dist/*.mp4
Output: dist/shorts/<ep>_short.mp4
"""
import glob
import os
import subprocess
import sys

DEFAULT_SECONDS = 45


def make_short(ep: str, seconds: int = DEFAULT_SECONDS) -> bool:
    src = f"dist/{ep}.mp4"
    if not os.path.exists(src):
        print(f"  [skip] no video: {src}")
        return False
    os.makedirs("dist/shorts", exist_ok=True)
    out = f"dist/shorts/{ep}_short.mp4"
    srt = f"dist/{ep}.srt"

    # 16:9 -> 9:16: blurred fill background + the slide centered on top.
    vf = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,boxblur=26:5[bg];"
        "[0:v]scale=1040:-2[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2[v]"
    )
    if os.path.exists(srt):
        # burn captions (relative forward-slash path avoids Windows escaping issues)
        style = "Alignment=2,Fontsize=16,Bold=1,Outline=2,Shadow=1,MarginV=140"
        vf = vf[:-3] + f",subtitles={ep_srt(srt)}:force_style='{style}'[v]"

    args = [
        "ffmpeg", "-y", "-t", str(seconds), "-i", src,
        "-filter_complex", vf, "-map", "[v]", "-map", "0:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-t", str(seconds), out,
    ]
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  [FAIL] {ep}: {r.stderr.strip().splitlines()[-1] if r.stderr else 'ffmpeg error'}")
        return False
    print(f"  [ok] {out}")
    return True


def ep_srt(path: str) -> str:
    # ffmpeg subtitles filter: forward slashes, escape the few special chars.
    return path.replace("\\", "/").replace(":", "\\:")


def main():
    args = sys.argv[1:]
    seconds = DEFAULT_SECONDS
    if args and args[-1].isdigit():
        seconds = int(args[-1]); args = args[:-1]
    if args and args[0] == "--all":
        eps = sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob("dist/*.mp4"))
        eps = [e for e in eps if not e.endswith("_short")]
    elif args:
        eps = args
    else:
        print(__doc__); return
    done = sum(make_short(e, seconds) for e in eps)
    print(f"DONE: {done} short(s) created in dist/shorts/")


if __name__ == "__main__":
    main()
