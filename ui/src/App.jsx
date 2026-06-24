import { useState, useRef, useCallback } from 'react';
import Header from './components/Header.jsx';
import ChapterList from './components/ChapterList.jsx';
import UploadSection from './components/UploadSection.jsx';
import SlideEditor from './components/SlideEditor.jsx';
import ModelSelector from './components/ModelSelector.jsx';
import BuildConsole from './components/BuildConsole.jsx';
import Stepper from './components/Stepper.jsx';
import { getScript, slideImageUrl } from './api.js';

export default function App() {
  const [view, setView] = useState('dashboard');
  const [chapter, setChapter] = useState(null);
  const [slides, setSlides] = useState([]);
  const [loading, setLoading] = useState(false);
  const [existingScript, setExistingScript] = useState(null);
  const [flow, setFlow] = useState('existing'); // 'new' shows the New Chapter wizard steps
  const scriptRef = useRef([]);

  const handleUploadComplete = useCallback((result) => {
    setChapter(result.chapter);
    setSlides(result.slides || []);
    setExistingScript(null);
    scriptRef.current = (result.slides || []).map((s) => ({
      n: s.n,
      narration: '',
    }));
    setView('editor');
  }, []);

  const handleScriptChange = useCallback((slideData) => {
    scriptRef.current = slideData;
  }, []);

  async function handleSelectChapter(ch) {
    setFlow('existing');
    setChapter(ch.id);

    const slideList = [];
    for (let i = 1; i <= ch.slide_count; i++) {
      slideList.push({
        n: i,
        image_url: slideImageUrl(ch.id, `slide_${String(i).padStart(3, '0')}.png`),
      });
    }
    setSlides(slideList);

    try {
      const scriptData = await getScript(ch.id);
      setExistingScript(scriptData);
      scriptRef.current = (scriptData.slides || []).map((s) => ({
        n: s.n,
        narration: s.narration || '',
        voice_description: s.voice_description || undefined,
        visual_prompt: s.visual_prompt || undefined,
      }));
    } catch {
      setExistingScript(null);
      scriptRef.current = slideList.map((s) => ({ n: s.n, narration: '' }));
    }

    setView('editor');
  }

  function handleBack() {
    setView('dashboard');
    setChapter(null);
    setSlides([]);
    setExistingScript(null);
    setFlow('existing');
    scriptRef.current = [];
  }

  function handleNew() {
    setFlow('new');
    setView('upload');
  }

  return (
    <div className="app">
      <Header />

      <main className="main">
        {view === 'dashboard' && (
          <ChapterList
            onSelect={handleSelectChapter}
            onNew={handleNew}
          />
        )}

        {view === 'upload' && (
          <>
            <div className="nav-bar">
              <button className="btn-back" onClick={handleBack}>Back to Dashboard</button>
            </div>
            {flow === 'new' && <Stepper current={1} />}
            <UploadSection
              onUploadComplete={handleUploadComplete}
              loading={loading}
              setLoading={setLoading}
            />
          </>
        )}

        {view === 'editor' && chapter && (
          <>
            <div className="nav-bar">
              <button className="btn-back" onClick={handleBack}>Back to Dashboard</button>
              <span className="nav-chapter">
                Chapter: <strong>{chapter}</strong> — {slides.length} slide{slides.length !== 1 ? 's' : ''}
              </span>
            </div>

            {flow === 'new' && <Stepper current={2} />}

            <BuildConsole chapter={chapter} scriptData={scriptRef.current} />

            <ModelSelector />

            <SlideEditor
              chapter={chapter}
              slides={slides}
              existingScript={existingScript}
              onScriptChange={handleScriptChange}
            />
          </>
        )}
      </main>
    </div>
  );
}
