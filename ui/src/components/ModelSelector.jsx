import { useState, useEffect } from 'react';
import { getModels, setVoiceModel } from '../api.js';

export default function ModelSelector() {
  const [models, setModels] = useState([]);
  const [current, setCurrent] = useState('');
  const [switching, setSwitching] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    getModels()
      .then((data) => {
        setModels(data.models || []);
        setCurrent(data.current || '');
      })
      .catch(() => {});
  }, []);

  const categories = [...new Set(models.map((m) => m.category))];

  async function handleChange(modelId) {
    if (!modelId || modelId === current) return;
    setSwitching(true);
    setError('');
    try {
      await setVoiceModel(modelId);
      setCurrent(modelId);
    } catch (err) {
      setError(err.message);
    } finally {
      setSwitching(false);
    }
  }

  const sel = models.find((m) => m.id === current);

  return (
    <section className="model-selector-compact">
      <label htmlFor="voice-select">Voice</label>
      <select
        id="voice-select"
        value={current}
        onChange={(e) => handleChange(e.target.value)}
        disabled={switching}
      >
        {categories.map((cat) => (
          <optgroup key={cat} label={cat}>
            {models
              .filter((m) => m.category === cat)
              .map((m) => (
                <option key={m.id} value={m.id}>{m.name}</option>
              ))}
          </optgroup>
        ))}
      </select>
      {switching && <span className="spinner" />}
      {sel && <span className="voice-hint">{sel.size}</span>}
      {error && <span className="error">{error}</span>}
    </section>
  );
}
