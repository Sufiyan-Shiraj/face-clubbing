import React, { useState, useEffect } from 'react';
import { ViewerConfig, PeopleData, PersonCluster } from './types';
import { Header, ViewerTheme } from './components/Header';
import { PeopleGrid } from './components/PeopleGrid';
import { Footer } from './components/Footer';
import { AlertCircle, RefreshCw } from 'lucide-react';

const PhotoGallery = React.lazy(() => import('./components/PhotoGallery').then(m => ({ default: m.PhotoGallery })));
const UnrecognizedGallery = React.lazy(() => import('./components/UnrecognizedGallery').then(m => ({ default: m.UnrecognizedGallery })));

export const App: React.FC = () => {
  const [theme, setTheme] = useState<ViewerTheme>('t-dark');

  const [config, setConfig] = useState<ViewerConfig>({
    title: 'CatLog Gallery',
    accent: '#fa7175',
    font: 'Inter',
    footer: 'Published with CatLog',
    show_labels: true,
  });

  const [data, setData] = useState<PeopleData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [activeView, setActiveView] = useState<'grid' | 'person' | 'unrecognized'>('grid');
  const [selectedPerson, setSelectedPerson] = useState<PersonCluster | null>(null);

  // Sync theme with DOM
  useEffect(() => {
    document.documentElement.classList.remove('t-dark', 't-paper', 't-navy');
    document.body.classList.remove('t-dark', 't-paper', 't-navy');
    document.documentElement.classList.add(theme);
    document.body.classList.add(theme);
  }, [theme]);

  const handleThemeChange = (newTheme: ViewerTheme) => {
    setTheme(newTheme);
  };

  // Fetch bundle files: config.json and people.json
  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 1. Fetch config.json (tolerant of missing)
      try {
        const configRes = await fetch('./config.json');
        if (configRes.ok) {
          const configJson = await configRes.json();
          setConfig((prev) => ({ ...prev, ...configJson }));

          if (configJson.theme && (configJson.theme === 't-dark' || configJson.theme === 't-paper' || configJson.theme === 't-navy')) {
            setTheme(configJson.theme);
          }

          if (configJson.accent) {
            document.documentElement.style.setProperty('--color-accent', configJson.accent);
          }
          if (configJson.font) {
            document.documentElement.style.setProperty(
              '--font-family',
              `'${configJson.font}', system-ui, sans-serif`
            );
          }
          if (configJson.title) {
            document.title = configJson.title;
          }
        }
      } catch (err) {
        console.warn('Could not load config.json, using defaults.', err);
      }

      // 2. Fetch people.json
      const peopleRes = await fetch('./people.json');
      if (!peopleRes.ok) {
        throw new Error(`Failed to load people.json (status ${peopleRes.status})`);
      }
      const peopleJson: PeopleData = await peopleRes.json();
      setData(peopleJson);
    } catch (err: any) {
      console.error('Error loading gallery bundle:', err);
      setError(err.message || 'Failed to load gallery data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Hash-based routing: #p001, #unrecognized
  useEffect(() => {
    if (!data) return;
    const handleHash = () => {
      const hash = window.location.hash.replace('#', '');
      if (hash === 'unrecognized') {
        setSelectedPerson(null);
        setActiveView('unrecognized');
      } else if (hash.startsWith('p')) {
        const found = data.people.find((p) => p.id === hash);
        if (found) {
          setSelectedPerson(found);
          setActiveView('person');
        } else {
          setActiveView('grid');
        }
      } else {
        setSelectedPerson(null);
        setActiveView('grid');
      }
    };

    handleHash();
    window.addEventListener('hashchange', handleHash);
    return () => window.removeEventListener('hashchange', handleHash);
  }, [data]);

  const handleSelectPerson = (person: PersonCluster) => {
    setSelectedPerson(person);
    setActiveView('person');
    window.location.hash = person.id;
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleSelectUnrecognized = () => {
    setSelectedPerson(null);
    setActiveView('unrecognized');
    window.location.hash = 'unrecognized';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleBackToGrid = () => {
    setSelectedPerson(null);
    setActiveView('grid');
    window.location.hash = '';
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const totalPhotos = data ? Object.keys(data.photos).length : 0;
  const totalPeople = data ? data.people.length : 0;

  return (
    <div className={`min-h-screen flex flex-col bg-[var(--bg-main)] text-[var(--text-main)] ${theme}`}>
      <Header
        config={config}
        totalPeople={totalPeople}
        totalPhotos={totalPhotos}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        activeView={activeView}
        onBackToGrid={handleBackToGrid}
        theme={theme}
        onThemeChange={handleThemeChange}
      />

      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5 w-full">
        {loading && (
          <div className="py-24 flex flex-col items-center justify-center space-y-3">
            <div className="w-8 h-8 border-3 border-[var(--color-accent)] border-t-transparent rounded-full animate-spin" />
            <p className="text-xs sm:text-sm text-[var(--text-muted)] font-medium">Loading gallery...</p>
          </div>
        )}

        {error && !loading && (
          <div className="max-w-md mx-auto my-16 p-6 rounded-2xl glass-card border-red-500/30 text-center space-y-4">
            <div className="w-12 h-12 mx-auto rounded-full bg-red-500/10 text-red-400 flex items-center justify-center">
              <AlertCircle className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-[var(--text)]">Gallery Data Missing</h3>
              <p className="text-xs text-[var(--text-muted)] mt-1">
                Could not find <code className="text-[var(--text-main)]">people.json</code>.
                Ensure export bundle files are located in the gallery folder.
              </p>
            </div>
            <button
              onClick={loadData}
              className="touch-target inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-[var(--color-accent)] text-[var(--color-accent-text)] text-xs font-bold transition-all shadow-sm"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry</span>
            </button>
          </div>
        )}

        {!loading && !error && data && (
          <>
            {activeView === 'grid' && (
              <PeopleGrid
                people={data.people}
                unrecognized={data.unrecognized}
                photos={data.photos}
                searchQuery={searchQuery}
                showLabels={config.show_labels !== false}
                hideSinglePhotoDefault={config.hide_single_photo_default}
                onSelectPerson={handleSelectPerson}
                onSelectUnrecognized={handleSelectUnrecognized}
                theme={theme}
              />
            )}

            <React.Suspense fallback={<div className="flex justify-center items-center py-20"><div className="w-7 h-7 rounded-full border-2 border-[var(--color-accent)] border-t-transparent animate-spin" /></div>}>
              {activeView === 'person' && selectedPerson && (
                <PhotoGallery
                  person={selectedPerson}
                  photos={data.photos}
                  includeMaybe={config.include_maybe === true}
                  onBack={handleBackToGrid}
                />
              )}

              {activeView === 'unrecognized' && (
                <UnrecognizedGallery
                  unrecognized={data.unrecognized}
                  photos={data.photos}
                  onBack={handleBackToGrid}
                />
              )}
            </React.Suspense>
          </>
        )}
      </main>

      <Footer config={config} generatedAt={data?.generated_at} theme={theme} />
    </div>
  );
};
export default App;
