# Shiksha-Cast / Kinnu — Troubleshooting (do-it-yourself)

Practical fixes for the issues that come up when building videos on a Windows
laptop with an 8 GB GPU. All commands are **Windows** (Command Prompt / PowerShell),
run from the project folder: `cd C:\dileepkm\Learning\Shiksha-Cast`.

---

## 0. Golden rules (avoid 90% of problems)

1. **Only ONE build at a time.** Two GPU jobs together → "CUDA out of memory". Never
   run two `build`/`ai-build` at once, and don't trigger a dashboard build while a
   terminal build runs.
2. **Keep the laptop awake & plugged in.** If it sleeps, the build pauses/dies. Set
   Power mode so it never sleeps while building. A cooling pad helps (less throttling).
3. **Close GPU-hungry apps while building** — Chrome with many tabs/videos, NVIDIA
   Broadcast, games, Photoshop. They eat VRAM and slow generation.
4. **Run builds in your OWN terminal window** (`build-video.bat <id>`). A window you
   open yourself keeps running even if other tools/sessions close.
5. **Builds are resumable.** If one dies, just run it again — finished slides/images
   and audio are cached and skipped.

---

## 1. Quick health checks

```bat
nvidia-smi                                  REM GPU memory + utilization (live)
tasklist | findstr python                   REM is a build/server running?
tasklist | findstr node                     REM is the frontend (vite) running?
netstat -ano | findstr :8000                REM is the backend port in use?
netstat -ano | findstr :5173                REM is the frontend port in use?
```
- GPU **utilization > 0%** and memory a few GB = a build is actively working.
- GPU back to ~1–2 GB and your build window gone = the build **stopped**.

---

## 2. Free up GPU RAM / kill a stuck or runaway build

Find the python process id (PID) and kill it (and its children with `/T`):
```bat
tasklist | findstr python                   REM note the PID number
taskkill /PID <PID> /T /F                    REM kill that process tree
```
Kill ALL python (use only if nothing important else is running in Python):
```bat
taskkill /IM python.exe /F
```
Then confirm VRAM is freed:
```bat
nvidia-smi
```
> A leftover ~1–3 GB after killing is normal — that's your desktop apps, not the build.

---

## 3. "CUDA out of memory" (OOM)

Causes & fixes:
- **Two models at once.** e.g. SDXL (images) + Veena (voice) together. For `ai-build`,
  if it OOMs at narration: the images are already cached, so **just run it again** —
  the re-run skips SDXL and Veena gets the whole GPU.
- **Desktop apps using VRAM.** Close them (rule #3), check with `nvidia-smi`, retry.
- **Too-big model.** Parler **Large** (fp32 ~8.5 GB) does NOT fit 8 GB — use **Veena**
  or Parler **Mini** instead. Set the voice in `config\channel.yaml`.
- SDXL is already configured to **CPU-offload** (fits 8 GB). If you still OOM on images,
  close apps and retry.

---

## 4. A build died / how to resume

Just re-run the same command — it continues from where it stopped:
```bat
build-video.bat <episode-id>                       REM normal (text slides)
python -m shiksha_cast ai-build -c <episode-id>     REM AI images version
build-all.bat                                       REM all episodes; skips finished
```
Why it works: each slide's **audio is saved after it's made**, and **images are cached**,
so a resumed build skips everything already done.

---

## 5. "Veena worker exited before becoming ready"

This means the Veena voice model couldn't load — almost always **not enough free VRAM**.
Fix:
1. `nvidia-smi` — make sure nothing else big is on the GPU.
2. Close GPU apps; if you just ran `ai-build`, run it **again** (images are cached now,
   so SDXL won't load and Veena gets the full GPU).
3. Make sure the env exists: `dir .venv-veena\Scripts\python.exe`. If missing, recreate
   it (section 8).

---

## 6. Backend/dashboard not responding, or won't start

- **Port already in use** (`netstat -ano | findstr :8000` shows a PID): kill it, then
  restart:
  ```bat
  taskkill /PID <PID> /F
  run-backend.bat
  ```
- **Server wedged during a build** (API slow/blank): that's normal while the GPU is busy
  — wait, or stop the build (section 2) and restart `run-backend.bat`.
- **New voices/options not showing** in the dashboard: restart the backend
  (`run-backend.bat`) and hard-refresh the browser (**Ctrl+Shift+R**).
- **Frontend on a different port** (5174 instead of 5173): it prints the URL in its
  window — just open that URL.

---

## 7. Builds are very slow

- Normal on an 8 GB laptop GPU: Veena voice is a few minutes per slide. A full episode
  can take 30–90 min.
- Speed it up: close GPU apps, plug in, improve cooling (throttling makes it worse over
  time), keep the laptop awake.
- For many videos, run `build-all.bat` overnight (it's resumable).

---

## 8. Recreate the Veena voice environment (if it breaks)

```bat
python -m venv .venv-veena --system-site-packages
.venv-veena\Scripts\python -m pip install snac bitsandbytes accelerate
```
Quick test it works:
```bat
.venv-veena\Scripts\python -c "import bitsandbytes, torch; print(torch.cuda.is_available())"
```
Should print `True`.

---

## 9. Where the settings are

- **Voice / model:** `config\channel.yaml` → `voice.provider` (veena) + `voice.model`
  (kavya / maitri / agastya / vinaya). Per-slide voice or `F:`/`M:` dialogue tags go in
  the episode's `script.yaml`.
- **Per-episode brand on slides:** add `brand: "KINNU"` at the top of `script.yaml`.
- **Image motion (ai-build):** `config\channel.yaml` → `imagegen.motion`
  (kenburns / parallax / static).
- **Outputs:** videos in `dist\`, slides in `build\<id>\slides\`, decks in `decks\<id>\`.

---

## 10. Verify a finished video before uploading

```bat
ffprobe dist\<id>.mp4                                          REM streams + duration
ffmpeg -i dist\<id>.mp4 -af volumedetect -f null -             REM check audio is real
```
A real narrated video has `mean_volume` around **-18 to -23 dB**. If it's around
**-45 dB or lower**, the audio is basically silent (e.g. the "Test Tone" voice) — rebuild
with a real voice (Veena).

---

## 11. Recover something you deleted

Everything committed is on GitHub. To get a file back:
```bat
git log --oneline                       REM find a commit before the change
git checkout <commit> -- path\to\file   REM restore that file
```
Branch: `claude/youthful-mccarthy-xg0wn7` (and `main`). Remote:
`https://github.com/DileepJexpert/Shiksha-Cast`.
