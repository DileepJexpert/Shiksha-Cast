"""Upload built episodes to YouTube (video + thumbnail + metadata), optionally scheduled.

ONE-TIME SETUP:
  1) pip install google-api-python-client google-auth-oauthlib
  2) Google Cloud Console -> create project -> enable "YouTube Data API v3"
  3) Create an OAuth client ID of type "Desktop app", download it as
     client_secret.json into the project root.
  First run opens a browser to authorize; the token is cached in token.json.

USAGE:
  python scripts/youtube_upload.py s06-yawning --privacy unlisted
  python scripts/youtube_upload.py --all --privacy private
  python scripts/youtube_upload.py s06-yawning --publish-at 2026-07-01T09:00:00Z

Reads dist/<ep>.mp4 + dist/<ep>.thumb.png and derives title/description/tags
from your metadata.py. Category 27 = Education.
"""
import glob
import os
import sys
from pathlib import Path

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.force-ssl"]
ROOT = Path(__file__).resolve().parents[1]


def _service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    token = ROOT / "token.json"
    secret = ROOT / "client_secret.json"
    creds = None
    if token.exists():
        creds = Credentials.from_authorized_user_file(str(token), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not secret.exists():
                raise SystemExit(f"Missing {secret}. See setup instructions at top of this file.")
            creds = InstalledAppFlow.from_client_secrets_file(str(secret), SCOPES).run_local_server(port=0)
        token.write_text(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def upload(ep: str, privacy: str = "private", publish_at: str | None = None) -> bool:
    from googleapiclient.http import MediaFileUpload
    from shiksha_cast.metadata import build_metadata

    video = ROOT / "dist" / f"{ep}.mp4"
    if not video.exists():
        print(f"  [skip] no video: {video}")
        return False
    m = build_metadata(ep, ROOT)
    status = {"privacyStatus": privacy, "selfDeclaredMadeForKids": False}
    if publish_at:
        status["privacyStatus"] = "private"
        status["publishAt"] = publish_at  # ISO 8601 UTC, e.g. 2026-07-01T09:00:00Z

    yt = _service()
    body = {
        "snippet": {"title": m.title[:100], "description": m.description,
                    "tags": m.tags[:30], "categoryId": "27"},
        "status": status,
    }
    req = yt.videos().insert(part="snippet,status", body=body,
                            media_body=MediaFileUpload(str(video), chunksize=-1, resumable=True))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    vid = resp["id"]
    print(f"  [uploaded] {ep} -> https://youtu.be/{vid}")

    thumb = ROOT / "dist" / f"{ep}.thumb.png"
    if thumb.exists():
        yt.thumbnails().set(videoId=vid, media_body=MediaFileUpload(str(thumb))).execute()
        print("    thumbnail set")
    return True


def main():
    args = sys.argv[1:]
    privacy, publish_at, eps = "private", None, []
    i = 0
    while i < len(args):
        a = args[i]
        if a == "--privacy":
            privacy = args[i + 1]; i += 2
        elif a == "--publish-at":
            publish_at = args[i + 1]; i += 2
        elif a == "--all":
            eps = sorted(os.path.splitext(os.path.basename(p))[0]
                         for p in glob.glob(str(ROOT / "dist" / "*.mp4")))
            eps = [e for e in eps if not e.endswith("_short")]; i += 1
        else:
            eps.append(a); i += 1
    if not eps:
        print(__doc__); return
    done = sum(upload(e, privacy, publish_at) for e in eps)
    print(f"DONE: {done} uploaded ({privacy}).")


if __name__ == "__main__":
    main()
