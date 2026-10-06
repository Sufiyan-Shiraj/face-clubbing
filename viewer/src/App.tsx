import React, { useState, useEffect } from 'react';
import { ViewerConfig, PeopleData, PersonCluster } from './types';
import { Header } from './components/Header';
import { PeopleGrid } from './components/PeopleGrid';
import { PhotoGallery } from './components/PhotoGallery';
import { UnrecognizedGallery } from './components/UnrecognizedGallery';
import { Footer } from './components/Footer';
import { AlertCircle, RefreshCw } from 'lucide-react';

export const App: React.FC = () => {
  const [config, setConfig] = useState<ViewerConfig>({
    title: 'Event Gallery',
    subtitle: 'Photos grouped by person',
    accent: '#3b82f6',
    font: 'Inter',
    footer: 'Published with PhotoSorter',
    show_labels: true,
  });

  const [data, setData] = useState<PeopleData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [activeView, setActiveView] = useState<'grid' | 'person' | 'unrecognized'>('grid');
  const [selectedPerson, setSelectedPerson] = useState<PersonCluster | null>(null);

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

          // Apply theme CSS variables
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
        console.warn('Could not load custom config.json, using defaults.', err);
      }

      // 2. Fetch people.json
      const peopleRes = await fetch('./people.json');
      if (!peopleRes.ok) {
        throw new Error(`Failed to load people.json (status ${peopleRes.status})`);
      }
      const peopleJson: PeopleData = await peopleRes.json();
      setData(peopleJson);

      // Initial hash navigation handled in separate effect
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

  // Listen to hash changes (e.g. #p001, #unrecognized, back/forward button)
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

  // Total unique photos count across people + unrecognized
  const totalPhotos = data ? Object.keys(data.photos).length : 0;
  const totalPeople = data ? data.people.length : 0;

  return (
    <div className="min-h-screen flex flex-col bg-neutral-950 text-neutral-100">
      <Header
        config={config}
        totalPeople={totalPeople}
        totalPhotos={totalPhotos}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        activeView={activeView}
        onBackToGrid={handleBackToGrid}
      />

      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 w-full">
        {loading && (
          <div className="py-24 flex flex-col items-center justify-center space-y-4">
            <div className="w-10 h-10 border-3 border-accent border-t-transparent rounded-full animate-spin" />
            <p className="text-sm text-neutral-400 font-medium">Loading event gallery...</p>
          </div>
        )}

        {error && !loading && (
          <div className="max-w-md mx-auto my-16 p-6 rounded-2xl glass-card border-red-500/30 text-center space-y-4">
            <div className="w-12 h-12 mx-auto rounded-full bg-red-500/10 text-red-400 flex items-center justify-center">
              <AlertCircle className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-white">Gallery Data Missing</h3>
              <p className="text-xs text-neutral-400 mt-1">
                Could not find <code className="text-neutral-200">people.json</code> in this folder.
                Please ensure the static export bundle files are located in the root or public directory.
              </p>
            </div>
            <button
              onClick={loadData}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-neutral-800 hover:bg-neutral-700 text-white text-xs font-medium transition-colors"
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
                searchQuery={searchQuery}
                showLabels={config.show_labels !== false}
                onSelectPerson={handleSelectPerson}
                onSelectUnrecognized={handleSelectUnrecognized}
              />
            )}

            {activeView === 'person' && selectedPerson && (
              <PhotoGallery
                person={selectedPerson}
                photos={data.photos}
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
          </>
        )}
      </main>

      <Footer config={config} generatedAt={data?.generated_at} />
    </div>
  );
};
export default App;
