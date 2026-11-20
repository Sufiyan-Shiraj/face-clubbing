import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { TutorialSpotlight, TUTORIAL_SPOTLIGHT_STEPS } from '../components/TutorialSpotlight';
import { TutorialHandbookModal } from '../components/TutorialHandbookModal';

describe('TutorialSpotlight - Streamlined 5-Step Tour', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('renders spotlight SVG mask and tooltip box with 5 total steps', () => {
    const handleClose = vi.fn();
    const handleNavigateTab = vi.fn();
    const handleSetSourceMode = vi.fn();
    const handleSetReviewSubTab = vi.fn();
    const handleSetSelectedPeopleIds = vi.fn();

    expect(TUTORIAL_SPOTLIGHT_STEPS).toHaveLength(5);

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
    expect(screen.getByText(/1 \/ 5/i)).toBeTruthy();
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

    const mascotImg = screen.getByTestId('tutorial-mascot-img');
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

    const mascotImgPaper = screen.getByTestId('tutorial-mascot-img');
    expect(mascotImgPaper.getAttribute('src')).toBe('/mascot/paper/pose1.png');
  });

  it('walks sequentially through all 5 workflow steps and restores starting tab on finish', () => {
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
    expect(screen.getByText(/2 \/ 5/i)).toBeTruthy();
    expect(screen.getByText(/Detachable Activity Logs/i)).toBeTruthy();
    expect(handleNavigateTab).toHaveBeenCalledWith('progress');

    // Step 2 -> Step 3 (Review: Multi-Select & Batch Merge)
    fireEvent.click(nextBtn);
    expect(screen.getByText(/3 \/ 5/i)).toBeTruthy();
    expect(screen.getByText(/Multi-Select & Batch Merge/i)).toBeTruthy();
    expect(handleNavigateTab).toHaveBeenCalledWith('people');
    expect(handleSetReviewSubTab).toHaveBeenCalledWith('people');
    expect(handleSetSelectedPeopleIds).toHaveBeenCalledWith(new Set(['demo_p001', 'demo_p002']));

    // Step 3 -> Step 4 (Review: Suggestions & Face Inspector)
    fireEvent.click(nextBtn);
    expect(screen.getByText(/4 \/ 5/i)).toBeTruthy();
    expect(screen.getByText(/Borderline Matches & Face Inspector/i)).toBeTruthy();
    expect(handleSetReviewSubTab).toHaveBeenCalledWith('suggestions');

    // Step 4 -> Step 5 (Publish: Offline Gallery)
    fireEvent.click(nextBtn);
    expect(screen.getByText(/5 \/ 5/i)).toBeTruthy();
    expect(screen.getByText(/Zero-Server Offline Gallery/i)).toBeTruthy();
    expect(handleNavigateTab).toHaveBeenCalledWith('export');

    // Click Finish on Step 5
    fireEvent.click(nextBtn);
    expect(handleClose).toHaveBeenCalledTimes(1);
    // Verifies starting tab 'home' was restored!
    expect(handleNavigateTab).toHaveBeenCalledWith('home');
    expect(localStorage.getItem('photosorter-tutorial-seen')).toBe('true');
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
    expect(screen.getByText(/2 \/ 5/i)).toBeTruthy();

    // ArrowLeft -> back to step 1
    fireEvent.keyDown(window, { key: 'ArrowLeft' });
    expect(screen.getByText(/1 \/ 5/i)).toBeTruthy();

    // Escape -> triggers close and restores tab
    fireEvent.keyDown(window, { key: 'Escape' });
    expect(handleClose).toHaveBeenCalledTimes(1);
    expect(handleNavigateTab).toHaveBeenCalledWith('home');
    expect(localStorage.getItem('photosorter-tutorial-seen')).toBe('true');
  });
});

describe('TutorialHandbookModal - Visual Interactive Guide', () => {
  it('renders modal with all 5 chapters and navigates between them', () => {
    const onClose = vi.fn();
    const onStartSpotlightTour = vi.fn();

    render(
      <TutorialHandbookModal
        isOpen={true}
        onClose={onClose}
        onStartSpotlightTour={onStartSpotlightTour}
        theme="t-dark"
        initialTab="sources"
      />
    );

    expect(screen.getByTestId('tutorial-handbook-modal')).toBeTruthy();
    expect(screen.getByText(/CatLog Visual Handbook & Guide/i)).toBeTruthy();

    // Chapter 1 is active initially
    expect(screen.getByTestId('handbook-tab-sources')).toBeTruthy();
    expect(screen.getByText(/Have a Google Photos Album\? Use the 1-Click ZIP Workflow/i)).toBeTruthy();

    // Switch to Chapter 2: Pipeline
    fireEvent.click(screen.getByTestId('tab-handbook-pipeline'));
    expect(screen.getByTestId('handbook-tab-pipeline')).toBeTruthy();
    expect(screen.getByText(/100% Offline AI Face Recognition/i)).toBeTruthy();

    // Switch to Chapter 3: Review
    fireEvent.click(screen.getByTestId('tab-handbook-review'));
    expect(screen.getByTestId('handbook-tab-review')).toBeTruthy();
    expect(screen.getByText(/Reviewing Attendees & Batch Merging/i)).toBeTruthy();

    // Switch to Chapter 4: Export
    fireEvent.click(screen.getByTestId('tab-handbook-export'));
    expect(screen.getByTestId('handbook-tab-export')).toBeTruthy();
    expect(screen.getByText(/Standalone Zero-Server Gallery & Project Merges/i)).toBeTruthy();

    // Switch to Chapter 5: Shortcuts
    fireEvent.click(screen.getByTestId('tab-handbook-shortcuts'));
    expect(screen.getByTestId('handbook-tab-shortcuts')).toBeTruthy();
    expect(screen.getByText(/Keyboard Shortcuts Cheatsheet/i)).toBeTruthy();

    // Test launching spotlight tour from handbook
    fireEvent.click(screen.getByTestId('btn-handbook-start-spotlight'));
    expect(onClose).toHaveBeenCalled();
    expect(onStartSpotlightTour).toHaveBeenCalled();
  });
});
