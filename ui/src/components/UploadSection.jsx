import { useState, useRef } from 'react';
import { uploadPdf, uploadSlides } from '../api.js';

export default function UploadSection({ onUploadComplete, loading, setLoading }) {
  const [mode, setMode] = useState('pdf'); // 'pdf' | 'slides'
  const [chapter, setChapter] = useState('');
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  async function handleFiles(files) {
    if (!files || files.length === 0) return;
    setError(null);
    setLoading(true);

    const chapterName = chapter.trim() || undefined;

    try {
      let result;
      if (mode === 'pdf') {
        result = await uploadPdf(files[0], chapterName);
      } else {
        result = await uploadSlides(Array.from(files), chapterName);
      }
      onUploadComplete(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    setDragOver(false);
    handleFiles(e.dataTransfer.files);
  }

  function handleDragOver(e) {
    e.preventDefault();
    setDragOver(true);
  }

  function handleDragLeave() {
    setDragOver(false);
  }

  function handleInputChange(e) {
    handleFiles(e.target.files);
    e.target.value = '';
  }

  const accept = mode === 'pdf' ? '.pdf' : '.png,.jpg,.jpeg';
  const multiple = mode === 'slides';

  return (
    <section className="upload-section">
      <div className="upload-tabs">
        <button
          className={`tab-btn ${mode === 'pdf' ? 'active' : ''}`}
          onClick={() => setMode('pdf')}
          disabled={loading}
        >
          Upload PDF
        </button>
        <button
          className={`tab-btn ${mode === 'slides' ? 'active' : ''}`}
          onClick={() => setMode('slides')}
          disabled={loading}
        >
          Upload Slides (PNG)
        </button>
      </div>

      <div className="chapter-input">
        <label htmlFor="chapter-name">Chapter name</label>
        <input
          id="chapter-name"
          type="text"
          placeholder="e.g. ch01 (auto-generated if blank)"
          value={chapter}
          onChange={(e) => setChapter(e.target.value)}
          disabled={loading}
        />
      </div>

      <div
        className={`drop-zone ${dragOver ? 'drag-over' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          multiple={multiple}
          onChange={handleInputChange}
          style={{ display: 'none' }}
        />
        {loading ? (
          <p className="drop-text">Uploading...</p>
        ) : (
          <>
            <p className="drop-text">
              {mode === 'pdf'
                ? 'Drop a PDF here or click to browse'
                : 'Drop PNG slide images here or click to browse'}
            </p>
            <p className="drop-hint">
              {mode === 'pdf' ? 'Accepts .pdf files' : 'Accepts .png, .jpg files (select multiple)'}
            </p>
          </>
        )}
      </div>

      {error && <p className="error">{error}</p>}
    </section>
  );
}
