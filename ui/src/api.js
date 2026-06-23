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

export async function saveScript(chapter, slides) {
  const res = await fetch(`${BASE}/api/chapter/${chapter}/script`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ slides }),
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
