import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ExportScreen } from '../components/ExportScreen';
import { ProgressScreen } from '../components/ProgressScreen';
import { api } from '../api/client';
import { JobStatus } from '../types';

vi.mock('../api/client', () => ({
  api: {
    getSettings: vi.fn(),
    browseFolder: vi.fn(),
    createFolder: vi.fn(),
    openFolderDialog: vi.fn(),
    exportBundle: vi.fn(),
  },
}));

describe('ExportScreen Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();

    (api.getSettings as any).mockResolvedValue({
      output_dir: 'export',
      event_title: 'Face Clubbing Gallery',
      event_subtitle: 'Auto-sorted face albums and photo gallery',
      include_maybe: false,
    });

    (api.browseFolder as any).mockResolvedValue({
      current_path: 'C:\\Users\\DELL\\face-clubbing\\export',
      parent_path: 'C:\\Users\\DELL\\face-clubbing',
      name: 'export',
      exists: true,
      is_directory: true,
      directories: [
        { name: 'faces', path: 'C:\\Users\\DELL\\face-clubbing\\export\\faces', modified_time: '2026-10-15 12:00' },
        { name: 'thumbs', path: 'C:\\Users\\DELL\\face-clubbing\\export\\thumbs', modified_time: '2026-10-15 12:01' },
      ],
      shortcuts: [
        { label: 'Project Export', path: 'C:\\Users\\DELL\\face-clubbing\\export' },
        { label: 'Desktop', path: 'C:\\Users\\DELL\\Desktop' },
      ],
    });
  });

  it('renders file explorer window with breadcrumbs and directory items', async () => {
    render(
      <ExportScreen
        initialTitle="Graduation 2026 Drive"
        peopleCount={12}
        photosCount={84}
      />
    );

    // Explorer title bar and breadcrumb
    await waitFor(() => {
      expect(screen.getByText('OUTPUT DESTINATION EXPLORER')).toBeTruthy();
      expect(screen.getByText('faces')).toBeTruthy();
      expect(screen.getByText('thumbs')).toBeTruthy();
    });

    // Output dir input should be populated
    const outputInput = screen.getByTestId('export-output-dir-input') as HTMLInputElement;
    expect(outputInput.value).toBe('export');
  });

  it('auto-populates gallery title from initialTitle / drive folder', async () => {
    render(
      <ExportScreen
        initialTitle="Batch 2026 Reunion"
        peopleCount={5}
        photosCount={30}
      />
    );

    const titleInput = screen.getByTestId('export-title-input') as HTMLInputElement;
    expect(titleInput.value).toBe('Batch 2026 Reunion');

    // Drive synced badge should be visible
    expect(screen.getByText('DRIVE SYNCED')).toBeTruthy();
  });

  it('filters directory listing in file explorer', async () => {
    render(<ExportScreen peopleCount={5} photosCount={30} />);

    await waitFor(() => {
      expect(screen.getByText('faces')).toBeTruthy();
      expect(screen.getByText('thumbs')).toBeTruthy();
    });

    const searchInput = screen.getByPlaceholderText('Filter subfolders...');
    fireEvent.change(searchInput, { target: { value: 'fac' } });

    expect(screen.getByText('faces')).toBeTruthy();
    expect(screen.queryByText('thumbs')).toBeNull();
  });

  it('triggers exportBundle on button click and renders summary stats', async () => {
    (api.exportBundle as any).mockResolvedValue({
      success: true,
      output_dir: 'C:\\Users\\DELL\\face-clubbing\\export',
      files_exported: ['index.html', 'manifest.json'],
      people_count: 12,
      photos_count: 84,
    });

    render(
      <ExportScreen
        initialTitle="My Drive Event"
        peopleCount={12}
        photosCount={84}
      />
    );

    const exportBtn = screen.getByTestId('export-bundle-btn');
    fireEvent.click(exportBtn);

    await waitFor(() => {
      expect(api.exportBundle).toHaveBeenCalled();
      expect(screen.getByTestId('export-success-summary')).toBeTruthy();
      expect(screen.getByTestId('export-stat-people').textContent).toContain('12');
      expect(screen.getByTestId('export-stat-photos').textContent).toContain('84');
    });
  });
});

describe('ProgressScreen Time Elapsed Component', () => {
  it('renders time elapsed badge and elapsed card', () => {
    const runningStatus: JobStatus = {
      status: 'running',
      stage: 'faces',
      current: 40,
      total: 100,
      percent: 40,
      message: 'Extracting face crops...',
      elapsed_seconds: 65,
    };

    render(
      <ProgressScreen
        status={runningStatus}
        progressHistory={[]}
        onCancelJob={vi.fn()}
        onGoToReview={vi.fn()}
      />
    );

    const elapsedBadge = screen.getByTestId('progress-elapsed-badge');
    expect(elapsedBadge).toBeTruthy();
    expect(elapsedBadge.textContent).toContain('01:05');

    const elapsedCard = screen.getByTestId('time-elapsed-card');
    expect(elapsedCard).toBeTruthy();
    expect(elapsedCard.textContent).toContain('01:05');
  });
});
