import { useState, useEffect } from 'react';
import { slideImageUrl, getModels } from '../api.js';

export default function SlideEditor({ chapter, slides, existingScript, onScriptChange }) {
  const [voiceDesc, setVoiceDesc] = useState('');
  const [perSlideVoiceDesc, setPerSlideVoiceDesc] = useState({}); // free-text voice_description
  const [perSlideSpeaker, setPerSlideSpeaker] = useState({});     // Veena speaker -> slide.voice
  const [visualPrompts, setVisualPrompts] = useState({});
  const [narrations, setNarrations] = useState(() =>
    Object.fromEntries(slides.map((s) => [s.n, '']))
  );
  const [bulkText, setBulkText] = useState('');
  const [bulkOpen, setBulkOpen] = useState(false);
  const [voiceOptions, setVoiceOptions] = useState([]); // [{id:'kavya', name:'...'}]

  // Load the available Veena speaker voices for the per-slide dropdown.
  useEffect(() => {
    getModels()
      .then((data) => {
        const veena = (data.models || [])
          .filter((m) => m.id.startsWith('veena:'))
          .map((m) => ({ id: m.id.split(':')[1], name: m.name.replace('Veena — ', '') }));
        setVoiceOptions(veena);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (existingScript && existingScript.slides) {
      const narr = {};
      const voices = {};
      const speakers = {};
      const prompts = {};
      for (const s of existingScript.slides) {
        narr[s.n] = s.narration || '';
        if (s.voice_description) voices[s.n] = s.voice_description;
        if (s.voice) speakers[s.n] = s.voice;
        if (s.visual_prompt) prompts[s.n] = s.visual_prompt;
      }
      setNarrations(narr);
      setPerSlideVoiceDesc(voices);
      setPerSlideSpeaker(speakers);
      setVisualPrompts(prompts);
      emitChange(narr, voiceDesc, voices, speakers, prompts);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [existingScript]);

  function updateNarration(n, text) {
    const updated = { ...narrations, [n]: text };
    setNarrations(updated);
    emitChange(updated, voiceDesc, perSlideVoiceDesc, perSlideSpeaker, visualPrompts);
  }

  function updateVoiceDesc(val) {
    setVoiceDesc(val);
    emitChange(narrations, val, perSlideVoiceDesc, perSlideSpeaker, visualPrompts);
  }

  function updatePerSlideVoiceDesc(n, val) {
    const updated = { ...perSlideVoiceDesc, [n]: val };
    setPerSlideVoiceDesc(updated);
    emitChange(narrations, voiceDesc, updated, perSlideSpeaker, visualPrompts);
  }

  function updateSpeaker(n, val) {
    const updated = { ...perSlideSpeaker };
    if (val) updated[n] = val; else delete updated[n];
    setPerSlideSpeaker(updated);
    emitChange(narrations, voiceDesc, perSlideVoiceDesc, updated, visualPrompts);
  }

  function updateVisualPrompt(n, val) {
    const updated = { ...visualPrompts, [n]: val };
    setVisualPrompts(updated);
    emitChange(narrations, voiceDesc, perSlideVoiceDesc, perSlideSpeaker, updated);
  }

  // Split a pasted script into per-slide narration. Blocks are separated by a blank
  // line; assigned to slides 1..N in order. "---" on its own line also splits.
  function applyBulk() {
    const blocks = bulkText
      .split(/\n\s*\n|\n-{3,}\n/)
      .map((b) => b.trim())
      .filter(Boolean);
    const updated = { ...narrations };
    slides.forEach((s, i) => {
      if (blocks[i] !== undefined) updated[s.n] = blocks[i];
    });
    setNarrations(updated);
    emitChange(updated, voiceDesc, perSlideVoiceDesc, perSlideSpeaker, visualPrompts);
    setBulkOpen(false);
  }

  function emitChange(narr, voice, perVoice, speakers, visuals) {
    const slideData = slides.map((s) => ({
      n: s.n,
      narration: narr[s.n] || '',
      voice_description: perVoice[s.n] || voice || undefined,
      voice: speakers[s.n] || undefined,
      visual_prompt: visuals[s.n] || undefined,
    }));
    onScriptChange(slideData);
  }

  const wordCount = Object.values(narrations).join(' ').split(/\s+/).filter(Boolean).length;
  const filledCount = Object.values(narrations).filter((n) => n.trim()).length;
  const bulkBlocks = bulkText.split(/\n\s*\n|\n-{3,}\n/).map((b) => b.trim()).filter(Boolean).length;

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

      {/* Bulk paste: paste a whole script, auto-split into slides */}
      <div className="bulk-paste">
        <button className="btn-secondary" onClick={() => setBulkOpen((v) => !v)}>
          {bulkOpen ? 'Close bulk paste' : '📋 Paste full script'}
        </button>
        {bulkOpen && (
          <div className="bulk-paste-body">
            <p className="bulk-hint">
              Paste your whole script below. Separate each slide with a <strong>blank line</strong>
              {' '}(or a line with <code>---</code>). It fills slides 1→{slides.length} in order.
            </p>
            <textarea
              rows={8}
              placeholder={"Slide 1 narration...\n\nSlide 2 narration...\n\nSlide 3 narration..."}
              value={bulkText}
              onChange={(e) => setBulkText(e.target.value)}
            />
            <div className="bulk-actions">
              <span className="stat">{bulkBlocks} block{bulkBlocks !== 1 ? 's' : ''} → {slides.length} slides</span>
              <button className="btn-primary" onClick={applyBulk} disabled={!bulkBlocks}>
                Apply to slides
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="dialogue-tip">
        💬 <strong>Two-host dialogue in one slide:</strong> start lines with <code>F:</code> (female) or
        <code>M:</code> (male) — e.g. <code>F: Aaj hum…</code> / <code>M: Haan, aur…</code> — and each
        line is voiced separately and stitched. Or set a single voice per slide with the dropdown below.
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
        {slides.map((slide) => (
          <div key={slide.n} className={`slide-card ${narrations[slide.n]?.trim() ? 'has-narration' : ''}`}>
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
                value={narrations[slide.n] || ''}
                onChange={(e) => updateNarration(slide.n, e.target.value)}
              />
              {voiceOptions.length > 0 && (
                <div className="slide-voice-row">
                  <label>Voice for this slide</label>
                  <select
                    value={perSlideSpeaker[slide.n] || ''}
                    onChange={(e) => updateSpeaker(slide.n, e.target.value)}
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
                  value={visualPrompts[slide.n] || ''}
                  onChange={(e) => updateVisualPrompt(slide.n, e.target.value)}
                />
              </details>
              <details className="voice-override">
                <summary>Advanced voice description</summary>
                <input
                  type="text"
                  placeholder="Free-text voice description for this slide"
                  value={perSlideVoiceDesc[slide.n] || ''}
                  onChange={(e) => updatePerSlideVoiceDesc(slide.n, e.target.value)}
                />
              </details>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
