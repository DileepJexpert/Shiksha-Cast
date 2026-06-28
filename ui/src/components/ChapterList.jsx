import { useState, useEffect, useMemo } from 'react';
import { getChapters, downloadUrl, srtUrl } from '../api.js';

// Friendly "pillars" mapped from the raw content/ folders.
const PILLARS = [
  { key: 'cartoon', label: '🎬 Cartoons', cats: ['cartoon'] },
  { key: 'kids', label: '🧒 Kids / Kinnu', cats: ['kinnu', 'kids-learning'] },
  { key: 'how', label: '🔬 How It Works', cats: ['how-it-works'] },
  { key: 'class', label: '📚 Class Tutorials', cats: ['class-chapter', 'science', 'comparisons'] },
  { key: 'stories', label: '📖 Stories & Wisdom', cats: ['wisdom-stories', 'stories'] },
  { key: 'money', label: '💰 Money & Govt', cats: ['banking-finance', 'government-process'] },
  { key: 'tech', label: '🤖 Tech & AI', cats: ['ai-tools', 'software-architecture'] },
  { key: 'general', label: '🌍 General', cats: ['general-knowledge', 'pashu-palan'] },
];
const OTHER = { key: 'other', label: '📦 Other', cats: [] };

function pillarOf(cat) {
  return PILLARS.find((p) => p.cats.includes(cat))?.key || 'other';
}

export default function ChapterList({ onSelect, onNew, onNewTopic }) {
  const [chapters, setChapters] = useState([]);
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState('');
  const [status, setStatus] = useState('all'); // all | draft | ready
  const [open, setOpen] = useState({});

  useEffect(() => {
    loadChapters();
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

  const isReady = (ch) => ch.has_video || ch.build_status === 'done';

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return chapters.filter((ch) => {
      if (status === 'ready' && !isReady(ch)) return false;
      if (status === 'draft' && isReady(ch)) return false;
      if (needle) {
        const hay = `${ch.id} ${ch.title || ''} ${ch.category || ''}`.toLowerCase();
        if (!hay.includes(needle)) return false;
      }
      return true;
    });
  }, [chapters, q, status]);

  const groups = useMemo(() => {
    return [...PILLARS, OTHER]
      .map((p) => ({ ...p, items: filtered.filter((ch) => pillarOf(ch.category) === p.key) }))
      .filter((g) => g.items.length > 0);
  }, [filtered]);

  const searching = q.trim().length > 0;
  const isOpen = (k) => searching || !!open[k];
  const toggle = (k) => setOpen((o) => ({ ...o, [k]: !o[k] }));

  return (
    <section className="chapter-list">
      <div className="chapter-list-header">
        <h2>Your Content <span className="count-pill">{chapters.length}</span></h2>
        <div className="chapter-list-actions">
          <button className="btn-refresh" onClick={loadChapters} disabled={loading}>
            {loading ? 'Loading...' : 'Refresh'}
          </button>
          {onNewTopic && <button className="btn-primary" onClick={onNewTopic}>✨ New from Topic</button>}
          <button className="btn-secondary" onClick={onNew}>+ New Chapter (PDF)</button>
        </div>
      </div>

      <div className="cat-toolbar">
        <input
          className="cat-search"
          type="text"
          placeholder="🔍 Search by title, id or category…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <div className="cat-status">
          {['all', 'draft', 'ready'].map((s) => (
            <button
              key={s}
              className={`status-chip ${status === s ? 'active' : ''}`}
              onClick={() => setStatus(s)}
            >
              {s === 'all' ? 'All' : s === 'draft' ? 'Draft' : 'Ready'}
            </button>
          ))}
        </div>
      </div>

      {loading && chapters.length === 0 && <div className="chapter-empty">Loading…</div>}
      {!loading && filtered.length === 0 && (
        <div className="chapter-empty"><p>No matching content. Try a different search or filter.</p></div>
      )}

      {groups.map((g) => (
        <div className="cat-group" key={g.key}>
          <button className="cat-group-header" onClick={() => toggle(g.key)}>
            <span className="cat-caret">{isOpen(g.key) ? '▾' : '▸'}</span>
            <span className="cat-label">{g.label}</span>
            <span className="count-pill">{g.items.length}</span>
          </button>
          {isOpen(g.key) && (
            <div className="chapter-grid">
              {g.items.map((ch) => (
                <div
                  key={ch.id}
                  className={`chapter-card ${ch.build_status === 'running' ? 'building' : ''} ${ch.is_cartoon ? 'is-cartoon' : ''}`}
                  onClick={() => !ch.is_cartoon && onSelect(ch)}
                  title={ch.is_cartoon ? 'Cartoon episode — build via CLI: python -m shiksha_cast cartoon-build -c ' + ch.id : undefined}
                >
                  <div className="chapter-card-top">
                    <span className="chapter-id">{ch.id}</span>
                    <StatusBadge status={ch.build_status} hasVideo={ch.has_video} />
                  </div>
                  <h3 className="chapter-title">{ch.title}</h3>
                  <div className="chapter-meta">
                    <span>{ch.slide_count} {ch.is_cartoon ? 'scenes' : 'slides'}</span>
                    {ch.is_cartoon && <span className="tag tag-cartoon">Cartoon</span>}
                    {ch.has_pdf && <span className="tag tag-pdf">PDF</span>}
                    {!ch.is_cartoon && ch.has_script && <span className="tag tag-script">Script</span>}
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
          )}
        </div>
      ))}
    </section>
  );
}

function StatusBadge({ status, hasVideo }) {
  if (status === 'running') return <span className="status-badge status-running">Building</span>;
  if (status === 'error') return <span className="status-badge status-error">Error</span>;
  if (status === 'done' || hasVideo) return <span className="status-badge status-done">Ready</span>;
  return <span className="status-badge status-idle">Draft</span>;
}
