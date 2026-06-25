import { useState } from 'react';
import { newEpisode } from '../api.js';

const CATEGORIES = [
  'how-it-works/human-body',
  'how-it-works/space',
  'how-it-works/technology',
  'how-it-works/physics',
  'how-it-works/chemistry',
  'how-it-works/earth-nature',
  'class-chapter/class-06',
  'class-chapter/class-07',
  'class-chapter/class-08',
  'class-chapter/class-09',
  'class-chapter/class-10',
  'general-knowledge',
];

export default function TopicForm({ onCreated, onCancel }) {
  const [topic, setTopic] = useState('');
  const [category, setCategory] = useState('general-knowledge');
  const [slides, setSlides] = useState(8);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function handleGenerate() {
    if (!topic.trim()) {
      setError('Enter a topic first.');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await newEpisode({ topic: topic.trim(), category, slides: Number(slides) });
      onCreated(res); // { chapter, title, slide_count, missing_visual_prompts }
    } catch (e) {
      setError(e.message || 'Generation failed.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="topic-form card">
      <h2>✨ New from Topic</h2>
      <p className="topic-hint">
        Describe a topic — a local AI (Ollama) writes the full narration script. Then review it,
        pick a voice, and build. No command line needed.
      </p>

      <label className="field">
        <span>Topic</span>
        <input
          type="text"
          value={topic}
          placeholder='e.g. "Why do we get hiccups?"'
          onChange={(e) => setTopic(e.target.value)}
          disabled={busy}
          autoFocus
        />
      </label>

      <div className="field-row">
        <label className="field">
          <span>Category</span>
          <select value={category} onChange={(e) => setCategory(e.target.value)} disabled={busy}>
            {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>

        <label className="field field-narrow">
          <span>Slides</span>
          <input
            type="number" min="4" max="20" value={slides}
            onChange={(e) => setSlides(e.target.value)} disabled={busy}
          />
        </label>
      </div>

      {error && <div className="topic-error">⚠️ {error}</div>}

      <div className="topic-actions">
        <button className="btn-back" onClick={onCancel} disabled={busy}>Cancel</button>
        <button className="btn-primary" onClick={handleGenerate} disabled={busy}>
          {busy ? 'Generating script… (~1 min)' : 'Generate Script'}
        </button>
      </div>
    </section>
  );
}
