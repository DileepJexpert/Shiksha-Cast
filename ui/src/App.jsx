import { useState, useCallback } from 'react';
import Header from './components/Header.jsx';
import ChapterList from './components/ChapterList.jsx';
import UploadSection from './components/UploadSection.jsx';
import SlideEditor from './components/SlideEditor.jsx';
import ModelSelector from './components/ModelSelector.jsx';
import BuildConsole from './components/BuildConsole.jsx';
import Stepper from './components/Stepper.jsx';
import TopicForm from './components/TopicForm.jsx';
import PublishKit from './components/PublishKit.jsx';
import { getScript, slideImageUrl } from './api.js';

export default function App() {
  const [view, setView] = useState('dashboard');
  const [chapter, setChapter] = useState(null);
  const [slides, setSlides] = useState([]);
  const [loading, setLoading] = useState(false);
  const [existingScript, setExistingScript] = useState(null);
  const [scriptData, setScriptData] = useState([]);
  const [flow, setFlow] = useState('existing'); // 'new' shows the New Chapter wizard steps
  const [chapterHasVideo, setChapterHasVideo] = useState(false);

  const handleUploadComplete = useCallback((result) => {
    setChapter(result.chapter);
    setSlides(result.slides || []);
    setExistingScript(null);
    setScriptData((result.slides || []).map((s) => ({
      n: s.n,
      narration: '',
    })));
    setView('editor');
  }, []);

  const handleScriptChange = useCallback((slideData) => {
    setScriptData(slideData);
  }, []);

  async function handleSelectChapter(ch) {
    setFlow('existing');
    setChapter(ch.id);
    setChapterHasVideo(!!ch.has_video);

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
      setScriptData((scriptData.slides || []).map((s) => ({
        n: s.n,
        narration: s.narration || '',
        voice_description: s.voice_description || undefined,
        voice: s.voice || undefined,
        visual_prompt: s.visual_prompt || undefined,
      })));
    } catch {
      setExistingScript(null);
      setScriptData(slideList.map((s) => ({ n: s.n, narration: '' })));
    }

    setView('editor');
  }

  function handleBack() {
    setView('dashboard');
    setChapter(null);
    setSlides([]);
    setExistingScript(null);
    setScriptData([]);
    setFlow('existing');
  }

  function handleNew() {
    setFlow('new');
    setView('upload');
  }

  function handleNewTopic() {
    setView('topic');
  }

  function handleTopicCreated(res) {
    // res = { chapter, title, slide_count, missing_visual_prompts }
    handleSelectChapter({ id: res.chapter, slide_count: res.slide_count, has_video: false });
  }

  return (
    <div className="app">
      <Header />

      <main className="main">
        {view === 'dashboard' && (
          <ChapterList
            onSelect={handleSelectChapter}
            onNew={handleNew}
            onNewTopic={handleNewTopic}
          />
        )}

        {view === 'topic' && (
          <>
            <div className="nav-bar">
              <button className="btn-back" onClick={handleBack}>Back to Dashboard</button>
            </div>
            <TopicForm onCreated={handleTopicCreated} onCancel={handleBack} />
          </>
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

            <BuildConsole
              chapter={chapter}
              scriptData={scriptData}
              title={existingScript?.chapter}
            />

            <ModelSelector />

            <SlideEditor
              chapter={chapter}
              slides={slides}
              existingScript={existingScript}
              scriptData={scriptData}
              onScriptChange={handleScriptChange}
            />

            <PublishKit chapter={chapter} hasVideo={chapterHasVideo} />
          </>
        )}
      </main>
    </div>
  );
}
