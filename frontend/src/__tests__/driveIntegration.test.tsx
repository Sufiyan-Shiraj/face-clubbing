import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { HomeScreen } from '../components/HomeScreen';
import { SettingsScreen } from '../components/SettingsScreen';
import { api } from '../api/client';

vi.mock('../api/client', () => ({
  api: {
    getSettings: vi.fn(),
    updateSettings: vi.fn(),
    rerun: vi.fn(),
  },
}));

describe('Phase 6 UI: HomeScreen Drive Mode & Link Input', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('switches to Google Drive mode and renders Drive folder input', () => {
    const handleStartJob = vi.fn();
    render(<HomeScreen onStartJob={handleStartJob} />);

    // Initially in local mode
    expect(screen.getByTestId('btn-source-local')).toBeTruthy();
    expect(screen.getByTestId('btn-source-drive')).toBeTruthy();

    // Click Google Drive tab
    fireEvent.click(screen.getByTestId('btn-source-drive'));

    // Drive URL input should appear
    const driveInput = screen.getByTestId('input-drive-link') as HTMLInputElement;
    expect(driveInput).toBeTruthy();
    expect(driveInput.placeholder).toContain('drive.google.com/drive/folders');
  });

  it('validates and submits Drive folder link when Start is clicked', async () => {
    const handleStartJob = vi.fn();
    render(<HomeScreen onStartJob={handleStartJob} />);

    // Switch to Drive mode
    fireEvent.click(screen.getByTestId('btn-source-drive'));

    const driveInput = screen.getByTestId('input-drive-link') as HTMLInputElement;
    fireEvent.change(driveInput, {
      target: { value: 'https://drive.google.com/drive/folders/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs?usp=sharing' },
    });

    const startBtn = screen.getByTestId('start-job-btn');
    expect(startBtn).toBeTruthy();

    fireEvent.click(startBtn);

    await waitFor(() => {
      expect(handleStartJob).toHaveBeenCalledTimes(1);
      expect(handleStartJob).toHaveBeenCalledWith(
        undefined,
        'https://drive.google.com/drive/folders/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs?usp=sharing',
        undefined
      );
    });
  });

  it('displays warning when submitting an invalid Drive URL or ID', async () => {
    const handleStartJob = vi.fn();
    render(<HomeScreen onStartJob={handleStartJob} />);

    fireEvent.click(screen.getByTestId('btn-source-drive'));

    const driveInput = screen.getByTestId('input-drive-link') as HTMLInputElement;
    fireEvent.change(driveInput, { target: { value: 'invalid_drive_input!!' } });

    const startBtn = screen.getByTestId('start-job-btn');
    fireEvent.click(startBtn);

    expect(handleStartJob).not.toHaveBeenCalled();
    expect(screen.getByText(/Invalid Google Drive folder link or folder ID/i)).toBeTruthy();
  });

  it('displays warning when submitting a file link instead of a folder link', async () => {
    const handleStartJob = vi.fn();
    render(<HomeScreen onStartJob={handleStartJob} />);

    fireEvent.click(screen.getByTestId('btn-source-drive'));

    const driveInput = screen.getByTestId('input-drive-link') as HTMLInputElement;
    fireEvent.change(driveInput, {
      target: { value: 'https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs/view' },
    });

    const startBtn = screen.getByTestId('start-job-btn');
    fireEvent.click(startBtn);

    expect(handleStartJob).not.toHaveBeenCalled();
    expect(screen.getByText(/You entered a Google Drive file link, but a folder link or folder ID is required/i)).toBeTruthy();
  });
});

describe('Phase 6 UI: SettingsScreen Drive API Key Management', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders Drive API Key status and masked key when configured', async () => {
    vi.mocked(api.getSettings).mockResolvedValue({
      output_dir: 'export',
      distance_threshold: 0.5,
      min_det_score: 0.5,
      min_face_size: 64,
      max_yaw: 70,
      seed_min_det_score: 0.7,
      seed_min_face_size: 64,
      seed_max_yaw: 60,
      max_image_dim: 1600,
      thumb_size: 400,
      face_crop_size: 256,
      second_pass_merge: true,
      merge_threshold: 0.5,
      maybe_threshold: 0.65,
      same_photo_merge_max: 0.4,
      attach_distance_cap: 0.45,
      flip_average: false,
      include_maybe: false,
      event_title: 'Face Clubbing Gallery',
      event_subtitle: 'Auto-sorted face albums',
      drive_api_key_configured: true,
      drive_api_key_masked: 'AIzaSy...7e8f',
    } as any);

    render(<SettingsScreen />);

    await waitFor(() => {
      const badge = document.getElementById('drive-key-status-badge');
      expect(badge?.textContent).toContain('Configured');
      expect(badge?.textContent).toContain('AIzaSy...7e8f');
    });

    expect(screen.getByText(/How to get a free Google Drive API Key/i)).toBeTruthy();
  });

  it('allows entering and saving a new Drive API key securely', async () => {
    vi.mocked(api.getSettings).mockResolvedValue({
      output_dir: 'export',
      distance_threshold: 0.5,
      min_det_score: 0.5,
      min_face_size: 64,
      max_yaw: 70,
      seed_min_det_score: 0.7,
      seed_min_face_size: 64,
      seed_max_yaw: 60,
      max_image_dim: 1600,
      thumb_size: 400,
      face_crop_size: 256,
      second_pass_merge: true,
      merge_threshold: 0.5,
      maybe_threshold: 0.65,
      same_photo_merge_max: 0.4,
      attach_distance_cap: 0.45,
      flip_average: false,
      include_maybe: false,
      event_title: 'Test',
      event_subtitle: 'Test Subtitle',
      drive_api_key_configured: false,
      drive_api_key_masked: '',
    } as any);

    vi.mocked(api.updateSettings).mockResolvedValue({} as any);

    render(<SettingsScreen />);

    await waitFor(() => {
      const badge = document.getElementById('drive-key-status-badge');
      expect(badge?.textContent).toContain('Not Configured');
    });

    const keyInput = document.getElementById('setting-drive-api-key') as HTMLInputElement;
    expect(keyInput).toBeTruthy();

    fireEvent.change(keyInput, { target: { value: 'AIzaSyTestKey1234567890abcdef' } });

    const saveBtn = document.getElementById('save-drive-key-btn') as HTMLButtonElement;
    expect(saveBtn.disabled).toBe(false);

    fireEvent.click(saveBtn);

    await waitFor(() => {
      expect(api.updateSettings).toHaveBeenCalledWith({
        drive_api_key: 'AIzaSyTestKey1234567890abcdef',
      });
    });
  });

  it('allows removing an existing Drive API key', async () => {
    vi.mocked(api.getSettings).mockResolvedValue({
      output_dir: 'export',
      distance_threshold: 0.5,
      min_det_score: 0.5,
      min_face_size: 64,
      max_yaw: 70,
      seed_min_det_score: 0.7,
      seed_min_face_size: 64,
      seed_max_yaw: 60,
      max_image_dim: 1600,
      thumb_size: 400,
      face_crop_size: 256,
      second_pass_merge: true,
      merge_threshold: 0.5,
      maybe_threshold: 0.65,
      same_photo_merge_max: 0.4,
      attach_distance_cap: 0.45,
      flip_average: false,
      include_maybe: false,
      event_title: 'Test',
      event_subtitle: 'Test Subtitle',
      drive_api_key_configured: true,
      drive_api_key_masked: 'AIzaSy...7e8f',
    } as any);

    vi.mocked(api.updateSettings).mockResolvedValue({} as any);

    render(<SettingsScreen />);

    await waitFor(() => {
      const clearBtn = document.getElementById('clear-drive-key-btn');
      expect(clearBtn).toBeTruthy();
    });

    const clearBtn = document.getElementById('clear-drive-key-btn') as HTMLButtonElement;
    fireEvent.click(clearBtn);

    await waitFor(() => {
      expect(api.updateSettings).toHaveBeenCalledWith({
        drive_api_key: '',
      });
    });
  });
});
