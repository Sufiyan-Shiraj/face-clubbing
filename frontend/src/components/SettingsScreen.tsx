import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Settings } from '../types';
import { Sliders, RefreshCw, Key, CheckCircle2, AlertTriangle, ShieldCheck, HelpCircle, ExternalLink, Save, Trash2 } from 'lucide-react';

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

  const [driveKeyInput, setDriveKeyInput] = useState('');
  const [isSavingKey, setIsSavingKey] = useState(false);
  const [keySavedMessage, setKeySavedMessage] = useState<string | null>(null);
  const [showGuide, setShowGuide] = useState(true);
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

  const handleSaveDriveKey = async () => {
    if (!driveKeyInput.trim()) return;
    setIsSavingKey(true);
    setError(null);
    setKeySavedMessage(null);
    try {
      await api.updateSettings({ drive_api_key: driveKeyInput.trim() });
      const updated = await api.getSettings();
      setSettings((prev) => ({ ...prev, ...updated }));
      setDriveKeyInput('');
      setKeySavedMessage('Drive API key saved to ~/.photosorter/settings.json (outside repository).');
      setTimeout(() => setKeySavedMessage(null), 5000);
    } catch (err: any) {
      setError(err.message || 'Failed to save Drive API key');
    } finally {
      setIsSavingKey(false);
    }
  };

  const handleClearDriveKey = async () => {
    setIsSavingKey(true);
    setError(null);
    setKeySavedMessage(null);
    try {
      await api.updateSettings({ drive_api_key: '' });
      const updated = await api.getSettings();
      setSettings((prev) => ({ ...prev, ...updated }));
      setDriveKeyInput('');
      setKeySavedMessage('Drive API key removed from local settings.');
      setTimeout(() => setKeySavedMessage(null), 5000);
    } catch (err: any) {
      setError(err.message || 'Failed to clear Drive API key');
    } finally {
      setIsSavingKey(false);
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

      {/* Section 3: Google Drive API Key */}
      <div className="glass-card p-6 rounded-2xl space-y-5">
        <div className="flex items-center justify-between border-b border-neutral-800 pb-3">
          <div className="flex items-center gap-2">
            <Key className="w-5 h-5 text-amber-400" />
            <h3 className="text-base font-semibold text-white">Google Drive API Key</h3>
          </div>
          {settings.drive_api_key_configured ? (
            <span
              id="drive-key-status-badge"
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-800"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Configured ({settings.drive_api_key_masked || 'Active'})</span>
            </span>
          ) : (
            <span
              id="drive-key-status-badge"
              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-950/80 text-amber-400 border border-amber-800"
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Not Configured</span>
            </span>
          )}
        </div>

        {keySavedMessage && (
          <div
            id="drive-key-saved-message"
            className="p-3.5 rounded-xl bg-emerald-950/60 border border-emerald-800 text-emerald-300 text-xs flex items-center gap-2 animate-fadeIn"
          >
            <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
            <span>{keySavedMessage}</span>
          </div>
        )}

        {/* API Key Input and Action Buttons */}
        <div className="space-y-3">
          <label htmlFor="setting-drive-api-key" className="block text-xs font-semibold uppercase tracking-wider text-neutral-400">
            {settings.drive_api_key_configured ? 'Update API Key' : 'Enter API Key'}
          </label>
          <div className="flex flex-col sm:flex-row gap-3">
            <input
              id="setting-drive-api-key"
              type="password"
              value={driveKeyInput}
              onChange={(e) => setDriveKeyInput(e.target.value)}
              placeholder={
                settings.drive_api_key_configured
                  ? `Configured (${settings.drive_api_key_masked || 'Hidden'}) - paste new key to update`
                  : 'AIzaSy... (free Google Cloud API key)'
              }
              className="flex-1 px-4 py-2.5 bg-neutral-900 border border-neutral-800 rounded-xl text-neutral-200 text-sm focus:outline-none focus:border-accent font-mono placeholder:text-neutral-600"
            />
            <div className="flex gap-2">
              <button
                id="save-drive-key-btn"
                type="button"
                onClick={handleSaveDriveKey}
                disabled={isSavingKey || !driveKeyInput.trim()}
                className={`px-4 py-2.5 rounded-xl font-semibold text-xs flex items-center gap-1.5 transition-all shadow-md ${
                  isSavingKey || !driveKeyInput.trim()
                    ? 'bg-neutral-800 text-neutral-500 cursor-not-allowed'
                    : 'bg-accent text-white hover:brightness-110 shadow-accent/20 cursor-pointer'
                }`}
              >
                <Save className="w-3.5 h-3.5" />
                <span>{isSavingKey ? 'Saving...' : 'Save Key'}</span>
              </button>
              {settings.drive_api_key_configured && (
                <button
                  id="clear-drive-key-btn"
                  type="button"
                  onClick={handleClearDriveKey}
                  disabled={isSavingKey}
                  className="px-3.5 py-2.5 rounded-xl font-semibold text-xs flex items-center gap-1.5 bg-red-950/40 hover:bg-red-950/80 text-red-300 border border-red-800/80 transition-all cursor-pointer"
                  title="Remove saved key from local settings"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Remove</span>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Security Guarantee */}
        <div className="flex items-start gap-2.5 p-3 rounded-xl bg-neutral-900/60 border border-neutral-800/80 text-[11px] text-neutral-400">
          <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold text-neutral-300">Security Guarantee: </span>
            Stored only in your local profile (<code className="text-neutral-300">~/.photosorter/settings.json</code>) or read from the <code className="text-neutral-300">DRIVE_API_KEY</code> environment variable. Never committed to git, never written to project files, never included in exports or client bundles, and masked in logs.
          </div>
        </div>

        {/* In-App Guide */}
        <div className="border border-neutral-800 rounded-xl overflow-hidden bg-neutral-900/40">
          <button
            type="button"
            onClick={() => setShowGuide(!showGuide)}
            className="w-full px-4 py-2.5 flex items-center justify-between text-xs font-semibold text-neutral-300 hover:text-white transition-colors"
          >
            <span className="flex items-center gap-2">
              <HelpCircle className="w-4 h-4 text-accent" />
              <span>How to get a free Google Drive API Key (3 minutes)</span>
            </span>
            <span className="text-[11px] text-neutral-500">{showGuide ? 'Hide Guide' : 'Show Guide'}</span>
          </button>

          {showGuide && (
            <div className="px-4 pb-4 pt-1 space-y-2.5 text-xs text-neutral-400 border-t border-neutral-800/60">
              <ol className="list-decimal list-inside space-y-2">
                <li>
                  Go to the{' '}
                  <a
                    href="https://console.cloud.google.com/"
                    target="_blank"
                    rel="noreferrer"
                    className="text-accent hover:underline inline-flex items-center gap-1 font-medium"
                  >
                    Google Cloud Console <ExternalLink className="w-3 h-3" />
                  </a>{' '}
                  and sign in with any Google account.
                </li>
                <li>
                  Click the project selector at the top and click <strong className="text-neutral-200">New Project</strong> (e.g. name it <code className="text-neutral-200">PhotoSorter</code>).
                </li>
                <li>
                  Go to <strong className="text-neutral-200">APIs &amp; Services &gt; Library</strong>, search for <strong className="text-neutral-200">Google Drive API</strong>, and click <strong className="text-neutral-200">Enable</strong>.
                </li>
                <li>
                  Go to <strong className="text-neutral-200">APIs &amp; Services &gt; Credentials</strong>, click <strong className="text-neutral-200">+ Create Credentials</strong>, and select <strong className="text-neutral-200">API key</strong>.
                </li>
                <li>
                  <strong className="text-neutral-300">(Recommended)</strong> Click <strong className="text-neutral-200">Edit API key</strong>, under <em className="text-neutral-300">API restrictions</em> select <strong className="text-neutral-200">Restrict key</strong> and choose <strong className="text-neutral-200">Google Drive API</strong>.
                </li>
                <li>
                  Paste the generated key above and click <strong className="text-neutral-200">Save Key</strong>, or set the <code className="text-neutral-200">DRIVE_API_KEY</code> environment variable.
                </li>
              </ol>
              <p className="text-[11px] text-neutral-500 pt-1">
                Note: Standard Google Cloud free tier includes hundreds of thousands of Drive API requests per day at zero cost.
              </p>
            </div>
          )}
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
