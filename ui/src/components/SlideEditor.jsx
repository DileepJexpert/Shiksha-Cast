import { useState } from 'react';
import { slideImageUrl } from '../api.js';

export default function SlideEditor({ chapter, slides, onScriptChange }) {
  const [voiceDesc, setVoiceDesc] = useState('');
  const [perSlideVoice, setPerSlideVoice] = useState({});
  const [narrations, setNarrations] = useState(() =>
    Object.fromEntries(slides.map((s) => [s.n, '']))
  );

  function updateNarration(n, text) {
    const updated = { ...narrations, [n]: text };
    setNarrations(updated);
    emitChange(updated, voiceDesc, perSlideVoice);
  }

  function updateVoiceDesc(val) {
    setVoiceDesc(val);
    emitChange(narrations, val, perSlideVoice);
  }

  function updatePerSlideVoice(n, val) {
    const updated = { ...perSlideVoice, [n]: val };
    setPerSlideVoice(updated);
    emitChange(narrations, voiceDesc, updated);
  }

  function emitChange(narr, voice, perVoice) {
    const slideData = slides.map((s) => ({
      n: s.n,
      narration: narr[s.n] || '',
      voice_description: perVoice[s.n] || voice || undefined,
    }));
    onScriptChange(slideData);
  }

  return (
    <section className="slide-editor">
      <h2>Slide Editor</h2>

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
          <div key={slide.n} className="slide-card">
            <div className="slide-thumb-container">
              <span className="slide-number">#{slide.n}</span>
              <img
                className="slide-thumb"
                src={slide.image_url || slideImageUrl(chapter, `slide_${slide.n}.png`)}
                alt={`Slide ${slide.n}`}
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
