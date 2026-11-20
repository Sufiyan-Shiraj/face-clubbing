import React, { useState, useEffect } from 'react';
import {
  X,
  Compass,
  FolderOpen,
  Cpu,
  Users,
  Share2,
  Keyboard,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  HardDrive,
  Download,
  AlertTriangle,
  Layers,
  Undo2,
  FileArchive,
  Eye,
  Sliders,
} from 'lucide-react';
import { RisoTheme } from './Header';

export interface TutorialHandbookModalProps {
  isOpen: boolean;
  onClose: () => void;
  onStartSpotlightTour: () => void;
  theme?: RisoTheme;
  initialTab?: 'sources' | 'pipeline' | 'review' | 'export' | 'shortcuts';
}

type HandbookTab = 'sources' | 'pipeline' | 'review' | 'export' | 'shortcuts';

export const TutorialHandbookModal: React.FC<TutorialHandbookModalProps> = ({
  isOpen,
  onClose,
  onStartSpotlightTour,
  theme = 't-dark',
  initialTab = 'sources',
}) => {
  const [activeTab, setActiveTab] = useState<HandbookTab>(initialTab);

  useEffect(() => {
    if (isOpen) {
      setActiveTab(initialTab);
    }
  }, [isOpen, initialTab]);

  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      } else if (e.key === 'ArrowRight' && !['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement)?.tagName)) {
        const tabs: HandbookTab[] = ['sources', 'pipeline', 'review', 'export', 'shortcuts'];
        const nextIdx = (tabs.indexOf(activeTab) + 1) % tabs.length;
        setActiveTab(tabs[nextIdx]);
      } else if (e.key === 'ArrowLeft' && !['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement)?.tagName)) {
        const tabs: HandbookTab[] = ['sources', 'pipeline', 'review', 'export', 'shortcuts'];
        const prevIdx = (tabs.indexOf(activeTab) - 1 + tabs.length) % tabs.length;
        setActiveTab(tabs[prevIdx]);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, activeTab, onClose]);

  if (!isOpen) return null;

  const getThemeFolder = (t: RisoTheme): 'dark' | 'navy' | 'paper' => {
    if (t === 't-navy') return 'navy';
    if (t === 't-paper') return 'paper';
    return 'dark';
  };
  const themeFolder = getThemeFolder(theme);

  const getMascotSrc = (pose: number) => `/mascot/${themeFolder}/pose${pose}.png`;

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-5 bg-black/75 backdrop-blur-sm ${theme}`}
      data-testid="tutorial-handbook-modal"
    >
      <div
        className="relative w-full max-w-4xl overflow-hidden flex flex-col max-h-[92vh] rounded"
        style={{
          background: 'var(--bg)',
          border: '2px solid var(--line)',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.75), 0 0 0 1px var(--line)',
          color: 'var(--text)',
          fontFamily: '"JetBrains Mono", monospace',
        }}
      >
        {/* Header Bar */}
        <div
          className="flex-shrink-0 flex items-center justify-between px-5 py-3.5 border-b"
          style={{ borderColor: 'var(--line)', background: 'var(--panel)' }}
        >
          <div className="flex items-center gap-3">
            <div
              className="w-8 h-8 rounded flex items-center justify-center font-bold"
              style={{
                background: 'var(--bg)',
                border: '1.5px solid var(--accent)',
                color: 'var(--accent)',
              }}
            >
              <Compass className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-base font-bold font-mono tracking-tight" style={{ color: 'var(--text)' }}>
                CatLog Visual Handbook &amp; Guide
              </h2>
              <p className="text-xs" style={{ color: 'var(--muted)' }}>
                Master event photo clustering, review workflows, and zero-server sharing
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              id="btn-handbook-start-spotlight"
              data-testid="btn-handbook-start-spotlight"
              onClick={() => {
                onClose();
                onStartSpotlightTour();
              }}
              className="btn sm inline-flex items-center gap-1.5"
              style={{
                background: 'rgba(234, 88, 12, 0.12)',
                borderColor: 'var(--accent)',
                color: 'var(--accent)',
              }}
              title="Launch interactive step-by-step tour across live screens"
            >
              <Sparkles className="w-3.5 h-3.5 text-amber-500" />
              <span className="font-bold text-xs">Start In-App Tour</span>
            </button>
            <button
              type="button"
              onClick={onClose}
              className="riso-btn-sec"
              style={{ width: '34px', height: '34px', padding: 0 }}
              title="Close Handbook (Esc)"
              aria-label="Close Handbook"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Tab Navigation Navigation */}
        <div
          className="flex-shrink-0 flex items-center gap-1 px-4 py-2 border-b overflow-x-auto text-xs"
          style={{ borderColor: 'var(--line)', background: 'rgba(0,0,0,0.08)' }}
        >
          {[
            { id: 'sources' as HandbookTab, label: '1. Getting Photos In', icon: FolderOpen },
            { id: 'pipeline' as HandbookTab, label: '2. Offline AI Pipeline', icon: Cpu },
            { id: 'review' as HandbookTab, label: '3. Review & Merging', icon: Users },
            { id: 'export' as HandbookTab, label: '4. Export & Sharing', icon: Share2 },
            { id: 'shortcuts' as HandbookTab, label: '5. Shortcuts Cheatsheet', icon: Keyboard },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                type="button"
                id={`tab-handbook-${tab.id}`}
                data-testid={`tab-handbook-${tab.id}`}
                onClick={() => setActiveTab(tab.id)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded transition-all font-semibold whitespace-nowrap"
                style={{
                  background: isActive ? 'var(--panel)' : 'transparent',
                  border: isActive ? '1px solid var(--line)' : '1px solid transparent',
                  color: isActive ? 'var(--accent)' : 'var(--muted)',
                  boxShadow: isActive ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
                }}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Tab Body Content */}
        <div className="flex-1 overflow-y-auto p-5 sm:p-6 space-y-5">
          {/* TAB 1: GETTING PHOTOS IN */}
          {activeTab === 'sources' && (
            <div className="space-y-4" data-testid="handbook-tab-sources">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <span className="text-[11px] font-bold text-[var(--accent)] uppercase tracking-wider">
                    Chapter 01 • Input Sources
                  </span>
                  <h3 className="text-lg font-bold text-[var(--text)]">
                    Three Ways to Bring Your Photos In
                  </h3>
                  <p className="text-xs text-[var(--muted)] leading-relaxed max-w-xl">
                    CatLog supports scanning from single directories, multiple mixed sources at once, zip archives, or directly streaming public Google Drive albums.
                  </p>
                </div>
                <img
                  src={getMascotSrc(1)}
                  alt="CatLog Mascot Hello"
                  className="w-16 h-16 object-contain shrink-0 hidden sm:block"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
                {/* Card 1: Local Folders & ZIPs */}
                <div
                  className="p-3.5 rounded border space-y-2"
                  style={{ background: 'var(--panel)', borderColor: 'var(--line)' }}
                >
                  <div className="flex items-center gap-2 text-[var(--accent)] font-bold text-xs">
                    <HardDrive className="w-4 h-4" />
                    <span>Local Folder or SD Card</span>
                  </div>
                  <p className="text-[11px] text-[var(--muted)] leading-relaxed">
                    Select any local directory or SD card partition. Subfolders are automatically crawled up to 5 levels deep, or customized in Scan Options.
                  </p>
                  <span className="inline-block text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--bg)] border border-[var(--line)] text-[var(--muted)]">
                    Fastest • Direct Disk I/O
                  </span>
                </div>

                {/* Card 2: ZIP Archives */}
                <div
                  className="p-3.5 rounded border space-y-2"
                  style={{ background: 'var(--panel)', borderColor: 'var(--line)' }}
                >
                  <div className="flex items-center gap-2 text-indigo-400 font-bold text-xs">
                    <FileArchive className="w-4 h-4" />
                    <span>Zip Archives (.zip)</span>
                  </div>
                  <p className="text-[11px] text-[var(--muted)] leading-relaxed">
                    Ideal for photo batch exports. CatLog streams and unpacks photos directly in memory without having to manually extract gigabytes beforehand.
                  </p>
                  <span className="inline-block text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--bg)] border border-[var(--line)] text-[var(--muted)]">
                    1-Click Unpack
                  </span>
                </div>

                {/* Card 3: Google Drive */}
                <div
                  className="p-3.5 rounded border space-y-2"
                  style={{ background: 'var(--panel)', borderColor: 'var(--line)' }}
                >
                  <div className="flex items-center gap-2 text-blue-400 font-bold text-xs">
                    <Download className="w-4 h-4" />
                    <span>Google Drive Link</span>
                  </div>
                  <p className="text-[11px] text-[var(--muted)] leading-relaxed">
                    Paste any public folder URL. CatLog automatically checks disk space, calculates size estimates across image quality tiers, and streams photos safely.
                  </p>
                  <span className="inline-block text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--bg)] border border-[var(--line)] text-[var(--muted)]">
                    Public Link • No OAuth
                  </span>
                </div>
              </div>

              {/* Google Photos Callout Box */}
              <div
                className="p-4 rounded border text-xs space-y-2"
                style={{
                  background: 'rgba(245, 158, 11, 0.08)',
                  borderColor: '#f59e0b',
                }}
              >
                <div className="flex items-center gap-2 font-bold text-amber-500">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span>Have a Google Photos Album? Use the 1-Click ZIP Workflow</span>
                </div>
                <p className="text-[11px] text-[var(--text)] leading-relaxed">
                  Due to Google Photos API rules (updated March 2025), shared album links cannot be scraped directly. The easiest 10-second workaround:
                </p>
                <div className="p-2.5 rounded bg-[var(--bg)] border border-[var(--line)] font-mono text-[11px] space-y-1">
                  <div>1. In Google Photos, press <kbd className="px-1.5 py-0.5 rounded bg-[var(--panel)] border border-[var(--line)] font-bold">Shift + D</kbd> (or click <strong>⋮ &rarr; Download all</strong>).</div>
                  <div>2. In CatLog, choose <strong>Zip Archive</strong> and pick the downloaded zip. CatLog sorts it immediately!</div>
                </div>
              </div>

              {/* Multi-Source Queue Tip */}
              <div
                className="p-3.5 rounded border text-xs flex items-center justify-between"
                style={{ background: 'var(--panel)', borderColor: 'var(--line)' }}
              >
                <div className="flex items-center gap-2.5">
                  <Layers className="w-4 h-4 text-[var(--accent)]" />
                  <div>
                    <span className="font-bold text-[var(--text)]">Multi-Source Queueing</span>
                    <p className="text-[11px] text-[var(--muted)]">Click &ldquo;+ Add to Sources List&rdquo; to merge local folders, camera cards, and Drive links into a unified scan.</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: OFFLINE AI PIPELINE */}
          {activeTab === 'pipeline' && (
            <div className="space-y-4" data-testid="handbook-tab-pipeline">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <span className="text-[11px] font-bold text-[var(--accent)] uppercase tracking-wider">
                    Chapter 02 • Local Intelligence
                  </span>
                  <h3 className="text-lg font-bold text-[var(--text)]">
                    100% Offline AI Face Recognition
                  </h3>
                  <p className="text-xs text-[var(--muted)] leading-relaxed max-w-xl">
                    Your photos never leave your machine. CatLog runs high-performance InsightFace models entirely on local ONNX Runtime inference engines.
                  </p>
                </div>
                <img
                  src={getMascotSrc(5)}
                  alt="CatLog Mascot Working"
                  className="w-16 h-16 object-contain shrink-0 hidden sm:block"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
                <div className="p-3.5 rounded border space-y-2" style={{ background: 'var(--panel)', borderColor: 'var(--line)' }}>
                  <div className="font-bold text-xs text-[var(--accent)] flex items-center gap-2">
                    <span className="w-5 h-5 rounded-full bg-[var(--bg)] border border-[var(--line)] flex items-center justify-center text-[10px]">1</span>
                    <span>Face Detection</span>
                  </div>
                  <p className="text-[11px] text-[var(--muted)] leading-relaxed">
                    Scans each image with SCRFD neural detectors to locate attendee faces, filter out micro-crops &lt;64px, and align 3D landmark points.
                  </p>
                </div>

                <div className="p-3.5 rounded border space-y-2" style={{ background: 'var(--panel)', borderColor: 'var(--line)' }}>
                  <div className="font-bold text-xs text-blue-400 flex items-center gap-2">
                    <span className="w-5 h-5 rounded-full bg-[var(--bg)] border border-[var(--line)] flex items-center justify-center text-[10px]">2</span>
                    <span>512-D Embeddings</span>
                  </div>
                  <p className="text-[11px] text-[var(--muted)] leading-relaxed">
                    Passes normalized crops through ArcFace to generate mathematical 512-dimensional facial representations invariant to expression and lighting.
                  </p>
                </div>

                <div className="p-3.5 rounded border space-y-2" style={{ background: 'var(--panel)', borderColor: 'var(--line)' }}>
                  <div className="font-bold text-xs text-emerald-400 flex items-center gap-2">
                    <span className="w-5 h-5 rounded-full bg-[var(--bg)] border border-[var(--line)] flex items-center justify-center text-[10px]">3</span>
                    <span>Constrained Clustering</span>
                  </div>
                  <p className="text-[11px] text-[var(--muted)] leading-relaxed">
                    Agglomerates faces with cosine distance thresholds, enforced by Same-Photo Negative Guards to guarantee co-present people never fuse.
                  </p>
                </div>
              </div>

              {/* Detachable Logs Note */}
              <div
                className="p-3.5 rounded border text-xs space-y-1.5"
                style={{ background: 'var(--panel)', borderColor: 'var(--line)' }}
              >
                <div className="flex items-center gap-2 text-[var(--text)] font-bold">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>Real-Time Detachable Activity Window</span>
                </div>
                <p className="text-[11px] text-[var(--muted)] leading-relaxed">
                  During a scan, click <strong>&ldquo;Detach&rdquo;</strong> to pop out the log viewer into an independent floating desktop window. You can monitor progress while multitasking.
                </p>
              </div>
            </div>
          )}

          {/* TAB 3: REVIEW & MERGING */}
          {activeTab === 'review' && (
            <div className="space-y-4" data-testid="handbook-tab-review">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <span className="text-[11px] font-bold text-[var(--accent)] uppercase tracking-wider">
                    Chapter 03 • Curation &amp; Triage
                  </span>
                  <h3 className="text-lg font-bold text-[var(--text)]">
                    Reviewing Attendees &amp; Batch Merging
                  </h3>
                  <p className="text-xs text-[var(--muted)] leading-relaxed max-w-xl">
                    Quickly verify identities, combine clusters, review match suggestions, and inspect individual face boxes with non-destructive instant undo.
                  </p>
                </div>
                <img
                  src={getMascotSrc(3)}
                  alt="CatLog Mascot Pointing"
                  className="w-16 h-16 object-contain shrink-0 hidden sm:block"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                <div className="p-3.5 rounded border space-y-2" style={{ background: 'var(--panel)', borderColor: 'var(--line)' }}>
                  <div className="font-bold text-xs text-[var(--accent)] flex items-center gap-2">
                    <Users className="w-4 h-4" />
                    <span>Multi-Select &amp; Batch Merge</span>
                  </div>
                  <p className="text-[11px] text-[var(--muted)] leading-relaxed">
                    Check the boxes on multiple cards representing the same attendee. Click <strong>&ldquo;Merge Selected&rdquo;</strong> in the bottom banner. They instantly combine under the chosen label.
                  </p>
                  <div className="text-[10px] text-[var(--muted)] flex items-center gap-1.5 pt-1">
                    <Undo2 className="w-3.5 h-3.5 text-blue-400" />
                    <span>Mistake? Press <kbd className="font-mono font-bold px-1 py-0.5 rounded bg-[var(--bg)] border border-[var(--line)]">Ctrl + Z</kbd> to undo instantly.</span>
                  </div>
                </div>

                <div className="p-3.5 rounded border space-y-2" style={{ background: 'var(--panel)', borderColor: 'var(--line)' }}>
                  <div className="font-bold text-xs text-amber-400 flex items-center gap-2">
                    <Sparkles className="w-4 h-4" />
                    <span>Match Suggestions</span>
                  </div>
                  <p className="text-[11px] text-[var(--muted)] leading-relaxed">
                    Pairs falling in the borderline range appear in the <strong>Suggestions</strong> subtab. Inspect side-by-side face comparisons and click <strong>Accept</strong> or <strong>Reject</strong> with 1 click.
                  </p>
                </div>

                <div className="p-3.5 rounded border space-y-2" style={{ background: 'var(--panel)', borderColor: 'var(--line)' }}>
                  <div className="font-bold text-xs text-purple-400 flex items-center gap-2">
                    <Eye className="w-4 h-4" />
                    <span>Inspect Faces Drawer</span>
                  </div>
                  <p className="text-[11px] text-[var(--muted)] leading-relaxed">
                    Click any photo in the viewer and press <strong>&ldquo;Inspect Faces&rdquo;</strong> to reveal all face boxes. Reassign mislabeled faces to existing people, create new people, or detach faces.
                  </p>
                </div>

                <div className="p-3.5 rounded border space-y-2" style={{ background: 'var(--panel)', borderColor: 'var(--line)' }}>
                  <div className="font-bold text-xs text-emerald-400 flex items-center gap-2">
                    <Layers className="w-4 h-4" />
                    <span>Unrecognized Triage</span>
                  </div>
                  <p className="text-[11px] text-[var(--muted)] leading-relaxed">
                    Blurry, side-profile, or extreme yaw angle faces are safely collected in the <strong>Unrecognized</strong> subtab. Assign them in bulk to known people or create singletons with one click.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: EXPORT & SHARING */}
          {activeTab === 'export' && (
            <div className="space-y-4" data-testid="handbook-tab-export">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <span className="text-[11px] font-bold text-[var(--accent)] uppercase tracking-wider">
                    Chapter 04 • Distribution
                  </span>
                  <h3 className="text-lg font-bold text-[var(--text)]">
                    Standalone Zero-Server Gallery &amp; Project Merges
                  </h3>
                  <p className="text-xs text-[var(--muted)] leading-relaxed max-w-xl">
                    Create portable offline photo galleries that attendees can open on any browser, or merge separate event days together into a unified project.
                  </p>
                </div>
                <img
                  src={getMascotSrc(6)}
                  alt="CatLog Mascot Done"
                  className="w-16 h-16 object-contain shrink-0 hidden sm:block"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
                <div className="p-4 rounded border space-y-2" style={{ background: 'var(--panel)', borderColor: 'var(--line)' }}>
                  <div className="font-bold text-xs text-emerald-400 flex items-center gap-2">
                    <Share2 className="w-4 h-4" />
                    <span>Zero-Server Static Gallery</span>
                  </div>
                  <p className="text-[11px] text-[var(--muted)] leading-relaxed">
                    Export compiles a clean, static web bundle containing <code className="font-mono text-[var(--text)]">gallery.html</code>, thumbnail sprites, and JSON index. Attendees can double-click and browse offline directly from a USB stick without installing any software.
                  </p>
                  <ul className="text-[10px] text-[var(--muted)] list-disc pl-4 space-y-0.5">
                    <li>100% Client-Side Search by Name</li>
                    <li>Full Resolution Photo Lightbox</li>
                    <li>Zero server or internet connection required</li>
                  </ul>
                </div>

                <div className="p-4 rounded border space-y-2" style={{ background: 'var(--panel)', borderColor: 'var(--line)' }}>
                  <div className="font-bold text-xs text-indigo-400 flex items-center gap-2">
                    <Sliders className="w-4 h-4" />
                    <span>Merge Two Projects</span>
                  </div>
                  <p className="text-[11px] text-[var(--muted)] leading-relaxed">
                    Shot Day 1 and Day 2 of a multi-day conference? Go to <strong>File &rarr; Merge Projects</strong>. CatLog safely unions photo sets, identifies shared faces, and lets you resolve naming conflicts side-by-side without touching the original projects.
                  </p>
                  <ul className="text-[10px] text-[var(--muted)] list-disc pl-4 space-y-0.5">
                    <li>Side-by-side radio conflict resolution</li>
                    <li>Leaves original project folders intact</li>
                    <li>Creates a unified master gallery</li>
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: KEYBOARD SHORTCUTS */}
          {activeTab === 'shortcuts' && (
            <div className="space-y-4" data-testid="handbook-tab-shortcuts">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1">
                  <span className="text-[11px] font-bold text-[var(--accent)] uppercase tracking-wider">
                    Chapter 05 • Power User Tools
                  </span>
                  <h3 className="text-lg font-bold text-[var(--text)]">
                    Keyboard Shortcuts Cheatsheet
                  </h3>
                  <p className="text-xs text-[var(--muted)] leading-relaxed max-w-xl">
                    Navigate, merge, undo, and review without lifting your hands from the keyboard.
                  </p>
                </div>
                <img
                  src={getMascotSrc(4)}
                  alt="CatLog Mascot Excited"
                  className="w-16 h-16 object-contain shrink-0 hidden sm:block"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2 text-xs">
                {/* Global Shortcuts */}
                <div className="p-3.5 rounded border space-y-2.5" style={{ background: 'var(--panel)', borderColor: 'var(--line)' }}>
                  <h4 className="font-bold text-xs text-[var(--accent)]">Global Shortcuts</h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] text-[var(--muted)]">Open Handbook &amp; Cheatsheet</span>
                      <kbd className="px-2 py-0.5 rounded font-mono font-bold bg-[var(--bg)] border border-[var(--line)]">?</kbd>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] text-[var(--muted)]">Undo Last Edit</span>
                      <kbd className="px-2 py-0.5 rounded font-mono font-bold bg-[var(--bg)] border border-[var(--line)]">Ctrl + Z</kbd>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] text-[var(--muted)]">Open Saved Project</span>
                      <kbd className="px-2 py-0.5 rounded font-mono font-bold bg-[var(--bg)] border border-[var(--line)]">Ctrl + O</kbd>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] text-[var(--muted)]">New Project</span>
                      <kbd className="px-2 py-0.5 rounded font-mono font-bold bg-[var(--bg)] border border-[var(--line)]">Ctrl + N</kbd>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] text-[var(--muted)]">Jump to Screen (1-5)</span>
                      <kbd className="px-2 py-0.5 rounded font-mono font-bold bg-[var(--bg)] border border-[var(--line)]">1, 2, 3, 4, 5</kbd>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] text-[var(--muted)]">Close Active Modal / Drawer</span>
                      <kbd className="px-2 py-0.5 rounded font-mono font-bold bg-[var(--bg)] border border-[var(--line)]">Esc</kbd>
                    </div>
                  </div>
                </div>

                {/* Photo Viewer & Review Shortcuts */}
                <div className="p-3.5 rounded border space-y-2.5" style={{ background: 'var(--panel)', borderColor: 'var(--line)' }}>
                  <h4 className="font-bold text-xs text-blue-400">Review &amp; Photo Viewer</h4>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] text-[var(--muted)]">Next / Previous Photo</span>
                      <kbd className="px-2 py-0.5 rounded font-mono font-bold bg-[var(--bg)] border border-[var(--line)]">&larr; / &rarr;</kbd>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] text-[var(--muted)]">Zoom In / Out</span>
                      <kbd className="px-2 py-0.5 rounded font-mono font-bold bg-[var(--bg)] border border-[var(--line)]">Mouse Wheel</kbd>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] text-[var(--muted)]">Pan Photo Canvas</span>
                      <kbd className="px-2 py-0.5 rounded font-mono font-bold bg-[var(--bg)] border border-[var(--line)]">Click + Drag</kbd>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] text-[var(--muted)]">Select All People Cards</span>
                      <kbd className="px-2 py-0.5 rounded font-mono font-bold bg-[var(--bg)] border border-[var(--line)]">Ctrl + A</kbd>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-[11px] text-[var(--muted)]">Download All (Google Photos)</span>
                      <kbd className="px-2 py-0.5 rounded font-mono font-bold bg-[var(--bg)] border border-[var(--line)]">Shift + D</kbd>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer Bar */}
        <div
          className="flex-shrink-0 flex items-center justify-between px-5 py-3.5 border-t text-xs"
          style={{ borderColor: 'var(--line)', background: 'var(--panel)' }}
        >
          <div className="text-[11px] text-[var(--muted)] flex items-center gap-1.5 hidden sm:flex">
            <span>Use</span>
            <kbd className="px-1 py-0.5 rounded bg-[var(--bg)] border border-[var(--line)] font-bold">&larr;</kbd>
            <kbd className="px-1 py-0.5 rounded bg-[var(--bg)] border border-[var(--line)] font-bold">&rarr;</kbd>
            <span>to cycle chapters • Press</span>
            <kbd className="px-1 py-0.5 rounded bg-[var(--bg)] border border-[var(--line)] font-bold">Esc</kbd>
            <span>to close</span>
          </div>

          <div className="flex items-center gap-2 ml-auto">
            <button
              type="button"
              id="btn-handbook-got-it"
              data-testid="btn-handbook-got-it"
              onClick={onClose}
              className="btn pri sm px-5"
            >
              Got It
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
