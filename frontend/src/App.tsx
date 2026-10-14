import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { api } from './api/client';
import {
  ActiveTab,
  PersonCluster,
  PhotoInfo,
  UnrecognizedData,
  SuggestionsData,
  JobStatus,
} from './types';
import { Header, RisoTheme } from './components/Header';
import { HomeScreen } from './components/HomeScreen';
import { ProgressScreen } from './components/ProgressScreen';
import { ReviewPeopleScreen } from './components/ReviewPeopleScreen';
import { ExportScreen } from './components/ExportScreen';
import { SettingsScreen } from './components/SettingsScreen';
import { Lock } from 'lucide-react';

export const App: React.FC = () => {
  const [theme, setTheme] = useState<RisoTheme>(() => {
    try {
      const saved = localStorage.getItem('photosorter-theme');
      if (saved === 't-paper' || saved === 't-navy' || saved === 't-dark') {
        return saved;
      }
    } catch (e) {}
    return 't-dark';
  });

  const handleThemeChange = (newTheme: RisoTheme, e?: React.MouseEvent) => {
    if (newTheme === theme) return;

    const x = e ? e.clientX : window.innerWidth - 80;
    const y = e ? e.clientY : 32;

    document.documentElement.style.setProperty('--click-x', `${x}px`);
    document.documentElement.style.setProperty('--click-y', `${y}px`);

    const update = () => {
      setTheme(newTheme);
      try {
        localStorage.setItem('photosorter-theme', newTheme);
      } catch (err) {}
    };

    if ('startViewTransition' in document) {
      (document as any).startViewTransition(update);
    } else {
      update();
    }
  };

  const [activeTab, setActiveTab] = useState<ActiveTab>(() => {
    try {
      const saved = localStorage.getItem('photosorter-active-tab');
      if (saved && ['home', 'progress', 'people', 'export', 'settings'].includes(saved)) {
        return saved as ActiveTab;
      }
    } catch (e) {}
    return 'home';
  });

  const handleTabChange = (t: ActiveTab) => {
    setActiveTab(t);
    try {
      localStorage.setItem('photosorter-active-tab', t);
    } catch (e) {}
  };
  const [people, setPeople] = useState<PersonCluster[]>([]);
  const [photos, setPhotos] = useState<Record<string, PhotoInfo>>({});
  const [unrecognized, setUnrecognized] = useState<UnrecognizedData>({
    total_unrecognized_photos: 0,
    no_face_photos: [],
    faces: [],
  });
  const [suggestions, setSuggestions] = useState<SuggestionsData>({
    maybe_groups_count: 0,
    maybe_groups: [],
    possibly_the_same_count: 0,
    possibly_the_same: [],
    ambiguous_faces_count: 0,
    ambiguous_faces: [],
  });

  const [jobStatus, setJobStatus] = useState<JobStatus>({
    status: 'idle',
    stage: 'idle',
    current: 0,
    total: 0,
    percent: 0,
    message: 'Ready to sort photos',
  });
  const [progressHistory, setProgressHistory] = useState<JobStatus[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [rejectedPairs, setRejectedPairs] = useState<Set<string>>(new Set());
  const [appliedEditsCount, setAppliedEditsCount] = useState<number>(0);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [isInitialLoading, setIsInitialLoading] = useState<boolean>(true);
  const [isMerging, setIsMerging] = useState<boolean>(false);
  const [isCancelling, setIsCancelling] = useState<boolean>(false);

  // Load all data from API
  const loadAllData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const [peopleData, unrecData, sugData, photoData] = await Promise.all([
        api.getPeople().catch(() => []),
        api.getUnrecognized().catch(() => ({ total_unrecognized_photos: 0, no_face_photos: [], faces: [] })),
        api.getSuggestions().catch(() => ({
          maybe_groups_count: 0,
          maybe_groups: [],
          possibly_the_same_count: 0,
          possibly_the_same: [],
          ambiguous_faces_count: 0,
          ambiguous_faces: [],
        })),
        api.getPhotos().catch(() => ({})),
      ]);

      setPeople(peopleData);
      setUnrecognized(unrecData);
      setSuggestions(sugData);
      setPhotos(photoData);
    } catch (err) {
      console.error('Failed to load dataset from API:', err);
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  // Initial load
  useEffect(() => {
    Promise.all([
      loadAllData(),
      api.getJobStatus()
        .then((status) => {
          setJobStatus(status);
          if (status.status === 'running') {
            setActiveTab('progress');
          }
        })
        .catch(() => {}),
    ]).finally(() => {
      setIsInitialLoading(false);
    });
  }, [loadAllData]);

  // Subscribe to SSE updates if job starts or page mounts
  useEffect(() => {
    const unsubscribe = api.subscribeProgress((status) => {
      setJobStatus(status);
      setProgressHistory((prev) => {
        const last = prev[prev.length - 1];
        if (last && last.current === status.current && last.stage === status.stage && last.status === status.status && last.percent === status.percent) {
          return prev;
        }
        return [...prev.slice(-49), status];
      });
      if (status.status === 'completed') {
        loadAllData();
      }
    });
    return () => {
      unsubscribe();
    };
  }, [loadAllData]);

  // Robust live polling fallback to guarantee real-time updates even if SSE is buffered
  useEffect(() => {
    if (jobStatus.status === 'running' || isCancelling || activeTab === 'progress') {
      const timer = setInterval(async () => {
        try {
          const st = await api.getJobStatus();
          setJobStatus(st);
          setProgressHistory((prev) => {
            const last = prev[prev.length - 1];
            if (last && last.current === st.current && last.stage === st.stage && last.status === st.status && last.percent === st.percent) {
              return prev;
            }
            return [...prev.slice(-49), st];
          });
          if (st.status === 'completed') {
            loadAllData();
          }
        } catch (err) {
          // ignore transient poll error
        }
      }, 500);
      return () => clearInterval(timer);
    }
  }, [jobStatus.status, isCancelling, activeTab, loadAllData]);

  // Multi-select helpers
  const handleToggleSelect = (personId: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(personId)) {
        next.delete(personId);
      } else {
        next.add(personId);
      }
      return next;
    });
  };

  const handleSelectAll = () => {
    setSelectedIds(new Set(people.map((p) => p.id)));
  };

  const handleClearSelection = () => {
    setSelectedIds(new Set());
  };

  // Merge selected people
  const handleMergeSelected = async () => {
    if (selectedIds.size < 2) return;
    setIsMerging(true);
    try {
      const selectedPeople = people.filter((p) => selectedIds.has(p.id));
      const personIds = Array.from(selectedIds);
      const anchors = selectedPeople.map((p) => p.anchor_face_ids);

      const res = await api.applyEdit({
        op: 'merge',
        person_ids: personIds,
        anchors: anchors,
      });

      if (res.success) {
        setAppliedEditsCount((c) => c + 1);
        handleClearSelection();
        await loadAllData();
      }
    } catch (err: any) {
      alert(`Merge failed: ${err.message || err}`);
    } finally {
      setIsMerging(false);
    }
  };

  // Suggestion actions
  const handleAcceptSuggestion = async (personAId: string, personBId: string) => {
    try {
      const personA = people.find((p) => p.id === personAId);
      const personB = people.find((p) => p.id === personBId);
      const anchors = [
        personA ? personA.anchor_face_ids : [personAId],
        personB ? personB.anchor_face_ids : [personBId],
      ];

      const res = await api.applyEdit({
        op: 'merge',
        person_ids: [personAId, personBId],
        anchors: anchors,
      });

      if (res.success) {
        setAppliedEditsCount((c) => c + 1);
        await loadAllData();
      }
    } catch (err: any) {
      alert(`Suggestion accept failed: ${err.message || err}`);
    }
  };

  const handleRejectSuggestion = (personAId: string, personBId: string) => {
    const key = [personAId, personBId].sort().join(':::');
    setRejectedPairs((prev) => new Set([...prev, key]));
  };

  // Unrecognized triage assign
  const handleAssignFace = async (faceId: string, targetPersonId?: string | null) => {
    try {
      const res = await api.assignFace(faceId, targetPersonId);
      if (res.success) {
        setAppliedEditsCount((c) => c + 1);
        await loadAllData();
      }
    } catch (err: any) {
      alert(`Assign face failed: ${err.message || err}`);
    }
  };

  // Person edits
  const handleRenamePerson = async (personId: string, label: string) => {
    try {
      const res = await api.namePerson(personId, label);
      if (res.success) {
        setAppliedEditsCount((c) => c + 1);
        await loadAllData();
      }
    } catch (err: any) {
      alert(`Rename failed: ${err.message || err}`);
    }
  };

  const handleHidePerson = async (personId: string) => {
    try {
      const res = await api.hidePerson(personId);
      if (res.success) {
        setAppliedEditsCount((c) => c + 1);
        await loadAllData();
      }
    } catch (err: any) {
      alert(`Hide failed: ${err.message || err}`);
    }
  };

  const handleRemoveFace = async (personId: string, faceId: string) => {
    try {
      const res = await api.removeFace(personId, faceId);
      if (res.success) {
        setAppliedEditsCount((c) => c + 1);
        await loadAllData();
      }
    } catch (err: any) {
      alert(`Remove face failed: ${err.message || err}`);
    }
  };

  const handleRemovePhoto = async (personId: string, photoId: string) => {
    try {
      const res = await api.removePhoto(personId, photoId);
      if (res.success) {
        setAppliedEditsCount((c) => c + 1);
        await loadAllData();
      }
    } catch (err: any) {
      alert(`Remove photo failed: ${err.message || err}`);
    }
  };

  // Undo action
  const handleUndo = async () => {
    try {
      const res = await api.undo();
      if (res.success) {
        setAppliedEditsCount((c) => Math.max(0, c - 1));
        await loadAllData();
      } else {
        alert(res.message || 'No edits to undo');
      }
    } catch (err: any) {
      alert(`Undo failed: ${err.message || err}`);
    }
  };

  // Start job
  const handleStartJob = async (inputPath?: string, driveFolder?: string, driveApiKey?: string) => {
    try {
      const st = await api.startJob(inputPath, driveFolder, driveApiKey);
      setJobStatus(st);
      setProgressHistory([st]);
      setActiveTab('progress');
    } catch (err: any) {
      alert(`Failed to start sorting job: ${err.message || err}`);
    }
  };

  // Cancel job
  const handleCancelJob = async () => {
    setIsCancelling(true);
    try {
      const st = await api.cancelJob();
      setJobStatus(st);
    } catch (err: any) {
      alert(`Cancel failed: ${err.message || err}`);
    } finally {
      setIsCancelling(false);
    }
  };

  // Invariant calculation
  const clusteredFacesCount = useMemo(() => {
    return people.reduce((acc, p) => acc + (p.faces ? p.faces.length : 0), 0);
  }, [people]);

  const unrecFacesCount = unrecognized.faces ? unrecognized.faces.length : 0;
  const unrecPhotosCount = unrecognized.total_unrecognized_photos || 0;
  const totalFacesCount = clusteredFacesCount + unrecFacesCount;

  const handleOpenProject = async () => {
    if (window.pywebview?.api?.select_folder) {
      try {
        const selected = await window.pywebview.api.select_folder('Open Photo Folder or Project');
        if (selected) {
          handleStartJob(selected);
        }
      } catch (err) {
        console.error('Failed to open project folder:', err);
      }
    } else {
      setActiveTab('home');
    }
  };

  if (isInitialLoading) {
    return (
      <div className={`app ${theme}`} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ width: '28px', height: '28px', border: '2px solid var(--line)', borderTopColor: 'var(--accent)', borderRadius: '50%', margin: '0 auto', animation: 'dot-spin 0.8s linear infinite' }}></div>
          <p style={{ marginTop: '14px', fontFamily: "'Archivo Black', sans-serif", fontSize: '16px', letterSpacing: '0.05em' }}>ORGANIZER</p>
          <p style={{ color: 'var(--muted)', fontSize: '12px' }}>Connecting to local engine...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`app ${theme}`}>
      <Header
        activeTab={activeTab}
        onTabChange={(t) => handleTabChange(t)}
        peopleCount={people.length}
        unrecFacesCount={unrecFacesCount}
        unrecPhotosCount={unrecPhotosCount}
        clusteredFacesCount={clusteredFacesCount}
        totalFacesCount={totalFacesCount}
        appliedEditsCount={appliedEditsCount}
        onUndo={handleUndo}
        onRefresh={loadAllData}
        isRefreshing={isRefreshing}
        theme={theme}
        onThemeChange={handleThemeChange}
        onOpenProject={handleOpenProject}
      />

      {/* Left Vertical Step Rail matching screenshot */}
      <div className="rail" aria-label="Workflow Steps">
        <div className="rail-steps">
          <button
            type="button"
            onClick={() => handleTabChange('home')}
            className={`step ${activeTab === 'home' ? 'on' : ''}`}
          >
            <b>01</b>
            <span>Source</span>
          </button>
          <button
            type="button"
            onClick={() => handleTabChange('progress')}
            className={`step ${activeTab === 'progress' ? 'on' : ''}`}
          >
            <b>02</b>
            <span>Scan</span>
          </button>
          <button
            type="button"
            onClick={() => handleTabChange('people')}
            className={`step ${activeTab === 'people' ? 'on' : ''}`}
          >
            <b>03</b>
            <span>Review</span>
          </button>
          <button
            type="button"
            onClick={() => handleTabChange('export')}
            className={`step ${activeTab === 'export' ? 'on' : ''}`}
          >
            <b>04</b>
            <span>Publish</span>
          </button>
          <button
            type="button"
            onClick={() => handleTabChange('settings')}
            className={`step ${activeTab === 'settings' ? 'on' : ''}`}
          >
            <b>05</b>
            <span>Settings</span>
          </button>
        </div>

        <div className="rail-footer">
          <div style={{ fontWeight: 700, color: 'var(--text)', letterSpacing: '0.04em' }}>ORGANIZER</div>
          <div>On-Device Engine</div>
          <div style={{ color: 'var(--accent-ink)', marginTop: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ display: 'inline-block', width: '6px', height: '6px', borderRadius: '50%', background: 'var(--accent)' }}></span>
            <span>Local Mode</span>
          </div>
        </div>
      </div>

      {/* Main Screen Content */}
      <div className="main">
        {activeTab === 'home' && (
          <HomeScreen
            onStartJob={handleStartJob}
            isLoading={jobStatus.status === 'running'}
            onNavigateTab={(t: any) => handleTabChange(t)}
            theme={theme}
          />
        )}

        {activeTab === 'progress' && (
          <ProgressScreen
            status={jobStatus}
            progressHistory={progressHistory}
            onCancelJob={handleCancelJob}
            onGoToReview={() => setActiveTab('people')}
            isCancelling={isCancelling}
          />
        )}

        {activeTab === 'people' && (
          <ReviewPeopleScreen
            people={people}
            photos={photos}
            unrecognized={unrecognized}
            suggestions={suggestions}
            selectedIds={selectedIds}
            onToggleSelect={handleToggleSelect}
            onSelectAll={handleSelectAll}
            onClearSelection={handleClearSelection}
            onMergeSelected={handleMergeSelected}
            onAcceptSuggestion={handleAcceptSuggestion}
            onRejectSuggestion={handleRejectSuggestion}
            rejectedPairs={rejectedPairs}
            onAssignFace={handleAssignFace}
            onRenamePerson={handleRenamePerson}
            onHidePerson={handleHidePerson}
            onRemoveFace={handleRemoveFace}
            onRemovePhoto={handleRemovePhoto}
            isMerging={isMerging}
          />
        )}

        {activeTab === 'export' && (
          <ExportScreen onRefreshStats={loadAllData} />
        )}

        {activeTab === 'settings' && (
          <SettingsScreen onRerunComplete={loadAllData} />
        )}
      </div>

      {/* Reassurance Footer matching screenshot */}
      <div className="ftr">
        <Lock className="w-3.5 h-3.5 text-[var(--accent)] flex-shrink-0" />
        <span>Projects and credentials stay on this computer. Nothing is uploaded or shared.</span>
      </div>
    </div>
  );
};
