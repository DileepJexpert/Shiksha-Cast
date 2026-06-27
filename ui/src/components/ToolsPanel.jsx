import { useState, useEffect, useCallback } from 'react';
import { getGpu, freeGpu } from '../api.js';

export default function ToolsPanel() {
  const [gpu, setGpu] = useState(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState('');

  const refresh = useCallback(() => {
    getGpu().then(setGpu).catch(() => setGpu({ error: 'unavailable' }));
  }, []);

  useEffect(() => {
    refresh();
    const t = setInterval(refresh, 6000);
    return () => clearInterval(t);
  }, [refresh]);

  async function handleFree() {
    if (!window.confirm('Stop any running builds and free the GPU?\n(The app/server keeps running.)')) return;
    setBusy(true);
    setMsg('');
    try {
      const r = await freeGpu();
      setMsg(`Stopped ${r.count} process${r.count !== 1 ? 'es' : ''} — GPU freed.`);
      if (r.gpu) setGpu(r.gpu);
    } catch (e) {
      setMsg('Error: ' + e.message);
    } finally {
      setBusy(false);
      setTimeout(refresh, 1500);
    }
  }

  const pct = gpu && gpu.memory_total_mb ? Math.round((100 * gpu.memory_used_mb) / gpu.memory_total_mb) : 0;
  const high = pct >= 80;

  return (
    <section className="tools-panel">
      <div className="tools-row">
        <span className="tools-title">🛠️ Maintenance</span>
        {gpu && !gpu.error ? (
          <span className={`gpu-stat ${high ? 'gpu-high' : ''}`}>
            GPU <strong>{gpu.memory_used_mb}</strong> / {gpu.memory_total_mb} MB ({pct}%) · util {gpu.utilization_pct}%
          </span>
        ) : (
          <span className="gpu-stat">GPU: {gpu?.error || '…'}</span>
        )}
        <span className="tools-spacer" />
        <button className="btn-refresh" onClick={refresh} disabled={busy}>Refresh</button>
        <button className="btn-danger" onClick={handleFree} disabled={busy}>
          {busy ? 'Stopping…' : 'Free GPU / Stop builds'}
        </button>
      </div>
      {msg && <div className="tools-msg">{msg}</div>}
      <p className="tools-hint">
        Use <strong>Free GPU</strong> if a build is stuck or you get "out of memory" — it stops builds &amp;
        frees VRAM but keeps the app running. (Per-chapter <strong>Clear cache</strong> is in the chapter editor.)
      </p>
    </section>
  );
}
