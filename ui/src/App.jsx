import { useState, useRef } from 'react';
import Header from './components/Header.jsx';
import UploadSection from './components/UploadSection.jsx';
import SlideEditor from './components/SlideEditor.jsx';
import ModelSelector from './components/ModelSelector.jsx';
import BuildSection from './components/BuildSection.jsx';

export default function App() {
  const [chapter, setChapter] = useState(null);
  const [slides, setSlides] = useState([]);
  const [loading, setLoading] = useState(false);
  const scriptRef = useRef([]);

  function handleUploadComplete(result) {
    setChapter(result.chapter);
    setSlides(result.slides || []);
    scriptRef.current = (result.slides || []).map((s) => ({
      n: s.n,
      narration: '',
    }));
  }

  function handleScriptChange(slideData) {
    scriptRef.current = slideData;
  }

  function handleReset() {
    setChapter(null);
    setSlides([]);
    scriptRef.current = [];
  }

  return (
    <div className="app">
      <Header />

      <main className="main">
        {!chapter ? (
          <UploadSection
            onUploadComplete={handleUploadComplete}
            loading={loading}
            setLoading={setLoading}
          />
        ) : (
          <>
            <div className="chapter-bar">
              <span className="chapter-label">
                Chapter: <strong>{chapter}</strong> &mdash; {slides.length} slide
                {slides.length !== 1 ? 's' : ''}
              </span>
              <button className="reset-btn" onClick={handleReset}>
                Start Over
              </button>
            </div>

            <SlideEditor
              chapter={chapter}
              slides={slides}
              onScriptChange={handleScriptChange}
            />

            <ModelSelector />

            <BuildSection chapter={chapter} scriptData={scriptRef.current} />
          </>
        )}
      </main>
    </div>
  );
}
