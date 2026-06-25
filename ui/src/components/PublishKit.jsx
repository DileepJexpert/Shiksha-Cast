import { useState } from 'react';
import { generatePackage, packageZipUrl, thumbnailUrl } from '../api.js';

const STYLES = ['curiosity', 'exam', 'kids', 'hinglish'];

export default function PublishKit({ chapter, hasVideo }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [kit, setKit] = useState(null);
  const [copied, setCopied] = useState('');

  async function handleGenerate() {
    setBusy(true);
    setError(null);
    try {
      setKit(await generatePackage(chapter, { includeShort: hasVideo }));
    } catch (e) {
      setError(e.message || 'Packaging failed.');
    } finally {
      setBusy(false);
    }
  }

  function copy(label, text) {
    navigator.clipboard?.writeText(text);
    setCopied(label);
    setTimeout(() => setCopied(''), 1500);
  }

  return (
    <section className="publish-kit card">
      <div className="pk-header">
        <h3>📦 Publish Kit</h3>
        <button className="btn-primary" onClick={handleGenerate} disabled={busy}>
          {busy ? 'Generating… (thumbnail + metadata + Short)' : kit ? 'Regenerate' : 'Generate Publish Kit'}
        </button>
      </div>
      <p className="pk-hint">
        Creates thumbnails (4 styles), title/description/tags, a pinned comment, and a vertical Short —
        then bundles everything into one downloadable folder.
        {!hasVideo && ' (Build the video first to include the Short.)'}
      </p>

      {error && <div className="topic-error">⚠️ {error}</div>}

      {kit && (
        <div className="pk-body">
          <div className="pk-thumbs">
            {STYLES.map((s) => (
              <figure key={s} className="pk-thumb">
                <img src={thumbnailUrl(chapter, s)} alt={`${s} thumbnail`} loading="lazy" />
                <figcaption>{s}</figcaption>
              </figure>
            ))}
          </div>

          {kit.chapter_warnings?.length > 0 && (
            <div className="pk-warn">
              ⚠️ Chapter warnings:
              <ul>{kit.chapter_warnings.map((w, i) => <li key={i}>{w}</li>)}</ul>
            </div>
          )}

          <PkField label="Title" value={kit.title} copied={copied} onCopy={copy} />
          {kit.title_variants && Object.entries(kit.title_variants).map(([k, v]) => (
            <PkField key={k} label={`Title (${k})`} value={v} copied={copied} onCopy={copy} />
          ))}
          <PkField label="Tags" value={(kit.tags || []).join(', ')} copied={copied} onCopy={copy} />
          <PkField label="Description" value={kit.description} copied={copied} onCopy={copy} multiline />
          <PkField label="Pinned comment" value={kit.pinned_comment} copied={copied} onCopy={copy} multiline />

          <div className="pk-download">
            <a className="btn-primary" href={packageZipUrl(chapter)} download>
              ⬇ Download full package (.zip)
            </a>
          </div>
        </div>
      )}
    </section>
  );
}

function PkField({ label, value, multiline, copied, onCopy }) {
  return (
    <div className="pk-field">
      <div className="pk-field-head">
        <span>{label}</span>
        <button className="pk-copy" onClick={() => onCopy(label, value)}>
          {copied === label ? '✓ Copied' : 'Copy'}
        </button>
      </div>
      {multiline
        ? <pre className="pk-value pk-multiline">{value}</pre>
        : <div className="pk-value">{value}</div>}
    </div>
  );
}
