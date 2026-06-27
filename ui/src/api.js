const BASE = '';

export async function uploadPdf(file, chapter) {
  const form = new FormData();
  form.append('file', file);
  if (chapter) form.append('chapter', chapter);
  const res = await fetch(`${BASE}/api/upload-pdf`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
  return res.json();
}

export async function uploadSlides(files, chapter) {
  const form = new FormData();
  for (const f of files) form.append('files', f);
  if (chapter) form.append('chapter', chapter);
  const res = await fetch(`${BASE}/api/upload-slides`, { method: 'POST', body: form });
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
  return res.json();
}

export async function saveScript(chapter, slides, title) {
  const body = title ? { title, slides } : { slides };
  const res = await fetch(`${BASE}/api/chapter/${chapter}/script`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Save failed: ${res.status}`);
  return res.json();
}

export async function triggerBuild(chapter, { aiMode = false, force = false } = {}) {
  const res = await fetch(`${BASE}/api/chapter/${chapter}/build`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ai_mode: aiMode, force }),
  });
  if (!res.ok) throw new Error(`Build trigger failed: ${res.status}`);
  return res.json();
}

export async function getStatus(chapter) {
  const res = await fetch(`${BASE}/api/chapter/${chapter}/status`);
  if (!res.ok) throw new Error(`Status check failed: ${res.status}`);
  return res.json();
}

export function downloadUrl(chapter) {
  return `${BASE}/api/chapter/${chapter}/download`;
}

export function srtUrl(chapter) {
  return `${BASE}/api/chapter/${chapter}/srt`;
}

export function slideImageUrl(chapter, filename) {
  return `${BASE}/api/slides/${chapter}/${filename}`;
}

export async function getModels() {
  const res = await fetch(`${BASE}/api/models`);
  if (!res.ok) throw new Error(`Failed to load models: ${res.status}`);
  return res.json();
}

export async function setVoiceModel(model) {
  const res = await fetch(`${BASE}/api/config/voice-model`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model }),
  });
  if (!res.ok) throw new Error(`Failed to set model: ${res.status}`);
  return res.json();
}

export async function getChapters() {
  const res = await fetch(`${BASE}/api/chapters`);
  if (!res.ok) throw new Error(`Failed to load chapters: ${res.status}`);
  return res.json();
}

export async function getScript(chapter) {
  const res = await fetch(`${BASE}/api/chapter/${chapter}/script`);
  if (!res.ok) throw new Error(`Failed to load script: ${res.status}`);
  return res.json();
}

export function logStreamUrl(chapter) {
  return `${BASE}/api/chapter/${chapter}/logs`;
}

export async function newEpisode({ topic, category, slides, model } = {}) {
  const res = await fetch(`${BASE}/api/new-episode`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ topic, category, slides, model }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Generation failed: ${res.status}`);
  return data;
}

export async function generatePackage(chapter, { includeShort = true } = {}) {
  const res = await fetch(`${BASE}/api/chapter/${chapter}/package`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ include_short: includeShort }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Packaging failed: ${res.status}`);
  return data;
}

export function thumbnailUrl(chapter, style = 'curiosity') {
  return `${BASE}/api/chapter/${chapter}/thumbnail?style=${style}&t=${Date.now()}`;
}

export function packageZipUrl(chapter) {
  return `${BASE}/api/chapter/${chapter}/package.zip`;
}

// ---- Maintenance / tools ----
export async function getGpu() {
  const res = await fetch(`${BASE}/api/tools/gpu`);
  if (!res.ok) throw new Error(`GPU status failed: ${res.status}`);
  return res.json();
}

export async function freeGpu() {
  const res = await fetch(`${BASE}/api/tools/free-gpu`, { method: 'POST' });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Free GPU failed: ${res.status}`);
  return data;
}

export async function clearCache(chapter) {
  const res = await fetch(`${BASE}/api/tools/clear-cache/${chapter}`, { method: 'POST' });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Clear cache failed: ${res.status}`);
  return data;
}
