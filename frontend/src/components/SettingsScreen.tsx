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
  Cpu,
  Compass,
  FolderTree,
} from 'lucide-react';
import { MascotSticker } from './MascotSticker';
import { CopyDiagnosticsButton } from './CopyDiagnosticsButton';
import { ModelDownloadBanner } from './ModelDownloadBanner';
import {
  OrbitalClusterVisualizer,
  MergeFusionVisualizer,
  RadarSuggestionVisualizer,
  PhotoCollisionShieldVisualizer,
  DimensionPreviewVisualizer,
} from './SliderVisualizers';
import {
  CustomDropdown,
  CustomCheckbox,
  DropdownOption,
} from './SettingsControls';

interface SettingsScreenProps {
  onRerunComplete?: () => void;
  onOpenProject?: () => void;
  onOpenTutorial?: () => void;
  theme?: string;
}

const SPEC_6_2_DEFAULTS: Partial<Settings> = {
  distance_threshold: 0.50,
  min_det_score: 0.50,
  min_face_size: 64,
  max_yaw: 70.0,
  seed_min_det_score: 0.70,
  seed_min_face_size: 64,
  seed_max_yaw: 60.0,
  attach_distance_cap: 0.45,
  second_pass_merge: true,
  merge_threshold: 0.50,
  maybe_threshold: 0.65,
  same_photo_merge_max: 0.40,
  flip_average: false,
  thumb_size: 400,
  face_crop_size: 256,
  scan_subfolders: true,
  max_subfolder_depth: 5,
  follow_shortcuts: false,
};

const THUMB_OPTIONS: DropdownOption[] = [
  { value: 300, label: '300 px', desc: 'Compact', badge: 'LOW RAM' },
  { value: 400, label: '400 px', desc: 'Standard', badge: 'DEFAULT' },
  { value: 500, label: '500 px', desc: 'High Detail', badge: 'HD' },
  { value: 600, label: '600 px', desc: 'Ultra HD', badge: '4K' },
];

const FACE_CROP_OPTIONS: DropdownOption[] = [
  { value: 192, label: '192 px', desc: 'Compact', badge: 'FAST' },
  { value: 256, label: '256 px', desc: 'Standard', badge: 'DEFAULT' },
  { value: 320, label: '320 px', desc: 'High Detail', badge: 'CRISP' },
];

const SUBFOLDER_DEPTH_OPTIONS: DropdownOption[] = [
  { value: 1, label: '1 Level', desc: 'Direct children only' },
  { value: 2, label: '2 Levels', desc: 'Shallow' },
  { value: 3, label: '3 Levels', desc: 'Moderate' },
  { value: 4, label: '4 Levels', desc: 'Deep' },
  { value: 5, label: '5 Levels', desc: 'Standard', badge: 'DEFAULT' },
  { value: 6, label: '6 Levels', desc: 'Very deep' },
  { value: 8, label: '8 Levels', desc: 'Extra deep' },
  { value: 10, label: '10 Levels', desc: 'Maximum' },
];

export const SettingsScreen: React.FC<SettingsScreenProps> = ({
  onRerunComplete,
  onOpenProject,
  onOpenTutorial,
  theme = 't-dark',
}) => {
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
    event_title: 'CatLog Gallery',
    event_subtitle: 'Auto-sorted face albums and photo gallery',
    scan_subfolders: true,
    max_subfolder_depth: 5,
    follow_shortcuts: false,
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
      setKeySavedMessage('Drive API key saved to ~/.catlog/settings.json (outside repository).');
      try {
        localStorage.setItem('photosorter-api-key-configured', 'true');
      } catch (e) {}
      if (onRerunComplete) {
        onRerunComplete();
      }
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
      try {
        localStorage.setItem('photosorter-api-key-configured', 'false');
      } catch (e) {}
      if (onRerunComplete) {
        onRerunComplete();
      }
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
      {/* Top Header Row with Actions */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-4 border-b-2 border-[var(--line)]">
        <div className="flex items-center gap-3.5">
          <div className="w-11 h-11 rounded bg-[var(--input)] border-2 border-[var(--panel-border)] shadow-[3px_3px_0px_var(--line)] flex items-center justify-center text-[var(--accent)] flex-shrink-0">
            <Sliders className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl md:text-2xl font-black tracking-tight text-[var(--text)] uppercase font-mono">
              Clustering &amp; Pipeline Settings
            </h2>
          </div>
        </div>

        {/* Top Action Controls */}
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={handleResetDefaults}
            className="btn sm"
            style={{ height: '42px', padding: '0 18px', fontSize: '15px', fontWeight: 700 }}
            title="Reset parameters to default recommendations"
          >
            <RotateCcw className="w-4 h-4 text-[var(--muted)]" />
            <span>Reset Defaults</span>
          </button>

          <button
            id="save-rerun-btn"
            disabled={isRerunning || isLoading}
            onClick={handleSaveAndRerun}
            className="btn pri"
            style={{ height: '42px', padding: '0 24px', fontSize: '15px', fontWeight: 800 }}
          >
            <RefreshCw className={`w-4 h-4 ${isRerunning ? 'animate-spin' : ''}`} />
            <span>{isRerunning ? 'Replaying Edits...' : 'Save & Rerun Clustering'}</span>
          </button>
        </div>
      </div>

      {/* Global Error Banner */}
      {error && (
        <div className="p-3 rounded bg-red-950/80 border-2 border-red-700 text-red-200 text-sm flex items-center gap-2 animate-fadeIn">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 text-red-400" />
          <span className="font-semibold">{error}</span>
        </div>
      )}

      {/* Interactive Tutorial & Tour Banner */}
      {onOpenTutorial && (
        <div
          id="card-settings-tutorial-launcher"
          data-testid="card-settings-tutorial-launcher"
          className="p-5 sm:p-6 rounded-lg border-2 border-[var(--accent)] bg-[var(--card-bg)] flex flex-col md:flex-row items-center justify-between gap-5 transition-all shadow-[3px_3px_0px_var(--line)]"
        >
          <div className="flex items-center gap-4 sm:gap-5 w-full md:w-auto">
            <div className="w-16 h-16 sm:w-20 sm:h-20 rounded-xl bg-[var(--input)] border-2 border-[var(--line)] flex items-center justify-center p-1.5 flex-shrink-0 shadow-[2px_2px_0px_var(--line)]">
              <MascotSticker pose={1} theme={theme} className="w-full h-full object-contain" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="settings-badge accent text-xs uppercase px-2 py-0.5">
                  Spotlight Guide
                </span>
                <span className="text-xs font-mono text-[var(--muted)] font-semibold">
                  11 Interactive Steps
                </span>
              </div>
              <h3 className="text-lg sm:text-xl font-black text-[var(--text)] uppercase font-mono mt-1">
                Interactive Tutorial &amp; Feature Walkthrough
              </h3>
              <p className="text-xs sm:text-sm text-[var(--muted)] mt-1 max-w-2xl leading-relaxed">
                Step-by-step spotlight tour across all features: photo source selection, live engine scan &amp; logs, multi-select cluster merging, smart match suggestions, triage, and offline gallery export.
              </p>
            </div>
          </div>

          <div className="flex-shrink-0 w-full md:w-auto flex justify-end">
            <button
              type="button"
              id="btn-launch-tutorial-settings"
              data-testid="btn-launch-tutorial-settings"
              onClick={onOpenTutorial}
              className="btn pri w-full md:w-auto flex items-center justify-center gap-2.5 px-6 shadow-[3px_3px_0px_var(--line)]"
              style={{ height: '46px', fontSize: '15px', fontWeight: 800 }}
            >
              <Compass className="w-4 h-4" />
              <span>Launch Interactive Tutorial</span>
            </button>
          </div>
        </div>
      )}

      {/* SECTION 1: Clustering Sensitivity Thresholds (Top Spacious Section) */}
      <div className="space-y-3.5">
        <div className="flex items-center justify-between text-xs md:text-sm font-mono px-1">
          <span className="font-extrabold text-[var(--text)] uppercase tracking-wider flex items-center gap-2 text-sm md:text-base">
            <Sparkles className="w-4 h-4 text-[var(--accent)]" />
            Clustering Sensitivity Thresholds
          </span>
        </div>

        {/* 2x2 Grid of Spacious Visualizer Slider Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Slider 1: Distance Threshold */}
          <div id="card-slider-distance" className="settings-slider-card">
            <div className="flex items-start justify-between gap-2">
              <div>
                <label htmlFor="setting-distance-threshold" className="text-base md:text-lg font-black text-[var(--text)] block leading-tight">
                  Primary Distance Cutoff
                </label>
                <span className="text-sm font-mono text-[var(--muted)] font-semibold">
                  distance_threshold
                </span>
              </div>
              <span
                id="setting-distance-threshold-val"
                className="settings-badge accent text-base md:text-lg px-3 py-0.5"
              >
                {settings.distance_threshold.toFixed(2)}
              </span>
            </div>

            {/* Interactive Visualizer: Orbital Face Constellation */}
            <div className="h-[110px] md:h-[125px] w-full my-1">
              <OrbitalClusterVisualizer value={settings.distance_threshold} />
            </div>

            <div className="space-y-1">
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
              <div className="flex justify-between text-sm font-mono text-[var(--muted)] font-bold">
                <span>0.30 (Strict / 1 Node)</span>
                <span className="text-[var(--text)]">Default: 0.50</span>
                <span>0.65 (Loose / 10 Nodes)</span>
              </div>
            </div>

            <p className="text-sm md:text-base text-[var(--muted)] leading-relaxed">
              Cosine cutoff for seed face clustering. Moving to the right increases cluster nodes and links wider facial variations.
            </p>
          </div>

          {/* Slider 2: Merge Threshold */}
          <div id="card-slider-merge" className="settings-slider-card">
            <div className="flex items-start justify-between gap-2">
              <div>
                <label htmlFor="setting-merge-threshold" className="text-base md:text-lg font-black text-[var(--text)] block leading-tight">
                  Second-Pass Merge Cutoff
                </label>
                <span className="text-sm font-mono text-[var(--muted)] font-semibold">
                  merge_threshold
                </span>
              </div>
              <span
                id="setting-merge-threshold-val"
                className="settings-badge accent text-base md:text-lg px-3 py-0.5"
              >
                {settings.merge_threshold.toFixed(2)}
              </span>
            </div>

            {/* Interactive Visualizer: Centroid Gravitational Fusion */}
            <div className="h-[110px] md:h-[125px] w-full my-1">
              <MergeFusionVisualizer value={settings.merge_threshold} />
            </div>

            <div className="space-y-1">
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
              <div className="flex justify-between text-sm font-mono text-[var(--muted)] font-bold">
                <span>0.30 (Separate)</span>
                <span className="text-[var(--text)]">Default: 0.50</span>
                <span>0.60 (Aggressive)</span>
              </div>
            </div>

            <p className="text-sm md:text-base text-[var(--muted)] leading-relaxed">
              Centroid distance cutoff for automatic duplicate consolidation. Pulls separate sub-clusters into a unified identity.
            </p>
          </div>

          {/* Slider 3: Maybe Threshold */}
          <div id="card-slider-maybe" className="settings-slider-card">
            <div className="flex items-start justify-between gap-2">
              <div>
                <label htmlFor="setting-maybe-threshold" className="text-base md:text-lg font-black text-[var(--text)] block leading-tight">
                  Suggestion Range Cap
                </label>
                <span className="text-sm font-mono text-[var(--muted)] font-semibold">
                  maybe_threshold
                </span>
              </div>
              <span
                id="setting-maybe-threshold-val"
                className="settings-badge accent text-base md:text-lg px-3 py-0.5"
              >
                {settings.maybe_threshold.toFixed(2)}
              </span>
            </div>

            {/* Interactive Visualizer: Sonar Radar Hologram */}
            <div className="h-[110px] md:h-[125px] w-full my-1">
              <RadarSuggestionVisualizer value={settings.maybe_threshold} />
            </div>

            <div className="space-y-1">
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
              <div className="flex justify-between text-sm font-mono text-[var(--muted)] font-bold">
                <span>0.50 (Close)</span>
                <span className="text-[var(--text)]">Default: 0.65</span>
                <span>0.75 (Wide Sweep)</span>
              </div>
            </div>

            <p className="text-sm md:text-base text-[var(--muted)] leading-relaxed">
              Upper centroid radar distance for generating candidate &quot;Maybe Same Person&quot; review pairs for organizer approval.
            </p>
          </div>

          {/* Slider 4: Same-Photo Guard */}
          <div id="card-slider-guard" className="settings-slider-card">
            <div className="flex items-start justify-between gap-2">
              <div>
                <label htmlFor="setting-same-photo-guard" className="text-base md:text-lg font-black text-[var(--text)] block leading-tight">
                  Same-Photo Guard Cap
                </label>
                <span className="text-sm font-mono text-[var(--muted)] font-semibold">
                  same_photo_merge_max
                </span>
              </div>
              <span
                id="setting-same-photo-guard-val"
                className="settings-badge text-base md:text-lg px-3 py-0.5"
              >
                {settings.same_photo_merge_max.toFixed(2)}
              </span>
            </div>

            {/* Interactive Visualizer: Laser Collision Shield */}
            <div className="h-[110px] md:h-[125px] w-full my-1">
              <PhotoCollisionShieldVisualizer value={settings.same_photo_merge_max} />
            </div>

            <div className="space-y-1">
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
              <div className="flex justify-between text-sm font-mono text-[var(--muted)] font-bold">
                <span>0.20 (Locked)</span>
                <span className="text-[var(--text)]">Default: 0.40</span>
                <span>0.50 (Permissive)</span>
              </div>
            </div>

            <p className="text-sm md:text-base text-[var(--muted)] leading-relaxed">
              Prevents merging two clusters if any two faces appearing in the identical photograph exceed this barrier.
            </p>
          </div>
        </div>

        {/* Algorithm Switches Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
          <CustomCheckbox
            id="setting-second-pass-toggle"
            checked={settings.second_pass_merge}
            onChange={(checked) =>
              setSettings({ ...settings, second_pass_merge: checked })
            }
            title="Second-Pass Centroid Merge"
            subtitle="Automatically merges split sub-clusters with strict same-photo collision protection."
          />

          <CustomCheckbox
            id="setting-flip-average-toggle"
            checked={settings.flip_average}
            onChange={(checked) =>
              setSettings({ ...settings, flip_average: checked })
            }
            title="Flip-Averaged Embeddings"
            subtitle="Calculates horizontal mirrored embedding averages for increased pose invariance."
          />
        </div>
      </div>

      {/* SECTION 2: Below That — "Other Stuff" (Asset Dimensions, Google Drive API & Telemetry) */}
      <div className="space-y-4 pt-4 border-t-2 border-[var(--line)]">
        <div className="flex items-center justify-between text-xs md:text-sm font-mono px-1">
          <span className="font-extrabold text-[var(--text)] uppercase tracking-wider flex items-center gap-2 text-sm md:text-base">
            <Cpu className="w-4 h-4 text-[var(--accent)]" />
            Storage, Cloud &amp; Pipeline Configuration
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
          {/* Left Side: Google Drive Cloud API Configuration (6 Cols) */}
          <div className="lg:col-span-6 flex flex-col gap-4">
            <div id="card-settings-drive-key" className="settings-panel p-5 space-y-3.5">
              <div className="flex items-center justify-between border-b-2 border-[var(--line)] pb-2.5">
                <div className="flex items-center gap-2">
                  <Key className="w-5 h-5 text-amber-500" />
                  <span className="text-sm md:text-base font-extrabold uppercase tracking-wider text-[var(--text)]">
                    Google Drive Cloud API
                  </span>
                </div>

                {settings.drive_api_key_configured ? (
                  <span
                    id="drive-key-status-badge"
                    className="settings-badge text-xs md:text-sm"
                    style={{
                      background: 'rgba(16, 185, 129, 0.16)',
                      borderColor: '#10b981',
                      color: '#10b981',
                    }}
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Configured ({settings.drive_api_key_masked || 'Active'})</span>
                  </span>
                ) : (
                  <span
                    id="drive-key-status-badge"
                    className="settings-badge text-xs md:text-sm"
                    style={{
                      background: 'rgba(245, 158, 11, 0.16)',
                      borderColor: '#f59e0b',
                      color: '#f59e0b',
                    }}
                  >
                    <AlertTriangle className="w-4 h-4" />
                    <span>Not Configured</span>
                  </span>
                )}
              </div>

              {keySavedMessage && (
                <div
                  id="drive-key-saved-message"
                  className="p-2.5 rounded bg-emerald-950/70 border border-emerald-800 text-emerald-300 text-xs md:text-sm flex items-center gap-2 animate-fadeIn"
                >
                  <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                  <span className="font-semibold">{keySavedMessage}</span>
                </div>
              )}

              {/* API Key Input and Action Buttons */}
              <div className="space-y-1.5">
                <label
                  htmlFor="setting-drive-api-key"
                  className="block text-xs font-bold uppercase tracking-wider text-[var(--muted)]"
                >
                  {settings.drive_api_key_configured ? 'Update API Key' : 'Enter API Key'}
                </label>
                <div className="flex gap-2.5">
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
                    style={{ height: '40px', fontSize: '13px' }}
                  />
                  <button
                    id="save-drive-key-btn"
                    type="button"
                    onClick={handleSaveDriveKey}
                    disabled={isSavingKey || !driveKeyInput.trim()}
                    className="btn pri sm"
                    style={{ height: '40px', padding: '0 18px', fontSize: '13px', fontWeight: 800 }}
                  >
                    <Save className="w-4 h-4" />
                    <span>{isSavingKey ? 'Saving...' : 'Save'}</span>
                  </button>
                  {settings.drive_api_key_configured && (
                    <button
                      id="clear-drive-key-btn"
                      type="button"
                      onClick={handleClearDriveKey}
                      disabled={isSavingKey}
                      className="btn sm"
                      style={{ height: '42px', padding: '0 16px', fontSize: '15px', borderColor: 'rgba(239, 68, 68, 0.6)', color: '#f87171' }}
                      title="Remove saved key from local settings"
                    >
                      <Trash2 className="w-4 h-4" />
                      <span>Clear</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Security Guarantee Note */}
              <div className="flex items-start gap-2.5 p-3 rounded bg-[var(--input)] border border-[var(--panel-border)] text-sm text-[var(--muted)] leading-relaxed">
                <ShieldCheck className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                <div>
                  <strong className="text-[var(--text)]">Local Security Guarantee: </strong>
                  Stored strictly in your home directory profile (<code className="font-mono text-[var(--text)]">~/.catlog/settings.json</code>). Never committed to git, never uploaded, and masked in logs.
                </div>
              </div>

              {/* Collapsible 3-Minute Guide Drawer */}
              <div className="border border-[var(--panel-border)] rounded overflow-hidden bg-[var(--input)]">
                <button
                  type="button"
                  onClick={() => setShowGuide(!showGuide)}
                  className="w-full px-3.5 py-2.5 flex items-center justify-between text-sm md:text-base font-bold text-[var(--text)] hover:text-[var(--accent)] transition-colors"
                >
                  <span className="flex items-center gap-2">
                    <HelpCircle className="w-4 h-4 text-[var(--accent)]" />
                    <span>How to get a free Google Drive API Key (3 minutes)</span>
                  </span>
                  {showGuide ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>

                {showGuide && (
                  <div className="px-4 pb-4 pt-1.5 space-y-1.5 text-sm text-[var(--muted)] border-t border-[var(--line)] leading-relaxed">
                    <ol className="list-decimal list-inside space-y-1.5">
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
                      <li>Create or select a project (e.g. <code className="text-[var(--text)]">CatLog</code>).</li>
                      <li>Go to <strong>APIs & Services &gt; Library</strong>, search for <strong>Google Drive API</strong>, click <strong>Enable</strong>.</li>
                      <li>Go to <strong>Credentials</strong>, click <strong>+ Create Credentials &gt; API key</strong>.</li>
                      <li>Paste the generated key above and click <strong>Save</strong>.</li>
                    </ol>
                    <p className="text-xs text-[var(--muted)] pt-1 font-semibold">
                      Standard Google Cloud free tier includes hundreds of thousands of Drive requests per day at zero cost.
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Folder & Cloud Traversal Options */}
            <div id="card-settings-subfolders" className="settings-panel p-5 space-y-4">
              <div className="flex items-center justify-between border-b-2 border-[var(--line)] pb-2.5">
                <span className="text-sm md:text-base font-extrabold uppercase tracking-wider text-[var(--text)] flex items-center gap-2">
                  <FolderTree className="w-4 h-4 text-[var(--accent)]" />
                  Folder &amp; Cloud Traversal
                </span>
                <span className="text-xs font-mono text-[var(--muted)]">Recursion Options</span>
              </div>

              <div className="space-y-3.5">
                <CustomCheckbox
                  id="setting-scan-subfolders"
                  checked={settings.scan_subfolders ?? true}
                  onChange={(checked) => {
                    const updated = { ...settings, scan_subfolders: checked };
                    setSettings(updated);
                    api.updateSettings({ scan_subfolders: checked }).catch(console.error);
                  }}
                  title="Scan Subfolders"
                  subtitle="Recursively traverse nested subfolders to discover photos (default: enabled)."
                />

                {(settings.scan_subfolders ?? true) && (
                  <div className="pl-6 border-l-2 border-[var(--line)] space-y-2">
                    <CustomDropdown
                      id="setting-subfolder-depth"
                      label="Recursive Subfolder Depth Limit"
                      value={settings.max_subfolder_depth ?? 5}
                      onChange={(val) => {
                        const updated = { ...settings, max_subfolder_depth: val };
                        setSettings(updated);
                        api.updateSettings({ max_subfolder_depth: val }).catch(console.error);
                      }}
                      options={SUBFOLDER_DEPTH_OPTIONS}
                    />
                    <p className="text-xs text-[var(--muted)]">
                      Maximum levels of nested folders to search down. Default is 5 levels.
                    </p>
                  </div>
                )}

                <CustomCheckbox
                  id="setting-follow-shortcuts"
                  checked={settings.follow_shortcuts ?? false}
                  onChange={(checked) => {
                    const updated = { ...settings, follow_shortcuts: checked };
                    setSettings(updated);
                    api.updateSettings({ follow_shortcuts: checked }).catch(console.error);
                  }}
                  title="Include Shortcut Folders"
                  subtitle="Follow Google Drive shortcuts to other folders (default: disabled)."
                />
              </div>
            </div>
          </div>

          {/* Right Side: Asset Dimensions & Clustering Telemetry (6 Cols) */}
          <div className="lg:col-span-6 flex flex-col gap-4">
            {/* Asset Generation Dimensions */}
            <div className="settings-panel p-5 space-y-3.5">
              <div className="flex items-center justify-between border-b-2 border-[var(--line)] pb-2.5">
                <span className="text-sm md:text-base font-extrabold uppercase tracking-wider text-[var(--text)] flex items-center gap-2">
                  <Layers className="w-4 h-4 text-[var(--accent)]" />
                  Asset Generation Dimensions
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3.5">
                <CustomDropdown
                  id="setting-thumb-size"
                  label="Thumbnail Size"
                  value={settings.thumb_size}
                  onChange={(val) => setSettings({ ...settings, thumb_size: val })}
                  options={THUMB_OPTIONS}
                />

                <CustomDropdown
                  id="setting-face-crop-size"
                  label="Face Crop Size"
                  value={settings.face_crop_size}
                  onChange={(val) => setSettings({ ...settings, face_crop_size: val })}
                  options={FACE_CROP_OPTIONS}
                />
              </div>

              {/* Interactive Dimension Scale Preview */}
              <DimensionPreviewVisualizer
                thumbSize={settings.thumb_size}
                faceCropSize={settings.face_crop_size}
              />
            </div>

            {/* Clustering Telemetry & Replay */}
            <div className="settings-panel p-5 space-y-3.5">
              <div className="flex items-center justify-between border-b-2 border-[var(--line)] pb-2.5">
                <span className="text-sm md:text-base font-extrabold uppercase tracking-wider text-[var(--text)]">
                  Clustering Telemetry & Replay
                </span>
              </div>

              {rerunResult && (
                <div
                  id="rerun-result-summary"
                  className="space-y-3 animate-fadeIn"
                >
                  <div className="flex items-center gap-2 text-emerald-400">
                    <CheckCircle2 className="w-5 h-5 flex-shrink-0" />
                    <p className="text-sm font-bold text-[var(--text)]">
                      Re-clustering completed. {rerunResult.applied_count} edits replayed!
                    </p>
                  </div>

                  <div className="grid grid-cols-3 gap-2.5">
                    <div className="p-2.5 rounded bg-[var(--input)] border-2 border-[var(--panel-border)] text-center shadow-[1px_1px_0px_var(--line)]">
                      <span className="text-sm text-[var(--muted)] font-mono uppercase font-bold">People</span>
                      <p id="rerun-stat-people" className="text-lg md:text-xl font-black text-[var(--text)] font-mono mt-0.5">{rerunResult.people_count}</p>
                    </div>
                    <div className="p-2.5 rounded bg-[var(--input)] border-2 border-[var(--panel-border)] text-center shadow-[1px_1px_0px_var(--line)]">
                      <span className="text-sm text-[var(--muted)] font-mono uppercase font-bold">Unrec Faces</span>
                      <p id="rerun-stat-unrec" className="text-lg md:text-xl font-black text-[var(--text)] font-mono mt-0.5">{rerunResult.unrecognized_faces_count}</p>
                    </div>
                    <div className="p-2.5 rounded bg-[var(--input)] border-2 border-[var(--panel-border)] text-center shadow-[1px_1px_0px_var(--line)]">
                      <span className="text-sm text-[var(--muted)] font-mono uppercase font-bold">Replayed</span>
                      <p id="rerun-stat-edits" className="text-lg md:text-xl font-black text-[var(--accent)] font-mono mt-0.5">{rerunResult.applied_count}</p>
                    </div>
                  </div>

                  {rerunResult.unapplied_edits && rerunResult.unapplied_edits.length > 0 ? (
                    <div id="unapplied-edits-box" className="p-3 rounded bg-amber-950/40 border-2 border-amber-800 text-xs space-y-1">
                      <p className="font-bold text-amber-300 flex items-center gap-1.5 text-xs md:text-sm">
                        <AlertTriangle className="w-4 h-4" />
                        {rerunResult.unapplied_edits.length} edit(s) could not be re-applied:
                      </p>
                      <ul className="text-xs text-[var(--muted)] list-disc list-inside space-y-0.5 font-mono">
                        {rerunResult.unapplied_edits.map((item, idx) => (
                          <li key={idx}>
                            {item.op}: {item.reason || JSON.stringify(item)}
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : (
                    <p id="all-edits-survived-msg" className="text-xs md:text-sm text-emerald-400 font-bold flex items-center gap-2">
                      <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                      All organizer edits survived and were re-applied by stable face ID anchors!
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* AI Face Recognition Models */}
            <div className="settings-panel p-5 space-y-3.5">
              <div className="flex items-center justify-between border-b-2 border-[var(--line)] pb-2.5">
                <div className="flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-[var(--accent)]" />
                  <span className="text-sm md:text-base font-extrabold uppercase tracking-wider text-[var(--text)]">
                    Face Recognition Models
                  </span>
                </div>
              </div>

              <p className="text-xs text-[var(--muted)] m-0 leading-relaxed">
                CatLog uses InsightFace deep learning models (<code className="text-[var(--accent)]">buffalo_l</code>: SCRFD detector + ResNet50 ArcFace) to detect faces and compute normalized 512-d embeddings.
              </p>

              <ModelDownloadBanner />
            </div>

            {/* System Diagnostics & Privacy */}
            <div className="settings-panel p-5 space-y-3.5">
              <div className="flex items-center justify-between border-b-2 border-[var(--line)] pb-2.5">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-[var(--accent)]" />
                  <span className="text-sm md:text-base font-extrabold uppercase tracking-wider text-[var(--text)]">
                    System Diagnostics & Privacy
                  </span>
                </div>
                <CopyDiagnosticsButton variant="secondary" showPrivacyHint={false} />
              </div>

              <p className="text-xs text-[var(--muted)] m-0 leading-relaxed">
                Generate a privacy-safe diagnostic report for bug reporting on GitHub.
                The report strictly contains system details (OS, Python version, CatLog build, settings hash)
                and counts of photos and clusters.
              </p>

              <div className="p-3 rounded bg-[var(--input)] border border-[var(--panel-border)] text-[11px] text-[var(--muted)] space-y-1">
                <span className="font-bold text-[var(--text)] block">Privacy Guarantee:</span>
                <ul className="list-disc list-inside space-y-0.5 font-mono text-[10px]">
                  <li>ZERO personal photos or facial crops</li>
                  <li>ZERO local folder or file paths</li>
                  <li>ZERO Google Drive URLs or API keys</li>
                  <li>ZERO attendee names or biometrics</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
