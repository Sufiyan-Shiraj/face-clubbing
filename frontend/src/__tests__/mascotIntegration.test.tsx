import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { Header } from '../components/Header';
import { SettingsScreen } from '../components/SettingsScreen';
import { PeopleGrid } from '../components/PeopleGrid';
import { SuggestionReview } from '../components/SuggestionReview';
import { UnrecognizedTriage } from '../components/UnrecognizedTriage';
import { ProgressScreen } from '../components/ProgressScreen';
import { ExportScreen } from '../components/ExportScreen';
import { MascotSticker, getMascotUrl } from '../components/MascotSticker';
import { api } from '../api/client';

vi.mock('../api/client', () => ({
  api: {
    getSettings: vi.fn().mockResolvedValue({
      output_dir: 'export',
      distance_threshold: 0.50,
      merge_threshold: 0.50,
      maybe_threshold: 0.65,
      same_photo_merge_max: 0.40,
    }),
    updateSettings: vi.fn().mockResolvedValue({ success: true }),
    browseFolder: vi.fn().mockResolvedValue({
      current: 'export',
      parent: '',
      subdirectories: [],
      shortcuts: [],
    }),
    exportBundle: vi.fn().mockResolvedValue({
      success: true,
      output_dir: 'C:/export',
      people_count: 12,
      photos_count: 84,
      files_exported: ['index.html'],
    }),
  },
}));

describe('Mascots & Tutorial in Settings Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('getMascotUrl correctly maps themes and clamps poses 1-8', () => {
    expect(getMascotUrl('t-dark', 1)).toBe('/mascot/dark/pose1.png');
    expect(getMascotUrl('t-navy', 5)).toBe('/mascot/navy/pose5.png');
    expect(getMascotUrl('t-paper', 8)).toBe('/mascot/paper/pose8.png');
    // Clamping checks
    expect(getMascotUrl('t-dark', 0)).toBe('/mascot/dark/pose1.png');
    expect(getMascotUrl('t-dark', 99)).toBe('/mascot/dark/pose8.png');
  });

  it('Header does NOT render any tutorial button in top bar', () => {
    const handleTabChange = vi.fn();
    render(
      <Header
        activeTab="home"
        onTabChange={handleTabChange}
        peopleCount={0}
        unrecFacesCount={0}
        unrecPhotosCount={0}
        clusteredFacesCount={0}
        totalFacesCount={0}
        appliedEditsCount={0}
        onUndo={vi.fn()}
        onRefresh={vi.fn()}
      />
    );

    // #header-tutorial-btn should NOT exist
    expect(screen.queryByTestId('header-tutorial-btn')).toBeNull();
    expect(screen.queryByText(/^tutorial$/i)).toBeNull();
  });

  it('SettingsScreen renders Interactive Tutorial card with pose 1 and fires onOpenTutorial', async () => {
    const handleOpenTutorial = vi.fn();

    render(
      <SettingsScreen
        onOpenTutorial={handleOpenTutorial}
        theme="t-dark"
      />
    );

    // Wait for settings to load
    await waitFor(() => {
      expect(screen.getByTestId('card-settings-tutorial-launcher')).toBeTruthy();
    });

    const launcherCard = screen.getByTestId('card-settings-tutorial-launcher');
    expect(launcherCard).toBeTruthy();
    expect(screen.getByText(/Interactive Tutorial & Feature Walkthrough/i)).toBeTruthy();

    // Verify mascot sticker in Settings card (Pose 1: Hello)
    const mascotImg = launcherCard.querySelector('img');
    expect(mascotImg).toBeTruthy();
    expect(mascotImg?.getAttribute('src')).toBe('/mascot/dark/pose1.png');

    // Click launch button
    const launchBtn = screen.getByTestId('btn-launch-tutorial-settings');
    expect(launchBtn).toBeTruthy();
    fireEvent.click(launchBtn);
    expect(handleOpenTutorial).toHaveBeenCalledTimes(1);
  });

  it('PeopleGrid empty state renders resting mascot (Pose 8)', () => {
    render(
      <PeopleGrid
        people={[]}
        photos={{}}
        selectedIds={new Set()}
        onToggleSelect={vi.fn()}
        onSelectAll={vi.fn()}
        onClearSelection={vi.fn()}
        onMergeSelected={vi.fn()}
        onSelectPerson={vi.fn()}
        theme="t-navy"
      />
    );

    const emptyBox = screen.getByTestId('people-empty-state');
    expect(emptyBox).toBeTruthy();
    expect(screen.getByText(/No People Clusters Yet/i)).toBeTruthy();

    const mascotImg = emptyBox.querySelector('img');
    expect(mascotImg).toBeTruthy();
    expect(mascotImg?.getAttribute('src')).toBe('/mascot/navy/pose8.png');
  });

  it('SuggestionReview empty state renders done checklist mascot (Pose 6)', () => {
    render(
      <SuggestionReview
        suggestions={[]}
        peopleMap={{}}
        onAccept={vi.fn()}
        onReject={vi.fn()}
        rejectedPairs={new Set()}
        theme="t-paper"
      />
    );

    const emptyBox = screen.getByTestId('suggestions-empty-state');
    expect(emptyBox).toBeTruthy();
    expect(screen.getByText(/All Suggestions Caught Up!/i)).toBeTruthy();

    const mascotImg = emptyBox.querySelector('img');
    expect(mascotImg).toBeTruthy();
    expect(mascotImg?.getAttribute('src')).toBe('/mascot/paper/pose6.png');
  });

  it('UnrecognizedTriage empty state renders resting mascot (Pose 8)', () => {
    render(
      <UnrecognizedTriage
        unrecognized={{ total_unrecognized_photos: 0, no_face_photos: [], faces: [] }}
        ambiguousMap={{}}
        people={[]}
        photos={{}}
        onAssignFace={vi.fn()}
        onOpenPhotoViewer={vi.fn()}
        theme="t-dark"
      />
    );

    const emptyBox = screen.getByTestId('unrec-faces-empty-state');
    expect(emptyBox).toBeTruthy();
    expect(screen.getByText(/Zero Unrecognized Faces!/i)).toBeTruthy();

    const mascotImg = emptyBox.querySelector('img');
    expect(mascotImg).toBeTruthy();
    expect(mascotImg?.getAttribute('src')).toBe('/mascot/dark/pose8.png');
  });

  it('ProgressScreen renders working mascot (Pose 5) while running and excited mascot (Pose 4) when complete', () => {
    // 1. Running state
    const { rerender } = render(
      <ProgressScreen
        status={{
          status: 'running',
          stage: 'detecting',
          current: 40,
          total: 100,
          percent: 40,
          elapsed_seconds: 12,
          message: 'Detecting faces...',
        }}
        progressHistory={[]}
        onCancelJob={vi.fn()}
        onGoToReview={vi.fn()}
        theme="t-dark"
      />
    );

    expect(screen.getByText(/Local Engine Active/i)).toBeTruthy();
    const workingImg = document.querySelector('img[src="/mascot/dark/pose5.png"]');
    expect(workingImg).toBeTruthy();

    // 2. Completed state
    rerender(
      <ProgressScreen
        status={{
          status: 'completed',
          stage: 'done',
          current: 100,
          total: 100,
          percent: 100,
          elapsed_seconds: 28,
          message: 'Clustering completed successfully',
        }}
        progressHistory={[]}
        onCancelJob={vi.fn()}
        onGoToReview={vi.fn()}
        theme="t-navy"
      />
    );

    const banner = screen.getByTestId('scan-completion-banner');
    expect(banner).toBeTruthy();
    const excitedImg = banner.querySelector('img');
    expect(excitedImg).toBeTruthy();
    expect(excitedImg?.getAttribute('src')).toBe('/mascot/navy/pose4.png');
  });

  it('ExportScreen success summary renders leaving mascot with packed bundle (Pose 7)', async () => {
    render(
      <ExportScreen
        peopleCount={12}
        photosCount={84}
        theme="t-dark"
      />
    );

    // Initial state: bundle button present
    const exportBtn = screen.getByTestId('export-bundle-btn');
    expect(exportBtn).toBeTruthy();

    // Trigger export
    fireEvent.click(exportBtn);

    await waitFor(() => {
      expect(screen.getByTestId('export-success-summary')).toBeTruthy();
    });

    const summary = screen.getByTestId('export-success-summary');
    const leavingImg = summary.querySelector('img');
    expect(leavingImg).toBeTruthy();
    expect(leavingImg?.getAttribute('src')).toBe('/mascot/dark/pose7.png');
  });
});
