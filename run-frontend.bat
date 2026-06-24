@echo off
REM Start the Shiksha-Cast dashboard (Vite dev server).
REM It will print a URL like http://localhost:5173 — open it in your browser.
cd /d %~dp0\ui
npm run dev
