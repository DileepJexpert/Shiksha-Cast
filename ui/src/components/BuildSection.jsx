import { useState, useRef, useCallback } from 'react';
import { saveScript, triggerBuild, getStatus, downloadUrl } from '../api.js';

export default function BuildSection({ chapter, scriptData }) {
  const [status, setStatus] = useState('idle');
  const [message, setMessage] = useState('');
  const [videoUrl, setVideoUrl] = useState(null);
  const [aiMode, setAiMode] = useState(false);
  const pollingRef = useRef(null);

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  const hasVisualPrompts = scriptData?.some((s) => s.visual_prompt);

  async function handleBuild() {
    stopPolling();
    setVideoUrl(null);

    try {
      setStatus('saving');
      setMessage('Saving narration script...');
      await saveScript(chapter, scriptData);

      setStatus('building');
      setMessage(
        aiMode
          ? 'Generating AI images + narration + video... this may take several minutes.'
          : 'Triggering build pipeline...'
      );
      const buildRes = await triggerBuild(chapter, { aiMode });

      if (buildRes.video_url) {
        setStatus('done');
        setMessage('Build complete!');
        setVideoUrl(buildRes.video_url);
        return;
      }

      setStatus('polling');
      setMessage(
        aiMode
          ? 'AI build in progress... generating images and assembling video.'
          : 'Building video... this may take a few minutes.'
      );

      pollingRef.current = setInterval(async () => {
        try {
          const statusRes = await getStatus(chapter);
          if (statusRes.status === 'done' || statusRes.status === 'complete') {
            stopPolling();
            setStatus('done');
            setMessage('Build complete!');
            setVideoUrl(statusRes.video_url || downloadUrl(chapter));
          } else if (statusRes.status === 'error' || statusRes.status === 'failed') {
            stopPolling();
            setStatus('error');
            setMessage(`Build failed: ${statusRes.error || 'Unknown error'}`);
          } else {
            setMessage(
              aiMode
                ? `AI build in progress... (${statusRes.status || 'generating'})`
                : `Building... (${statusRes.status || 'in progress'})`
            );
          }
        } catch (err) {
          stopPolling();
          setStatus('error');
          setMessage(`Polling error: ${err.message}`);
        }
      }, 3000);
    } catch (err) {
      setStatus('error');
      setMessage(`Error: ${err.message}`);
    }
  }

  const busy = status === 'saving' || status === 'building' || status === 'polling';

  return (
    <section className="build-section">
      <h2>Build Video</h2>

      <div className="build-mode-toggle">
        <label className="toggle-label">
          <input
            type="checkbox"
            checked={aiMode}
            onChange={(e) => setAiMode(e.target.checked)}
            disabled={busy}
          />
          <span className="toggle-text">
            AI Visual Mode
          </span>
        </label>
        <span className="toggle-hint">
          {aiMode
            ? 'Uses AI to generate contextual images from your visual prompts + Ken Burns animation'
            : 'Uses uploaded PDF/PNG slides as-is'}
        </span>
        {aiMode && !hasVisualPrompts && (
          <span className="toggle-warning">
            Add visual prompts to your slides above for AI image generation
          </span>
        )}
      </div>

      <button className="build-btn" onClick={handleBuild} disabled={busy || !chapter}>
        {busy ? 'Building...' : aiMode ? 'AI Build Video' : 'Build Video'}
      </button>

      {message && (
        <div className={`build-message ${status}`}>
          {busy && <span className="spinner" />}
          <span>{message}</span>
        </div>
      )}

      {status === 'done' && videoUrl && (
        <div className="download-area">
          <a href={videoUrl} download className="download-btn">
            Download MP4
          </a>
        </div>
      )}
    </section>
  );
}
