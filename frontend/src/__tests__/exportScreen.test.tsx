import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
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
      current_path: 'C:\\Users\\mockuser\\face-clubbing\\export',
      parent_path: 'C:\\Users\\mockuser\\face-clubbing',
      name: 'export',
      exists: true,
      is_directory: true,
      directories: [
        { name: 'faces', path: 'C:\\Users\\mockuser\\face-clubbing\\export\\faces', modified_time: '2026-10-15 12:00' },
        { name: 'thumbs', path: 'C:\\Users\\mockuser\\face-clubbing\\export\\thumbs', modified_time: '2026-10-15 12:01' },
      ],
      shortcuts: [
        { label: 'Project Export', path: 'C:\\Users\\mockuser\\face-clubbing\\export' },
        { label: 'Desktop', path: 'C:\\Users\\mockuser\\Desktop' },
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

    // Output dir input should be populated with nested drive folder
    const outputInput = screen.getByTestId('export-output-dir-input') as HTMLInputElement;
    expect(outputInput.value).toBe('export/Graduation 2026 Drive');
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
      output_dir: 'C:\\Users\\mockuser\\face-clubbing\\export',
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

  it('unlocked behavior: renders destination explorer and shortcuts on cold boot with 0 people and photos', async () => {
    render(
      <ExportScreen
        peopleCount={0}
        photosCount={0}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('OUTPUT DESTINATION EXPLORER')).toBeTruthy();
      expect(screen.getByText('Project Export')).toBeTruthy();
      expect(screen.getByText('Desktop')).toBeTruthy();
    });

    const exportBtn = screen.getByTestId('export-bundle-btn');
    expect(exportBtn).toBeTruthy();
    expect(screen.getByText(/Export Static Web Bundle/i)).toBeTruthy();
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

  it('renders Logs button, omits removed hint text, and opens dedicated activity logs window with all logs', async () => {
    const history: JobStatus[] = [
      { status: 'running', stage: 'detecting', current: 1, total: 20, percent: 5, message: 'Processing photo 1' },
      { status: 'running', stage: 'detecting', current: 5, total: 20, percent: 25, message: 'Processing photo 5' },
      { status: 'running', stage: 'clustering', current: 15, total: 20, percent: 75, message: 'Grouping faces' },
      { status: 'running', stage: 'exporting', current: 20, total: 20, percent: 100, message: 'Finishing up' },
    ];

    render(
      <ProgressScreen
        status={history[3]}
        progressHistory={history}
        onCancelJob={vi.fn()}
        onGoToReview={vi.fn()}
      />
    );

    // Verify "Face crops stay on this computer" was removed
    expect(screen.queryByText(/Face crops stay on this computer/i)).toBeNull();

    // Verify Logs button is rendered
    const logsBtn = screen.getByTestId('btn-open-logs');
    expect(logsBtn).toBeTruthy();
    expect(logsBtn.textContent).toContain('Logs');

    const viewAllBtn = screen.getByTestId('btn-view-all-logs');
    expect(viewAllBtn).toBeTruthy();

    // Click to open dedicated logs window
    fireEvent.click(viewAllBtn);

    // Modal should be open with role="dialog" and title
    const dialog = screen.getByRole('dialog', { name: /Engine Activity Logs/i });
    expect(dialog).toBeTruthy();
    expect(within(dialog).getByText(/Engine Activity Log/i)).toBeTruthy();

    // Verify all 4 log entries are present in the window
    expect(within(dialog).getByText(/Processing photo 1/i)).toBeTruthy();
    expect(within(dialog).getByText(/Processing photo 5/i)).toBeTruthy();
    expect(within(dialog).getByText(/Grouping faces/i)).toBeTruthy();
    expect(within(dialog).getByText(/Finishing up/i)).toBeTruthy();

    // Close the logs window
    const closeBtn = screen.getByTestId('btn-close-logs-modal');
    fireEvent.click(closeBtn);
    expect(screen.queryByRole('dialog')).toBeNull();
  });

  it('supports detaching into a separate window with elapsed time in the window name', async () => {
    // Mock window.open to simulate browser popup window
    const mockPopupDoc = {
      title: '',
      body: document.createElement('body'),
      head: document.createElement('head'),
      documentElement: document.createElement('html'),
      createElement: (tag: string) => document.createElement(tag),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    };
    const mockPopup = {
      document: mockPopupDoc,
      closed: false,
      close: vi.fn(),
      focus: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
    } as any;

    const windowOpenSpy = vi.spyOn(window, 'open').mockReturnValue(mockPopup);

    const history: JobStatus[] = [
      { status: 'running', stage: 'detecting', current: 10, total: 50, percent: 20, message: 'Detecting faces', elapsed_seconds: 75 },
    ];

    render(
      <ProgressScreen
        status={history[0]}
        progressHistory={history}
        onCancelJob={vi.fn()}
        onGoToReview={vi.fn()}
      />
    );

    // Verify Detach button is rendered on top action bar and bottom bar
    const detachTopBtn = screen.getByTestId('btn-detach-logs');
    expect(detachTopBtn).toBeTruthy();
    expect(detachTopBtn.textContent).toContain('Detach');

    const detachBottomBtn = screen.getByTestId('btn-detach-bottom');
    expect(detachBottomBtn).toBeTruthy();

    // Click detach button
    fireEvent.click(detachTopBtn);

    // Verify window.open was called with dimensions for detached floating window
    expect(windowOpenSpy).toHaveBeenCalledWith(
      '',
      'PhotoSorterDetachedLogs',
      expect.stringContaining('width=880')
    );

    // Verify the window name/title contains the elapsed time (01:15 = 75 seconds)
    expect(mockPopup.document.title).toContain('01:15');
    expect(mockPopup.document.title).toContain('Engine Activity Log');

    windowOpenSpy.mockRestore();
  });
});
