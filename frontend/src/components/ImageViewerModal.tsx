import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { PhotoInfo, PersonCluster, UnrecognizedData, FaceItem } from '../types';
import {
  X,
  Download,
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Scan,
  User,
  ExternalLink,
  Layers,
  Sparkles,
  UserPlus,
  UserMinus,
  Check,
  Edit2,
  Loader2,
} from 'lucide-react';

interface DetectedFaceInPhoto {
  faceId: string;
  photoId: string;
  bbox?: number[] | null;
  detScore?: number | null;
  isUnrecognized: boolean;
  rejectionReason?: string | null;
  personId?: string | null;
  personLabel?: string | null;
  personFace?: string | null;
  faceThumbUrl: string;
}

interface ImageViewerModalProps {
  photoId: string;
  photos: Record<string, PhotoInfo>;
  photoIds?: string[];
  people?: PersonCluster[];
  unrecognized?: UnrecognizedData;
  onClose: () => void;
  onNavigatePhoto: (photoId: string) => void;
  onAssignFace?: (faceId: string, personId?: string | null) => void;
  onRemoveFace?: (personId: string, faceId: string) => void;
  onInspectPerson?: (person: PersonCluster) => void;
}

export const ImageViewerModal: React.FC<ImageViewerModalProps> = ({
  photoId,
  photos,
  photoIds,
  people = [],
  unrecognized,
  onClose,
  onNavigatePhoto,
  onAssignFace,
  onRemoveFace,
  onInspectPerson,
}) => {
  const currentPhoto = photos[photoId];

  // List of all photo IDs in the navigation set
  const allIds = useMemo(() => {
    if (photoIds && photoIds.length > 0) return photoIds;
    return Object.keys(photos);
  }, [photoIds, photos]);

  const currentIndex = allIds.indexOf(photoId);
  const hasPrev = currentIndex > 0;
  const hasNext = currentIndex >= 0 && currentIndex < allIds.length - 1;

  // Zoom and Pan states
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const dragStartRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const panStartRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });

  // UI state toggles
  const [showFaceHighlights, setShowFaceHighlights] = useState<boolean>(true);
  const [showFacesDrawer, setShowFacesDrawer] = useState<boolean>(false);
  const [showFilmstrip, setShowFilmstrip] = useState<boolean>(true);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [hoveredFaceId, setHoveredFaceId] = useState<string | null>(null);

  // Face assignment & reassign state
  const [localAssignments, setLocalAssignments] = useState<
    Record<string, { personId?: string | null; personLabel?: string; isUnrecognized: boolean }>
  >({});
  const [activePopoverFaceId, setActivePopoverFaceId] = useState<string | null>(null);
  const [drawerSelectedPerson, setDrawerSelectedPerson] = useState<Record<string, string>>({});
  const [popoverSelectedPerson, setPopoverSelectedPerson] = useState<string>('');
  const [assigningFaceId, setAssigningFaceId] = useState<string | null>(null);
  const [feedbackMsg, setFeedbackMsg] = useState<Record<string, string>>({});

  // Natural image dimensions state
  const [naturalDim, setNaturalDim] = useState<{ width: number; height: number } | null>(null);
  const [imgFailed, setImgFailed] = useState<boolean>(false);

  const containerRef = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const filmstripRef = useRef<HTMLDivElement>(null);

  // Keyboard navigation & accessibility: Escape dismisses popover -> drawer -> modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (activePopoverFaceId !== null) {
          setActivePopoverFaceId(null);
        } else if (showFacesDrawer) {
          setShowFacesDrawer(false);
        } else {
          onClose();
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [activePopoverFaceId, showFacesDrawer, onClose]);

  // Reset zoom, pan, and error on photo change
  useEffect(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
    setHoveredFaceId(null);
    setActivePopoverFaceId(null);
    setPopoverSelectedPerson('');
    setImgFailed(false);
  }, [photoId]);

  // Scroll active thumbnail into view in filmstrip
  useEffect(() => {
    if (filmstripRef.current) {
      const activeThumb = filmstripRef.current.querySelector(`[data-filmstrip-id="${photoId}"]`);
      if (activeThumb && typeof activeThumb.scrollIntoView === 'function') {
        activeThumb.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
      }
    }
  }, [photoId, showFilmstrip]);

  // Sorted list of people for the select dropdowns
  const sortedPeople = useMemo(() => {
    return [...people].sort((a, b) => {
      const nameA = (a.label || a.id).toLowerCase();
      const nameB = (b.label || b.id).toLowerCase();
      return nameA.localeCompare(nameB);
    });
  }, [people]);

  // Gather all detected faces in this photo (both known and unknown)
  const detectedFaces = useMemo<DetectedFaceInPhoto[]>(() => {
    if (!photoId) return [];
    const result: DetectedFaceInPhoto[] = [];

    // 1. Faces from clustered people
    for (const person of people) {
      if (person.faces) {
        for (const f of person.faces) {
          if (f.photo_id === photoId) {
            result.push({
              faceId: f.face_id,
              photoId: f.photo_id,
              bbox: f.bbox,
              detScore: f.det_score,
              isUnrecognized: false,
              personId: person.id,
              personLabel: person.label || person.id,
              personFace: person.face,
              faceThumbUrl: `/faces/${f.face_id}.jpg`,
            });
          }
        }
      }
    }

    // 2. Unrecognized faces in this photo
    if (unrecognized && unrecognized.faces) {
      for (const uf of unrecognized.faces) {
        if (uf.photo_id === photoId) {
          const fid = uf.face_id || `unrec_${uf.photo_id}`;
          // Resolve bbox: check uf.bbox first, then currentPhoto.faces
          let bbox = uf.bbox;
          if (!bbox && currentPhoto?.faces) {
            const match = currentPhoto.faces.find((f) => f.face_id === fid);
            if (match) bbox = match.bbox;
          }

          result.push({
            faceId: fid,
            photoId: uf.photo_id,
            bbox: bbox,
            detScore: uf.det_score,
            isUnrecognized: true,
            rejectionReason: uf.rejection_reason || 'unattached',
            faceThumbUrl: uf.face || `/faces/${fid}.jpg`,
          });
        }
      }
    }

    // 3. Fallback to photos[photoId].faces for any detected faces not yet accounted for
    if (currentPhoto && currentPhoto.faces) {
      const existingIds = new Set(result.map((r) => r.faceId));
      for (const pf of currentPhoto.faces) {
        if (!existingIds.has(pf.face_id)) {
          result.push({
            faceId: pf.face_id,
            photoId: photoId,
            bbox: pf.bbox,
            detScore: pf.det_score,
            isUnrecognized: true,
            rejectionReason: 'unassigned',
            faceThumbUrl: `/faces/${pf.face_id}.jpg`,
          });
        }
      }
    }

    // 4. Apply optimistic local overrides
    return result.map((f) => {
      const override = localAssignments[f.faceId];
      if (!override) return f;
      const targetPerson = override.personId ? people.find((p) => p.id === override.personId) : null;
      return {
        ...f,
        isUnrecognized: override.isUnrecognized,
        personId: override.personId,
        personLabel:
          override.personLabel ||
          targetPerson?.label ||
          override.personId ||
          (override.isUnrecognized ? 'Unrecognized Face' : 'New Person'),
        personFace: targetPerson?.face,
      };
    });
  }, [photoId, people, unrecognized, currentPhoto, localAssignments]);

  // Assignment handlers
  const handleAssignFaceToPerson = async (faceId: string, targetPersonId: string | null) => {
    if (!onAssignFace) return;
    setAssigningFaceId(faceId);
    try {
      const targetPerson = targetPersonId ? people.find((p) => p.id === targetPersonId) : null;
      const newLabel = targetPerson ? (targetPerson.label || targetPerson.id) : 'New Person';

      // Optimistic update
      setLocalAssignments((prev) => ({
        ...prev,
        [faceId]: {
          personId: targetPersonId,
          personLabel: newLabel,
          isUnrecognized: false,
        },
      }));

      await onAssignFace(faceId, targetPersonId);

      setFeedbackMsg((prev) => ({
        ...prev,
        [faceId]: targetPersonId ? `Assigned to ${newLabel}` : 'Created new person',
      }));
      setTimeout(() => {
        setFeedbackMsg((prev) => {
          const next = { ...prev };
          delete next[faceId];
          return next;
        });
      }, 3500);

      if (activePopoverFaceId === faceId) {
        setActivePopoverFaceId(null);
      }
    } catch (err: any) {
      alert(`Assignment failed: ${err.message || err}`);
    } finally {
      setAssigningFaceId(null);
    }
  };

  const handleDetachFaceFromPerson = async (personId: string, faceId: string) => {
    if (!onRemoveFace) return;
    setAssigningFaceId(faceId);
    try {
      setLocalAssignments((prev) => ({
        ...prev,
        [faceId]: {
          personId: null,
          personLabel: undefined,
          isUnrecognized: true,
        },
      }));

      await onRemoveFace(personId, faceId);

      setFeedbackMsg((prev) => ({
        ...prev,
        [faceId]: 'Detached to unknown',
      }));
      setTimeout(() => {
        setFeedbackMsg((prev) => {
          const next = { ...prev };
          delete next[faceId];
          return next;
        });
      }, 3500);

      if (activePopoverFaceId === faceId) {
        setActivePopoverFaceId(null);
      }
    } catch (err: any) {
      alert(`Detach failed: ${err.message || err}`);
    } finally {
      setAssigningFaceId(null);
    }
  };

  // Navigation handlers
  const handlePrev = useCallback(() => {
    if (hasPrev) onNavigatePhoto(allIds[currentIndex - 1]);
  }, [hasPrev, currentIndex, allIds, onNavigatePhoto]);

  const handleNext = useCallback(() => {
    if (hasNext) onNavigatePhoto(allIds[currentIndex + 1]);
  }, [hasNext, currentIndex, allIds, onNavigatePhoto]);

  // Keyboard controls
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't intercept if typing in an input
      if (['INPUT', 'TEXTAREA', 'SELECT'].includes((e.target as HTMLElement).tagName)) {
        return;
      }

      switch (e.key) {
        case 'ArrowLeft':
          e.preventDefault();
          handlePrev();
          break;
        case 'ArrowRight':
          e.preventDefault();
          handleNext();
          break;
        case 'Escape':
          e.preventDefault();
          if (activePopoverFaceId) {
            setActivePopoverFaceId(null);
          } else if (showFacesDrawer) {
            setShowFacesDrawer(false);
          } else {
            onClose();
          }
          break;
        case '+':
        case '=':
          e.preventDefault();
          setZoom((z) => Math.min(z + 0.25, 4));
          break;
        case '-':
        case '_':
          e.preventDefault();
          setZoom((z) => {
            const next = Math.max(z - 0.25, 1);
            if (next === 1) setPan({ x: 0, y: 0 });
            return next;
          });
          break;
        case '0':
          e.preventDefault();
          setZoom(1);
          setPan({ x: 0, y: 0 });
          break;
        case 'f':
        case 'F':
          e.preventDefault();
          setIsFullscreen((f) => !f);
          break;
        case 'h':
        case 'H':
          e.preventDefault();
          setShowFaceHighlights((h) => !h);
          break;
        default:
          break;
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handlePrev, handleNext, onClose, activePopoverFaceId, showFacesDrawer]);

  // Pan dragging logic
  const handleMouseDown = (e: React.MouseEvent) => {
    if (zoom <= 1) return;
    setIsDragging(true);
    dragStartRef.current = { x: e.clientX, y: e.clientY };
    panStartRef.current = { ...pan };
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    const dx = e.clientX - dragStartRef.current.x;
    const dy = e.clientY - dragStartRef.current.y;
    setPan({
      x: panStartRef.current.x + dx,
      y: panStartRef.current.y + dy,
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Wheel zoom
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY * -0.002;
    setZoom((prev) => {
      const next = Math.min(Math.max(prev + delta, 1), 4);
      if (next === 1) setPan({ x: 0, y: 0 });
      return next;
    });
  };

  const handleZoomIn = () => setZoom((z) => Math.min(z + 0.25, 4));
  const handleZoomOut = () =>
    setZoom((z) => {
      const next = Math.max(z - 0.25, 1);
      if (next === 1) setPan({ x: 0, y: 0 });
      return next;
    });
  const handleResetZoom = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  if (!currentPhoto) return null;

  const photoSrc = currentPhoto.thumb || `/thumbs/${currentPhoto.photo_id}.jpg`;
  const fileName = currentPhoto.file_name || `${currentPhoto.photo_id}.jpg`;
  // Use original photo dimensions first because bbox coordinates from backend are in original image space
  const imgWidth = currentPhoto.width || naturalDim?.width || 1;
  const imgHeight = currentPhoto.height || naturalDim?.height || 1;
  const aspectRatio = imgWidth / imgHeight;

  return (
    <div
      className="fixed inset-0 z-50 flex flex-col select-none animate-fadeIn p-2 sm:p-4"
      style={{
        background: 'rgba(14, 18, 24, 0.94)',
        backdropFilter: 'blur(10px)',
        fontFamily: "'JetBrains Mono', monospace",
        color: 'var(--text)',
      }}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
    >
      {/* Top Navigation Bar */}
      <div
        className="flex-shrink-0 z-20 flex items-center justify-between gap-4 px-5 py-3 rounded mb-2 flex-wrap"
        style={{
          background: 'var(--panel)',
          border: '1.5px solid var(--line)',
          boxShadow: '2px 3px 0px rgba(0, 0, 0, 0.2)',
        }}
      >
        {/* Photo Info */}
        <div className="flex items-center gap-3.5 min-w-0 pr-2">
          <div
            className="w-10 h-10 rounded flex items-center justify-center flex-shrink-0"
            style={{
              background: 'var(--input)',
              border: '1.5px solid var(--accent)',
              color: 'var(--accent)',
            }}
          >
            <Scan className="w-5 h-5" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2.5">
              <h3 className="text-base sm:text-lg font-bold font-mono truncate" style={{ color: 'var(--text)' }} title={fileName}>
                {fileName}
              </h3>
              <span className="riso-tab-badge">
                {currentIndex >= 0 ? `${currentIndex + 1} / ${allIds.length}` : ''}
              </span>
              {currentPhoto.source_label && (
                <span
                  id="photo-source-badge"
                  data-testid="photo-source-badge"
                  className="px-2 py-0.5 rounded text-xs font-mono font-bold flex items-center gap-1"
                  style={{
                    background: 'var(--input)',
                    border: '1px solid var(--accent)',
                    color: 'var(--accent)',
                  }}
                  title={`Source: ${currentPhoto.source_label}`}
                >
                  {currentPhoto.source_label}
                </span>
              )}
              {(currentPhoto.source_exists === false || imgFailed) && (
                <span
                  data-testid="source-missing-badge"
                  className="px-2 py-0.5 rounded text-xs font-bold"
                  style={{
                    background: 'rgba(239, 68, 68, 0.2)',
                    border: '1px solid #ef4444',
                    color: '#f87171',
                  }}
                  title="Source photo missing or moved from disk"
                >
                  Source missing
                </span>
              )}
            </div>
            <div className="flex items-center gap-3 text-xs mt-0.5" style={{ color: 'var(--muted)' }}>
              {imgWidth && imgHeight && (
                <span>
                  {imgWidth} × {imgHeight} px
                </span>
              )}
              {detectedFaces.length > 0 && (
                <span className="flex items-center gap-1 font-bold" style={{ color: 'var(--accent)' }}>
                  <Sparkles className="w-3.5 h-3.5" />
                  {detectedFaces.length} detected {detectedFaces.length === 1 ? 'face' : 'faces'}
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Toolbar Controls */}
        <div className="flex items-center gap-2 flex-shrink-0 flex-wrap">
          {/* Face Highlights Toggle */}
          <button
            onClick={() => setShowFaceHighlights((h) => !h)}
            className="riso-btn-sec"
            style={{
              height: '40px',
              padding: '0 14px',
              borderColor: showFaceHighlights ? 'var(--accent)' : 'var(--line)',
              color: showFaceHighlights ? 'var(--accent)' : 'var(--text)',
            }}
            title="Toggle Face Highlights (H)"
          >
            <Scan className="w-4 h-4" />
            <span className="hidden md:inline">Faces</span>
            {detectedFaces.length > 0 && (
              <span className="riso-tab-badge ml-1">
                {detectedFaces.length}
              </span>
            )}
          </button>

          {/* Faces Inspector Drawer Toggle */}
          {detectedFaces.length > 0 && (
            <button
              onClick={() => setShowFacesDrawer((d) => !d)}
              className="riso-btn-sec"
              style={{
                height: '40px',
                padding: '0 14px',
                borderColor: showFacesDrawer ? 'var(--accent)' : 'var(--line)',
                color: showFacesDrawer ? 'var(--accent)' : 'var(--text)',
              }}
              title="View Detected Faces List"
            >
              <User className="w-4 h-4" />
              <span className="hidden md:inline">Inspect Faces</span>
            </button>
          )}

          {/* Zoom Controls */}
          <div
            className="hidden sm:flex items-center gap-1.5 p-1 rounded"
            style={{
              background: 'var(--input)',
              border: '1.5px solid var(--line)',
            }}
          >
            <button
              onClick={handleZoomOut}
              className="riso-btn-sec"
              style={{ width: '32px', height: '32px', padding: 0 }}
              title="Zoom Out (-)"
            >
              <ZoomOut className="w-4 h-4" />
            </button>
            <span
              onClick={handleResetZoom}
              className="px-2 text-xs font-mono font-bold cursor-pointer"
              style={{ color: 'var(--text)' }}
              title="Click to Reset Zoom (0)"
            >
              {Math.round(zoom * 100)}%
            </span>
            <button
              onClick={handleZoomIn}
              className="riso-btn-sec"
              style={{ width: '32px', height: '32px', padding: 0 }}
              title="Zoom In (+)"
            >
              <ZoomIn className="w-4 h-4" />
            </button>
            <button
              onClick={handleResetZoom}
              className="riso-btn-sec"
              style={{ width: '32px', height: '32px', padding: 0 }}
              title="Fit to Window"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
          </div>

          {/* Download Original */}
          {currentPhoto.download && (
            currentPhoto.source_exists === false ? (
              <button
                type="button"
                disabled
                data-testid="download-missing-btn"
                className="riso-btn-sec opacity-40 cursor-not-allowed"
                style={{ width: '40px', height: '40px', padding: 0 }}
                title="Source photo missing or moved on disk"
              >
                <Download className="w-4 h-4" />
              </button>
            ) : (
              <a
                href={currentPhoto.download}
                target="_blank"
                rel="noopener noreferrer"
                download={fileName}
                className="riso-btn-sec"
                style={{ width: '40px', height: '40px', padding: 0 }}
                title="Download Photo"
              >
                <Download className="w-4 h-4" />
              </a>
            )
          )}

          {/* Filmstrip Toggle */}
          <button
            onClick={() => setShowFilmstrip((s) => !s)}
            className="riso-btn-sec"
            style={{
              width: '40px',
              height: '40px',
              padding: 0,
              borderColor: showFilmstrip ? 'var(--accent)' : 'var(--line)',
            }}
            title="Toggle Thumbnail Filmstrip"
          >
            <Layers className="w-4 h-4" />
          </button>

          {/* Close Modal Button */}
          <button
            onClick={onClose}
            className="riso-btn-sec"
            style={{ width: '40px', height: '40px', padding: 0 }}
            title="Close Viewer (Esc)"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Main Photo Viewport */}
      <div
        ref={containerRef}
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        className="relative flex-1 w-full overflow-hidden flex items-center justify-center rounded"
        style={{
          background: 'rgba(0, 0, 0, 0.45)',
          border: '1.5px solid var(--line)',
          boxShadow: 'inset 0 2px 10px rgba(0, 0, 0, 0.3)',
          cursor: zoom > 1 ? (isDragging ? 'grabbing' : 'grab') : 'default',
        }}
      >
        {/* Navigation Prev Button */}
        {hasPrev && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              handlePrev();
            }}
            className="absolute left-5 top-1/2 -translate-y-1/2 z-30 w-14 h-14 rounded flex items-center justify-center transition-all cursor-pointer"
            style={{
              background: 'var(--panel)',
              border: '2px solid var(--line)',
              color: 'var(--text)',
              boxShadow: '2px 3px 0px rgba(0, 0, 0, 0.3)',
            }}
            title="Previous Photo (Left Arrow)"
          >
            <ChevronLeft className="w-7 h-7" />
          </button>
        )}

        {/* Navigation Next Button */}
        {hasNext && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleNext();
            }}
            className="absolute right-5 top-1/2 -translate-y-1/2 z-30 w-14 h-14 rounded flex items-center justify-center transition-all cursor-pointer"
            style={{
              background: 'var(--panel)',
              border: '2px solid var(--line)',
              color: 'var(--text)',
              boxShadow: '2px 3px 0px rgba(0, 0, 0, 0.3)',
            }}
            title="Next Photo (Right Arrow)"
          >
            <ChevronRight className="w-7 h-7" />
          </button>
        )}

        {/* Scaled Image & Overlays Wrapper - Expands to fill viewport nicely */}
        <div
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: 'center center',
            transition: isDragging ? 'none' : 'transform 0.15s ease-out',
            position: 'relative',
            width: `min(85vw, calc(72vh * ${aspectRatio}))`,
            height: `min(72vh, calc(85vw / ${aspectRatio}))`,
            maxWidth: '100%',
            maxHeight: '100%',
          }}
        >
          {imgFailed ? (
            <div
              data-testid="source-missing-placeholder"
              className="w-full h-full min-h-[300px] flex flex-col items-center justify-center p-6 text-center rounded"
              style={{
                background: 'var(--panel)',
                border: '2px dashed #ef4444',
                color: 'var(--muted)',
              }}
            >
              <Scan className="w-12 h-12 mb-3 text-red-400 opacity-60" />
              <p className="font-bold text-base text-red-400">Source photo missing or moved</p>
              <p className="text-xs mt-1 max-w-sm">The original photo file could not be found or loaded from disk.</p>
              {currentPhoto.original_path && (
                <p className="text-xs font-mono mt-2 opacity-70 break-all">{currentPhoto.original_path}</p>
              )}
            </div>
          ) : (
            <img
              ref={imgRef}
              src={photoSrc}
              alt={fileName}
              draggable={false}
              onLoad={(e) => {
                const target = e.target as HTMLImageElement;
                setNaturalDim({ width: target.naturalWidth, height: target.naturalHeight });
              }}
              onError={() => setImgFailed(true)}
              className="w-full h-full object-contain rounded shadow-2xl pointer-events-none block"
              style={{
                border: '1.5px solid var(--line)',
              }}
            />
          )}

          {/* Source Missing Floating Banner */}
          {(currentPhoto.source_exists === false || imgFailed) && (
            <div
              data-testid="source-missing-banner"
              className="absolute -top-12 left-1/2 -translate-x-1/2 z-40 px-3 py-1.5 rounded flex items-center gap-2 shadow-lg text-xs"
              style={{
                background: '#dc2626',
                color: '#ffffff',
                fontWeight: 600,
                border: '1px solid #b91c1c',
                whiteSpace: 'nowrap',
              }}
            >
              <span>Source photo missing or moved on disk</span>
            </div>
          )}

          {/* Face Highlights Overlay */}
          {showFaceHighlights &&
            imgWidth &&
            imgHeight &&
            detectedFaces.map((f) => {
              if (!f.bbox || f.bbox.length < 4) return null;
              const [x1, y1, x2, y2] = f.bbox;
              const leftPct = Math.max(0, Math.min(100, (x1 / imgWidth) * 100));
              const topPct = Math.max(0, Math.min(100, (y1 / imgHeight) * 100));
              const widthPct = Math.max(0, Math.min(100 - leftPct, ((x2 - x1) / imgWidth) * 100));
              const heightPct = Math.max(0, Math.min(100 - topPct, ((y2 - y1) / imgHeight) * 100));

              const isHovered = hoveredFaceId === f.faceId;
              const isPopoverOpen = activePopoverFaceId === f.faceId;
              const isAssigning = assigningFaceId === f.faceId;
              const feedback = feedbackMsg[f.faceId];

              return (
                <div
                  key={f.faceId}
                  onMouseEnter={() => setHoveredFaceId(f.faceId)}
                  onMouseLeave={() => setHoveredFaceId(null)}
                  onClick={(e) => {
                    e.stopPropagation();
                    setActivePopoverFaceId((prev) => (prev === f.faceId ? null : f.faceId));
                    setPopoverSelectedPerson(f.personId || '');
                  }}
                  className="absolute cursor-pointer transition-all rounded-sm"
                  style={{
                    left: `${leftPct}%`,
                    top: `${topPct}%`,
                    width: `${widthPct}%`,
                    height: `${heightPct}%`,
                    border: isHovered || isPopoverOpen
                      ? '2.5px solid var(--accent)'
                      : f.isUnrecognized
                      ? '2px dashed var(--accent)'
                      : '2px solid rgba(255, 255, 255, 0.75)',
                    background: isHovered || isPopoverOpen
                      ? 'rgba(250, 113, 117, 0.28)'
                      : f.isUnrecognized
                      ? 'rgba(250, 113, 117, 0.14)'
                      : 'rgba(255, 255, 255, 0.08)',
                    boxShadow: isHovered || isPopoverOpen
                      ? '0 0 14px var(--accent)'
                      : f.isUnrecognized
                      ? '0 0 6px rgba(250, 113, 117, 0.35)'
                      : 'none',
                    zIndex: isPopoverOpen ? 40 : 10,
                  }}
                  title={f.isUnrecognized ? `Unrecognized: ${f.faceId} (Click to change person)` : `${f.personLabel} (Click to change person)`}
                >
                  {/* Floating Tag over face */}
                  <div
                    className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2.5 py-1 rounded text-xs font-bold whitespace-nowrap shadow-xl flex items-center gap-2 transition-all cursor-pointer"
                    style={{
                      background: 'var(--panel)',
                      border: f.isUnrecognized ? '1.5px solid var(--accent)' : '1.5px solid var(--line)',
                      color: f.isUnrecognized ? 'var(--accent)' : 'var(--text)',
                      fontFamily: "'JetBrains Mono', monospace",
                      boxShadow: '2px 2px 0px rgba(0,0,0,0.3)',
                    }}
                    role="button"
                    tabIndex={0}
                    aria-label={`Face options for ${f.isUnrecognized ? 'unrecognized face' : f.personLabel}`}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        e.stopPropagation();
                        setActivePopoverFaceId((prev) => (prev === f.faceId ? null : f.faceId));
                        setPopoverSelectedPerson(f.personId || '');
                      }
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      setActivePopoverFaceId((prev) => (prev === f.faceId ? null : f.faceId));
                      setPopoverSelectedPerson(f.personId || '');
                    }}
                  >
                    {f.personFace ? (
                      <img src={f.personFace} alt="" className="w-5 h-5 rounded object-cover border border-white/20" />
                    ) : (
                      <span
                        className="w-2.5 h-2.5 rounded-full"
                        style={{ background: f.isUnrecognized ? 'var(--accent)' : '#4ade80' }}
                      />
                    )}
                    <span>{f.isUnrecognized ? `Unknown (${f.rejectionReason})` : f.personLabel}</span>
                    <span
                      className="px-1.5 py-0.5 rounded text-xs font-mono uppercase tracking-wider"
                      style={{
                        background: 'var(--input)',
                        border: '1px solid var(--line)',
                        color: 'var(--accent)',
                      }}
                    >
                      {f.isUnrecognized ? '+ Assign' : '✎ Change'}
                    </span>
                  </div>

                  {/* Interactive Quick Change Popover on Image */}
                  {isPopoverOpen && (
                    <div
                      className="absolute top-full left-1/2 -translate-x-1/2 mt-2 w-72 sm:w-80 p-3.5 rounded shadow-2xl z-50 animate-fadeIn"
                      style={{
                        background: 'var(--panel)',
                        border: '2px solid var(--accent)',
                        boxShadow: '0 8px 30px rgba(0, 0, 0, 0.7), 2px 3px 0px rgba(0,0,0,0.4)',
                        color: 'var(--text)',
                      }}
                      onClick={(e) => e.stopPropagation()}
                      onMouseDown={(e) => e.stopPropagation()}
                    >
                      <div className="flex items-center justify-between pb-2 mb-2.5 border-b border-[var(--line)]">
                        <div className="flex items-center gap-2 min-w-0">
                          <img src={f.faceThumbUrl} alt="" className="w-7 h-7 rounded object-cover border border-[var(--line)]" />
                          <div className="min-w-0">
                            <div className="text-xs font-bold font-mono truncate" style={{ color: 'var(--text)' }}>
                              {f.isUnrecognized ? 'Unrecognized Face' : f.personLabel}
                            </div>
                            <div className="text-xs font-mono text-[var(--muted)] truncate">{f.faceId}</div>
                          </div>
                        </div>
                        <button
                          onClick={() => setActivePopoverFaceId(null)}
                          className="w-6 h-6 flex items-center justify-center rounded hover:bg-white/10"
                          style={{ color: 'var(--muted)' }}
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>

                      {feedback && (
                        <div
                          className="mb-2 p-1.5 rounded text-xs text-center font-bold font-mono flex items-center justify-center gap-1.5"
                          style={{ background: 'rgba(74, 222, 128, 0.15)', color: '#4ade80', border: '1px solid rgba(74, 222, 128, 0.3)' }}
                        >
                          <Check className="w-3.5 h-3.5" />
                          {feedback}
                        </div>
                      )}

                      <div className="space-y-2">
                        <label className="text-xs font-bold uppercase tracking-wider block" style={{ color: 'var(--muted)' }}>
                          Assign / Change Person:
                        </label>
                        <select
                          value={popoverSelectedPerson}
                          onChange={(e) => setPopoverSelectedPerson(e.target.value)}
                          className="riso-select w-full text-xs py-1.5 px-2"
                          style={{ height: '34px' }}
                        >
                          <option value="">-- Choose Person --</option>
                          <option value="__new__">+ Create New Person</option>
                          {!f.isUnrecognized && f.personId && (
                            <option value="__detach__">✕ Detach to Unknown</option>
                          )}
                          <optgroup label={`Existing People (${sortedPeople.length})`}>
                            {sortedPeople.map((p) => (
                              <option key={p.id} value={p.id}>
                                {p.label || p.id} ({p.photo_count || p.photos?.length || 0} photos)
                              </option>
                            ))}
                          </optgroup>
                        </select>

                        <div className="flex items-center gap-2 pt-1 flex-wrap">
                          <button
                            disabled={!popoverSelectedPerson || isAssigning}
                            onClick={() => {
                              if (popoverSelectedPerson === '__new__') {
                                handleAssignFaceToPerson(f.faceId, null);
                              } else if (popoverSelectedPerson === '__detach__' && f.personId) {
                                handleDetachFaceFromPerson(f.personId, f.faceId);
                              } else if (popoverSelectedPerson) {
                                handleAssignFaceToPerson(f.faceId, popoverSelectedPerson);
                              }
                            }}
                            className="btn pri flex-1 text-xs py-1.5 h-8 font-bold flex items-center justify-center gap-1.5 disabled:opacity-50"
                          >
                            {isAssigning ? (
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            ) : (
                              <Check className="w-3.5 h-3.5" />
                            )}
                            <span>Apply</span>
                          </button>

                          <button
                            disabled={isAssigning}
                            onClick={() => handleAssignFaceToPerson(f.faceId, null)}
                            className="riso-btn-sec text-xs px-2.5 h-8 flex items-center gap-1"
                            title="Create a brand new person cluster for this face"
                          >
                            <UserPlus className="w-3.5 h-3.5 text-[var(--accent)]" />
                            <span>+ New</span>
                          </button>

                          {!f.isUnrecognized && f.personId && onRemoveFace && (
                            <button
                              disabled={isAssigning}
                              onClick={() => handleDetachFaceFromPerson(f.personId!, f.faceId)}
                              className="riso-btn-sec text-xs px-2.5 h-8 flex items-center gap-1 hover:border-red-500 hover:text-red-400"
                              title="Detach face to unrecognized"
                            >
                              <UserMinus className="w-3.5 h-3.5 text-red-400" />
                              <span>Detach</span>
                            </button>
                          )}
                        </div>

                        <div className="pt-1.5 flex justify-end">
                          <button
                            onClick={() => {
                              setActivePopoverFaceId(null);
                              setShowFacesDrawer(true);
                            }}
                            className="text-xs font-mono flex items-center gap-1 hover:underline"
                            style={{ color: 'var(--accent)' }}
                          >
                            <span>Inspect in Drawer</span>
                            <ChevronRight className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
        </div>

        {/* Faces Inspector Side Drawer */}
        {showFacesDrawer && detectedFaces.length > 0 && (
          <div
            className="absolute right-4 top-4 bottom-4 w-96 sm:w-[420px] max-w-[calc(100vw-2rem)] z-30 p-5 rounded flex flex-col justify-between overflow-hidden animate-fadeIn"
            style={{
              background: 'var(--panel)',
              border: '2px solid var(--line)',
              boxShadow: '-4px 0 24px rgba(0,0,0,0.4)',
            }}
            onClick={(e) => e.stopPropagation()}
            onMouseDown={(e) => e.stopPropagation()}
          >
            <div className="flex flex-col h-full">
              <div
                className="flex items-center justify-between pb-3.5 flex-shrink-0"
                style={{ borderBottom: '1.5px solid var(--line)' }}
              >
                <div>
                  <h4 className="text-base font-bold flex items-center gap-2" style={{ color: 'var(--text)' }}>
                    <User className="w-5 h-5" style={{ color: 'var(--accent)' }} />
                    Faces in this Photo ({detectedFaces.length})
                  </h4>
                  <p className="text-xs font-mono mt-0.5" style={{ color: 'var(--muted)' }}>
                    Reassign or create people directly from here
                  </p>
                </div>
                <button
                  onClick={() => setShowFacesDrawer(false)}
                  className="riso-btn-sec"
                  style={{ width: '32px', height: '32px', padding: 0 }}
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="mt-4 space-y-4 overflow-y-auto flex-1 pr-1.5 pb-2">
                {detectedFaces.map((f) => {
                  const isHovered = hoveredFaceId === f.faceId;
                  const isAssigning = assigningFaceId === f.faceId;
                  const feedback = feedbackMsg[f.faceId];
                  const selectedTarget = drawerSelectedPerson[f.faceId] || '';

                  return (
                    <div
                      key={f.faceId}
                      onMouseEnter={() => setHoveredFaceId(f.faceId)}
                      onMouseLeave={() => setHoveredFaceId(null)}
                      className="p-3.5 rounded transition-all"
                      style={{
                        background: 'var(--card-bg)',
                        border: isHovered ? '2px solid var(--accent)' : '1.5px solid var(--line)',
                        boxShadow: '2px 2px 0px rgba(0,0,0,0.15)',
                      }}
                    >
                      <div className="flex items-start gap-3.5">
                        <div
                          className="w-16 h-16 rounded overflow-hidden flex-shrink-0 relative"
                          style={{
                            border: f.isUnrecognized ? '1.5px dashed var(--accent)' : '1.5px solid var(--line)',
                            background: 'var(--input)',
                          }}
                        >
                          <img src={f.faceThumbUrl} alt={f.faceId} className="w-full h-full object-cover" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-1.5">
                            <span
                              className="w-2 h-2 rounded-full flex-shrink-0"
                              style={{ background: f.isUnrecognized ? 'var(--accent)' : '#4ade80' }}
                            />
                            <div className="text-sm font-mono font-bold truncate" style={{ color: 'var(--text)' }}>
                              {f.isUnrecognized ? 'Unrecognized Face' : f.personLabel}
                            </div>
                          </div>
                          <div className="text-xs font-mono mt-0.5 truncate" style={{ color: 'var(--muted)' }}>
                            {f.faceId}
                          </div>
                          <div className="mt-1.5 flex items-center gap-2 flex-wrap">
                            {f.isUnrecognized ? (
                              <span className="riso-tab-badge" style={{ color: 'var(--accent)', borderColor: 'var(--accent)' }}>
                                {f.rejectionReason}
                              </span>
                            ) : (
                              <span className="riso-tab-badge">
                                Person: {f.personId}
                              </span>
                            )}
                            {f.detScore != null && (
                              <span className="text-xs font-mono text-[var(--muted)]">
                                {(f.detScore * 100).toFixed(0)}% conf
                              </span>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Feedback notification */}
                      {feedback && (
                        <div
                          className="mt-2.5 p-1.5 rounded text-xs text-center font-bold font-mono flex items-center justify-center gap-1.5"
                          style={{
                            background: 'rgba(74, 222, 128, 0.15)',
                            color: '#4ade80',
                            border: '1px solid rgba(74, 222, 128, 0.3)',
                          }}
                        >
                          <Check className="w-3.5 h-3.5" />
                          {feedback}
                        </div>
                      )}

                      {/* Change / Reassign Person Controls */}
                      <div
                        className="mt-3 pt-3 flex flex-col gap-2.5"
                        style={{ borderTop: '1px solid var(--line)' }}
                      >
                        <div className="text-xs font-mono font-bold uppercase tracking-wider text-[var(--muted)]">
                          Change Assignment:
                        </div>

                        {/* Select Target Person */}
                        <select
                          value={selectedTarget}
                          onChange={(e) =>
                            setDrawerSelectedPerson((prev) => ({ ...prev, [f.faceId]: e.target.value }))
                          }
                          className="riso-select w-full text-xs py-1.5 px-2"
                          style={{ height: '34px' }}
                        >
                          <option value="">-- Select Person to Assign --</option>
                          <option value="__new__">+ Create New Person</option>
                          {!f.isUnrecognized && f.personId && (
                            <option value="__detach__">✕ Detach to Unknown</option>
                          )}
                          <optgroup label={`Existing People (${sortedPeople.length})`}>
                            {sortedPeople.map((p) => (
                              <option key={p.id} value={p.id}>
                                {p.label || p.id} ({p.photo_count || p.photos?.length || 0} photos)
                              </option>
                            ))}
                          </optgroup>
                        </select>

                        {/* Buttons Row */}
                        <div className="flex items-center gap-2 flex-wrap">
                          <button
                            disabled={!selectedTarget || isAssigning}
                            onClick={() => {
                              if (selectedTarget === '__new__') {
                                handleAssignFaceToPerson(f.faceId, null);
                              } else if (selectedTarget === '__detach__' && f.personId) {
                                handleDetachFaceFromPerson(f.personId, f.faceId);
                              } else if (selectedTarget) {
                                handleAssignFaceToPerson(f.faceId, selectedTarget);
                              }
                            }}
                            className="btn pri flex-1 min-w-[90px] text-xs h-8 font-bold flex items-center justify-center gap-1.5 disabled:opacity-50"
                          >
                            {isAssigning ? (
                              <Loader2 className="w-3.5 h-3.5 animate-spin" />
                            ) : (
                              <Check className="w-3.5 h-3.5" />
                            )}
                            <span>Assign</span>
                          </button>

                          <button
                            disabled={isAssigning}
                            onClick={() => handleAssignFaceToPerson(f.faceId, null)}
                            className="riso-btn-sec text-xs px-2.5 h-8 flex items-center gap-1 font-mono"
                            title="Create a new person from this face"
                          >
                            <UserPlus className="w-3.5 h-3.5 text-[var(--accent)]" />
                            <span>+ New</span>
                          </button>

                          {!f.isUnrecognized && f.personId && onRemoveFace && (
                            <button
                              disabled={isAssigning}
                              onClick={() => handleDetachFaceFromPerson(f.personId!, f.faceId)}
                              className="riso-btn-sec text-xs px-2.5 h-8 flex items-center gap-1 font-mono hover:border-red-500 hover:text-red-400"
                              title="Detach face and move to unknown"
                            >
                              <UserMinus className="w-3.5 h-3.5 text-red-400" />
                              <span>Detach</span>
                            </button>
                          )}

                          {!f.isUnrecognized && f.personId && onInspectPerson && (
                            <button
                              onClick={() => {
                                const p = people.find((item) => item.id === f.personId);
                                if (p) onInspectPerson(p);
                              }}
                              className="riso-btn-sec text-xs px-2.5 h-8 flex items-center gap-1 font-mono"
                              title="Inspect this person's photos"
                            >
                              <ExternalLink className="w-3.5 h-3.5 text-[var(--accent)]" />
                              <span>View</span>
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Bottom Thumbnail Strip (Filmstrip) */}
      {showFilmstrip && (
        <div
          className="flex-shrink-0 mt-2 p-3 rounded"
          style={{
            background: 'var(--panel)',
            border: '1.5px solid var(--line)',
            boxShadow: '2px 3px 0px rgba(0, 0, 0, 0.2)',
          }}
        >
          <div
            ref={filmstripRef}
            className="flex items-center gap-3 overflow-x-auto py-1 px-1"
            style={{ maxHeight: '115px' }}
          >
            {allIds.map((pId, idx) => {
              const pInfo = photos[pId];
              const thumbUrl = pInfo?.thumb || `/thumbs/${pId}.jpg`;
              const isActive = pId === photoId;

              return (
                <div
                  key={pId}
                  data-filmstrip-id={pId}
                  onClick={() => onNavigatePhoto(pId)}
                  className="flex-shrink-0 w-20 h-20 sm:w-24 sm:h-24 rounded overflow-hidden cursor-pointer transition-all"
                  style={{
                    background: 'var(--input)',
                    border: isActive ? '2.5px solid var(--accent)' : '1.5px solid var(--line)',
                    opacity: isActive ? 1 : 0.65,
                    transform: isActive ? 'scale(1.05)' : 'none',
                    boxShadow: isActive ? '0 0 0 2px var(--bg)' : 'none',
                  }}
                  title={`${pInfo?.file_name || pId} (${idx + 1} of ${allIds.length})`}
                >
                  <img
                    src={thumbUrl}
                    alt={pId}
                    loading="lazy"
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src =
                        'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%2327272a"><rect width="24" height="24"/></svg>';
                    }}
                  />
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
