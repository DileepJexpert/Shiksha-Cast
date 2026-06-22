import { useState, useEffect } from 'react';
import { getModels, setVoiceModel } from '../api.js';

const CATEGORIES = ['Hindi', 'Multilingual', 'Test'];

export default function ModelSelector() {
  const [models, setModels] = useState([]);
  const [current, setCurrent] = useState('');
  const [activeTab, setActiveTab] = useState('Hindi');
  const [switching, setSwitching] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getModels()
      .then((data) => {
        setModels(data.models || []);
        setCurrent(data.current || '');
      })
      .catch(() => {});
  }, []);

  async function handleSelect(modelId) {
    if (modelId === current) return;
    setSwitching(modelId);
    setError('');
    try {
      await setVoiceModel(modelId);
      setCurrent(modelId);
    } catch (err) {
      setError(err.message);
    } finally {
      setSwitching(null);
    }
  }

  const filtered = models.filter((m) => m.category === activeTab);

  return (
    <section className="model-selector">
      <h2>TTS Voice Model</h2>
      <p className="model-subtitle">
        Select a text-to-speech model. It will be downloaded automatically on first build.
      </p>

      <div className="model-tabs">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            className={`model-tab ${activeTab === cat ? 'active' : ''}`}
            onClick={() => setActiveTab(cat)}
          >
            {cat}
          </button>
        ))}
      </div>

      <div className="model-grid">
        {filtered.map((m) => {
          const isActive = m.id === current;
          const isLoading = m.id === switching;
          return (
            <div
              key={m.id}
              className={`model-card ${isActive ? 'selected' : ''}`}
              onClick={() => !isLoading && handleSelect(m.id)}
            >
              <div className="model-card-header">
                <span className="model-name">{m.name}</span>
                {isActive && <span className="model-badge active-badge">Active</span>}
                {m.gated && !isActive && (
                  <span className="model-badge gated-badge">HF Login</span>
                )}
              </div>
              <p className="model-desc">{m.description}</p>
              <div className="model-meta">
                <span className="model-size">{m.size}</span>
                {isLoading && <span className="spinner" />}
              </div>
            </div>
          );
        })}
      </div>

      {error && <p className="error">{error}</p>}
    </section>
  );
}
