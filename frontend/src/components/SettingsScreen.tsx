import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Settings } from '../types';
import { Sliders, RefreshCw, Key, HardDrive, CheckCircle2, AlertTriangle, ShieldCheck } from 'lucide-react';

interface SettingsScreenProps {
  onRerunComplete?: () => void;
}

export const SettingsScreen: React.FC<SettingsScreenProps> = ({ onRerunComplete }) => {
  const [settings, setSettings] = useState<Settings>({
    output_dir: 'export',
    distance_threshold: 0.50,
    min_det_score: 0.50,
    min_face_size: 64,
    max_yaw: 70,
    seed_min_det_score: 0.70,
    seed_min_face_size: 64,
    seed_max_yaw: 60,
    max_image_dim: 1600,
    thumb_size: 400,
    face_crop_size: 256,
    second_pass_merge: true,
    merge_threshold: 0.50,
    maybe_threshold: 0.65,
    same_photo_merge_max: 0.40,
    attach_distance_cap: 0.45,
    flip_average: false,
    include_maybe: false,
    event_title: 'Face Clubbing Gallery',
    event_subtitle: 'Auto-sorted face albums and photo gallery',
  });

  const [apiKey, setApiKey] = useState(() => {
    return sessionStorage.getItem('drive_api_key_ephemeral') || '';
  });
  const [storageLevel, setStorageLevel] = useState('local');
  const [isLoading, setIsLoading] = useState(false);
  const [isRerunning, setIsRerunning] = useState(false);
  const [rerunResult, setRerunResult] = useState<{
    success: boolean;
    applied_count: number;
    unapplied_edits: Array<Record<string, any>>;
    people_count: number;
    unrecognized_photos_count: number;
    unrecognized_faces_count: number;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setIsLoading(true);
    api.getSettings()
      .then((s) => setSettings((prev) => ({ ...prev, ...s })))
      .catch((err) => console.error('Failed to load settings:', err))
      .finally(() => setIsLoading(false));
  }, []);

  const handleApiKeyChange = (val: string) => {
    setApiKey(val);
    // Never persist to backend; store only in browser session storage
    if (val) {
      sessionStorage.setItem('drive_api_key_ephemeral', val);
    } else {
      sessionStorage.removeItem('drive_api_key_ephemeral');
    }
  };

  const handleSaveAndRerun = async () => {
    setIsRerunning(true);
    setError(null);
    setRerunResult(null);
    try {
      // 1. Update settings on server
      await api.updateSettings(settings);

      // 2. Trigger rerun pipeline with edit replay
      const result = await api.rerun({
        distance_threshold: settings.distance_threshold,
        merge_threshold: settings.merge_threshold,
        maybe_threshold: settings.maybe_threshold,
        same_photo_merge_max: settings.same_photo_merge_max,
        seed_min_det_score: settings.seed_min_det_score,
        seed_min_face_size: settings.seed_min_face_size,
        thumb_size: settings.thumb_size,
        face_crop_size: settings.face_crop_size,
        second_pass_merge: settings.second_pass_merge,
        flip_average: settings.flip_average,
      });

      setRerunResult(result);
      if (onRerunComplete) {
        onRerunComplete();
      }
    } catch (err: any) {
      setError(err.message || 'Rerun failed');
    } finally {
      setIsRerunning(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fadeIn pb-24">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
          <Sliders className="w-6 h-6 text-accent" />
          Clustering & Pipeline Settings
        </h2>
        <p className="text-sm text-neutral-400 mt-1">
          Tune clustering parameters (SPEC 6.2 defaults). Changing any clustering parameter triggers an automatic re-clustering with full edit replay.
        </p>
      </div>

      {/* Section 1: Clustering Sensitivity (SPEC 6.2 parameters) */}
      <div className="glass-card p-6 rounded-2xl space-y-6">
        <div className="flex items-center justify-between border-b border-neutral-800 pb-3">
          <h3 className="text-base font-semibold text-white">Clustering Sensitivity (SPEC 6.2)</h3>
          <span className="text-xs text-neutral-500 font-mono">Agglomerative Average Linkage</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Distance Threshold */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <label htmlFor="setting-distance-threshold" className="font-semibold text-neutral-300">
                Primary Distance Cutoff (`distance_threshold`)
              </label>
              <span id="setting-distance-threshold-val" className="font-mono text-accent font-bold">
                {settings.distance_threshold.toFixed(2)}
              </span>
            </div>
            <input
              id="setting-distance-threshold"
              type="range"
              min="0.30"
              max="0.65"
              step="0.01"
              value={settings.distance_threshold}
              onChange={(e) =>
                setSettings({ ...settings, distance_threshold: parseFloat(e.target.value) })
              }
              className="w-full accent-accent h-1.5 bg-neutral-800 rounded-lg cursor-pointer"
            />
            <p className="text-[11px] text-neutral-500">
              Cosine distance cutoff for seed face clustering. Default: 0.50. Lower values produce stricter, smaller clusters.
            </p>
          </div>

          {/* Merge Threshold */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <label htmlFor="setting-merge-threshold" className="font-semibold text-neutral-300">
                Second-Pass Merge Cutoff (`merge_threshold`)
              </label>
              <span id="setting-merge-threshold-val" className="font-mono text-accent font-bold">
                {settings.merge_threshold.toFixed(2)}
              </span>
            </div>
            <input
              id="setting-merge-threshold"
              type="range"
              min="0.30"
              max="0.60"
              step="0.01"
              value={settings.merge_threshold}
              onChange={(e) =>
                setSettings({ ...settings, merge_threshold: parseFloat(e.target.value) })
              }
              className="w-full accent-accent h-1.5 bg-neutral-800 rounded-lg cursor-pointer"
            />
            <p className="text-[11px] text-neutral-500">
              Centroid distance cutoff for automatic second-pass duplicate reduction. Default: 0.50.
            </p>
          </div>

          {/* Maybe Threshold */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <label htmlFor="setting-maybe-threshold" className="font-semibold text-neutral-300">
                Suggestion Range Cap (`maybe_threshold`)
              </label>
              <span id="setting-maybe-threshold-val" className="font-mono text-amber-400 font-bold">
                {settings.maybe_threshold.toFixed(2)}
              </span>
            </div>
            <input
              id="setting-maybe-threshold"
              type="range"
              min="0.50"
              max="0.75"
              step="0.01"
              value={settings.maybe_threshold}
              onChange={(e) =>
                setSettings({ ...settings, maybe_threshold: parseFloat(e.target.value) })
              }
              className="w-full accent-amber-400 h-1.5 bg-neutral-800 rounded-lg cursor-pointer"
            />
            <p className="text-[11px] text-neutral-500">
              Upper centroid distance for suggestion pair generation. Default: 0.65 (rev 2).
            </p>
          </div>

          {/* Same-photo guard */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <label htmlFor="setting-same-photo-guard" className="font-semibold text-neutral-300">
                Same-Photo Guard Cap (`same_photo_merge_max`)
              </label>
              <span id="setting-same-photo-guard-val" className="font-mono text-neutral-300 font-bold">
                {settings.same_photo_merge_max.toFixed(2)}
              </span>
            </div>
            <input
              id="setting-same-photo-guard"
              type="range"
              min="0.20"
              max="0.50"
              step="0.01"
              value={settings.same_photo_merge_max}
              onChange={(e) =>
                setSettings({ ...settings, same_photo_merge_max: parseFloat(e.target.value) })
              }
              className="w-full accent-neutral-300 h-1.5 bg-neutral-800 rounded-lg cursor-pointer"
            />
            <p className="text-[11px] text-neutral-500">
              Blocks merging clusters if two faces from one photo exceed this distance. Default: 0.40.
            </p>
          </div>
        </div>

        {/* Toggles */}
        <div className="pt-2 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <label className="flex items-center gap-3 p-3 rounded-xl bg-neutral-900 border border-neutral-800 cursor-pointer hover:border-neutral-700">
            <input
              id="setting-second-pass-toggle"
              type="checkbox"
              checked={settings.second_pass_merge}
              onChange={(e) =>
                setSettings({ ...settings, second_pass_merge: e.target.checked })
              }
              className="w-4 h-4 rounded border-neutral-700 bg-neutral-950 text-accent focus:ring-accent"
            />
            <div>
              <p className="text-xs font-semibold text-white">Enable Second-Pass Centroid Merge</p>
              <p className="text-[10px] text-neutral-400">Merges split clusters automatically with same-photo collision check</p>
            </div>
          </label>

          <label className="flex items-center gap-3 p-3 rounded-xl bg-neutral-900 border border-neutral-800 cursor-pointer hover:border-neutral-700">
            <input
              id="setting-flip-average-toggle"
              type="checkbox"
              checked={settings.flip_average}
              onChange={(e) =>
                setSettings({ ...settings, flip_average: e.target.checked })
              }
              className="w-4 h-4 rounded border-neutral-700 bg-neutral-950 text-accent focus:ring-accent"
            />
            <div>
              <p className="text-xs font-semibold text-white">Flip-Averaged Embeddings</p>
              <p className="text-[10px] text-neutral-400">Averages horizontal mirrored embeddings (default: false)</p>
            </div>
          </label>
        </div>
      </div>

      {/* Section 2: Visual & Image Sizing */}
      <div className="glass-card p-6 rounded-2xl space-y-4">
        <h3 className="text-base font-semibold text-white border-b border-neutral-800 pb-3">
          Asset Generation Sizes
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label htmlFor="setting-thumb-size" className="block text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-1.5">
              Photo Thumbnail Dimension (px)
            </label>
            <select
              id="setting-thumb-size"
              value={settings.thumb_size}
              onChange={(e) => setSettings({ ...settings, thumb_size: parseInt(e.target.value, 10) })}
              className="w-full px-4 py-2.5 bg-neutral-900 border border-neutral-800 rounded-xl text-neutral-200 text-sm focus:outline-none focus:border-accent"
            >
              <option value="300">300 px (Compact)</option>
              <option value="400">400 px (Default SPEC 6.2)</option>
              <option value="500">500 px (High Quality)</option>
              <option value="600">600 px (Ultra HD)</option>
            </select>
          </div>

          <div>
            <label htmlFor="setting-face-crop-size" className="block text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-1.5">
              Face Crop Dimension (px)
            </label>
            <select
              id="setting-face-crop-size"
              value={settings.face_crop_size}
              onChange={(e) =>
                setSettings({ ...settings, face_crop_size: parseInt(e.target.value, 10) })
              }
              className="w-full px-4 py-2.5 bg-neutral-900 border border-neutral-800 rounded-xl text-neutral-200 text-sm focus:outline-none focus:border-accent"
            >
              <option value="192">192 px (Compact)</option>
              <option value="256">256 px (Default SPEC 6.2)</option>
              <option value="320">320 px (High Detail)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Section 3: Google Drive API Key & Method 2 Storage Stub */}
      <div className="glass-card p-6 rounded-2xl space-y-5">
        <h3 className="text-base font-semibold text-white border-b border-neutral-800 pb-3 flex items-center justify-between">
          <span>Drive Integration & Storage</span>
          <span className="px-2 py-0.5 rounded text-[10px] bg-neutral-800 text-neutral-400 font-semibold uppercase">
            Phase 6 Preview
          </span>
        </h3>

        {/* API Key */}
        <div className="space-y-1.5">
          <label htmlFor="setting-api-key" className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-400">
            <Key className="w-3.5 h-3.5 text-amber-400" />
            <span>Google Drive API Key</span>
          </label>
          <input
            id="setting-api-key"
            type="password"
            value={apiKey}
            onChange={(e) => handleApiKeyChange(e.target.value)}
            placeholder="AIzaSy... (Client-only / Ephemeral)"
            className="w-full px-4 py-2.5 bg-neutral-900 border border-neutral-800 rounded-xl text-neutral-200 text-sm focus:outline-none focus:border-accent font-mono"
          />
          <div className="flex items-center gap-1.5 text-[11px] text-neutral-500 pt-0.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />
            <span>Security guarantee: Stored in browser session memory only. Never written to git or backend files. Phase 6 will use it for Drive queries.</span>
          </div>
        </div>

        {/* Method 2 Storage-Level Selector marked "stub" */}
        <div className="space-y-1.5 pt-2">
          <div className="flex items-center justify-between">
            <label htmlFor="setting-storage-level" className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-400">
              <HardDrive className="w-3.5 h-3.5 text-blue-400" />
              <span>Storage Level (Method 2 Architecture)</span>
            </label>
            <span id="storage-selector-stub-badge" className="px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 text-[10px] font-bold border border-blue-500/30">
              STUB
            </span>
          </div>
          <select
            id="setting-storage-level"
            value={storageLevel}
            onChange={(e) => setStorageLevel(e.target.value)}
            className="w-full px-4 py-2.5 bg-neutral-900 border border-neutral-800 rounded-xl text-neutral-200 text-sm focus:outline-none focus:border-accent"
          >
            <option value="local">Method 1: Local Only (default bundle export)</option>
            <option value="drive-readonly">Drive Read-Only (Attendee download links only)</option>
            <option value="drive-method2-stub" disabled>
              Method 2: Google Drive Auto-Upload [STUB - Phase 6]
            </option>
          </select>
          <p className="text-[11px] text-neutral-500">
            Method 2 allows uploading generated bundles directly into the organizer's Google Drive folder.
          </p>
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="p-4 rounded-xl bg-red-950/60 border border-red-800 text-red-300 text-xs flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Rerun Result Feedback */}
      {rerunResult && (
        <div
          id="rerun-result-summary"
          className="glass-card p-6 rounded-2xl space-y-4 border border-emerald-500/40 bg-emerald-950/20 animate-scaleUp"
        >
          <div className="flex items-center gap-3 text-emerald-400">
            <CheckCircle2 className="w-6 h-6 flex-shrink-0" />
            <div>
              <h3 className="text-base font-semibold text-white">Re-clustering Completed with Edit Replay</h3>
              <p className="text-xs text-neutral-300 mt-0.5">
                Clustering rerun finished. {rerunResult.applied_count} edits successfully replayed by face ID.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3 pt-2">
            <div className="p-3 rounded-xl bg-neutral-900/80 border border-neutral-800 text-center">
              <span className="text-xs text-neutral-400">People</span>
              <p id="rerun-stat-people" className="text-lg font-bold text-white mt-0.5">{rerunResult.people_count}</p>
            </div>
            <div className="p-3 rounded-xl bg-neutral-900/80 border border-neutral-800 text-center">
              <span className="text-xs text-neutral-400">Unrecognized Faces</span>
              <p id="rerun-stat-unrec" className="text-lg font-bold text-white mt-0.5">{rerunResult.unrecognized_faces_count}</p>
            </div>
            <div className="p-3 rounded-xl bg-neutral-900/80 border border-neutral-800 text-center">
              <span className="text-xs text-neutral-400">Replayed Edits</span>
              <p id="rerun-stat-edits" className="text-lg font-bold text-emerald-400 mt-0.5">{rerunResult.applied_count}</p>
            </div>
          </div>

          {/* Unapplied edits list if any */}
          {rerunResult.unapplied_edits && rerunResult.unapplied_edits.length > 0 ? (
            <div id="unapplied-edits-box" className="p-4 rounded-xl bg-amber-950/40 border border-amber-800/80 space-y-2">
              <p className="text-xs font-semibold text-amber-300 flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4" />
                {rerunResult.unapplied_edits.length} edit(s) could not be re-applied:
              </p>
              <ul className="text-xs text-neutral-300 list-disc list-inside space-y-1 font-mono">
                {rerunResult.unapplied_edits.map((item, idx) => (
                  <li key={idx}>
                    {item.op}: {item.reason || JSON.stringify(item)}
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <p id="all-edits-survived-msg" className="text-xs text-emerald-400 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" />
              All organizer edits survived and were re-applied by stable face ID anchors!
            </p>
          )}
        </div>
      )}

      {/* Action Button */}
      <div className="pt-2">
        <button
          id="save-rerun-btn"
          disabled={isRerunning || isLoading}
          onClick={handleSaveAndRerun}
          className={`w-full py-3.5 rounded-xl font-semibold text-sm flex items-center justify-center gap-2.5 transition-all shadow-lg ${
            isRerunning || isLoading
              ? 'bg-neutral-800 text-neutral-500 cursor-not-allowed'
              : 'bg-accent text-white hover:brightness-110 shadow-accent/20 cursor-pointer'
          }`}
        >
          <RefreshCw className={`w-4 h-4 ${isRerunning ? 'animate-spin' : ''}`} />
          <span>{isRerunning ? 'Re-running Pipeline & Replaying Edits...' : 'Save & Rerun Clustering'}</span>
        </button>
      </div>
    </div>
  );
};
