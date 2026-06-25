import { useMemo, useState, useEffect } from 'react';
import { slideImageUrl, getModels } from '../api.js';

export default function SlideEditor({
  chapter,
  slides,
  scriptData,
  onScriptChange,
}) {
  const [voiceDesc, setVoiceDesc] = useState('');
  const [bulkText, setBulkText] = useState('');
  const [bulkOpen, setBulkOpen] = useState(false);
  const [voiceOptions, setVoiceOptions] = useState([]);

  const scriptBySlide = useMemo(() => {
    return new Map((scriptData || []).map((s) => [s.n, s]));
  }, [scriptData]);

  useEffect(() => {
    getModels()
      .then((data) => {
        const veena = (data.models || [])
          .filter((m) => m.id.startsWith('veena:'))
          .map((m) => ({ id: m.id.split(':')[1], name: m.name.replace('Veena - ', '') }));
        setVoiceOptions(veena);
      })
      .catch(() => {});
  }, []);

  function normalizedScript() {
    return slides.map((s) => scriptBySlide.get(s.n) || { n: s.n, narration: '' });
  }

  function updateSlide(n, patch) {
    const next = normalizedScript().map((s) => (s.n === n ? { ...s, ...patch, n } : s));
    onScriptChange(next);
  }

  function updateVoiceDesc(val) {
    setVoiceDesc(val);
    const next = normalizedScript().map((s) => ({
      ...s,
      voice_description: s.voice_description || val || undefined,
    }));
    onScriptChange(next);
  }

  function applyBulk() {
    const blocks = bulkText
      .split(/\n\s*\n|\n-{3,}\n/)
      .map((b) => b.trim())
      .filter(Boolean);

    const next = normalizedScript().map((s, i) => ({
      ...s,
      narration: blocks[i] ?? s.narration ?? '',
    }));
    onScriptChange(next);
    setBulkOpen(false);
  }

  const narrations = normalizedScript().map((s) => s.narration || '');
  const wordCount = narrations.join(' ').split(/\s+/).filter(Boolean).length;
  const filledCount = narrations.filter((n) => n.trim()).length;
  const bulkBlocks = bulkText
    .split(/\n\s*\n|\n-{3,}\n/)
    .map((b) => b.trim())
    .filter(Boolean).length;

  return (
    <section className="slide-editor">
      <div className="editor-header">
        <h2>Slide Editor</h2>
        <div className="editor-stats">
          <span className="stat">{filledCount}/{slides.length} narrated</span>
          <span className="stat">{wordCount} words</span>
          <span className="stat">~{Math.ceil(wordCount / 130)} min</span>
        </div>
      </div>

      <div className="bulk-paste">
        <button className="btn-secondary" onClick={() => setBulkOpen((v) => !v)}>
          {bulkOpen ? 'Close bulk paste' : 'Paste full script'}
        </button>
        {bulkOpen && (
          <div className="bulk-paste-body">
            <p className="bulk-hint">
              Paste your whole script below. Separate each slide with a <strong>blank line</strong>
              {' '}(or a line with <code>---</code>). It fills slides 1 to {slides.length} in order.
            </p>
            <textarea
              rows={8}
              placeholder={"Slide 1 narration...\n\nSlide 2 narration...\n\nSlide 3 narration..."}
              value={bulkText}
              onChange={(e) => setBulkText(e.target.value)}
            />
            <div className="bulk-actions">
              <span className="stat">{bulkBlocks} block{bulkBlocks !== 1 ? 's' : ''} to {slides.length} slides</span>
              <button className="btn-primary" onClick={applyBulk} disabled={!bulkBlocks}>
                Apply to slides
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="dialogue-tip">
        <strong>Two-host dialogue in one slide:</strong> start lines with <code>F:</code> (female)
        or <code>M:</code> (male), and each line is voiced separately and stitched. You can also
        set a single voice per slide with the dropdown below.
      </div>

      <div className="voice-global">
        <label htmlFor="voice-desc">Voice description (all slides, optional)</label>
        <input
          id="voice-desc"
          type="text"
          placeholder="e.g. calm female narrator, Indian English accent"
          value={voiceDesc}
          onChange={(e) => updateVoiceDesc(e.target.value)}
        />
      </div>

      <div className="slide-list">
        {slides.map((slide) => {
          const scriptSlide = scriptBySlide.get(slide.n) || { n: slide.n, narration: '' };

          return (
            <div key={slide.n} className={`slide-card ${scriptSlide.narration?.trim() ? 'has-narration' : ''}`}>
              <div className="slide-thumb-container">
                <span className="slide-number">#{slide.n}</span>
                <img
                  className="slide-thumb"
                  src={slide.image_url || slideImageUrl(chapter, `slide_${String(slide.n).padStart(3, '0')}.png`)}
                  alt={`Slide ${slide.n}`}
                  onError={(e) => { e.target.style.display = 'none'; }}
                />
              </div>
              <div className="slide-fields">
                <label>Narration for slide {slide.n}</label>
                <textarea
                  rows={4}
                  placeholder="Enter narration text for this slide..."
                  value={scriptSlide.narration || ''}
                  onChange={(e) => updateSlide(slide.n, { narration: e.target.value })}
                />
                {voiceOptions.length > 0 && (
                  <div className="slide-voice-row">
                    <label>Voice for this slide</label>
                    <select
                      value={scriptSlide.voice || ''}
                      onChange={(e) => updateSlide(slide.n, { voice: e.target.value || undefined })}
                    >
                      <option value="">Default (chapter voice)</option>
                      {voiceOptions.map((v) => (
                        <option key={v.id} value={v.id}>{v.name}</option>
                      ))}
                    </select>
                  </div>
                )}
                <details className="visual-prompt-section">
                  <summary>AI Visual Prompt (optional)</summary>
                  <textarea
                    rows={2}
                    className="visual-prompt-input"
                    placeholder="Describe the image to generate, e.g. 'Colorful 2D shapes on a chalkboard'"
                    value={scriptSlide.visual_prompt || ''}
                    onChange={(e) => updateSlide(slide.n, { visual_prompt: e.target.value || undefined })}
                  />
                </details>
                <details className="voice-override">
                  <summary>Advanced voice description</summary>
                  <input
                    type="text"
                    placeholder="Free-text voice description for this slide"
                    value={scriptSlide.voice_description || ''}
                    onChange={(e) => updateSlide(slide.n, { voice_description: e.target.value || undefined })}
                  />
                </details>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
