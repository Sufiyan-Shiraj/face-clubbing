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
import { Header } from './components/Header';
import { HomeScreen } from './components/HomeScreen';
import { ProgressScreen } from './components/ProgressScreen';
import { ReviewPeopleScreen } from './components/ReviewPeopleScreen';
import { ExportScreen } from './components/ExportScreen';
import { SettingsScreen } from './components/SettingsScreen';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('people');
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
    loadAllData();
    api.getJobStatus()
      .then((status) => {
        setJobStatus(status);
        if (status.status === 'running') {
          setActiveTab('progress');
        }
      })
      .catch(() => {});
  }, [loadAllData]);

  // Subscribe to SSE updates if job starts or page mounts
  useEffect(() => {
    const unsubscribe = api.subscribeProgress((status) => {
      setJobStatus(status);
      setProgressHistory((prev) => [...prev.slice(-49), status]);
      if (status.status === 'completed') {
        loadAllData();
      }
    });
    return () => {
      unsubscribe();
    };
  }, [loadAllData]);

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
  const handleStartJob = async (inputPath: string) => {
    try {
      const st = await api.startJob(inputPath);
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

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 flex flex-col font-sans">
      <Header
        activeTab={activeTab}
        onTabChange={(t) => setActiveTab(t)}
        peopleCount={people.length}
        unrecFacesCount={unrecFacesCount}
        unrecPhotosCount={unrecPhotosCount}
        clusteredFacesCount={clusteredFacesCount}
        totalFacesCount={totalFacesCount}
        appliedEditsCount={appliedEditsCount}
        onUndo={handleUndo}
        onRefresh={loadAllData}
        isRefreshing={isRefreshing}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {activeTab === 'home' && (
          <HomeScreen
            onStartJob={handleStartJob}
            isLoading={jobStatus.status === 'running'}
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
      </main>
    </div>
  );
};
