import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { TutorialSpotlight, TUTORIAL_SPOTLIGHT_STEPS } from '../components/TutorialSpotlight';

describe('TutorialSpotlight - Streamlined Tour with In-Depth Slider Explanations', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders spotlight SVG mask and tooltip box with 11 total steps', () => {
    const handleClose = vi.fn();
    const handleNavigateTab = vi.fn();
    const handleSetSourceMode = vi.fn();
    const handleSetReviewSubTab = vi.fn();
    const handleSetSelectedPeopleIds = vi.fn();

    expect(TUTORIAL_SPOTLIGHT_STEPS).toHaveLength(11);

    render(
      <TutorialSpotlight
        isOpen={true}
        onClose={handleClose}
        onNavigateTab={handleNavigateTab}
        onSetReviewSubTab={handleSetReviewSubTab}
        onSetSelectedPeopleIds={handleSetSelectedPeopleIds}
        onSetSourceMode={handleSetSourceMode}
        activeTab="home"
        theme="t-dark"
      />
    );

    // Tooltip box exists
    const tooltip = screen.getByTestId('tutorial-tooltip-box');
    expect(tooltip).toBeTruthy();

    // Step 1 title and counter
    expect(screen.getByText(/1 \/ 11/i)).toBeTruthy();
    expect(screen.getByText(/Photo Source Modes/i)).toBeTruthy();
    expect(screen.getByText(/01 SOURCE • INPUT OPTIONS/i)).toBeTruthy();

    // Back button disabled on first step
    const prevBtn = screen.getByTestId('tutorial-prev-btn');
    expect(prevBtn).toHaveProperty('disabled', true);

    // Mascot image rendered with theme path and pose
    const mascotImg = screen.getByTestId('tutorial-mascot-img');
    expect(mascotImg).toBeTruthy();
    expect(mascotImg.getAttribute('src')).toBe('/mascot/dark/pose1.png');
  });

  it('renders theme-adaptive mascot image for navy and paper themes', () => {
    const { rerender } = render(
      <TutorialSpotlight
        isOpen={true}
        onClose={vi.fn()}
        onNavigateTab={vi.fn()}
        activeTab="home"
        theme="t-navy"
      />
    );

    let mascotImg = screen.getByTestId('tutorial-mascot-img');
    expect(mascotImg.getAttribute('src')).toBe('/mascot/navy/pose1.png');

    rerender(
      <TutorialSpotlight
        isOpen={true}
        onClose={vi.fn()}
        onNavigateTab={vi.fn()}
        activeTab="home"
        theme="t-paper"
      />
    );

    mascotImg = screen.getByTestId('tutorial-mascot-img');
    expect(mascotImg.getAttribute('src')).toBe('/mascot/paper/pose1.png');
  });

  it('navigates through steps sequentially and updates tabs, subtabs, and selection', () => {
    const handleClose = vi.fn();
    const handleNavigateTab = vi.fn();
    const handleSetReviewSubTab = vi.fn();
    const handleSetSelectedPeopleIds = vi.fn();
    const handleSetSourceMode = vi.fn();

    render(
      <TutorialSpotlight
        isOpen={true}
        onClose={handleClose}
        onNavigateTab={handleNavigateTab}
        onSetReviewSubTab={handleSetReviewSubTab}
        onSetSelectedPeopleIds={handleSetSelectedPeopleIds}
        onSetSourceMode={handleSetSourceMode}
        activeTab="home"
        theme="t-dark"
      />
    );

    const nextBtn = screen.getByTestId('tutorial-next-btn');

    // Step 1 -> Step 2 (Scan & Detachable Logs)
    fireEvent.click(nextBtn);
    expect(screen.getByText(/2 \/ 11/i)).toBeTruthy();
    expect(screen.getByText(/Detachable Activity Logs/i)).toBeTruthy();
    expect(handleNavigateTab).toHaveBeenCalledWith('progress');

    // Step 2 -> Step 3 (Review: Selection & Batch Merge)
    fireEvent.click(nextBtn);
    expect(screen.getByText(/3 \/ 11/i)).toBeTruthy();
    expect(screen.getByText(/Multi-Select & Batch Merge/i)).toBeTruthy();
    expect(handleNavigateTab).toHaveBeenCalledWith('people');
    expect(handleSetReviewSubTab).toHaveBeenCalledWith('people');
    expect(handleSetSelectedPeopleIds).toHaveBeenCalledWith(new Set(['demo_p001', 'demo_p002']));

    // Step 3 -> Step 4 (Review: Borderline Match Suggestions)
    fireEvent.click(nextBtn);
    expect(screen.getByText(/4 \/ 11/i)).toBeTruthy();
    expect(screen.getByText(/Borderline Match Suggestions/i)).toBeTruthy();
    expect(handleSetReviewSubTab).toHaveBeenCalledWith('suggestions');

    // Step 4 -> Step 5 (Review: Unrecognized Faces Triage)
    fireEvent.click(nextBtn);
    expect(screen.getByText(/5 \/ 11/i)).toBeTruthy();
    expect(screen.getByText(/Unrecognized Faces Triage/i)).toBeTruthy();
    expect(handleSetReviewSubTab).toHaveBeenCalledWith('unrecognized');

    // Step 5 -> Step 6 (Publish: Offline Gallery)
    fireEvent.click(nextBtn);
    expect(screen.getByText(/6 \/ 11/i)).toBeTruthy();
    expect(screen.getByText(/Zero-Server Offline Gallery/i)).toBeTruthy();
    expect(handleNavigateTab).toHaveBeenCalledWith('export');
  });

  it('explains what each of the 4 clustering sliders does in Settings', () => {
    const handleClose = vi.fn();
    const handleNavigateTab = vi.fn();
    const handleSetReviewSubTab = vi.fn();
    const handleSetSelectedPeopleIds = vi.fn();

    render(
      <TutorialSpotlight
        isOpen={true}
        onClose={handleClose}
        onNavigateTab={handleNavigateTab}
        onSetReviewSubTab={handleSetReviewSubTab}
        onSetSelectedPeopleIds={handleSetSelectedPeopleIds}
        activeTab="home"
        theme="t-dark"
      />
    );

    const nextBtn = screen.getByTestId('tutorial-next-btn');

    // Fast-forward to step 7 (Slider 1: Primary Distance Cutoff)
    for (let i = 0; i < 6; i++) {
      fireEvent.click(nextBtn);
    }

    // Step 7: Slider 1
    expect(screen.getByText(/7 \/ 11/i)).toBeTruthy();
    expect(screen.getByText(/Primary Distance Cutoff \(0.30 - 0.65\)/i)).toBeTruthy();
    expect(screen.getByText(/Controls initial clustering strictness/i)).toBeTruthy();

    // Step 8: Slider 2
    fireEvent.click(nextBtn);
    expect(screen.getByText(/8 \/ 11/i)).toBeTruthy();
    expect(screen.getByText(/Second-Pass Merge Cutoff \(0.30 - 0.60\)/i)).toBeTruthy();
    expect(screen.getByText(/Consolidates sub-clusters by centroid distance/i)).toBeTruthy();

    // Step 9: Slider 3
    fireEvent.click(nextBtn);
    expect(screen.getByText(/9 \/ 11/i)).toBeTruthy();
    expect(screen.getByText(/Suggestion Range Cap \(0.50 - 0.75\)/i)).toBeTruthy();
    expect(screen.getByText(/Defines the radar sweep for the "Suggestions" tab/i)).toBeTruthy();

    // Step 10: Slider 4
    fireEvent.click(nextBtn);
    expect(screen.getByText(/10 \/ 11/i)).toBeTruthy();
    expect(screen.getByText(/Same-Photo Guard Cap \(0.20 - 0.50\)/i)).toBeTruthy();
    expect(screen.getByText(/The sanity-check barrier\. Prevents merging two faces that appear together/i)).toBeTruthy();

    // Step 11: Drive API key
    fireEvent.click(nextBtn);
    expect(screen.getByText(/11 \/ 11/i)).toBeTruthy();
    expect(screen.getByText(/Optional Cloud API Key/i)).toBeTruthy();
  });

  it('jumps across pages when clicking "Skip page"', () => {
    const handleClose = vi.fn();
    const handleNavigateTab = vi.fn();

    render(
      <TutorialSpotlight
        isOpen={true}
        onClose={handleClose}
        onNavigateTab={handleNavigateTab}
        activeTab="home"
        theme="t-dark"
      />
    );

    // On Step 1 (tab: home). Skip page jumps to Step 2 (tab: progress)
    const skipPageBtn = screen.getByTestId('tutorial-skip-page-btn');
    fireEvent.click(skipPageBtn);
    expect(screen.getByText(/2 \/ 11/i)).toBeTruthy();
    expect(screen.getByText(/02 SCAN • LIVE ENGINE & LOGS/i)).toBeTruthy();

    // On Step 2 (tab: progress). Skip page jumps to Step 3 (tab: people)
    fireEvent.click(skipPageBtn);
    expect(screen.getByText(/3 \/ 11/i)).toBeTruthy();
    expect(screen.getByText(/03 REVIEW • SELECTION & MERGE/i)).toBeTruthy();

    // On Step 3 (tab: people). Skip page jumps to next page: Step 6 (tab: export)
    fireEvent.click(skipPageBtn);
    expect(screen.getByText(/6 \/ 11/i)).toBeTruthy();
    expect(screen.getByText(/04 PUBLISH • STANDALONE VIEWER/i)).toBeTruthy();
  });

  it('supports keyboard navigation via ArrowRight, ArrowLeft, and Escape', () => {
    const handleClose = vi.fn();
    const handleNavigateTab = vi.fn();

    render(
      <TutorialSpotlight
        isOpen={true}
        onClose={handleClose}
        onNavigateTab={handleNavigateTab}
        activeTab="home"
        theme="t-dark"
      />
    );

    // ArrowRight -> step 2
    fireEvent.keyDown(window, { key: 'ArrowRight' });
    expect(screen.getByText(/2 \/ 11/i)).toBeTruthy();

    // ArrowLeft -> back to step 1
    fireEvent.keyDown(window, { key: 'ArrowLeft' });
    expect(screen.getByText(/1 \/ 11/i)).toBeTruthy();

    // Escape -> triggers close
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(handleClose).toHaveBeenCalledTimes(1);
    expect(localStorage.getItem('photosorter-tutorial-seen')).toBe('true');
  });

  it('distinctly utilizes all 8 camera cat poses across the 11 tutorial steps', () => {
    const handleClose = vi.fn();
    const handleNavigateTab = vi.fn();

    render(
      <TutorialSpotlight
        isOpen={true}
        onClose={handleClose}
        onNavigateTab={handleNavigateTab}
        activeTab="home"
        theme="t-dark"
      />
    );

    const nextBtn = screen.getByTestId('tutorial-next-btn');

    // Expected poses for each of the 11 steps:
    // Step 1: Pose 1 (Hello)
    // Step 2: Pose 5 (Working)
    // Step 3: Pose 3 (Pointing)
    // Step 4: Pose 2 (Looking around)
    // Step 5: Pose 8 (Idle)
    // Step 6: Pose 6 (Done!)
    // Step 7: Pose 3 (Pointing)
    // Step 8: Pose 2 (Looking around)
    // Step 9: Pose 5 (Working)
    // Step 10: Pose 7 (Leaving)
    // Step 11: Pose 4 (Excited)
    const expectedPoses = [1, 5, 3, 2, 8, 6, 3, 2, 5, 7, 4];
    const observedPoses = new Set<number>();

    for (let i = 0; i < expectedPoses.length; i++) {
      const pose = expectedPoses[i];
      observedPoses.add(pose);
      const mascotImg = screen.getByTestId('tutorial-mascot-img');
      expect(mascotImg.getAttribute('src')).toBe(`/mascot/dark/pose${pose}.png`);

      if (i < expectedPoses.length - 1) {
        fireEvent.click(nextBtn);
      }
    }

    // Verify all 8 distinct poses (1 through 8) are actively experienced during the tour!
    for (let p = 1; p <= 8; p++) {
      expect(observedPoses.has(p)).toBe(true);
    }
  });
});

