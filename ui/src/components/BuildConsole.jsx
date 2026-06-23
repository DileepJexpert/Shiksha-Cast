import { useState, useRef, useEffect, useCallback } from 'react';
import { saveScript, triggerBuild, getStatus, downloadUrl, srtUrl, logStreamUrl } from '../api.js';

export default function BuildConsole({ chapter, scriptData }) {
  const [status, setStatus] = useState('idle');
  const [logs, setLogs] = useState([]);
  const [videoUrl, setVideoUrl] = useState(null);
  const [buildInfo, setBuildInfo] = useState(null);
  const [aiMode, setAiMode] = useState(false);
  const [forceRebuild, setForceRebuild] = useState(false);
  const [stage, setStage] = useState('');
  const logEndRef = useRef(null);
  const eventSourceRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [logs, scrollToBottom]);

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  function addLog(msg, type = 'info') {
    setLogs((prev) => [...prev, { text: msg, type, time: new Date().toLocaleTimeString() }]);
  }

  function connectLogStream() {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const es = new EventSource(logStreamUrl(chapter));
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      const msg = event.data;

      if (msg === '[END]') {
        es.close();
        eventSourceRef.current = null;
        checkFinalStatus();
        return;
      }

      if (msg.startsWith('[STAGE]')) {
        const stageName = msg.replace('[STAGE]', '').trim();
        setStage(stageName);
        addLog(stageName, 'stage');
      } else if (msg.startsWith('[ERROR]')) {
        addLog(msg.replace('[ERROR]', '').trim(), 'error');
      } else if (msg.startsWith('[DONE]')) {
        addLog(msg.replace('[DONE]', '').trim(), 'success');
      } else if (msg.startsWith('[PROGRESS]')) {
        addLog(msg.replace('[PROGRESS]', '').trim(), 'progress');
      } else if (msg.startsWith('[BUILD]')) {
        addLog(msg.replace('[BUILD]', '').trim(), 'stage');
      } else if (msg.startsWith('[CONNECTED]')) {
        addLog('Connected to build log stream', 'info');
      } else if (!msg.startsWith(':')) {
        addLog(msg, 'info');
      }
    };

    es.onerror = () => {
      es.close();
      eventSourceRef.current = null;
      checkFinalStatus();
    };
  }

  async function checkFinalStatus() {
    try {
      const st = await getStatus(chapter);
      if (st.status === 'done') {
        setStatus('done');
        setStage('Complete');
        setVideoUrl(st.video_url || downloadUrl(chapter));
        setBuildInfo({ duration: st.duration, slides: st.slides });
      } else if (st.status === 'error') {
        setStatus('error');
        setStage('Failed');
        if (st.error) addLog(st.error, 'error');
      }
    } catch (err) {
      addLog(`Status check failed: ${err.message}`, 'error');
    }
  }

  async function handleBuild() {
    setLogs([]);
    setVideoUrl(null);
    setBuildInfo(null);
    setStage('');

    try {
      setStatus('saving');
      addLog('Saving narration script...', 'info');
      await saveScript(chapter, scriptData);
      addLog('Script saved', 'success');

      setStatus('building');
      addLog(`Starting ${aiMode ? 'AI' : 'standard'} build${forceRebuild ? ' (force rebuild)' : ''}...`, 'stage');

      await triggerBuild(chapter, { aiMode, force: forceRebuild });

      connectLogStream();
    } catch (err) {
      setStatus('error');
      addLog(`Error: ${err.message}`, 'error');
    }
  }

  const busy = status === 'saving' || status === 'building';
  const hasVisualPrompts = scriptData?.some((s) => s.visual_prompt);

  return (
    <section className="build-console">
      <h2>Build Video</h2>

      <div className="build-options">
        <label className="build-option">
          <input
            type="checkbox"
            checked={aiMode}
            onChange={(e) => setAiMode(e.target.checked)}
            disabled={busy}
          />
          <span>AI Visual Mode</span>
        </label>
        {aiMode && !hasVisualPrompts && (
          <span className="option-warning">Add visual prompts to slides for AI image generation</span>
        )}

        <label className="build-option">
          <input
            type="checkbox"
            checked={forceRebuild}
            onChange={(e) => setForceRebuild(e.target.checked)}
            disabled={busy}
          />
          <span>Force Rebuild (ignore cache)</span>
        </label>
      </div>

      <div className="build-actions">
        <button className="btn-build" onClick={handleBuild} disabled={busy || !chapter}>
          {busy ? 'Building...' : aiMode ? 'AI Build' : 'Build Video'}
        </button>

        {stage && (
          <div className="build-stage">
            {(status === 'building' || status === 'saving') && <span className="spinner" />}
            <span className="stage-label">{stage}</span>
          </div>
        )}
      </div>

      {logs.length > 0 && (
        <div className="log-container">
          <div className="log-header">
            <span>Build Log</span>
            <button className="btn-clear-log" onClick={() => setLogs([])}>Clear</button>
          </div>
          <div className="log-output">
            {logs.map((log, i) => (
              <div key={i} className={`log-line log-${log.type}`}>
                <span className="log-time">{log.time}</span>
                <span className="log-text">{log.text}</span>
              </div>
            ))}
            <div ref={logEndRef} />
          </div>
        </div>
      )}

      {status === 'done' && videoUrl && (
        <div className="build-result">
          <div className="result-banner">
            Build complete!
            {buildInfo && (
              <span className="result-info">
                {buildInfo.slides} slides, {buildInfo.duration?.toFixed(1)}s video
              </span>
            )}
          </div>
          <div className="result-actions">
            <a href={videoUrl} download className="btn-download">Download MP4</a>
            <a href={srtUrl(chapter)} download className="btn-download btn-download-srt">Download SRT</a>
          </div>
        </div>
      )}

      {status === 'error' && (
        <div className="build-error-banner">
          Build failed. Check the log above for details.
        </div>
      )}
    </section>
  );
}
