import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { HomeScreen } from '../components/HomeScreen';
import { SettingsScreen } from '../components/SettingsScreen';
import { AddSourceModal } from '../components/AddSourceModal';
import { api } from '../api/client';

vi.mock('../api/client', () => ({
  api: {
    getSettings: vi.fn(),
    updateSettings: vi.fn(),
    rerun: vi.fn(),
    verifyDriveFolder: vi.fn(),
    estimateDrive: vi.fn(),
    getModelStatus: vi.fn().mockResolvedValue({ models_downloaded: true }),
  },
}));

describe('Google Drive Image Quality, Storage Estimation & Cache Location UI', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getSettings).mockResolvedValue({
      output_dir: 'export',
      cache_dir: 'cache',
      drive_image_quality: 'original',
      min_face_size: 64,
      distance_threshold: 0.50,
    } as any);

    vi.mocked(api.verifyDriveFolder).mockResolvedValue({
      valid: true,
      folder_id: 'test_drive_folder_123456789012345',
      folder_name: 'Wedding Photos 2026',
      has_images: true,
      image_count_preview: 50,
      message: 'Verified 50 photos',
    } as any);

    vi.mocked(api.estimateDrive).mockResolvedValue({
      valid: true,
      folder_id: 'test_drive_folder_123456789012345',
      folder_name: 'Wedding Photos 2026',
      total_photos: 50,
      total_original_bytes: 250000000, // 250 MB
      tier_estimates: {
        original: 250000000,
        best: 50 * 228000,
        better: 50 * 147000,
        fast: 50 * 64000,
      },
      selected_quality: 'original',
      required_bytes: 250000000,
      target_disk_free_bytes: 10000000000, // 10 GB
      temp_disk_free_bytes: 10000000000,
      is_space_sufficient: true,
      warning_message: null,
      folders_scanned: 2,
      skipped_videos: 0,
    } as any);
  });

  it('renders SettingsScreen with Drive Image Quality dropdown defaulting to original and storage inputs', async () => {
    render(<SettingsScreen />);

    await waitFor(() => {
      const dropdown = screen.getByTestId('select-drive-image-quality');
      expect(dropdown).toBeTruthy();
      expect(dropdown.textContent).toContain('Original (Full camera resolution)');
    });

    // Verify Output Dir and Cache Dir inputs exist
    expect(screen.getByTestId('setting-output-dir')).toBeTruthy();
    expect(screen.getByTestId('setting-cache-dir')).toBeTruthy();
  });

  it('renders AddSourceModal with Drive Image Quality select in drive mode defaulting to original', async () => {
    const handleAdd = vi.fn();
    render(<AddSourceModal onClose={vi.fn()} onSourceAdded={handleAdd} />);

    // Switch to Google Drive mode
    const driveTypeBtn = screen.getByTestId('btn-source-type-drive');
    fireEvent.click(driveTypeBtn);

    // Verify quality select exists and defaults to original
    const qualitySelect = screen.getByTestId('select-source-drive-quality') as HTMLSelectElement;
    expect(qualitySelect).toBeTruthy();
    expect(qualitySelect.value).toBe('original');

    // Change quality to 'better'
    fireEvent.change(qualitySelect, { target: { value: 'better' } });
    expect(qualitySelect.value).toBe('better');
  });

  it('renders HomeScreen with Drive Quality selector defaulting to original and passes to onStartJob', async () => {
    const handleStartJob = vi.fn();
    render(
      <HomeScreen
        onStartJob={handleStartJob}
        {...({ initialSourceMode: 'drive', controlledApiKeyConfigured: true } as any)}
      />
    );

    const qualitySelect = screen.getByTestId('select-home-drive-quality') as HTMLSelectElement;
    expect(qualitySelect).toBeTruthy();
    expect(qualitySelect.value).toBe('original');

    // Change to 'fast'
    fireEvent.change(qualitySelect, { target: { value: 'fast' } });
    expect(qualitySelect.value).toBe('fast');
  });

  it('verifies drive folder, fetches storage estimate, and displays download size and free space', async () => {
    const handleStartJob = vi.fn();
    render(
      <HomeScreen
        onStartJob={handleStartJob}
        {...({ initialSourceMode: 'drive', controlledApiKeyConfigured: true } as any)}
      />
    );

    const input = screen.getByTestId('input-drive-link') as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'https://drive.google.com/drive/folders/test_drive_folder_123456789012345' } });

    const checkBtn = screen.getByTestId('btn-check-drive');
    fireEvent.click(checkBtn);

    await waitFor(() => {
      expect(api.verifyDriveFolder).toHaveBeenCalled();
      expect(api.estimateDrive).toHaveBeenCalled();
    });

    await waitFor(() => {
      const estimateCard = screen.getByTestId('drive-storage-estimate-card');
      expect(estimateCard).toBeTruthy();
      expect(estimateCard.textContent).toContain('Download Size: ~238.4 MB');
      expect(estimateCard.textContent).toContain('50 photos across 2 folders');
      expect(estimateCard.textContent).toContain('Free disk space: 9.31 GB');
    });
  });

  it('displays warning banner when disk space is insufficient', async () => {
    vi.mocked(api.estimateDrive).mockResolvedValueOnce({
      valid: true,
      folder_id: 'test_drive_folder_123456789012345',
      folder_name: 'Big Event',
      total_photos: 1000,
      total_original_bytes: 5000000000, // 5 GB
      tier_estimates: { original: 5000000000, best: 228000000, better: 147000000, fast: 64000000 },
      selected_quality: 'original',
      required_bytes: 5000000000,
      target_disk_free_bytes: 1000000000, // 1 GB free
      temp_disk_free_bytes: 1000000000,
      is_space_sufficient: false,
      warning_message: 'Low disk space on export drive: 953.7 MB available, ~4.66 GB needed.',
      folders_scanned: 1,
      skipped_videos: 0,
    } as any);

    render(
      <HomeScreen
        onStartJob={vi.fn()}
        {...({ initialSourceMode: 'drive', controlledApiKeyConfigured: true } as any)}
      />
    );

    const input = screen.getByTestId('input-drive-link') as HTMLInputElement;
    fireEvent.change(input, { target: { value: 'https://drive.google.com/drive/folders/test_drive_folder_123456789012345' } });

    const checkBtn = screen.getByTestId('btn-check-drive');
    fireEvent.click(checkBtn);

    await waitFor(() => {
      const warningBanner = screen.getByTestId('drive-space-warning-banner');
      expect(warningBanner).toBeTruthy();
      expect(warningBanner.textContent).toContain('Low disk space on export drive');
    });
  });

  it('allows specifying custom cache_dir and passes it to onStartJob', async () => {
    const handleStartJob = vi.fn();
    render(
      <HomeScreen
        onStartJob={handleStartJob}
        {...({ initialSourceMode: 'drive', controlledApiKeyConfigured: true } as any)}
      />
    );

    // Open scan options
    const toggleBtn = screen.getByTestId('toggle-scan-options-btn');
    fireEvent.click(toggleBtn);

    // Enter custom cache dir
    const cacheInput = screen.getByTestId('input-cache-dir') as HTMLInputElement;
    fireEvent.change(cacheInput, { target: { value: 'D:\\custom_cache' } });

    // Enter folder link and check
    const linkInput = screen.getByTestId('input-drive-link') as HTMLInputElement;
    fireEvent.change(linkInput, { target: { value: 'https://drive.google.com/drive/folders/test_drive_folder_123456789012345' } });

    const checkBtn = screen.getByTestId('btn-check-drive');
    fireEvent.click(checkBtn);

    await waitFor(() => {
      expect(screen.getByTestId('select-home-drive-quality')).toBeTruthy();
    });

    const startBtn = screen.getByTestId('start-job-btn');
    fireEvent.click(startBtn);

    await waitFor(() => {
      expect(handleStartJob).toHaveBeenCalledWith(
        undefined,
        'https://drive.google.com/drive/folders/test_drive_folder_123456789012345',
        undefined,
        expect.objectContaining({
          drive_image_quality: 'original',
          cache_dir: 'D:\\custom_cache',
        })
      );
    });
  });
});
