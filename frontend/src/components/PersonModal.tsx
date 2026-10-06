import React, { useState } from 'react';
import { PersonCluster, PhotoInfo } from '../types';
import { X, EyeOff, Edit2, Check, Trash2, Image, UserX } from 'lucide-react';

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

  const displayName = person.label || person.id.toUpperCase();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 overflow-y-auto animate-fadeIn">
      <div className="relative w-full max-w-3xl bg-neutral-900 border border-neutral-800 rounded-2xl shadow-2xl overflow-hidden my-8">
        {/* Header */}
        <div className="p-5 border-b border-neutral-800 flex items-center justify-between bg-neutral-950/60">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-xl overflow-hidden border border-neutral-700/80 bg-neutral-800 flex-shrink-0">
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
                    className="px-2.5 py-1 text-sm rounded-lg bg-neutral-950 border border-blue-500 text-white focus:outline-none"
                  />
                  <button
                    onClick={handleSaveLabel}
                    className="p-1 rounded-lg bg-blue-600 hover:bg-blue-500 text-white"
                    title="Save"
                  >
                    <Check className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setIsEditingLabel(false)}
                    className="p-1 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-neutral-400"
                    title="Cancel"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <h3 className="text-lg font-bold text-white tracking-tight">{displayName}</h3>
                  <button
                    onClick={() => {
                      setLabelInput(person.label || '');
                      setIsEditingLabel(true);
                    }}
                    className="p-1 text-neutral-400 hover:text-neutral-200 transition-colors"
                    title="Rename"
                  >
                    <Edit2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}
              <div className="flex items-center gap-2 mt-1 text-xs text-neutral-400">
                <span className="font-mono text-neutral-500">Handle: {person.id}</span>
                <span>•</span>
                <span>{person.photos.length} photos</span>
                <span>•</span>
                <span>{person.faces.length} detected faces</span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => onHide(person.id)}
              className="px-3 py-1.5 rounded-xl bg-neutral-800 hover:bg-amber-950/60 text-neutral-300 hover:text-amber-300 border border-neutral-700 hover:border-amber-700/50 text-xs font-medium flex items-center gap-1.5 transition-colors"
              title="Hide this person from public export"
            >
              <EyeOff className="w-3.5 h-3.5" />
              <span>Hide</span>
            </button>
            <button
              onClick={onClose}
              className="p-2 rounded-xl text-neutral-400 hover:text-white hover:bg-neutral-800 transition-colors"
              title="Close modal"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Tabs: Photos vs Faces */}
        <div className="flex items-center gap-4 px-6 pt-4 border-b border-neutral-800 bg-neutral-900/40 text-xs font-medium">
          <button
            onClick={() => setActiveTab('photos')}
            className={`pb-3 border-b-2 flex items-center gap-1.5 transition-colors ${
              activeTab === 'photos'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-neutral-400 hover:text-neutral-200'
            }`}
          >
            <Image className="w-3.5 h-3.5" />
            <span>Photos ({person.photos.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('faces')}
            className={`pb-3 border-b-2 flex items-center gap-1.5 transition-colors ${
              activeTab === 'faces'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-neutral-400 hover:text-neutral-200'
            }`}
          >
            <UserX className="w-3.5 h-3.5" />
            <span>Faces ({person.faces.length})</span>
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 max-h-[60vh] overflow-y-auto">
          {activeTab === 'photos' ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
              {person.photos.map((photoId) => {
                const pInfo = photos[photoId];
                const thumbUrl = pInfo?.thumb || `thumbs/${photoId}.jpg`;
                const fileName = pInfo?.file_name || `${photoId}.jpg`;
                return (
                  <div
                    key={photoId}
                    className="group relative rounded-xl overflow-hidden bg-neutral-950 border border-neutral-800 aspect-square flex flex-col justify-end"
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
                    <div className="relative z-10 p-2 bg-gradient-to-t from-black/90 via-black/50 to-transparent flex items-center justify-between">
                      <span className="text-[10px] text-neutral-300 font-mono truncate max-w-[100px]" title={fileName}>
                        {fileName}
                      </span>
                      <button
                        onClick={() => onRemovePhoto(person.id, photoId)}
                        className="p-1 rounded bg-red-950/70 hover:bg-red-900 text-red-300 hover:text-red-100 transition-colors opacity-90 group-hover:opacity-100"
                        title="Remove photo from person"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {person.faces.map((face) => (
                <div
                  key={face.face_id}
                  className="rounded-xl p-3 bg-neutral-950 border border-neutral-800 flex flex-col items-center text-center relative group"
                >
                  <div className="w-16 h-16 rounded-xl overflow-hidden bg-neutral-900 mb-2 border border-neutral-800">
                    <img
                      src={`faces/${face.face_id}.jpg`}
                      alt={face.face_id}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src = person.face;
                      }}
                    />
                  </div>
                  <span className="text-[10px] font-mono text-neutral-400 truncate w-full" title={face.face_id}>
                    {face.face_id}
                  </span>
                  {face.det_score !== null && face.det_score !== undefined && (
                    <span className="text-[10px] text-neutral-500 font-mono mt-0.5">
                      score: {face.det_score.toFixed(2)}
                    </span>
                  )}
                  <button
                    onClick={() => onRemoveFace(person.id, face.face_id)}
                    className="mt-2.5 w-full py-1 px-2 rounded-lg bg-red-950/50 hover:bg-red-900/60 text-red-300 border border-red-800/40 text-[10px] font-medium flex items-center justify-center gap-1 transition-colors"
                  >
                    <Trash2 className="w-3 h-3" />
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
