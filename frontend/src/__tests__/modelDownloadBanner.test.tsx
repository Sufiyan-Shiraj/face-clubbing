import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ModelDownloadBanner } from '../components/ModelDownloadBanner';
import { api } from '../api/client';
import { ModelStatus } from '../types';

vi.mock('../api/client', () => ({
  api: {
    getModelStatus: vi.fn(),
    checkModelUpdates: vi.fn(),
    downloadModels: vi.fn(),
  },
}));

describe('ModelDownloadBanner & Model Management', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders blank download banner when models are already installed and up to date', async () => {
    const readyStatus: ModelStatus = {
      model_name: 'buffalo_l',
      installed: true,
      valid: true,
      status: 'ready',
      version: '1.0.0',
      latest_version: '1.0.0',
      update_available: false,
      is_downloading: false,
      stage: 'idle',
      percent: 0,
      current_bytes: 0,
      total_bytes: 288621354,
      message: 'Models verified and ready',
    };
    vi.mocked(api.getModelStatus).mockResolvedValue(readyStatus);

    render(<ModelDownloadBanner />);

    await waitFor(() => {
      expect(api.getModelStatus).toHaveBeenCalled();
    });

    // The download banner and download button must NOT be rendered (blank)
    expect(screen.queryByTestId('model-download-banner')).toBeNull();
    expect(screen.queryByTestId('download-models-btn')).toBeNull();

    // The compact refresh button is rendered so the user can check for updates
    expect(screen.getByTestId('check-models-update-btn')).toBeDefined();
    expect(screen.getByText(/AI face models installed/i)).toBeDefined();
  });

  it('renders prominent banner with Download button when models are missing', async () => {
    const missingStatus: ModelStatus = {
      model_name: 'buffalo_l',
      installed: false,
      valid: false,
      status: 'missing',
      version: '1.0.0',
      latest_version: '1.0.0',
      update_available: false,
      is_downloading: false,
      stage: 'idle',
      percent: 0,
      current_bytes: 0,
      total_bytes: 288621354,
      message: 'Models are missing',
    };
    vi.mocked(api.getModelStatus).mockResolvedValue(missingStatus);

    render(<ModelDownloadBanner />);

    await waitFor(() => {
      expect(screen.getByTestId('model-download-banner')).toBeDefined();
    });

    expect(screen.getByText(/Face Recognition Models Required/i)).toBeDefined();
    const downloadBtn = screen.getByTestId('download-models-btn');
    expect(downloadBtn).toBeDefined();
    expect(downloadBtn.textContent).toContain('Download Models');

    // Click download button
    vi.mocked(api.downloadModels).mockResolvedValue({
      ...missingStatus,
      is_downloading: true,
      stage: 'connecting',
    });

    fireEvent.click(downloadBtn);
    expect(api.downloadModels).toHaveBeenCalledWith(false);
  });

  it('shows update banner and converts download button to Update button when an update is found', async () => {
    const installedStatus: ModelStatus = {
      model_name: 'buffalo_l',
      installed: true,
      valid: true,
      status: 'ready',
      version: '1.0.0',
      latest_version: '1.0.0',
      update_available: false,
      is_downloading: false,
      stage: 'idle',
      percent: 0,
      current_bytes: 0,
      total_bytes: 288621354,
      message: 'Models ready',
    };

    const updateAvailableStatus: ModelStatus = {
      ...installedStatus,
      status: 'update_available',
      latest_version: '1.1.0',
      update_available: true,
      update_message: 'A new model update is available!',
    };

    // Initially installed & up to date
    vi.mocked(api.getModelStatus)
      .mockResolvedValueOnce(installedStatus)
      .mockResolvedValueOnce(updateAvailableStatus);

    vi.mocked(api.checkModelUpdates).mockResolvedValue({
      installed: true,
      update_available: true,
      version: '1.0.0',
      latest_version: '1.1.0',
      message: 'A new model update is available!',
    });

    render(<ModelDownloadBanner />);

    await waitFor(() => {
      expect(screen.getByTestId('check-models-update-btn')).toBeDefined();
    });
    // Currently blank
    expect(screen.queryByTestId('model-download-banner')).toBeNull();

    // Click refresh to check for updates
    fireEvent.click(screen.getByTestId('check-models-update-btn'));

    await waitFor(() => {
      expect(api.checkModelUpdates).toHaveBeenCalledWith(false);
    });

    // Now the banner shows and the button becomes "Update Models"
    await waitFor(() => {
      expect(screen.getByTestId('model-download-banner')).toBeDefined();
    });

    expect(screen.getByText(/Face Recognition Models Update Available/i)).toBeDefined();
    const updateBtn = screen.getByTestId('download-models-btn');
    expect(updateBtn).toBeDefined();
    expect(updateBtn.textContent).toContain('Update Models');

    // Clicking update initiates force download
    vi.mocked(api.downloadModels).mockResolvedValue({
      ...updateAvailableStatus,
      is_downloading: true,
      stage: 'downloading',
    });

    fireEvent.click(updateBtn);
    expect(api.downloadModels).toHaveBeenCalledWith(true);
  });

  it('renders progress bar and status when models are downloading', async () => {
    const downloadingStatus: ModelStatus = {
      model_name: 'buffalo_l',
      installed: false,
      valid: false,
      status: 'downloading',
      version: '1.0.0',
      latest_version: '1.0.0',
      update_available: false,
      is_downloading: true,
      stage: 'downloading',
      percent: 45.2,
      current_bytes: 130500000,
      total_bytes: 288621354,
      message: 'Downloading buffalo_l models (124.5 / 288.6 MB, 45.2%)...',
    };
    vi.mocked(api.getModelStatus).mockResolvedValue(downloadingStatus);

    render(<ModelDownloadBanner />);

    await waitFor(() => {
      expect(screen.getByTestId('model-download-banner')).toBeDefined();
    });

    expect(screen.getByText(/Downloading Face Models/i)).toBeDefined();
    expect(screen.getAllByText(/45.2%/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/124.5 MB \/ 275.3 MB/i)).toBeDefined();
  });
});
