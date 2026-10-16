import React from 'react';
import { PersonCluster, PhotoInfo } from '../types';
import { X, Check, UserCheck, AlertCircle, Sparkles } from 'lucide-react';

interface FaceCompareModalProps {
  unrecognizedFace: {
    faceId: string;
    faceUrl: string;
    photoId: string;
    fileName?: string;
    rejectionReason?: string | null;
  };
  targetPerson: PersonCluster;
  photos: Record<string, PhotoInfo>;
  onConfirm: (faceId: string, targetPersonId: string) => void;
  onClose: () => void;
  onOpenPhotoViewer?: (photoId: string) => void;
}

export const FaceCompareModal: React.FC<FaceCompareModalProps> = ({
  unrecognizedFace,
  targetPerson,
  photos,
  onConfirm,
  onClose,
  onOpenPhotoViewer,
}) => {
  const targetName = targetPerson.label || targetPerson.id;
  const sampleFaces = targetPerson.faces || [];
  const pInfo = photos[unrecognizedFace.photoId];
  const photoFileName = pInfo?.file_name || unrecognizedFace.fileName || `${unrecognizedFace.photoId}.jpg`;

  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fadeIn"
      style={{ background: 'rgba(0, 0, 0, 0.85)', backdropFilter: 'blur(8px)' }}
    >
      <div
        className="relative w-full max-w-4xl overflow-hidden flex flex-col max-h-[92vh] rounded"
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
          <div className="flex items-center gap-3.5">
            <div
              className="w-11 h-11 rounded flex items-center justify-center flex-shrink-0"
              style={{
                background: 'var(--input)',
                border: '1.5px solid var(--accent)',
                color: 'var(--accent)',
              }}
            >
              <Sparkles className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg sm:text-xl font-bold" style={{ color: 'var(--text)' }}>
                Compare Face Before Merging
              </h3>
              <p className="text-sm mt-0.5" style={{ color: 'var(--muted)' }}>
                Verify if this unrecognized face matches <span style={{ color: 'var(--accent)', fontWeight: 700 }}>{targetName}</span>
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="riso-btn-sec"
            style={{ width: '40px', height: '40px', padding: 0 }}
            title="Close (Esc)"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body: Side-by-Side Comparison */}
        <div className="p-6 sm:p-8 overflow-y-auto space-y-6 flex-1">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-stretch">
            {/* Left: Unrecognized Face Card */}
            <div
              className="p-6 rounded flex flex-col items-center text-center justify-between"
              style={{
                background: 'var(--card-bg)',
                border: '1.5px solid var(--line)',
                boxShadow: '2px 3px 0px rgba(0, 0, 0, 0.2)',
              }}
            >
              <div className="w-full flex items-center justify-between mb-4">
                <span
                  className="font-bold uppercase tracking-wider text-xs flex items-center gap-1.5"
                  style={{ color: 'var(--accent)' }}
                >
                  <AlertCircle className="w-4 h-4" /> Unrecognized Face
                </span>
                <span className="riso-tab-badge">
                  {unrecognizedFace.rejectionReason || 'unattached'}
                </span>
              </div>

              {/* Large Face Image */}
              <div
                className="w-56 h-56 sm:w-64 sm:h-64 rounded overflow-hidden shadow-xl my-2 flex-shrink-0"
                style={{
                  background: 'var(--input)',
                  border: '2px solid var(--line)',
                }}
              >
                <img
                  src={unrecognizedFace.faceUrl}
                  alt={unrecognizedFace.faceId}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src =
                      'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%2371717a"><circle cx="12" cy="8" r="5"/><path d="M20 21a8 8 0 1 0-16 0"/></svg>';
                  }}
                />
              </div>

              <div className="mt-3 text-sm font-mono font-bold truncate max-w-full" style={{ color: 'var(--text)' }}>
                {unrecognizedFace.faceId}
              </div>

              {/* Source Photo link */}
              <div className="mt-2 text-xs" style={{ color: 'var(--muted)' }}>
                Source photo:{' '}
                <button
                  onClick={() => onOpenPhotoViewer && onOpenPhotoViewer(unrecognizedFace.photoId)}
                  className="hover:underline font-mono font-bold"
                  style={{ color: 'var(--accent)', background: 'transparent', border: 'none', cursor: 'pointer', padding: 0 }}
                  title="View full source photo"
                >
                  {photoFileName}
                </button>
              </div>
            </div>

            {/* Right: Target Person Card */}
            <div
              className="p-6 rounded flex flex-col items-center text-center justify-between"
              style={{
                background: 'var(--card-bg)',
                border: '2px solid var(--accent)',
                boxShadow: '2px 4px 0px rgba(0, 0, 0, 0.25)',
              }}
            >
              <div className="w-full flex items-center justify-between mb-4">
                <span
                  className="font-bold uppercase tracking-wider text-xs flex items-center gap-1.5"
                  style={{ color: 'var(--accent)' }}
                >
                  <UserCheck className="w-4 h-4" /> Target Person Cluster
                </span>
                <span className="riso-tab-badge">
                  {targetPerson.photo_count || targetPerson.photos?.length || 0} photos
                </span>
              </div>

              {/* Large Primary Face */}
              <div
                className="w-56 h-56 sm:w-64 sm:h-64 rounded overflow-hidden shadow-xl my-2 flex-shrink-0"
                style={{
                  background: 'var(--input)',
                  border: '2.5px solid var(--accent)',
                }}
              >
                <img
                  src={targetPerson.face}
                  alt={targetName}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    (e.target as HTMLImageElement).src =
                      'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%2371717a"><circle cx="12" cy="8" r="5"/><path d="M20 21a8 8 0 1 0-16 0"/></svg>';
                  }}
                />
              </div>

              <div className="mt-3 text-base sm:text-lg font-bold font-mono truncate max-w-full" style={{ color: 'var(--text)' }}>
                {targetName}
              </div>
              <div className="text-xs font-mono" style={{ color: 'var(--muted)' }}>{targetPerson.id}</div>

              {/* Gallery of other faces for this person */}
              {sampleFaces.length > 1 && (
                <div className="mt-4 w-full">
                  <div className="text-xs font-bold uppercase tracking-wider mb-2 text-left" style={{ color: 'var(--muted)' }}>
                    Other Face Crops in Cluster ({sampleFaces.length}):
                  </div>
                  <div className="flex items-center gap-2 overflow-x-auto py-1">
                    {sampleFaces.slice(0, 6).map((f) => (
                      <div
                        key={f.face_id}
                        className="w-14 h-14 rounded overflow-hidden flex-shrink-0"
                        style={{ border: '1.5px solid var(--line)', background: 'var(--input)' }}
                        title={f.face_id}
                      >
                        <img
                          src={`/faces/${f.face_id}.jpg`}
                          alt=""
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            (e.target as HTMLImageElement).src = targetPerson.face;
                          }}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div
          className="p-5 flex items-center justify-between gap-4"
          style={{
            background: 'var(--card-bg)',
            borderTop: '1.5px solid var(--line)',
          }}
        >
          <button
            onClick={onClose}
            className="riso-btn-sec"
            style={{ height: '46px', padding: '0 24px', fontSize: '15px' }}
          >
            Cancel
          </button>

          <button
            onClick={() => onConfirm(unrecognizedFace.faceId, targetPerson.id)}
            className="btn pri"
            style={{
              height: '46px',
              padding: '0 28px',
              borderRadius: '4px',
              fontSize: '15px',
              fontWeight: 800,
              boxShadow: '2px 3px 0px rgba(0,0,0,0.25)',
            }}
          >
            <Check className="w-5 h-5 mr-1" />
            <span>Confirm: Assign Face to {targetName}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
