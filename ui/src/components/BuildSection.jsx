import { useState, useRef, useCallback } from 'react';
import { saveScript, triggerBuild, getStatus, downloadUrl } from '../api.js';

export default function BuildSection({ chapter, scriptData }) {
  const [status, setStatus] = useState('idle'); // idle | saving | building | polling | done | error
  const [message, setMessage] = useState('');
  const [videoUrl, setVideoUrl] = useState(null);
  const pollingRef = useRef(null);

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  async function handleBuild() {
    stopPolling();
    setVideoUrl(null);

    try {
      // 1. Save script
      setStatus('saving');
      setMessage('Saving narration script...');
      await saveScript(chapter, scriptData);

      // 2. Trigger build
      setStatus('building');
      setMessage('Triggering build pipeline...');
      const buildRes = await triggerBuild(chapter);

      if (buildRes.video_url) {
        setStatus('done');
        setMessage('Build complete!');
        setVideoUrl(buildRes.video_url);
        return;
      }

      // 3. Poll for status
      setStatus('polling');
      setMessage('Building video... this may take a few minutes.');

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
            setMessage(`Building... (${statusRes.status || 'in progress'})`);
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

      <button className="build-btn" onClick={handleBuild} disabled={busy || !chapter}>
        {busy ? 'Building...' : 'Build Video'}
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
