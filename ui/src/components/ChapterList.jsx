import { useState, useEffect } from 'react';
import { getChapters, downloadUrl, srtUrl } from '../api.js';

export default function ChapterList({ onSelect, onNew }) {
  const [chapters, setChapters] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadChapters();
    // Auto-refresh so manually-added chapters and finished builds appear without
    // clicking Refresh: poll periodically + whenever the window regains focus.
    const interval = setInterval(loadChapters, 8000);
    const onFocus = () => loadChapters();
    window.addEventListener('focus', onFocus);
    return () => {
      clearInterval(interval);
      window.removeEventListener('focus', onFocus);
    };
  }, []);

  async function loadChapters() {
    setLoading(true);
    try {
      const data = await getChapters();
      setChapters(data.chapters || []);
    } catch {
      setChapters([]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="chapter-list">
      <div className="chapter-list-header">
        <h2>Your Chapters</h2>
        <div className="chapter-list-actions">
          <button className="btn-refresh" onClick={loadChapters} disabled={loading}>
            {loading ? 'Loading...' : 'Refresh'}
          </button>
          <button className="btn-primary" onClick={onNew}>
            + New Chapter
          </button>
        </div>
      </div>

      <details className="howto-panel">
        <summary>📖 How to create a tutorial (click to expand)</summary>
        <div className="howto-body">
          <ol>
            <li><strong>+ New Chapter</strong> → upload the slide <strong>PDF</strong> (or PNG images) and name it (e.g. <code>ch07</code>).</li>
            <li>In the editor, click <strong>📋 Paste full script</strong> to drop in your whole narration at once (one blank line between slides), or type each slide.
              <br />For Hinglish, write Hindi with English terms inline: <em>"आज हम place value सीखेंगे"</em>.</li>
            <li>Pick the <strong>voice</strong> (Veena — Kavya for Hinglish) in the TTS panel, or set a different voice per slide.</li>
            <li>Click <strong>Save</strong>, then <strong>Build Video</strong>, watch the logs, and <strong>Download</strong> the MP4.</li>
          </ol>
          <p className="howto-note">
            Prefer files? Drop <code>chNN.pdf</code> + <code>chNN.yaml</code> into <code>content/chNN/</code> —
            it appears here automatically (this list auto-refreshes). One build at a time on the GPU.
          </p>
        </div>
      </details>

      {loading && chapters.length === 0 && (
        <div className="chapter-empty">Loading chapters...</div>
      )}

      {!loading && chapters.length === 0 && (
        <div className="chapter-empty">
          <p>No chapters yet. Upload a PDF or slide images to get started.</p>
        </div>
      )}

      <div className="chapter-grid">
        {chapters.map((ch) => (
          <div
            key={ch.id}
            className={`chapter-card ${ch.build_status === 'running' ? 'building' : ''}`}
            onClick={() => onSelect(ch)}
          >
            <div className="chapter-card-top">
              <span className="chapter-id">{ch.id}</span>
              <StatusBadge status={ch.build_status} hasVideo={ch.has_video} />
            </div>

            <h3 className="chapter-title">{ch.title}</h3>

            <div className="chapter-meta">
              <span>{ch.slide_count} slides</span>
              {ch.has_pdf && <span className="tag tag-pdf">PDF</span>}
              {ch.has_script && <span className="tag tag-script">Script</span>}
              {ch.has_video && <span className="tag tag-video">Video</span>}
            </div>

            {ch.has_video && (
              <div className="chapter-downloads" onClick={(e) => e.stopPropagation()}>
                <a href={downloadUrl(ch.id)} download className="dl-link">MP4</a>
                <a href={srtUrl(ch.id)} download className="dl-link">SRT</a>
              </div>
            )}
          </div>
        ))}
      </div>
    </section>
  );
}

function StatusBadge({ status, hasVideo }) {
  if (status === 'running') return <span className="status-badge status-running">Building</span>;
  if (status === 'error') return <span className="status-badge status-error">Error</span>;
  if (status === 'done' || hasVideo) return <span className="status-badge status-done">Ready</span>;
  return <span className="status-badge status-idle">Draft</span>;
}
