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

export async function triggerBuild(chapter) {
  const res = await fetch(`${BASE}/api/chapter/${chapter}/build`, { method: 'POST' });
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

export function slideImageUrl(chapter, filename) {
  return `${BASE}/api/slides/${chapter}/${filename}`;
}
