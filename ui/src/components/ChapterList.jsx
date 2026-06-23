import { useState, useEffect } from 'react';
import { getChapters, downloadUrl, srtUrl } from '../api.js';

export default function ChapterList({ onSelect, onNew }) {
  const [chapters, setChapters] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadChapters();
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
