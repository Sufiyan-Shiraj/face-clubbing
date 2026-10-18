import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { api } from './api/client';
import {
  ActiveTab,
  PersonCluster,
  PhotoInfo,
  UnrecognizedData,
  SuggestionsData,
  JobStatus,
  OpenProjectResponse,
} from './types';
import { Header, RisoTheme } from './components/Header';
import { HomeScreen } from './components/HomeScreen';
import { AlertTriangle, X } from 'lucide-react';

const ProgressScreen = React.lazy(() => import('./components/ProgressScreen').then(m => ({ default: m.ProgressScreen })));
const ReviewPeopleScreen = React.lazy(() => import('./components/ReviewPeopleScreen').then(m => ({ default: m.ReviewPeopleScreen })));
const ExportScreen = React.lazy(() => import('./components/ExportScreen').then(m => ({ default: m.ExportScreen })));
const SettingsScreen = React.lazy(() => import('./components/SettingsScreen').then(m => ({ default: m.SettingsScreen })));
const OpenProjectModal = React.lazy(() => import('./components/OpenProjectModal').then(m => ({ default: m.OpenProjectModal })));
const TutorialSpotlight = React.lazy(() => import('./components/TutorialSpotlight').then(m => ({ default: m.TutorialSpotlight })));

const DEMO_TUTORIAL_PEOPLE: PersonCluster[] = [
  {
    id: 'demo_p001',
    label: 'Maya Lin',
    face: '/faces/f_demo_001.jpg',
    photo_ids: ['photo_demo_001', 'photo_demo_002'],
    photos: ['photo_demo_001', 'photo_demo_002'],
    photo_count: 14,
    faces: [
      { face_id: 'f_demo_001', photo_id: 'photo_demo_001', det_score: 0.95, bbox: [100, 100, 300, 300] },
      { face_id: 'f_demo_002', photo_id: 'photo_demo_002', det_score: 0.92, bbox: [200, 200, 400, 400] },
    ],
    anchor_face_ids: ['f_demo_001'],
  },
  {
    id: 'demo_p002',
    label: 'David Kim',
    face: '/faces/f_demo_003.jpg',
    photo_ids: ['photo_demo_003'],
    photos: ['photo_demo_003'],
    photo_count: 8,
    faces: [
      { face_id: 'f_demo_003', photo_id: 'photo_demo_003', det_score: 0.89, bbox: [150, 150, 350, 350] },
    ],
    anchor_face_ids: ['f_demo_003'],
  },
  {
    id: 'demo_p003',
    label: 'Sarah Chen',
    face: '/faces/f_demo_004.jpg',
    photo_ids: ['photo_demo_004'],
    photos: ['photo_demo_004'],
    photo_count: 3,
    faces: [
      { face_id: 'f_demo_004', photo_id: 'photo_demo_004', det_score: 0.88, bbox: [180, 180, 380, 380] },
    ],
    anchor_face_ids: ['f_demo_004'],
  },
];

const DEMO_TUTORIAL_PHOTOS: Record<string, PhotoInfo> = {
  photo_demo_001: {
    photo_id: 'photo_demo_001',
    file_name: 'gala_001.jpg',
    width: 1920,
    height: 1080,
    faces: [{ face_id: 'f_demo_001', photo_id: 'photo_demo_001', bbox: [100, 100, 300, 300] }],
  },
  photo_demo_002: {
    photo_id: 'photo_demo_002',
    file_name: 'gala_002.jpg',
    width: 1920,
    height: 1080,
    faces: [{ face_id: 'f_demo_002', photo_id: 'photo_demo_002', bbox: [200, 200, 400, 400] }],
  },
  photo_demo_003: {
    photo_id: 'photo_demo_003',
    file_name: 'gala_003.jpg',
    width: 1920,
    height: 1080,
    faces: [{ face_id: 'f_demo_003', photo_id: 'photo_demo_003', bbox: [150, 150, 350, 350] }],
  },
  photo_demo_004: {
    photo_id: 'photo_demo_004',
    file_name: 'gala_004.jpg',
    width: 1920,
    height: 1080,
    faces: [{ face_id: 'f_demo_004', photo_id: 'photo_demo_004', bbox: [180, 180, 380, 380] }],
  },
};

const DEMO_TUTORIAL_SUGGESTIONS: SuggestionsData = {
  maybe_groups_count: 0,
  maybe_groups: [],
  possibly_the_same_count: 1,
  possibly_the_same: [
    {
      person_a_id: 'demo_p001',
      person_b_id: 'demo_p002',
      person_a_anchors: ['f_demo_001'],
      person_b_anchors: ['f_demo_003'],
      distance: 0.52,
      confidence: 'medium',
      reason: 'High facial feature similarity',
      person_a_photos: 14,
      person_b_photos: 8,
      person_a_best_face: '/faces/f_demo_001.jpg',
      person_b_best_face: '/faces/f_demo_003.jpg',
    },
  ],
  ambiguous_faces_count: 0,
  ambiguous_faces: [],
};

const DEMO_TUTORIAL_UNRECOGNIZED: UnrecognizedData = {
  total_unrecognized_photos: 1,
  no_face_photos: [],
  faces: [
    {
      face_id: 'f_demo_unrec_01',
      photo_id: 'photo_demo_001',
      face: '/faces/f_demo_unrec_01.jpg',
      rejection_reason: 'low_confidence',
      bbox: [50, 50, 120, 120],
      det_score: 0.42,
    },
    {
      face_id: 'f_demo_unrec_02',
      photo_id: 'photo_demo_002',
      face: '/faces/f_demo_unrec_02.jpg',
      rejection_reason: 'small_face',
      bbox: [80, 80, 140, 140],
      det_score: 0.55,
    },
  ],
};

export const App: React.FC = () => {
  const [theme, setTheme] = useState<RisoTheme>(() => {
    try {
      const saved = localStorage.getItem('photosorter-theme');
      if (saved === 't-paper' || saved === 't-navy' || saved === 't-dark') {
        return saved;
      }
    } catch (e) { }
    return 't-dark';
  });

  const [isThemeTransitioning, setIsThemeTransitioning] = useState(false);

  useEffect(() => {
    if (typeof document !== 'undefined') {
      document.body.classList.remove('t-dark', 't-paper', 't-navy');
      document.body.classList.add(theme);
      document.documentElement.classList.remove('t-dark', 't-paper', 't-navy');
      document.documentElement.classList.add(theme);
    }
  }, [theme]);

  const handleThemeChange = (newTheme: RisoTheme, e?: React.MouseEvent) => {
    if (newTheme === theme || isThemeTransitioning) return;

    const x = e ? e.clientX : window.innerWidth - 80;
    const y = e ? e.clientY : 32;

    document.documentElement.style.setProperty('--click-x', `${x}px`);
    document.documentElement.style.setProperty('--click-y', `${y}px`);

    const update = () => {
      setTheme(newTheme);
      try {
        localStorage.setItem('photosorter-theme', newTheme);
      } catch (err) { }
    };

    if ('startViewTransition' in document) {
      setIsThemeTransitioning(true);
      try {
        const transition = (document as any).startViewTransition(update);
        if (transition && transition.finished) {
          transition.finished
            .catch(() => { })
            .finally(() => {
              setIsThemeTransitioning(false);
            });
        } else {
          setTimeout(() => setIsThemeTransitioning(false), 550);
        }
      } catch (err) {
        update();
        setIsThemeTransitioning(false);
      }
    } else {
      update();
    }
  };

  const [activeTab, setActiveTab] = useState<ActiveTab>(() => {
    try {
      const saved = localStorage.getItem('photosorter-active-tab');
      if (saved && ['home', 'progress', 'settings'].includes(saved)) {
        return saved as ActiveTab;
      }
    } catch (e) { }
    return 'home';
  });

  const [people, setPeople] = useState<PersonCluster[]>([]);
  const [photos, setPhotos] = useState<Record<string, PhotoInfo>>({});
  const [isOpenProjectModalOpen, setIsOpenProjectModalOpen] = useState<boolean>(false);
  const [isTutorialOpen, setIsTutorialOpen] = useState<boolean>(false);

  const handleTabChange = (t: ActiveTab) => {
    setActiveTab(t);
    try {
      localStorage.setItem('photosorter-active-tab', t);
    } catch (e) { }
  };
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
  const [reviewSubTab, setReviewSubTab] = useState<'people' | 'suggestions' | 'unrecognized'>('people');
  const [rejectedPairs, setRejectedPairs] = useState<Set<string>>(new Set());
  const [appliedEditsCount, setAppliedEditsCount] = useState<number>(0);
  const [hasExportedCurrentSession, setHasExportedCurrentSession] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [isInitialLoading, setIsInitialLoading] = useState<boolean>(true);
  const [isMerging, setIsMerging] = useState<boolean>(false);
  const [isCancelling, setIsCancelling] = useState<boolean>(false);

  // Persistent Home Screen State
  const [sourceMode, setSourceMode] = useState<'drive' | 'local' | 'zip'>(() => {
    try {
      const saved = localStorage.getItem('photosorter-source-mode');
      if (saved === 'drive' || saved === 'local' || saved === 'zip') return saved;
    } catch (e) { }
    return 'drive';
  });

  const [folderPath, setFolderPath] = useState<string>(() => {
    try {
      return localStorage.getItem('photosorter-folder-path') || '';
    } catch (e) { }
    return '';
  });

  const [driveLink, setDriveLink] = useState<string>(() => {
    try {
      return localStorage.getItem('photosorter-drive-link') || '';
    } catch (e) { }
    return '';
  });

  const [driveVerified, setDriveVerified] = useState<boolean>(() => {
    try {
      return localStorage.getItem('photosorter-drive-verified') === 'true';
    } catch (e) { }
    return false;
  });

  const [verifiedFolderId, setVerifiedFolderId] = useState<string | null>(() => {
    try {
      return localStorage.getItem('photosorter-verified-folder-id') || null;
    } catch (e) { }
    return null;
  });

  const [verifiedFolderName, setVerifiedFolderName] = useState<string | null>(() => {
    try {
      return localStorage.getItem('photosorter-verified-folder-name') || null;
    } catch (e) { }
    return null;
  });

  const [verifiedImageCount, setVerifiedImageCount] = useState<number>(() => {
    try {
      const val = localStorage.getItem('photosorter-verified-img-count');
      return val ? parseInt(val, 10) : 0;
    } catch (e) { }
    return 0;
  });

  const [discoveredFaceIds, setDiscoveredFaceIds] = useState<string[]>([]);

  const [isApiKeyConfigured, setIsApiKeyConfigured] = useState<boolean | undefined>(() => {
    try {
      const val = localStorage.getItem('photosorter-api-key-configured');
      if (val === 'true') return true;
      if (val === 'false') return false;
    } catch (e) { }
    return undefined;
  });

  const handleSourceModeChange = (mode: 'drive' | 'local' | 'zip') => {
    setSourceMode(mode);
    try {
      localStorage.setItem('photosorter-source-mode', mode);
    } catch (e) { }
  };

  const handleFolderPathChange = (path: string) => {
    setFolderPath(path);
    try {
      localStorage.setItem('photosorter-folder-path', path);
    } catch (e) { }
  };

  const handleDriveLinkChange = (link: string) => {
    setDriveLink(link);
    try {
      localStorage.setItem('photosorter-drive-link', link);
    } catch (e) { }
  };

  const handleDriveVerifiedChange = (
    verified: boolean,
    folderId?: string | null,
    folderName?: string | null,
    imageCount?: number
  ) => {
    setDriveVerified(verified);
    setVerifiedFolderId(folderId || null);
    setVerifiedFolderName(folderName || null);
    setVerifiedImageCount(imageCount || 0);
    try {
      localStorage.setItem('photosorter-drive-verified', String(verified));
      if (folderId) localStorage.setItem('photosorter-verified-folder-id', folderId);
      else localStorage.removeItem('photosorter-verified-folder-id');
      if (folderName) localStorage.setItem('photosorter-verified-folder-name', folderName);
      else localStorage.removeItem('photosorter-verified-folder-name');
      localStorage.setItem('photosorter-verified-img-count', String(imageCount || 0));
    } catch (e) { }
  };

  // Load all data from API
  const loadAllData = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const settingsPromise = (api && typeof api.getSettings === 'function')
        ? Promise.resolve(api.getSettings()).catch(() => null)
        : Promise.resolve(null);

      const [peopleData, unrecData, sugData, photoData, settingsData] = await Promise.all([
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
        settingsPromise,
      ]);

      setPeople(peopleData);
      setUnrecognized(unrecData);
      setSuggestions(sugData);
      setPhotos(photoData);
      if (settingsData) {
        const isConf = Boolean(settingsData.drive_api_key_configured);
        setIsApiKeyConfigured(isConf);
        try {
          localStorage.setItem('photosorter-api-key-configured', String(isConf));
        } catch (e) { }
      }
    } catch (err) {
      console.error('Failed to load dataset from API:', err);
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  // Periodic background check & focus sync for API key status
  useEffect(() => {
    const checkSettings = () => {
      try {
        const p = api?.getSettings?.();
        if (p && typeof p.then === 'function') {
          p.then((s) => {
            if (s) {
              const isConf = Boolean(s.drive_api_key_configured);
              setIsApiKeyConfigured(isConf);
              try {
                localStorage.setItem('photosorter-api-key-configured', String(isConf));
              } catch (e) { }
            }
          }).catch(() => {});
        }
      } catch (e) {}
    };

    checkSettings();
    const interval = setInterval(checkSettings, 4000);
    window.addEventListener('focus', checkSettings);
    return () => {
      clearInterval(interval);
      window.removeEventListener('focus', checkSettings);
    };
  }, []);

  // Initial load
  useEffect(() => {
    Promise.all([
      loadAllData().then(() => {
        api.getActiveProject()
          .then((proj) => {
            if (!proj.active) {
              setActiveTab((prev) => (prev === 'people' ? 'home' : prev));
            }
          })
          .catch(() => {});
      }),
      api.getJobStatus()
        .then((status) => {
          setJobStatus(status);
          if (status.recent_faces && status.recent_faces.length > 0) {
            setDiscoveredFaceIds((prev) => {
              const s = new Set(prev);
              status.recent_faces!.forEach((fid) => s.add(fid));
              return Array.from(s);
            });
          }
          if (status.status === 'running') {
            setActiveTab('progress');
          }
        })
        .catch(() => { }),
    ]).finally(() => {
      setIsInitialLoading(false);
    });
  }, [loadAllData]);

  // Subscribe to SSE updates only when a job is actively running or on the progress tab
  useEffect(() => {
    if (jobStatus.status !== 'running' && !isCancelling && activeTab !== 'progress') {
      return;
    }
    const unsubscribe = api.subscribeProgress((status) => {
      setJobStatus(status);
      if (status.recent_faces && status.recent_faces.length > 0) {
        setDiscoveredFaceIds((prev) => {
          const s = new Set(prev);
          status.recent_faces!.forEach((fid) => s.add(fid));
          return Array.from(s);
        });
      }
      setProgressHistory((prev) => {
        const last = prev[prev.length - 1];
        if (last && last.current === status.current && last.stage === status.stage && last.status === status.status && last.percent === status.percent) {
          return prev;
        }
        return [...prev.slice(-4999), status];
      });
      if (status.status === 'completed') {
        loadAllData();
      }
    });
    return () => {
      unsubscribe();
    };
  }, [jobStatus.status, isCancelling, activeTab, loadAllData]);

  // Robust live polling fallback to guarantee real-time updates even if SSE is buffered
  useEffect(() => {
    if (jobStatus.status === 'running' || isCancelling || activeTab === 'progress') {
      const timer = setInterval(async () => {
        try {
          const st = await api.getJobStatus();
          setJobStatus(st);
          if (st.recent_faces && st.recent_faces.length > 0) {
            setDiscoveredFaceIds((prev) => {
              const s = new Set(prev);
              st.recent_faces!.forEach((fid) => s.add(fid));
              return Array.from(s);
            });
          }
          setProgressHistory((prev) => {
            const last = prev[prev.length - 1];
            if (last && last.current === st.current && last.stage === st.stage && last.status === st.status && last.percent === st.percent) {
              return prev;
            }
            return [...prev.slice(-4999), st];
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

  // Aggregate all discovered face crop URLs
  const allDiscoveredFaces = useMemo(() => {
    const list: string[] = [];
    const seen = new Set<string>();

    const addCrop = (raw: string | undefined | null) => {
      if (!raw) return;
      const clean = raw.startsWith('/') || raw.startsWith('faces/') ? `/${raw.replace(/^\//, '')}` : `/faces/${raw}`;
      if (!seen.has(clean)) {
        seen.add(clean);
        list.push(clean);
      }
    };

    discoveredFaceIds.forEach((fid) => {
      addCrop(`/faces/${fid}.jpg`);
    });

    // 1. First add representative face for each person so preview row shows distinct people
    people.forEach((p) => {
      addCrop(p.face);
    });

    // 2. Then add all other individual face crops for each person
    people.forEach((p) => {
      p.faces?.forEach((f) => {
        if (f.face_id) addCrop(`/faces/${f.face_id}.jpg`);
      });
    });

    // 3. Add unrecognized faces
    unrecognized.faces?.forEach((uf) => {
      if (uf.face) addCrop(uf.face);
      else if (uf.face_id) addCrop(`/faces/${uf.face_id}.jpg`);
    });

    return list;
  }, [discoveredFaceIds, people, unrecognized]);

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

  const handleAssignMultipleFaces = async (faceIds: string[], targetPersonId?: string | null) => {
    try {
      const res = await api.assignFaces(faceIds, targetPersonId);
      if (res.success) {
        setAppliedEditsCount((c) => c + faceIds.length);
        await loadAllData();
      }
    } catch (err: any) {
      alert(`Batch assign failed: ${err.message || err}`);
    }
  };

  const handleAssignPhotos = async (photoIds: string[], targetPersonId?: string | null) => {
    try {
      const res = await api.assignPhotos(photoIds, targetPersonId);
      if (res.success) {
        setAppliedEditsCount((c) => c + photoIds.length);
        await loadAllData();
      }
    } catch (err: any) {
      alert(`Assign photos failed: ${err.message || err}`);
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
      const st = await api.startJob(inputPath, driveFolder, driveApiKey, 'export');
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

  const hasUnexportedWork = (people.length > 0 || Object.keys(photos).length > 0) && !hasExportedCurrentSession;

  const [projectReadOnlyNotice, setProjectReadOnlyNotice] = useState<string | null>(null);

  const handleOpenProject = () => {
    setIsOpenProjectModalOpen(true);
  };

  const handleOpenTutorial = () => {
    setIsTutorialOpen(true);
  };

  const handleNewProject = async () => {
    if (hasUnexportedWork) {
      const confirmMsg =
        'You have an active project with unexported work.\n\nAre you sure you want to start a new project? Any unsaved edits will be discarded.';
      if (!window.confirm(confirmMsg)) {
        return;
      }
    }
    try {
      await api.newProject();
    } catch (e) {
      console.error('Failed to reset project on backend:', e);
    }
    setPeople([]);
    setPhotos({});
    setUnrecognized({ total_unrecognized_photos: 0, no_face_photos: [], faces: [] });
    setSuggestions({
      maybe_groups_count: 0,
      maybe_groups: [],
      possibly_the_same_count: 0,
      possibly_the_same: [],
      ambiguous_faces_count: 0,
      ambiguous_faces: [],
    });
    setSelectedIds(new Set());
    setRejectedPairs(new Set());
    setAppliedEditsCount(0);
    setHasExportedCurrentSession(false);
    setDriveVerified(false);
    setVerifiedFolderId(null);
    setVerifiedFolderName(null);
    setVerifiedImageCount(0);
    setProjectReadOnlyNotice(null);
    try {
      localStorage.removeItem('photosorter-active-tab');
      localStorage.removeItem('photosorter-drive-verified');
      localStorage.removeItem('photosorter-verified-folder-id');
      localStorage.removeItem('photosorter-verified-folder-name');
      localStorage.removeItem('photosorter-verified-img-count');
    } catch (e) { }
    setActiveTab('home');
  };

  const handleProjectOpened = async (res: OpenProjectResponse) => {
    setHasExportedCurrentSession(false);
    await loadAllData();
    handleTabChange('people');
    if (res.read_only) {
      setProjectReadOnlyNotice(
        `Project opened in read-only mode: ${res.edits_error || 'Corrupt edits.json detected'}. Modifications will not overwrite edits.json.`
      );
    } else {
      setProjectReadOnlyNotice(null);
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
    <div className={`app ${theme} ${activeTab === 'settings' ? 'app-settings-fixed' : ''}`}>
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
        onNewProject={handleNewProject}
        onOpenTutorial={handleOpenTutorial}
      />

      {/* Left Vertical Step Rail matching screenshot */}
      <div className="rail" aria-label="Workflow Steps">
        <div className="rail-steps">
          <button
            type="button"
            id="tab-home"
            onClick={() => handleTabChange('home')}
            className={`step ${activeTab === 'home' ? 'on' : ''}`}
          >
            <b>01</b>
            <span>Source</span>
          </button>
          <button
            type="button"
            id="tab-progress"
            onClick={() => handleTabChange('progress')}
            className={`step ${activeTab === 'progress' ? 'on' : ''}`}
          >
            <b>02</b>
            <span>Scan</span>
          </button>
          <button
            type="button"
            id="tab-people"
            onClick={() => handleTabChange('people')}
            className={`step ${activeTab === 'people' ? 'on' : ''}`}
            title="Review people and edits"
          >
            <b>03</b>
            <span>Review</span>
          </button>
          <button
            type="button"
            id="tab-export"
            onClick={() => handleTabChange('export')}
            className={`step ${activeTab === 'export' ? 'on' : ''}`}
            title="Publish standalone gallery"
          >
            <b>04</b>
            <span>Publish</span>
          </button>
          <button
            type="button"
            id="tab-settings"
            onClick={() => handleTabChange('settings')}
            className={`step ${activeTab === 'settings' ? 'on' : ''}`}
            title="Configure clustering parameters and cloud keys"
          >
            <b>05</b>
            <span>Settings</span>
          </button>
        </div>
      </div>

      {/* Main Screen Content */}
      <div className={`main ${activeTab === 'settings' ? 'settings-mode' : ''} ${activeTab === 'export' ? 'export-mode' : ''}`}>
        {projectReadOnlyNotice && (
          <div
            data-testid="read-only-banner"
            className="mx-4 mt-3 p-3 rounded flex items-center justify-between text-xs"
            style={{
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1.5px solid #ef4444',
              color: '#f87171',
            }}
          >
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              <span>{projectReadOnlyNotice}</span>
            </div>
            <button
              type="button"
              onClick={() => setProjectReadOnlyNotice(null)}
              className="p-1 opacity-70 hover:opacity-100"
              title="Dismiss notice"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {activeTab === 'home' && (
          <HomeScreen
            onStartJob={handleStartJob}
            isLoading={jobStatus.status === 'running'}
            onNavigateTab={(t: any) => handleTabChange(t)}
            theme={theme}
            sourceMode={sourceMode}
            onSourceModeChange={handleSourceModeChange}
            folderPath={folderPath}
            onFolderPathChange={handleFolderPathChange}
            driveLink={driveLink}
            onDriveLinkChange={handleDriveLinkChange}
            driveVerified={driveVerified}
            verifiedFolderId={verifiedFolderId}
            verifiedFolderName={verifiedFolderName}
            verifiedImageCount={verifiedImageCount}
            onDriveVerifiedChange={handleDriveVerifiedChange}
            discoveredFaceCrops={allDiscoveredFaces}
            onApiKeySaved={loadAllData}
            isApiKeyConfigured={isApiKeyConfigured}
            onOpenProject={handleOpenProject}
            onOpenTutorial={handleOpenTutorial}
          />
        )}

        <React.Suspense fallback={<div className="p-8 text-center text-xs font-mono opacity-50">Loading screen...</div>}>
        {activeTab === 'progress' && (
          <ProgressScreen
            status={
              isTutorialOpen && jobStatus.status === 'idle'
                ? {
                    status: 'running',
                    stage: 'detecting',
                    current: 82,
                    total: 105,
                    percent: 78,
                    message: 'Scanning face embeddings (buffalo_l)...',
                    elapsed_seconds: 14,
                  }
                : jobStatus
            }
            progressHistory={progressHistory}
            onCancelJob={handleCancelJob}
            onGoToReview={() => {
              setActiveTab('people');
              loadAllData();
            }}
            isCancelling={isCancelling}
            discoveredFaceCrops={
              isTutorialOpen && allDiscoveredFaces.length === 0
                ? ['f_demo_001', 'f_demo_002', 'f_demo_003', 'f_demo_004']
                : allDiscoveredFaces
            }
            theme={theme}
          />
        )}

        {activeTab === 'people' && (
          <ReviewPeopleScreen
            people={isTutorialOpen && people.length === 0 ? DEMO_TUTORIAL_PEOPLE : people}
            photos={isTutorialOpen && Object.keys(photos).length === 0 ? DEMO_TUTORIAL_PHOTOS : photos}
            unrecognized={isTutorialOpen && unrecognized.faces.length === 0 ? DEMO_TUTORIAL_UNRECOGNIZED : unrecognized}
            suggestions={isTutorialOpen && suggestions.possibly_the_same.length === 0 ? DEMO_TUTORIAL_SUGGESTIONS : suggestions}
            selectedIds={selectedIds}
            onToggleSelect={handleToggleSelect}
            onSelectAll={handleSelectAll}
            onClearSelection={handleClearSelection}
            onMergeSelected={handleMergeSelected}
            onAcceptSuggestion={handleAcceptSuggestion}
            onRejectSuggestion={handleRejectSuggestion}
            rejectedPairs={rejectedPairs}
            onAssignFace={handleAssignFace}
            onAssignMultipleFaces={handleAssignMultipleFaces}
            onAssignPhotos={handleAssignPhotos}
            onRenamePerson={handleRenamePerson}
            onHidePerson={handleHidePerson}
            onRemoveFace={handleRemoveFace}
            onRemovePhoto={handleRemovePhoto}
            onUndo={handleUndo}
            appliedEditsCount={appliedEditsCount}
            isMerging={isMerging}
            activeSubTab={reviewSubTab}
            onSubTabChange={setReviewSubTab}
            theme={theme}
          />
        )}

        {activeTab === 'export' && (
          <ExportScreen
            initialTitle={verifiedFolderName || (typeof window !== 'undefined' ? localStorage.getItem('photosorter-verified-folder-name') || undefined : undefined)}
            peopleCount={people.length}
            photosCount={Object.keys(photos).length}
            onRefreshStats={loadAllData}
            onExportSuccess={() => setHasExportedCurrentSession(true)}
            theme={theme}
          />
        )}

        {activeTab === 'settings' && (
          <SettingsScreen
            onRerunComplete={loadAllData}
            onOpenProject={handleOpenProject}
            onOpenTutorial={handleOpenTutorial}
            theme={theme}
          />
        )}
        </React.Suspense>
      </div>

      {/* Open Saved Project Modal */}
      <React.Suspense fallback={null}>
        {isOpenProjectModalOpen && (
          <OpenProjectModal
            onClose={() => setIsOpenProjectModalOpen(false)}
            onProjectOpened={handleProjectOpened}
            theme={theme}
            hasUnexportedWork={hasUnexportedWork}
            onNavigateToExport={() => {
              setIsOpenProjectModalOpen(false);
              handleTabChange('export');
            }}
          />
        )}

        {/* Interactive Onboarding Spotlight Tour */}
        {isTutorialOpen && (
          <TutorialSpotlight
            isOpen={isTutorialOpen}
            onClose={() => {
              setIsTutorialOpen(false);
              setSelectedIds(new Set());
              setReviewSubTab('people');
            }}
            onNavigateTab={handleTabChange}
            onSetReviewSubTab={setReviewSubTab}
            onSetSelectedPeopleIds={setSelectedIds}
            onSetSourceMode={handleSourceModeChange}
            activeTab={activeTab}
            theme={theme}
          />
        )}
      </React.Suspense>
    </div>
  );
};
