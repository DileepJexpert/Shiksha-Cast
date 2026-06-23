import { useState, useEffect } from 'react';
import { slideImageUrl } from '../api.js';

export default function SlideEditor({ chapter, slides, existingScript, onScriptChange }) {
  const [voiceDesc, setVoiceDesc] = useState('');
  const [perSlideVoice, setPerSlideVoice] = useState({});
  const [visualPrompts, setVisualPrompts] = useState({});
  const [narrations, setNarrations] = useState(() =>
    Object.fromEntries(slides.map((s) => [s.n, '']))
  );

  useEffect(() => {
    if (existingScript && existingScript.slides) {
      const narr = {};
      const voices = {};
      const prompts = {};
      for (const s of existingScript.slides) {
        narr[s.n] = s.narration || '';
        if (s.voice_description) voices[s.n] = s.voice_description;
        if (s.visual_prompt) prompts[s.n] = s.visual_prompt;
      }
      setNarrations(narr);
      setPerSlideVoice(voices);
      setVisualPrompts(prompts);
      emitChange(narr, voiceDesc, voices, prompts);
    }
  }, [existingScript]);

  function updateNarration(n, text) {
    const updated = { ...narrations, [n]: text };
    setNarrations(updated);
    emitChange(updated, voiceDesc, perSlideVoice, visualPrompts);
  }

  function updateVoiceDesc(val) {
    setVoiceDesc(val);
    emitChange(narrations, val, perSlideVoice, visualPrompts);
  }

  function updatePerSlideVoice(n, val) {
    const updated = { ...perSlideVoice, [n]: val };
    setPerSlideVoice(updated);
    emitChange(narrations, voiceDesc, updated, visualPrompts);
  }

  function updateVisualPrompt(n, val) {
    const updated = { ...visualPrompts, [n]: val };
    setVisualPrompts(updated);
    emitChange(narrations, voiceDesc, perSlideVoice, updated);
  }

  function emitChange(narr, voice, perVoice, visuals) {
    const slideData = slides.map((s) => ({
      n: s.n,
      narration: narr[s.n] || '',
      voice_description: perVoice[s.n] || voice || undefined,
      visual_prompt: visuals[s.n] || undefined,
    }));
    onScriptChange(slideData);
  }

  const wordCount = Object.values(narrations).join(' ').split(/\s+/).filter(Boolean).length;
  const filledCount = Object.values(narrations).filter((n) => n.trim()).length;

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

      <div className="voice-global">
        <label htmlFor="voice-desc">Voice description (all slides)</label>
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
              <details className="visual-prompt-section">
                <summary>AI Visual Prompt (optional)</summary>
                <textarea
                  rows={2}
                  className="visual-prompt-input"
                  placeholder="Describe the image to generate, e.g. 'Colorful 2D shapes - triangles, squares, circles on a chalkboard'"
                  value={visualPrompts[slide.n] || ''}
                  onChange={(e) => updateVisualPrompt(slide.n, e.target.value)}
                />
              </details>
              <details className="voice-override">
                <summary>Voice override</summary>
                <input
                  type="text"
                  placeholder="Override voice for this slide"
                  value={perSlideVoice[slide.n] || ''}
                  onChange={(e) => updatePerSlideVoice(slide.n, e.target.value)}
                />
              </details>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
