import React, { useState, useEffect } from 'react';
import { PersonCluster, PhotoInfo } from '../types';
import { X, EyeOff, Edit2, Check, Trash2, Image, UserX, Download } from 'lucide-react';

interface PersonModalProps {
  person: PersonCluster;
  photos: Record<string, PhotoInfo>;
  onClose: () => void;
  onRename: (personId: string, newLabel: string) => void;
  onHide: (personId: string) => void;
  onRemoveFace: (personId: string, faceId: string) => void;
  onRemovePhoto: (personId: string, photoId: string) => void;
  onOpenPhotoViewer: (photoId: string) => void;
}

export const PersonModal: React.FC<PersonModalProps> = ({
  person,
  photos,
  onClose,
  onRename,
  onHide,
  onRemoveFace,
  onRemovePhoto,
  onOpenPhotoViewer,
}) => {
  const [isEditingLabel, setIsEditingLabel] = useState(false);
  const [labelInput, setLabelInput] = useState(person.label || '');
  const [activeTab, setActiveTab] = useState<'photos' | 'faces'>('photos');

  const handleSaveLabel = () => {
    onRename(person.id, labelInput.trim());
    setIsEditingLabel(false);
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  const displayName = person.label || person.id.toUpperCase();

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto animate-fadeIn"
      style={{ background: 'rgba(0, 0, 0, 0.85)', backdropFilter: 'blur(8px)' }}
    >
      <div
        className="relative w-full max-w-3xl rounded overflow-hidden my-8"
        style={{
          background: 'var(--panel)',
          border: '2px solid var(--line)',
          boxShadow: '4px 6px 0px rgba(0, 0, 0, 0.35)',
          color: 'var(--text)',
          fontFamily: "'JetBrains Mono', monospace",
        }}
      >
        {/* Header */}
        <div
          className="p-5 sm:p-6 flex items-center justify-between"
          style={{
            background: 'var(--card-bg)',
            borderBottom: '1.5px solid var(--line)',
          }}
        >
          <div className="flex items-center gap-4">
            <div
              className="w-18 h-18 sm:w-20 sm:h-20 rounded overflow-hidden flex-shrink-0"
              style={{
                border: '2.5px solid var(--accent)',
                background: 'var(--input)',
                boxShadow: '2px 2px 0px rgba(0,0,0,0.2)',
              }}
            >
              <img
                src={person.face}
                alt={displayName}
                className="w-full h-full object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).src =
                    'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%2371717a"><circle cx="12" cy="8" r="5"/><path d="M20 21a8 8 0 1 0-16 0"/></svg>';
                }}
              />
            </div>

            <div>
              {isEditingLabel ? (
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    value={labelInput}
                    onChange={(e) => setLabelInput(e.target.value)}
                    placeholder="Enter person name"
                    autoFocus
                    className="riso-input px-3 py-1.5 text-base"
                    style={{ height: '40px' }}
                  />
                  <button
                    onClick={handleSaveLabel}
                    className="btn pri"
                    style={{ height: '40px', padding: '0 14px', borderRadius: '4px' }}
                    title="Save"
                  >
                    <Check className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setIsEditingLabel(false)}
                    className="riso-btn-sec"
                    style={{ height: '40px', padding: '0 12px' }}
                    title="Cancel"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-2.5">
                  <h3 className="text-xl sm:text-2xl font-bold tracking-tight" style={{ color: 'var(--text)' }}>
                    {displayName}
                  </h3>
                  <button
                    onClick={() => {
                      setLabelInput(person.label || '');
                      setIsEditingLabel(true);
                    }}
                    className="riso-btn-sec"
                    style={{ width: '32px', height: '32px', padding: 0 }}
                    title="Rename"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
              <div className="flex items-center gap-2 mt-1.5 text-sm" style={{ color: 'var(--muted)' }}>
                <span className="font-mono">ID: {person.id}</span>
                <span>•</span>
                <span>{person.photos.length} photos</span>
                <span>•</span>
                <span>{person.faces.length} detected faces</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2.5">
            <a
              href={`/api/people/${person.id}/download-zip`}
              download={`${(person.label || person.id).replace(/[^a-zA-Z0-9_-]/g, '_')}_photos.zip`}
              className="btn pri flex items-center gap-1.5"
              style={{
                height: '40px',
                padding: '0 14px',
                borderRadius: '4px',
                textDecoration: 'none',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                fontWeight: 'bold',
                fontSize: '13px',
              }}
              title="Download all photos for this person in full resolution as a ZIP archive"
            >
              <Download className="w-4 h-4" />
              <span>Download ZIP</span>
            </a>
            <button
              onClick={() => onHide(person.id)}
              className="riso-btn-sec"
              style={{ height: '40px', padding: '0 14px' }}
              title="Hide this person from public export"
            >
              <EyeOff className="w-4 h-4" />
              <span>Hide</span>
            </button>
            <button
              onClick={onClose}
              className="riso-btn-sec"
              style={{ width: '40px', height: '40px', padding: 0 }}
              title="Close modal"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Tabs: Photos vs Faces */}
        <div
          className="flex items-center gap-6 px-6 pt-4 text-sm font-bold"
          style={{
            background: 'var(--card-bg)',
            borderBottom: '1.5px solid var(--line)',
          }}
        >
          <button
            onClick={() => setActiveTab('photos')}
            className="pb-3 flex items-center gap-2 transition-all cursor-pointer"
            style={{
              background: 'transparent',
              border: 'none',
              borderBottom: activeTab === 'photos' ? '2.5px solid var(--accent)' : '2.5px solid transparent',
              color: activeTab === 'photos' ? 'var(--accent)' : 'var(--muted)',
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '15px',
            }}
          >
            <Image className="w-4 h-4" />
            <span>Photos ({person.photos.length})</span>
          </button>
          <button
            id="modal-tab-faces"
            onClick={() => setActiveTab('faces')}
            className="pb-3 flex items-center gap-2 transition-all cursor-pointer"
            style={{
              background: 'transparent',
              border: 'none',
              borderBottom: activeTab === 'faces' ? '2.5px solid var(--accent)' : '2.5px solid transparent',
              color: activeTab === 'faces' ? 'var(--accent)' : 'var(--muted)',
              fontFamily: "'JetBrains Mono', monospace",
              fontSize: '15px',
            }}
          >
            <UserX className="w-4 h-4" />
            <span>Faces ({person.faces.length})</span>
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 max-h-[60vh] overflow-y-auto">
          {activeTab === 'photos' ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
              {person.photos.map((photoId) => {
                const pInfo = photos[photoId];
                const thumbUrl = pInfo?.thumb || `thumbs/${photoId}.jpg`;
                const fileName = pInfo?.file_name || `${photoId}.jpg`;
                return (
                  <div
                    key={photoId}
                    className="group relative rounded overflow-hidden aspect-square flex flex-col justify-end"
                    style={{
                      background: 'var(--input)',
                      border: '1.5px solid var(--line)',
                      boxShadow: '2px 2px 0px rgba(0,0,0,0.15)',
                    }}
                  >
                    <img
                      src={thumbUrl}
                      alt={fileName}
                      loading="lazy"
                      onClick={() => onOpenPhotoViewer(photoId)}
                      className="absolute inset-0 w-full h-full object-cover cursor-pointer group-hover:scale-105 transition-transform duration-200"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src =
                          'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%2327272a"><rect width="24" height="24"/></svg>';
                      }}
                    />
                    <div
                      className="relative z-10 p-2 flex items-center justify-between gap-1"
                      style={{ background: 'var(--card-bg)', borderTop: '1px solid var(--line)' }}
                    >
                      <div className="flex items-center gap-1.5 min-w-0">
                        <span className="text-xs font-mono font-bold truncate max-w-[120px]" style={{ color: 'var(--text)' }} title={fileName}>
                          {fileName}
                        </span>
                        {pInfo?.source_label && (
                          <span
                            id={`photo-source-badge-${photoId}`}
                            data-testid={`photo-source-badge-${photoId}`}
                            className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded flex-shrink-0"
                            style={{
                              background: 'rgba(0,0,0,0.65)',
                              color: 'var(--accent)',
                              border: '1px solid var(--accent)',
                            }}
                            title={`Source: ${pInfo.source_label}`}
                          >
                            {pInfo.source_label}
                          </span>
                        )}
                      </div>
                      <button
                        onClick={() => onRemovePhoto(person.id, photoId)}
                        className="p-1 rounded text-red-400 hover:text-red-300 transition-colors flex-shrink-0"
                        style={{ background: 'transparent', border: 'none', cursor: 'pointer' }}
                        title="Remove photo from person"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
              {person.faces.map((face) => (
                <div
                  key={face.face_id}
                  className="rounded p-4 flex flex-col items-center text-center relative group"
                  style={{
                    background: 'var(--card-bg)',
                    border: '1.5px solid var(--line)',
                    boxShadow: '2px 2px 0px rgba(0,0,0,0.15)',
                  }}
                >
                  <div
                    className="w-20 h-20 rounded overflow-hidden mb-2.5"
                    style={{
                      background: 'var(--input)',
                      border: '1.5px solid var(--line)',
                    }}
                  >
                    <img
                      src={`faces/${face.face_id}.jpg`}
                      alt={face.face_id}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = person.face;
                      }}
                    />
                  </div>
                  <span className="text-xs font-mono font-bold truncate w-full" style={{ color: 'var(--text)' }} title={face.face_id}>
                    {face.face_id}
                  </span>
                  {face.det_score !== null && face.det_score !== undefined && (
                    <span className="text-xs font-mono mt-0.5" style={{ color: 'var(--muted)' }}>
                      score: {face.det_score.toFixed(2)}
                    </span>
                  )}
                  <button
                    onClick={() => onRemoveFace(person.id, face.face_id)}
                    className="mt-3 w-full py-1.5 px-2 rounded text-xs font-bold flex items-center justify-center gap-1.5 transition-colors"
                    style={{
                      background: 'var(--input)',
                      border: '1px solid var(--line)',
                      color: 'var(--accent)',
                      cursor: 'pointer',
                    }}
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Remove Face</span>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
