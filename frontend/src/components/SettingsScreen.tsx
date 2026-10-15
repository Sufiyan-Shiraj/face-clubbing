import React, { useState, useEffect } from 'react';
import { api } from '../api/client';
import { Settings } from '../types';
import {
  Sliders,
  RefreshCw,
  Key,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  HelpCircle,
  ExternalLink,
  Save,
  Trash2,
  RotateCcw,
  Sparkles,
  Layers,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import {
  OrbitalClusterVisualizer,
  MergeFusionVisualizer,
  RadarSuggestionVisualizer,
  PhotoCollisionShieldVisualizer,
  DimensionPreviewVisualizer,
} from './SliderVisualizers';

interface SettingsScreenProps {
  onRerunComplete?: () => void;
}

const SPEC_6_2_DEFAULTS: Partial<Settings> = {
  distance_threshold: 0.50,
  merge_threshold: 0.50,
  maybe_threshold: 0.65,
  same_photo_merge_max: 0.40,
  second_pass_merge: true,
  flip_average: false,
  thumb_size: 400,
  face_crop_size: 256,
};

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
  const [showGuide, setShowGuide] = useState(false);
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

  const handleResetDefaults = () => {
    setSettings((prev) => ({
      ...prev,
      ...SPEC_6_2_DEFAULTS,
    }));
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
    <div className="settings-dashboard animate-fadeIn select-none">
      {/* Top Header Row with Actions - Always Visible at Top */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-2 border-b border-[var(--line)]">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded bg-[var(--input)] border border-[var(--panel-border)] flex items-center justify-center text-[var(--accent)] flex-shrink-0">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-lg md:text-xl font-bold tracking-tight text-[var(--text)] uppercase font-mono">
                Clustering & Pipeline Engine
              </h2>
              <span className="settings-badge accent">
                SPEC 6.2 ACTIVE
              </span>
            </div>
            <p className="text-xs text-[var(--muted)] font-mono">
              Real-time parameter tuning with interactive visualizers. Changes trigger agglomerative re-clustering with stable edit replay.
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={handleResetDefaults}
            className="btn sm"
            title="Reset parameters to SPEC 6.2 default recommendations"
          >
            <RotateCcw className="w-3.5 h-3.5 text-[var(--muted)]" />
            <span>Reset Defaults</span>
          </button>

          <button
            id="save-rerun-btn"
            disabled={isRerunning || isLoading}
            onClick={handleSaveAndRerun}
            className="btn pri"
            style={{ height: '36px', padding: '0 20px', fontSize: '13px' }}
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRerunning ? 'animate-spin' : ''}`} />
            <span>{isRerunning ? 'Replaying Edits...' : 'Save & Rerun Clustering'}</span>
          </button>
        </div>
      </div>

      {/* Global Error Banner */}
      {error && (
        <div className="p-3 rounded bg-red-950/80 border border-red-800 text-red-200 text-xs flex items-center gap-2 animate-fadeIn">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 text-red-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Main Full-Width Dashboard Content Grid */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-3 flex-1 min-h-0">
        {/* Left Column: 4 Core Algorithm Sliders with Interactive Visualizers (7 Cols) */}
        <div className="xl:col-span-7 flex flex-col gap-3">
          {/* Section Subtitle */}
          <div className="flex items-center justify-between text-xs font-mono px-1">
            <span className="font-bold text-[var(--text)] uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-[var(--accent)]" />
              Clustering Sensitivity Thresholds
            </span>
            <span className="text-[var(--muted)]">Agglomerative Average Linkage</span>
          </div>

          {/* 2x2 Grid of Themed Visualizer Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {/* Slider 1: Distance Threshold */}
            <div className="settings-slider-card">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <label htmlFor="setting-distance-threshold" className="text-xs md:text-sm font-bold text-[var(--text)] block">
                    Primary Distance Cutoff
                  </label>
                  <span className="text-[11px] font-mono text-[var(--muted)]">
                    distance_threshold
                  </span>
                </div>
                <span
                  id="setting-distance-threshold-val"
                  className="settings-badge accent text-sm"
                >
                  {settings.distance_threshold.toFixed(2)}
                </span>
              </div>

              {/* Interactive Visualizer: Orbital Face Constellation */}
              <div className="h-[84px] w-full my-0.5">
                <OrbitalClusterVisualizer value={settings.distance_threshold} />
              </div>

              <div>
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
                  className="settings-range"
                />
                <div className="flex justify-between text-[10px] font-mono text-[var(--muted)]">
                  <span>0.30 (Strict / Tight)</span>
                  <span>Default: 0.50</span>
                  <span>0.65 (Loose / Wide)</span>
                </div>
              </div>

              <p className="text-[11px] text-[var(--muted)] leading-tight">
                Cosine cutoff for seed face clustering. Lower values require near-identical faces; higher values link wider variations.
              </p>
            </div>

            {/* Slider 2: Merge Threshold */}
            <div className="settings-slider-card">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <label htmlFor="setting-merge-threshold" className="text-xs md:text-sm font-bold text-[var(--text)] block">
                    Second-Pass Merge Cutoff
                  </label>
                  <span className="text-[11px] font-mono text-[var(--muted)]">
                    merge_threshold
                  </span>
                </div>
                <span
                  id="setting-merge-threshold-val"
                  className="settings-badge accent text-sm"
                >
                  {settings.merge_threshold.toFixed(2)}
                </span>
              </div>

              {/* Interactive Visualizer: Centroid Gravitational Fusion */}
              <div className="h-[84px] w-full my-0.5">
                <MergeFusionVisualizer value={settings.merge_threshold} />
              </div>

              <div>
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
                  className="settings-range"
                />
                <div className="flex justify-between text-[10px] font-mono text-[var(--muted)]">
                  <span>0.30 (Separate)</span>
                  <span>Default: 0.50</span>
                  <span>0.60 (Aggressive)</span>
                </div>
              </div>

              <p className="text-[11px] text-[var(--muted)] leading-tight">
                Centroid distance cutoff for automatic duplicate cluster consolidation into a unified person identity.
              </p>
            </div>

            {/* Slider 3: Maybe Threshold */}
            <div className="settings-slider-card">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <label htmlFor="setting-maybe-threshold" className="text-xs md:text-sm font-bold text-[var(--text)] block">
                    Suggestion Range Cap
                  </label>
                  <span className="text-[11px] font-mono text-[var(--muted)]">
                    maybe_threshold
                  </span>
                </div>
                <span
                  id="setting-maybe-threshold-val"
                  className="settings-badge accent text-sm"
                >
                  {settings.maybe_threshold.toFixed(2)}
                </span>
              </div>

              {/* Interactive Visualizer: Sonar Radar Hologram */}
              <div className="h-[84px] w-full my-0.5">
                <RadarSuggestionVisualizer value={settings.maybe_threshold} />
              </div>

              <div>
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
                  className="settings-range"
                />
                <div className="flex justify-between text-[10px] font-mono text-[var(--muted)]">
                  <span>0.50 (Close)</span>
                  <span>Default: 0.65</span>
                  <span>0.75 (Wide Sweep)</span>
                </div>
              </div>

              <p className="text-[11px] text-[var(--muted)] leading-tight">
                Upper centroid radar distance for generating candidate "Maybe Same Person" review pairs.
              </p>
            </div>

            {/* Slider 4: Same-Photo Guard */}
            <div className="settings-slider-card">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <label htmlFor="setting-same-photo-guard" className="text-xs md:text-sm font-bold text-[var(--text)] block">
                    Same-Photo Guard Cap
                  </label>
                  <span className="text-[11px] font-mono text-[var(--muted)]">
                    same_photo_merge_max
                  </span>
                </div>
                <span
                  id="setting-same-photo-guard-val"
                  className="settings-badge text-sm"
                >
                  {settings.same_photo_merge_max.toFixed(2)}
                </span>
              </div>

              {/* Interactive Visualizer: Laser Collision Shield */}
              <div className="h-[84px] w-full my-0.5">
                <PhotoCollisionShieldVisualizer value={settings.same_photo_merge_max} />
              </div>

              <div>
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
                  className="settings-range"
                />
                <div className="flex justify-between text-[10px] font-mono text-[var(--muted)]">
                  <span>0.20 (Impenetrable)</span>
                  <span>Default: 0.40</span>
                  <span>0.50 (Permissive)</span>
                </div>
              </div>

              <p className="text-[11px] text-[var(--muted)] leading-tight">
                Prevents merging two clusters if any two faces appearing in the identical photograph exceed this barrier.
              </p>
            </div>
          </div>

          {/* Algorithm Switches Row */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
            <label
              className={`settings-toggle-card ${settings.second_pass_merge ? 'active' : ''}`}
            >
              <input
                id="setting-second-pass-toggle"
                type="checkbox"
                checked={settings.second_pass_merge}
                onChange={(e) =>
                  setSettings({ ...settings, second_pass_merge: e.target.checked })
                }
                className="w-4 h-4 rounded border-[var(--panel-border)] bg-[var(--input)] text-[var(--accent)] focus:ring-[var(--accent)] cursor-pointer"
              />
              <div className="flex-1">
                <p className="text-xs font-bold text-[var(--text)] uppercase tracking-wide">
                  Second-Pass Centroid Merge
                </p>
                <p className="text-[11px] text-[var(--muted)] leading-tight">
                  Automatically merges split sub-clusters with strict same-photo collision protection.
                </p>
              </div>
            </label>

            <label
              className={`settings-toggle-card ${settings.flip_average ? 'active' : ''}`}
            >
              <input
                id="setting-flip-average-toggle"
                type="checkbox"
                checked={settings.flip_average}
                onChange={(e) =>
                  setSettings({ ...settings, flip_average: e.target.checked })
                }
                className="w-4 h-4 rounded border-[var(--panel-border)] bg-[var(--input)] text-[var(--accent)] focus:ring-[var(--accent)] cursor-pointer"
              />
              <div className="flex-1">
                <p className="text-xs font-bold text-[var(--text)] uppercase tracking-wide">
                  Flip-Averaged Embeddings
                </p>
                <p className="text-[11px] text-[var(--muted)] leading-tight">
                  Calculates horizontal mirrored embedding averages for increased pose invariance.
                </p>
              </div>
            </label>
          </div>
        </div>

        {/* Right Column: Asset Sizing, Cloud API Credentials & Telemetry (5 Cols) */}
        <div className="xl:col-span-5 flex flex-col gap-3">
          {/* Card 1: Asset Generation Sizes & Visual Dimension Scaling */}
          <div className="settings-panel p-3.5 space-y-2.5">
            <div className="flex items-center justify-between border-b border-[var(--line)] pb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-[var(--text)] flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-[var(--accent)]" />
                Asset Generation Dimensions
              </span>
              <span className="text-[10px] font-mono text-[var(--muted)]">SPEC 6.2 Standard</span>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label
                  htmlFor="setting-thumb-size"
                  className="block text-[11px] font-bold uppercase tracking-wider text-[var(--muted)] mb-1"
                >
                  Thumbnail Size
                </label>
                <select
                  id="setting-thumb-size"
                  value={settings.thumb_size}
                  onChange={(e) => setSettings({ ...settings, thumb_size: parseInt(e.target.value, 10) })}
                  className="settings-select"
                >
                  <option value="300">300 px (Compact)</option>
                  <option value="400">400 px (Default 6.2)</option>
                  <option value="500">500 px (High Detail)</option>
                  <option value="600">600 px (Ultra HD)</option>
                </select>
              </div>

              <div>
                <label
                  htmlFor="setting-face-crop-size"
                  className="block text-[11px] font-bold uppercase tracking-wider text-[var(--muted)] mb-1"
                >
                  Face Crop Size
                </label>
                <select
                  id="setting-face-crop-size"
                  value={settings.face_crop_size}
                  onChange={(e) =>
                    setSettings({ ...settings, face_crop_size: parseInt(e.target.value, 10) })
                  }
                  className="settings-select"
                >
                  <option value="192">192 px (Compact)</option>
                  <option value="256">256 px (Default 6.2)</option>
                  <option value="320">320 px (High Detail)</option>
                </select>
              </div>
            </div>

            {/* Interactive Dimension Scale Preview */}
            <DimensionPreviewVisualizer
              thumbSize={settings.thumb_size}
              faceCropSize={settings.face_crop_size}
            />
          </div>

          {/* Card 2: Google Drive API Key */}
          <div className="settings-panel p-3.5 space-y-2.5">
            <div className="flex items-center justify-between border-b border-[var(--line)] pb-2">
              <div className="flex items-center gap-1.5">
                <Key className="w-3.5 h-3.5 text-amber-500" />
                <span className="text-xs font-bold uppercase tracking-wider text-[var(--text)]">
                  Google Drive Cloud API
                </span>
              </div>

              {settings.drive_api_key_configured ? (
                <span
                  id="drive-key-status-badge"
                  className="settings-badge"
                  style={{
                    background: 'rgba(16, 185, 129, 0.12)',
                    borderColor: '#10b981',
                    color: '#10b981',
                  }}
                >
                  <CheckCircle2 className="w-3 h-3" />
                  <span>Configured ({settings.drive_api_key_masked || 'Active'})</span>
                </span>
              ) : (
                <span
                  id="drive-key-status-badge"
                  className="settings-badge"
                  style={{
                    background: 'rgba(245, 158, 11, 0.12)',
                    borderColor: '#f59e0b',
                    color: '#f59e0b',
                  }}
                >
                  <AlertTriangle className="w-3 h-3" />
                  <span>Not Configured</span>
                </span>
              )}
            </div>

            {keySavedMessage && (
              <div
                id="drive-key-saved-message"
                className="p-2 rounded bg-emerald-950/70 border border-emerald-800 text-emerald-300 text-xs flex items-center gap-2 animate-fadeIn"
              >
                <CheckCircle2 className="w-3.5 h-3.5 flex-shrink-0" />
                <span>{keySavedMessage}</span>
              </div>
            )}

            {/* API Key Input and Action Buttons */}
            <div>
              <label
                htmlFor="setting-drive-api-key"
                className="block text-[11px] font-bold uppercase tracking-wider text-[var(--muted)] mb-1"
              >
                {settings.drive_api_key_configured ? 'Update API Key' : 'Enter API Key'}
              </label>
              <div className="flex gap-2">
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
                  className="settings-input flex-1"
                />
                <button
                  id="save-drive-key-btn"
                  type="button"
                  onClick={handleSaveDriveKey}
                  disabled={isSavingKey || !driveKeyInput.trim()}
                  className="btn pri sm"
                >
                  <Save className="w-3.5 h-3.5" />
                  <span>{isSavingKey ? 'Saving...' : 'Save'}</span>
                </button>
                {settings.drive_api_key_configured && (
                  <button
                    id="clear-drive-key-btn"
                    type="button"
                    onClick={handleClearDriveKey}
                    disabled={isSavingKey}
                    className="btn sm"
                    style={{ borderColor: 'rgba(239, 68, 68, 0.5)', color: '#f87171' }}
                    title="Remove saved key from local settings"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Clear</span>
                  </button>
                )}
              </div>
            </div>

            {/* Security Guarantee Note */}
            <div className="flex items-start gap-2 p-2 rounded bg-[var(--input)] border border-[var(--panel-border)] text-[11px] text-[var(--muted)]">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="text-[var(--text)]">Local Security: </strong>
                Stored strictly in your home directory profile (<code className="font-mono text-[var(--text)]">~/.photosorter/settings.json</code>). Never committed to git, never written to project exports, and masked in telemetry logs.
              </div>
            </div>

            {/* Collapsible 3-Minute Guide Drawer */}
            <div className="border border-[var(--panel-border)] rounded overflow-hidden bg-[var(--input)]">
              <button
                type="button"
                onClick={() => setShowGuide(!showGuide)}
                className="w-full px-3 py-1.5 flex items-center justify-between text-xs font-semibold text-[var(--text)] hover:text-[var(--accent)] transition-colors"
              >
                <span className="flex items-center gap-1.5">
                  <HelpCircle className="w-3.5 h-3.5 text-[var(--accent)]" />
                  <span>How to get a free Google Drive API Key (3 minutes)</span>
                </span>
                {showGuide ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
              </button>

              {showGuide && (
                <div className="px-3 pb-3 pt-1 space-y-1.5 text-xs text-[var(--muted)] border-t border-[var(--line)]">
                  <ol className="list-decimal list-inside space-y-1">
                    <li>
                      Open{' '}
                      <a
                        href="https://console.cloud.google.com/"
                        target="_blank"
                        rel="noreferrer"
                        className="text-[var(--accent)] hover:underline inline-flex items-center gap-1 font-semibold"
                      >
                        Google Cloud Console <ExternalLink className="w-3 h-3" />
                      </a>.
                    </li>
                    <li>Create or select a project (e.g. <code className="text-[var(--text)]">PhotoSorter</code>).</li>
                    <li>Go to <strong>APIs & Services &gt; Library</strong>, search for <strong>Google Drive API</strong>, click <strong>Enable</strong>.</li>
                    <li>Go to <strong>Credentials</strong>, click <strong>+ Create Credentials &gt; API key</strong>.</li>
                    <li>Paste the generated key above and click <strong>Save</strong>.</li>
                  </ol>
                  <p className="text-[10px] text-[var(--muted)] pt-1">
                    Free tier includes unlimited personal scanning quotas with zero cloud fees.
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Card 3: Execution Telemetry & Result Summary */}
          <div className="settings-panel p-3.5 space-y-2">
            <div className="flex items-center justify-between border-b border-[var(--line)] pb-2">
              <span className="text-xs font-bold uppercase tracking-wider text-[var(--text)]">
                Clustering Telemetry & Replay
              </span>
              <span className="settings-badge">
                STABLE FACE IDS
              </span>
            </div>

            {rerunResult ? (
              <div
                id="rerun-result-summary"
                className="space-y-2.5 animate-fadeIn"
              >
                <div className="flex items-center gap-2 text-emerald-400">
                  <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                  <p className="text-xs font-semibold text-[var(--text)]">
                    Re-clustering completed. {rerunResult.applied_count} edits replayed!
                  </p>
                </div>

                <div className="grid grid-cols-3 gap-2">
                  <div className="p-2 rounded bg-[var(--input)] border border-[var(--panel-border)] text-center">
                    <span className="text-[10px] text-[var(--muted)] font-mono uppercase">People</span>
                    <p id="rerun-stat-people" className="text-base font-bold text-[var(--text)] font-mono">{rerunResult.people_count}</p>
                  </div>
                  <div className="p-2 rounded bg-[var(--input)] border border-[var(--panel-border)] text-center">
                    <span className="text-[10px] text-[var(--muted)] font-mono uppercase">Unrec Faces</span>
                    <p id="rerun-stat-unrec" className="text-base font-bold text-[var(--text)] font-mono">{rerunResult.unrecognized_faces_count}</p>
                  </div>
                  <div className="p-2 rounded bg-[var(--input)] border border-[var(--panel-border)] text-center">
                    <span className="text-[10px] text-[var(--muted)] font-mono uppercase">Replayed</span>
                    <p id="rerun-stat-edits" className="text-base font-bold text-[var(--accent)] font-mono">{rerunResult.applied_count}</p>
                  </div>
                </div>

                {rerunResult.unapplied_edits && rerunResult.unapplied_edits.length > 0 ? (
                  <div id="unapplied-edits-box" className="p-2.5 rounded bg-amber-950/40 border border-amber-800 text-xs space-y-1">
                    <p className="font-semibold text-amber-300 flex items-center gap-1.5">
                      <AlertTriangle className="w-3.5 h-3.5" />
                      {rerunResult.unapplied_edits.length} edit(s) could not be re-applied:
                    </p>
                    <ul className="text-[11px] text-[var(--muted)] list-disc list-inside space-y-0.5 font-mono">
                      {rerunResult.unapplied_edits.map((item, idx) => (
                        <li key={idx}>
                          {item.op}: {item.reason || JSON.stringify(item)}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <p id="all-edits-survived-msg" className="text-xs text-emerald-400 flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    All organizer edits survived and were re-applied by stable face ID anchors!
                  </p>
                )}
              </div>
            ) : (
              <div className="p-3 rounded bg-[var(--input)] border border-[var(--panel-border)] text-xs text-[var(--muted)] space-y-1 font-mono">
                <div className="flex items-center gap-2 text-[var(--text)]">
                  <span className="w-2 h-2 rounded-full bg-[var(--accent)] animate-pulse" />
                  <span className="font-semibold">Engine Ready</span>
                </div>
                <p className="text-[11px]">
                  When you change any parameter above and click &quot;Save &amp; Rerun Clustering&quot;, the engine will re-partition clusters from raw face embeddings and automatically replay all manual person renames, merges, and assigned faces.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
