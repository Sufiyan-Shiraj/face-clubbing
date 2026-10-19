import React, { useState, useEffect, useLayoutEffect, useCallback, useRef } from 'react';
import ReactDOM from 'react-dom';
import { ActiveTab } from '../types';
import { RisoTheme } from './Header';
import {
  X,
  ChevronLeft,
  ChevronRight,
  FastForward,
  Sparkles,
} from 'lucide-react';

export interface TutorialSpotlightStep {
  id: string;
  tab: ActiveTab;
  subTab?: 'people' | 'suggestions' | 'unrecognized';
  selectPeopleIds?: string[];
  sourceMode?: 'drive' | 'local' | 'zip';
  selector: string;
  fallbackSelector?: string;
  pageTitle: string;
  stepTitle: string;
  description: string;
  preferredPlacement?: 'bottom' | 'top' | 'right' | 'left';
  mascotPose?: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8;
}

export const TUTORIAL_SPOTLIGHT_STEPS: TutorialSpotlightStep[] = [
  // --- 01 SOURCE ---
  {
    id: 'source-modes',
    tab: 'home',
    sourceMode: 'drive',
    selector: '#source-mode-nav, .source-mode-nav',
    fallbackSelector: '#btn-source-drive',
    pageTitle: '01 SOURCE • INPUT OPTIONS',
    stepTitle: 'Photo Source Modes',
    description:
      'Choose where your event photos live: Google Drive (stream directly from a public folder link without OAuth), Local Folder (on-device hard drive/SD card), or Zip Archive.',
    preferredPlacement: 'bottom',
    mascotPose: 1, // Hello
  },

  // --- 02 SCAN ---
  {
    id: 'scan-pipeline-logs',
    tab: 'progress',
    selector: '#btn-view-all-logs',
    fallbackSelector: '#btn-detach-bottom',
    pageTitle: '02 SCAN • LIVE ENGINE & LOGS',
    stepTitle: 'Detachable Activity Logs',
    description:
      'Watch real-time face detection, InsightFace 512-D embeddings, and clustering. Click "Open Logs Window" or "Detach" to view all engine activity in a live modal or separate floating window.',
    preferredPlacement: 'top',
    mascotPose: 5, // Working on laptop
  },

  // --- 03 REVIEW: SELECTION & MULTI-MERGE ---
  {
    id: 'review-merge',
    tab: 'people',
    subTab: 'people',
    selectPeopleIds: ['demo_p001', 'demo_p002'],
    selector: '#merge-action-banner, #merge-selected-btn, [data-testid="person-card"]',
    fallbackSelector: '#people-cards-grid',
    pageTitle: '03 REVIEW • SELECTION & MERGE',
    stepTitle: 'Multi-Select & Batch Merge',
    description:
      'All attendees are clustered by identity. Select multiple people using the card checkboxes to merge duplicate clusters with one click. Instant Undo lets you revert any merge anytime.',
    preferredPlacement: 'bottom',
    mascotPose: 3, // Pointing
  },

  // --- 03 REVIEW: SUGGESTIONS ---
  {
    id: 'review-suggestions',
    tab: 'people',
    subTab: 'suggestions',
    selector: '#suggestions-list, [data-testid^="suggestion-card-"]',
    fallbackSelector: '.review-tabs-bar',
    pageTitle: '03 REVIEW • SMART MATCH SUGGESTIONS',
    stepTitle: 'Borderline Match Suggestions',
    description:
      'Pairs that fall in the "maybe" range (between auto-merge and the suggestion cap) appear here. Compare both faces side-by-side and click "Accept & Merge" or "Reject".',
    preferredPlacement: 'bottom',
    mascotPose: 2, // Looking around / examining
  },

  // --- 03 REVIEW: UNRECOGNIZED ---
  {
    id: 'review-unrecognized',
    tab: 'people',
    subTab: 'unrecognized',
    selector: '#unrec-faces-grid, #unrecognized-triage-container',
    fallbackSelector: '.review-tabs-bar',
    pageTitle: '03 REVIEW • UNRECOGNIZED TRIAGE',
    stepTitle: 'Unrecognized Faces Triage',
    description:
      'Low-confidence, blurry, or side-angle faces that missed cluster thresholds are gathered here. Select unassigned faces and quickly assign them to an attendee or create a new person.',
    preferredPlacement: 'bottom',
    mascotPose: 8, // Idle / snoozing while searching for stray faces
  },

  // --- 04 PUBLISH ---
  {
    id: 'export-publish',
    tab: 'export',
    selector: '#export-bundle-btn',
    fallbackSelector: '.export-actions-row',
    pageTitle: '04 PUBLISH • STANDALONE VIEWER',
    stepTitle: 'Zero-Server Offline Gallery',
    description:
      'Generates a self-contained gallery.html and static web bundle. Opens offline directly from a USB stick on any device or web host with zero backend dependencies.',
    preferredPlacement: 'top',
    mascotPose: 6, // Done! (checklist)
  },

  // --- 05 SETTINGS: SLIDER 1 ---
  {
    id: 'settings-distance',
    tab: 'settings',
    selector: '#card-slider-distance',
    fallbackSelector: '#setting-distance-threshold',
    pageTitle: '05 SETTINGS • SLIDER 1 OF 4',
    stepTitle: 'Primary Distance Cutoff (0.30 - 0.65)',
    description:
      'Controls initial clustering strictness. Lower (<0.45) = strict (matches only near-identical faces, creating separate clusters). Higher (>0.55) = loose (groups faces across angles, lighting, and expressions).',
    preferredPlacement: 'right',
    mascotPose: 3, // Pointing
  },

  // --- 05 SETTINGS: SLIDER 2 ---
  {
    id: 'settings-merge',
    tab: 'settings',
    selector: '#card-slider-merge',
    fallbackSelector: '#setting-merge-threshold',
    pageTitle: '05 SETTINGS • SLIDER 2 OF 4',
    stepTitle: 'Second-Pass Merge Cutoff (0.30 - 0.60)',
    description:
      'Consolidates sub-clusters by centroid distance. Lower (<0.45) keeps clusters separate. Higher (>0.55) aggressively auto-merges duplicate clusters into one person without asking.',
    preferredPlacement: 'left',
    mascotPose: 2, // Looking around / examining
  },

  // --- 05 SETTINGS: SLIDER 3 ---
  {
    id: 'settings-maybe',
    tab: 'settings',
    selector: '#card-slider-maybe',
    fallbackSelector: '#setting-maybe-threshold',
    pageTitle: '05 SETTINGS • SLIDER 3 OF 4',
    stepTitle: 'Suggestion Range Cap (0.50 - 0.75)',
    description:
      'Defines the radar sweep for the "Suggestions" tab. Borderline pairs between the merge cutoff and this ceiling are queued for 1-click human approval.',
    preferredPlacement: 'right',
    mascotPose: 5, // Working on laptop / tuning radar
  },

  // --- 05 SETTINGS: SLIDER 4 ---
  {
    id: 'settings-guard',
    tab: 'settings',
    selector: '#card-slider-guard',
    fallbackSelector: '#setting-same-photo-guard',
    pageTitle: '05 SETTINGS • SLIDER 4 OF 4',
    stepTitle: 'Same-Photo Guard Cap (0.20 - 0.50)',
    description:
      'The sanity-check barrier. Prevents merging two faces that appear together in the exact same photograph, guaranteeing distinct co-attendees never fuse.',
    preferredPlacement: 'left',
    mascotPose: 7, // Leaving / keeping distance
  },

  // --- 05 SETTINGS: DRIVE API KEY ---
  {
    id: 'settings-key',
    tab: 'settings',
    selector: '#card-settings-drive-key',
    fallbackSelector: '#setting-drive-api-key',
    pageTitle: '05 SETTINGS • GOOGLE DRIVE KEY',
    stepTitle: 'Optional Cloud API Key',
    description:
      'Stored locally in your browser. Raises Google Drive quota limits when scanning large event albums with hundreds of photos.',
    preferredPlacement: 'top',
    mascotPose: 4, // Excited
  },
];

export interface TutorialSpotlightProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigateTab: (tab: ActiveTab) => void;
  onSetReviewSubTab?: (subTab: 'people' | 'suggestions' | 'unrecognized') => void;
  onSetSelectedPeopleIds?: (ids: Set<string>) => void;
  onSetSourceMode?: (mode: 'drive' | 'local' | 'zip') => void;
  activeTab: ActiveTab;
  theme?: RisoTheme;
}

interface ElementRect {
  x: number;
  y: number;
  width: number;
  height: number;
  top: number;
  left: number;
  bottom: number;
  right: number;
}

export const TutorialSpotlight: React.FC<TutorialSpotlightProps> = ({
  isOpen,
  onClose,
  onNavigateTab,
  onSetReviewSubTab,
  onSetSelectedPeopleIds,
  onSetSourceMode,
  activeTab,
  theme = 't-dark',
}) => {
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [targetRect, setTargetRect] = useState<ElementRect | null>(null);
  const [targetFound, setTargetFound] = useState<boolean>(false);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [tooltipPos, setTooltipPos] = useState<{ top: number; left: number; arrowPlacement: 'top' | 'bottom' | 'left' | 'right'; arrowOffset: number }>({
    top: 100,
    left: 100,
    arrowPlacement: 'top',
    arrowOffset: 20,
  });

  const step = TUTORIAL_SPOTLIGHT_STEPS[currentStepIndex];

  // Map active theme to mascot subfolder: 'dark' | 'navy' | 'paper'
  const getThemeFolder = (t: RisoTheme): 'dark' | 'navy' | 'paper' => {
    if (t === 't-navy') return 'navy';
    if (t === 't-paper') return 'paper';
    return 'dark';
  };

  const themeFolder = getThemeFolder(theme);
  const poseNumber = step?.mascotPose || 1;
  const mascotSrc = `/mascot/${themeFolder}/pose${poseNumber}.png`;

  // Sync tab, subTab, selection, and sourceMode when step changes
  useEffect(() => {
    if (!isOpen || !step) return;

    if (step.tab !== activeTab) {
      onNavigateTab(step.tab);
    }

    if (step.subTab && onSetReviewSubTab) {
      onSetReviewSubTab(step.subTab);
    }

    if (step.selectPeopleIds && onSetSelectedPeopleIds) {
      onSetSelectedPeopleIds(new Set(step.selectPeopleIds));
    } else if (onSetSelectedPeopleIds) {
      onSetSelectedPeopleIds(new Set());
    }

    if (step.sourceMode && onSetSourceMode) {
      onSetSourceMode(step.sourceMode);
    }
  }, [isOpen, currentStepIndex, step?.tab, step?.subTab, step?.selectPeopleIds, step?.sourceMode]);

  // Locate highlighted element and compute bounding rect
  const updateRect = useCallback(() => {
    if (!isOpen || !step) return;

    let el = document.querySelector(step.selector) as HTMLElement | null;
    if (!el && step.fallbackSelector) {
      el = document.querySelector(step.fallbackSelector) as HTMLElement | null;
    }

    if (el) {
      const testR = el.getBoundingClientRect();
      if (testR.top < 60 || testR.bottom > window.innerHeight - 60) {
        try {
          el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        } catch (e) {}
      }

      const r = el.getBoundingClientRect();
      // Ensure element is somewhat in view
      if (r.width > 0 && r.height > 0) {
        setTargetRect({
          x: r.left,
          y: r.top,
          width: r.width,
          height: r.height,
          top: r.top,
          left: r.left,
          bottom: r.bottom,
          right: r.right,
        });
        setTargetFound(true);
        return;
      }
    }

    // Fallback: target main area if element not rendered yet
    const fallbackEl = (document.querySelector('.main') || document.body) as HTMLElement;
    const r = fallbackEl.getBoundingClientRect();
    setTargetRect({
      x: r.left + 40,
      y: r.top + 40,
      width: Math.min(r.width - 80, 600),
      height: 200,
      top: r.top + 40,
      left: r.left + 40,
      bottom: r.top + 240,
      right: r.left + 40 + Math.min(r.width - 80, 600),
    });
    setTargetFound(false);
  }, [isOpen, step]);

  useLayoutEffect(() => {
    updateRect();
    // Re-check after animations / tab mount
    const timer1 = setTimeout(updateRect, 100);
    const timer2 = setTimeout(updateRect, 300);

    window.addEventListener('resize', updateRect);
    window.addEventListener('scroll', updateRect, true);
    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      window.removeEventListener('resize', updateRect);
      window.removeEventListener('scroll', updateRect, true);
    };
  }, [updateRect, currentStepIndex, activeTab]);

  // Compute smart tooltip placement with arrow next to target element
  useLayoutEffect(() => {
    if (!targetRect) return;

    const tooltipEl = tooltipRef.current;
    const tooltipWidth = tooltipEl ? tooltipEl.offsetWidth : 410;
    const tooltipHeight = tooltipEl ? tooltipEl.offsetHeight : 240;
    const margin = 18;
    const vw = window.innerWidth;
    const vh = window.innerHeight;

    let placement: 'top' | 'bottom' | 'left' | 'right' = step.preferredPlacement || 'bottom';
    let top = 0;
    let left = 0;
    let arrowOffset = tooltipWidth / 2;

    // Check space
    const spaceBottom = vh - targetRect.bottom;
    const spaceTop = targetRect.top;
    const spaceRight = vw - targetRect.right;
    const spaceLeft = targetRect.left;

    if (placement === 'right') {
      if (spaceRight >= tooltipWidth + margin) {
        left = targetRect.right + margin;
        top = Math.max(16, Math.min(vh - tooltipHeight - 16, targetRect.top + targetRect.height / 2 - tooltipHeight / 2));
      } else if (spaceLeft >= tooltipWidth + margin) {
        placement = 'left';
        left = targetRect.left - tooltipWidth - margin;
        top = Math.max(16, Math.min(vh - tooltipHeight - 16, targetRect.top + targetRect.height / 2 - tooltipHeight / 2));
      } else {
        placement = 'bottom';
      }
    } else if (placement === 'left') {
      if (spaceLeft >= tooltipWidth + margin) {
        left = targetRect.left - tooltipWidth - margin;
        top = Math.max(16, Math.min(vh - tooltipHeight - 16, targetRect.top + targetRect.height / 2 - tooltipHeight / 2));
      } else if (spaceRight >= tooltipWidth + margin) {
        placement = 'right';
        left = targetRect.right + margin;
        top = Math.max(16, Math.min(vh - tooltipHeight - 16, targetRect.top + targetRect.height / 2 - tooltipHeight / 2));
      } else {
        placement = 'bottom';
      }
    }

    if (placement === 'bottom') {
      if (spaceBottom >= tooltipHeight + margin || spaceBottom >= spaceTop) {
        top = targetRect.bottom + margin;
        left = Math.max(16, Math.min(vw - tooltipWidth - 16, targetRect.left + targetRect.width / 2 - tooltipWidth / 2));
        placement = 'bottom';
      } else {
        top = Math.max(16, targetRect.top - tooltipHeight - margin);
        left = Math.max(16, Math.min(vw - tooltipWidth - 16, targetRect.left + targetRect.width / 2 - tooltipWidth / 2));
        placement = 'top';
      }
    } else if (placement === 'top') {
      if (spaceTop >= tooltipHeight + margin) {
        top = targetRect.top - tooltipHeight - margin;
        left = Math.max(16, Math.min(vw - tooltipWidth - 16, targetRect.left + targetRect.width / 2 - tooltipWidth / 2));
      } else {
        top = targetRect.bottom + margin;
        left = Math.max(16, Math.min(vw - tooltipWidth - 16, targetRect.left + targetRect.width / 2 - tooltipWidth / 2));
        placement = 'bottom';
      }
    }

    // Align arrow to center of target
    if (placement === 'bottom' || placement === 'top') {
      const targetCenter = targetRect.left + targetRect.width / 2;
      arrowOffset = Math.max(24, Math.min(tooltipWidth - 24, targetCenter - left));
    } else {
      const targetCenterY = targetRect.top + targetRect.height / 2;
      arrowOffset = Math.max(24, Math.min(tooltipHeight - 24, targetCenterY - top));
    }

    setTooltipPos({
      top,
      left,
      arrowPlacement: placement,
      arrowOffset,
    });
  }, [targetRect, step]);

  // Keyboard navigation: ArrowRight / ArrowLeft / Escape
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        handleFinish();
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        handleNext();
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        handlePrev();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, currentStepIndex]);

  const handleNext = () => {
    if (currentStepIndex < TUTORIAL_SPOTLIGHT_STEPS.length - 1) {
      setCurrentStepIndex(currentStepIndex + 1);
    } else {
      handleFinish();
    }
  };

  const handlePrev = () => {
    if (currentStepIndex > 0) {
      setCurrentStepIndex(currentStepIndex - 1);
    }
  };

  // Skip current entire page/screen
  const handleSkipPage = () => {
    const currentTab = step.tab;
    const nextPageIndex = TUTORIAL_SPOTLIGHT_STEPS.findIndex(
      (s, idx) => idx > currentStepIndex && s.tab !== currentTab
    );

    if (nextPageIndex !== -1) {
      setCurrentStepIndex(nextPageIndex);
    } else {
      handleFinish();
    }
  };

  const handleFinish = () => {
    try {
      localStorage.setItem('photosorter-tutorial-seen', 'true');
    } catch (e) { }
    onSetSelectedPeopleIds?.(new Set());
    onSetReviewSubTab?.('people');
    onClose();
  };

  if (!isOpen || !step) return null;

  // Spotlight padding around element
  const pad = 6;
  const cutX = targetRect ? Math.max(0, targetRect.x - pad) : 0;
  const cutY = targetRect ? Math.max(0, targetRect.y - pad) : 0;
  const cutW = targetRect ? targetRect.width + pad * 2 : 0;
  const cutH = targetRect ? targetRect.height + pad * 2 : 0;

  const totalSteps = TUTORIAL_SPOTLIGHT_STEPS.length;
  const stepNumber = currentStepIndex + 1;

  const spotlightContent = (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={`CatLog Walkthrough: ${step.stepTitle}`}
      className="fixed inset-0 z-[99999] overflow-hidden select-none"
      style={{ pointerEvents: 'auto' }}
    >
      {/* SVG Dimming Mask with Cutout Hole */}
      <svg
        className="fixed inset-0 w-full h-full pointer-events-none"
        style={{ zIndex: 99998 }}
        aria-hidden="true"
      >
        <defs>
          <mask id="photosorter-spotlight-mask">
            {/* White covers entire viewport (opaque mask) */}
            <rect width="100%" height="100%" fill="white" />
            {/* Black hole cuts through to reveal the real UI */}
            {targetRect && (
              <rect
                x={cutX}
                y={cutY}
                width={cutW}
                height={cutH}
                rx="8"
                ry="8"
                fill="black"
              />
            )}
          </mask>
        </defs>

        {/* Translucent Dimming Layer covering everything EXCEPT the spotlight hole */}
        <rect
          width="100%"
          height="100%"
          fill="rgba(8, 7, 6, 0.76)"
          mask="url(#photosorter-spotlight-mask)"
          style={{ pointerEvents: 'auto' }}
          onClick={handleNext}
        />

        {/* Vibrant Tactile Risograph Frame Around Highlighted Cutout */}
        {targetRect && (
          <rect
            x={cutX}
            y={cutY}
            width={cutW}
            height={cutH}
            rx="8"
            ry="8"
            fill="none"
            stroke="var(--accent)"
            strokeWidth="2.5"
            strokeDasharray="6 3"
            style={{
              filter: 'drop-shadow(0 0 8px var(--accent))',
              transition: 'all 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
            }}
          />
        )}
      </svg>

      {/* Floating Tooltip Callout Box */}
      <div
        ref={tooltipRef}
        data-testid="tutorial-tooltip-box"
        className="fixed z-[99999] w-[410px] max-w-[92vw] rounded-lg shadow-2xl animate-in fade-in zoom-in-95 duration-200"
        style={{
          top: `${tooltipPos.top}px`,
          left: `${tooltipPos.left}px`,
          background: 'var(--panel)',
          border: '2px solid var(--panel-border)',
          color: 'var(--text)',
          boxShadow: '0 20px 45px rgba(0,0,0,0.7), 0 0 0 1px var(--line)',
          transition: 'top 0.25s cubic-bezier(0.16, 1, 0.3, 1), left 0.25s cubic-bezier(0.16, 1, 0.3, 1)',
        }}
      >
        {/* SVG Arrow Pointing Directly from Tooltip to Highlighted Element */}
        {tooltipPos.arrowPlacement === 'bottom' && (
          <div
            className="absolute -top-[11px]"
            style={{ left: `${tooltipPos.arrowOffset - 12}px` }}
          >
            <svg width="24" height="12" viewBox="0 0 24 12" fill="none">
              <path
                d="M12 0L24 12H0L12 0Z"
                fill="var(--panel)"
                stroke="var(--panel-border)"
                strokeWidth="2"
              />
            </svg>
          </div>
        )}
        {tooltipPos.arrowPlacement === 'top' && (
          <div
            className="absolute -bottom-[11px]"
            style={{ left: `${tooltipPos.arrowOffset - 12}px` }}
          >
            <svg width="24" height="12" viewBox="0 0 24 12" fill="none">
              <path
                d="M12 12L0 0H24L12 12Z"
                fill="var(--panel)"
                stroke="var(--panel-border)"
                strokeWidth="2"
              />
            </svg>
          </div>
        )}
        {tooltipPos.arrowPlacement === 'right' && (
          <div
            className="absolute -left-[11px]"
            style={{ top: `${tooltipPos.arrowOffset - 12}px` }}
          >
            <svg width="12" height="24" viewBox="0 0 12 24" fill="none">
              <path
                d="M0 12L12 24V0L0 12Z"
                fill="var(--panel)"
                stroke="var(--panel-border)"
                strokeWidth="2"
              />
            </svg>
          </div>
        )}
        {tooltipPos.arrowPlacement === 'left' && (
          <div
            className="absolute -right-[11px]"
            style={{ top: `${tooltipPos.arrowOffset - 12}px` }}
          >
            <svg width="12" height="24" viewBox="0 0 12 24" fill="none">
              <path
                d="M12 12L0 24V0L12 12Z"
                fill="var(--panel)"
                stroke="var(--panel-border)"
                strokeWidth="2"
              />
            </svg>
          </div>
        )}

        {/* Tooltip Header Row with Step Indicator & Actions */}
        <div
          className="flex items-center justify-between px-4 py-2.5 border-b"
          style={{ borderColor: 'var(--line)', background: 'var(--card-bg)' }}
        >
          <div className="flex items-center gap-2">
            <span
              className="text-[11px] font-black px-2 py-0.5 rounded font-mono tracking-wider shadow-sm"
              style={{
                background: 'var(--accent)',
                color: '#121110',
              }}
            >
              {stepNumber} / {totalSteps}
            </span>
            <span className="text-[10px] font-bold tracking-wider uppercase opacity-75">
              {step.pageTitle}
            </span>
          </div>

          <div className="flex items-center gap-1.5">
            <button
              type="button"
              id="tutorial-skip-page-btn"
              data-testid="tutorial-skip-page-btn"
              onClick={handleSkipPage}
              className="px-2 py-0.5 rounded text-[10px] font-bold flex items-center gap-1 opacity-70 hover:opacity-100 transition-opacity"
              style={{
                background: 'rgba(255,255,255,0.06)',
                border: '1px solid var(--line)',
                color: 'var(--text)',
              }}
              title="Skip remaining steps on this page"
            >
              <FastForward className="w-3 h-3" />
              <span>Skip page</span>
            </button>

            <button
              type="button"
              id="tutorial-exit-btn"
              data-testid="tutorial-exit-btn"
              onClick={handleFinish}
              className="p-1 rounded opacity-70 hover:opacity-100 transition-opacity"
              style={{ color: 'var(--text)' }}
              title="Exit tutorial (Esc)"
              aria-label="Exit tutorial"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Tooltip Body: Title, Pedagogical Explanation & Theme-Matched Mascot */}
        <div className="p-4">
          <div className="flex items-start gap-3.5">
            <div className="flex-1 min-w-0 space-y-1.5">
              <h3 className="text-base font-black tracking-tight leading-snug text-[var(--text)]">
                {step.stepTitle}
              </h3>
              <p className="text-xs leading-relaxed opacity-90 font-medium">
                {step.description}
              </p>
            </div>

            {/* Theme-Adaptive Camera Cat Mascot Sticker */}
            <div
              className="shrink-0 w-20 h-20 -mt-1 flex items-center justify-center rounded-lg select-none"
              style={{
                filter: 'drop-shadow(0 4px 8px rgba(0,0,0,0.35))',
              }}
            >
              <img
                src={mascotSrc}
                alt={`Camera Cat Mascot Pose ${poseNumber}`}
                data-testid="tutorial-mascot-img"
                className="max-w-full max-h-full object-contain pointer-events-none transform hover:scale-105 transition-transform duration-200"
              />
            </div>
          </div>
        </div>

        {/* Tooltip Footer: Back & Next Buttons + Keyboard Hint */}
        <div
          className="flex items-center justify-between px-4 py-2.5 border-t"
          style={{ borderColor: 'var(--line)', background: 'var(--card-bg)' }}
        >
          <div className="text-[10px] font-mono text-[var(--muted)] hidden sm:block">
            Use <span className="font-bold text-[var(--text)]">←</span> / <span className="font-bold text-[var(--text)]">→</span> to navigate
          </div>

          <div className="flex items-center gap-2 ml-auto">
            <button
              type="button"
              id="tutorial-prev-btn"
              data-testid="tutorial-prev-btn"
              onClick={handlePrev}
              disabled={currentStepIndex === 0}
              className={`flex items-center gap-1 px-2.5 py-1 rounded text-xs font-bold transition-all ${
                currentStepIndex === 0 ? 'opacity-30 cursor-not-allowed' : 'hover:scale-105'
              }`}
              style={{
                background: 'rgba(255,255,255,0.06)',
                border: '1px solid var(--line)',
                color: 'var(--text)',
              }}
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              <span>Back</span>
            </button>

            <button
              type="button"
              id="tutorial-next-btn"
              data-testid="tutorial-next-btn"
              onClick={handleNext}
              className="flex items-center gap-1 px-3.5 py-1 rounded text-xs font-black tracking-wide uppercase transition-all shadow hover:scale-105"
              style={{
                background: 'var(--accent)',
                color: '#121110',
                border: '1.5px solid var(--accent)',
              }}
            >
              <span>{currentStepIndex === totalSteps - 1 ? 'Finish' : 'Next'}</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  if (typeof document !== 'undefined' && document.body) {
    return ReactDOM.createPortal(spotlightContent, document.body);
  }
  return spotlightContent;
};
