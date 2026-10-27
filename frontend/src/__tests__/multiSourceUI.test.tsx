import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { HomeScreen } from '../components/HomeScreen';
import { api } from '../api/client';
import { ScanSourceItem } from '../types';

vi.mock('../api/client', () => ({
  api: {
    getSettings: vi.fn().mockResolvedValue({
      scan_subfolders: true,
      max_subfolder_depth: 5,
      follow_shortcuts: false,
      drive_api_key_configured: true,
    }),
    verifyDriveFolder: vi.fn(),
    startJob: vi.fn().mockResolvedValue({ status: 'running' }),
    getProjectSources: vi.fn().mockResolvedValue({
      sources: [
        { id: 'src_01', type: 'local', path_or_url: '/photos/camera_a', label: 'camera_a' },
        { id: 'src_02', type: 'drive', path_or_url: 'https://drive.google.com/drive/folders/123xyz', label: 'Cloud Reception' },
      ],
      total_sources: 2,
      schema_version: 2,
    }),
    getModelStatus: vi.fn().mockResolvedValue({
      model_name: 'antelopev2',
      installed: true,
      valid: true,
      status: 'ready',
    }),
  },
}));

describe('Multi-Source Frontend UI & Sources Manager (Phase V2-2 Piece 2)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders initial state with no configured sources and sources-list hidden', () => {
    const handleStartJob = vi.fn();
    render(<HomeScreen onStartJob={handleStartJob} />);

    expect(screen.queryByTestId('sources-list')).toBeNull();
    expect(screen.queryByTestId('sources-count-badge')).toBeNull();
  });

  it('allows adding local folders to configured sources list', async () => {
    const handleStartJob = vi.fn();
    render(<HomeScreen onStartJob={handleStartJob} sourceMode="local" />);

    const pathInput = screen.getByTestId('input-source-path') as HTMLInputElement;
    fireEvent.change(pathInput, { target: { value: 'C:/Events/Wedding/Camera_A' } });

    const addBtn = screen.getByTestId('add-source-btn');
    fireEvent.click(addBtn);

    // List should now be visible with 1 source
    await waitFor(() => {
      const sourcesList = screen.getByTestId('sources-list');
      expect(sourcesList).toBeTruthy();
      expect(screen.getByTestId('sources-count-badge').textContent).toContain('1 source');
      expect(screen.getByText('Camera_A')).toBeTruthy();
      expect(screen.getByText('C:/Events/Wedding/Camera_A')).toBeTruthy();
      expect(screen.getByText('LOCAL')).toBeTruthy();
    });

    // Input path was cleared after adding
    expect(pathInput.value).toBe('');
  });

  it('supports adding multiple mixed sources (local, zip, drive)', async () => {
    const handleStartJob = vi.fn();
    const handleSourcesChange = vi.fn();

    vi.mocked(api.verifyDriveFolder).mockResolvedValue({
      valid: true,
      folder_id: '1aB2c3D4e5F6g7H8i9Jk',
      folder_name: 'Summer Vacation Cloud',
      has_images: true,
      image_count_preview: 50,
      message: 'Verified',
    });

    const { rerender } = render(
      <HomeScreen
        onStartJob={handleStartJob}
        onSourcesChange={handleSourcesChange}
        sourceMode="local"
      />
    );

    // 1. Add Local Source
    const pathInput = screen.getByTestId('input-source-path') as HTMLInputElement;
    fireEvent.change(pathInput, { target: { value: '/data/camera_one' } });
    fireEvent.click(screen.getByTestId('add-source-btn'));

    // 2. Add Zip Source
    rerender(
      <HomeScreen
        onStartJob={handleStartJob}
        onSourcesChange={handleSourcesChange}
        sourceMode="zip"
      />
    );
    const zipInput = screen.getByTestId('input-source-path') as HTMLInputElement;
    fireEvent.change(zipInput, { target: { value: '/data/reception_backup.zip' } });
    fireEvent.click(screen.getByTestId('add-source-btn'));

    // 3. Add Drive Source
    rerender(
      <HomeScreen
        onStartJob={handleStartJob}
        onSourcesChange={handleSourcesChange}
        sourceMode="drive"
      />
    );
    const driveInput = screen.getByTestId('input-drive-link') as HTMLInputElement;
    fireEvent.change(driveInput, {
      target: { value: 'https://drive.google.com/drive/folders/1aB2c3D4e5F6g7H8i9Jk' },
    });
    fireEvent.click(screen.getByTestId('add-source-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('sources-count-badge').textContent).toContain('3 sources');
      expect(screen.getByText('camera_one')).toBeTruthy();
      expect(screen.getByText('reception_backup.zip')).toBeTruthy();
      expect(screen.getByText('Summer Vacation Cloud')).toBeTruthy();
      expect(screen.getByText('LOCAL')).toBeTruthy();
      expect(screen.getByText('ZIP')).toBeTruthy();
      expect(screen.getByText('DRIVE')).toBeTruthy();
    });

    expect(handleSourcesChange).toHaveBeenCalledTimes(3);
  });

  it('allows removing an individual source from the list', async () => {
    const handleStartJob = vi.fn();
    const initialSources: ScanSourceItem[] = [
      { id: 'src_cam_a', type: 'local', path_or_url: '/photos/cam_a', label: 'Camera A' },
      { id: 'src_cam_b', type: 'local', path_or_url: '/photos/cam_b', label: 'Camera B' },
    ];

    render(
      <HomeScreen
        onStartJob={handleStartJob}
        sources={initialSources}
      />
    );

    expect(screen.getByTestId('sources-count-badge').textContent).toContain('2 sources');
    expect(screen.getByText('Camera A')).toBeTruthy();
    expect(screen.getByText('Camera B')).toBeTruthy();

    // Remove Camera A
    const removeBtn = screen.getByTestId('remove-source-src_cam_a');
    fireEvent.click(removeBtn);

    await waitFor(() => {
      expect(screen.queryByText('Camera A')).toBeNull();
      expect(screen.getByText('Camera B')).toBeTruthy();
      expect(screen.getByTestId('sources-count-badge').textContent).toContain('1 source');
    });
  });

  it('allows clearing all sources via Clear All button', async () => {
    const handleStartJob = vi.fn();
    const initialSources: ScanSourceItem[] = [
      { id: 'src_1', type: 'local', path_or_url: '/photos/a', label: 'A' },
      { id: 'src_2', type: 'local', path_or_url: '/photos/b', label: 'B' },
    ];

    render(<HomeScreen onStartJob={handleStartJob} sources={initialSources} />);

    expect(screen.getByTestId('sources-list')).toBeTruthy();
    const clearBtn = screen.getByTestId('clear-sources-btn');
    fireEvent.click(clearBtn);

    await waitFor(() => {
      expect(screen.queryByTestId('sources-list')).toBeNull();
    });
  });

  it('clicking Organize Photos passes the sources array as the 5th parameter to onStartJob', async () => {
    const handleStartJob = vi.fn();
    const testSources: ScanSourceItem[] = [
      { id: 'src_1', type: 'local', path_or_url: '/photos/camera_1', label: 'Camera 1' },
      { id: 'src_2', type: 'local', path_or_url: '/photos/camera_2', label: 'Camera 2' },
    ];

    render(<HomeScreen onStartJob={handleStartJob} sources={testSources} />);

    const startBtn = screen.getByTestId('start-sorting-btn');
    fireEvent.click(startBtn);

    await waitFor(() => {
      expect(handleStartJob).toHaveBeenCalledTimes(1);
      const args = handleStartJob.mock.calls[0];
      // 1st: inputPath, 2nd: driveFolder, 3rd: driveApiKey, 4th: scanOptions, 5th: sources
      expect(args[4]).toEqual(testSources);
    });
  });

  it('maintains backwards compatibility for single-source scans without multi-source queue', async () => {
    const handleStartJob = vi.fn();

    render(
      <HomeScreen
        onStartJob={handleStartJob}
        sourceMode="local"
        folderPath="/photos/single_event"
      />
    );

    const startBtn = screen.getByTestId('start-job-btn');
    fireEvent.click(startBtn);

    await waitFor(() => {
      expect(handleStartJob).toHaveBeenCalledTimes(1);
      expect(handleStartJob).toHaveBeenCalledWith('/photos/single_event');
    });
  });

  it('client api.getProjectSources calls /api/project/sources', async () => {
    const sourcesResp = await api.getProjectSources();
    expect(sourcesResp).toBeDefined();
    expect(sourcesResp.total_sources).toBe(2);
    expect(sourcesResp.sources[0].path_or_url).toBe('/photos/camera_a');
    expect(sourcesResp.sources[1].label).toBe('Cloud Reception');
  });
});
