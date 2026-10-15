import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { HomeScreen, extractDriveFolderId } from '../components/HomeScreen';
import { api } from '../api/client';

vi.mock('../api/client', () => ({
  api: {
    verifyDriveFolder: vi.fn(),
    getSettings: vi.fn(),
    updateSettings: vi.fn(),
  },
}));

describe('Organizer Two-Stage Interaction & Drive Folder ID Extraction', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('extracts Google Drive folder ID correctly from various valid link formats', () => {
    expect(
      extractDriveFolderId('https://drive.google.com/drive/folders/1aB2c3D4e5F6g7H8i9Jk?usp=sharing')
    ).toBe('1aB2c3D4e5F6g7H8i9Jk');

    expect(
      extractDriveFolderId('https://drive.google.com/drive/u/0/folders/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs')
    ).toBe('1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs');

    expect(
      extractDriveFolderId('https://drive.google.com/open?id=1234567890abcdef1234567890')
    ).toBe('1234567890abcdef1234567890');

    expect(
      extractDriveFolderId('1aB2c3D4e5F6g7H8i9Jk0123')
    ).toBe('1aB2c3D4e5F6g7H8i9Jk0123');

    // Rejects file links
    expect(
      extractDriveFolderId('https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs/view')
    ).toBeNull();

    // Rejects random text
    expect(extractDriveFolderId('hello world')).toBeNull();
  });

  it('renders Initial State with no face preview frames visible', () => {
    const handleStartJob = vi.fn();
    render(<HomeScreen onStartJob={handleStartJob} />);

    // Headline and subcaption
    expect(screen.getByText('Who was at the event?')).toBeTruthy();
    expect(screen.getByText('Sort your event photos by person using face clustering.')).toBeTruthy();

    // Three source-mode buttons
    expect(screen.getByRole('button', { name: /Google Drive/i })).toBeTruthy();
    expect(screen.getByRole('button', { name: /Local folder/i })).toBeTruthy();
    expect(screen.getByRole('button', { name: /Zip file/i })).toBeTruthy();

    // Initial input row and helper
    const driveInput = screen.getByTestId('input-drive-link') as HTMLInputElement;
    expect(driveInput).toBeTruthy();
    expect(screen.getByText(/Folder must be shared as 'Anyone with the link'/i)).toBeTruthy();

    // Face preview section must be hidden in initial state
    const facePreviewSection = document.querySelector('.faces-preview-section');
    expect(facePreviewSection).toBeTruthy();
    expect(facePreviewSection?.classList.contains('hidden')).toBe(true);
    expect(facePreviewSection?.classList.contains('visible')).toBe(false);

    // No character cells in initial state
    expect(document.querySelector('.char-cells-row')).toBeNull();
  });

  it('does NOT convert to cells on paste until Check link is clicked; then transitions to Stage 2 with folder name', async () => {
    const handleStartJob = vi.fn();
    vi.mocked(api.verifyDriveFolder).mockResolvedValue({
      valid: true,
      folder_id: '1aB2c3D4e5F6g7H8i9Jk',
      folder_name: 'Summer Vacation Photos',
      has_images: true,
      image_count_preview: 42,
    });

    render(<HomeScreen onStartJob={handleStartJob} />);

    const driveInput = screen.getByTestId('input-drive-link') as HTMLInputElement;
    fireEvent.change(driveInput, {
      target: { value: 'https://drive.google.com/drive/folders/1aB2c3D4e5F6g7H8i9Jk?usp=sharing' },
    });

    // 1. Must NOT automatically put into cells on paste!
    expect(document.querySelector('.char-cells-row')).toBeNull();

    // 2. Start Scan button must be grayed out before verification
    const scanBtnInitial = screen.getByTestId('start-job-btn') as HTMLButtonElement;
    expect(scanBtnInitial.disabled).toBe(true);

    // 3. Click Check link button
    const checkBtn = screen.getByTestId('btn-check-drive');
    fireEvent.click(checkBtn);

    // 4. Verification succeeds -> transitions to Stage 2
    await waitFor(() => {
      expect(api.verifyDriveFolder).toHaveBeenCalledWith(
        'https://drive.google.com/drive/folders/1aB2c3D4e5F6g7H8i9Jk?usp=sharing',
        undefined
      );
      expect(document.querySelector('.char-cells-row')).toBeTruthy();
      expect(screen.getAllByText('Summer Vacation Photos').length).toBeGreaterThan(0);
      expect(screen.getByText(/42\+ images detected/i)).toBeTruthy();
    });

    // Character cells row should appear with individual cells for each character (editable inputs)
    const charCells = document.querySelectorAll('.char-cell');
    expect(charCells.length).toBe('1aB2c3D4e5F6g7H8i9Jk'.length);
    expect((charCells[0] as HTMLInputElement).value).toBe('1');
    expect((charCells[1] as HTMLInputElement).value).toBe('a');
    expect((charCells[charCells.length - 1] as HTMLInputElement).value).toBe('k');

    // Test editing a character cell
    fireEvent.change(charCells[0], { target: { value: '9' } });
    expect((charCells[0] as HTMLInputElement).value).toBe('9');

    // Detected drive link text and folder header
    expect(screen.getByText('DRIVE FOLDER')).toBeTruthy();
    expect(screen.getAllByText('Summer Vacation Photos').length).toBeGreaterThan(0);

    // Stage expanded class applied for upward shift
    const stageContainer = document.querySelector('.home-stage-container');
    expect(stageContainer?.classList.contains('stage-expanded')).toBe(true);

    // Face preview section revealed
    const facePreviewSection = document.querySelector('.faces-preview-section');
    expect(facePreviewSection?.classList.contains('visible')).toBe(true);

    // Submitting Scan folder works now that link is verified
    const scanBtn = screen.getByTestId('start-job-btn') as HTMLButtonElement;
    expect(scanBtn.disabled).toBe(false);

    fireEvent.click(scanBtn);
    expect(handleStartJob).toHaveBeenCalledTimes(1);
    expect(handleStartJob).toHaveBeenCalledWith(
      undefined,
      'https://drive.google.com/drive/folders/9aB2c3D4e5F6g7H8i9Jk?usp=sharing',
      undefined
    );
  });

  it('prompts API key modal when API key is missing during verification', async () => {
    const handleStartJob = vi.fn();
    vi.mocked(api.verifyDriveFolder).mockResolvedValue({
      valid: false,
      folder_id: '1aB2c3D4e5F6g7H8i9Jk',
      error_type: 'api_key_missing',
      message: 'Google Drive API key is missing.',
    });
    vi.mocked(api.updateSettings).mockResolvedValue({} as any);

    render(<HomeScreen onStartJob={handleStartJob} />);

    const driveInput = screen.getByTestId('input-drive-link') as HTMLInputElement;
    fireEvent.change(driveInput, {
      target: { value: 'https://drive.google.com/drive/folders/1aB2c3D4e5F6g7H8i9Jk?usp=sharing' },
    });

    const checkBtn = screen.getByTestId('btn-check-drive');
    fireEvent.click(checkBtn);

    // Modal pops up
    await waitFor(() => {
      expect(screen.getByTestId('input-drive-api-key')).toBeTruthy();
      expect(screen.getByText(/Google Drive API key is missing/i)).toBeTruthy();
    });

    // Enter API key and save
    const apiKeyInput = screen.getByTestId('input-drive-api-key') as HTMLInputElement;
    fireEvent.change(apiKeyInput, { target: { value: 'AIzaSyNewKey123' } });

    // Mock successful re-verification
    vi.mocked(api.verifyDriveFolder).mockResolvedValueOnce({
      valid: true,
      folder_id: '1aB2c3D4e5F6g7H8i9Jk',
      folder_name: 'Verified Event Folder',
      has_images: true,
      image_count_preview: 10,
    });

    const saveKeyBtn = screen.getByTestId('btn-save-api-key');
    fireEvent.click(saveKeyBtn);

    await waitFor(() => {
      expect(api.updateSettings).toHaveBeenCalledWith({ drive_api_key: 'AIzaSyNewKey123' });
      // Modal closes
      expect(screen.queryByTestId('input-drive-api-key')).toBeNull();
    });
  });

  it('reverses to Initial State when Change link is clicked', async () => {
    const handleStartJob = vi.fn();
    vi.mocked(api.verifyDriveFolder).mockResolvedValue({
      valid: true,
      folder_id: '1aB2c3D4e5F6g7H8i9Jk',
      folder_name: 'Summer Vacation Photos',
      has_images: true,
      image_count_preview: 42,
    });

    render(<HomeScreen onStartJob={handleStartJob} />);

    const driveInput = screen.getByTestId('input-drive-link') as HTMLInputElement;
    fireEvent.change(driveInput, {
      target: { value: 'https://drive.google.com/drive/folders/1aB2c3D4e5F6g7H8i9Jk?usp=sharing' },
    });

    fireEvent.click(screen.getByTestId('btn-check-drive'));

    await waitFor(() => {
      expect(document.querySelector('.char-cells-row')).toBeTruthy();
    });

    // Click Change link
    const clearBtn = screen.getByRole('button', { name: /Change link/i });
    fireEvent.click(clearBtn);

    // Character cells removed
    expect(document.querySelector('.char-cells-row')).toBeNull();

    // Stage container restores initial position
    const stageContainer = document.querySelector('.home-stage-container');
    expect(stageContainer?.classList.contains('stage-expanded')).toBe(false);

    // Faces preview section hidden again
    const facePreviewSection = document.querySelector('.faces-preview-section');
    expect(facePreviewSection?.classList.contains('hidden')).toBe(true);
    expect(facePreviewSection?.classList.contains('visible')).toBe(false);
  });

  it('switches between source modes without leaving stale Drive content', async () => {
    const handleStartJob = vi.fn();
    vi.mocked(api.verifyDriveFolder).mockResolvedValue({
      valid: true,
      folder_id: '1aB2c3D4e5F6g7H8i9Jk',
      folder_name: 'Summer Vacation Photos',
      has_images: true,
      image_count_preview: 42,
    });

    render(<HomeScreen onStartJob={handleStartJob} />);

    // Enter Drive link and verify
    const driveInput = screen.getByTestId('input-drive-link') as HTMLInputElement;
    fireEvent.change(driveInput, {
      target: { value: 'https://drive.google.com/drive/folders/1aB2c3D4e5F6g7H8i9Jk?usp=sharing' },
    });
    fireEvent.click(screen.getByTestId('btn-check-drive'));

    await waitFor(() => {
      expect(document.querySelector('.char-cells-row')).toBeTruthy();
    });

    // Switch to Local folder
    const localBtn = screen.getByTestId('btn-source-local');
    fireEvent.click(localBtn);

    // Drive character cells should be hidden
    expect(document.querySelector('.char-cells-row')).toBeNull();
    expect(screen.getByTestId('input-source-path')).toBeTruthy();
    expect(screen.getByText(/Local target:/i)).toBeTruthy();

    // Switch to Zip file
    const zipBtn = screen.getByTestId('btn-source-zip');
    fireEvent.click(zipBtn);

    // Drive character cells still hidden
    expect(document.querySelector('.char-cells-row')).toBeNull();
    expect(screen.getByTestId('input-source-path')).toBeTruthy();
    expect(screen.getByText(/Archive target:/i)).toBeTruthy();
  });

  it('does NOT show Set API key button when API key is already configured', async () => {
    const handleStartJob = vi.fn();
    vi.mocked(api.getSettings).mockResolvedValue({
      drive_api_key_configured: true,
    } as any);

    render(<HomeScreen onStartJob={handleStartJob} isApiKeyConfigured={true} />);

    // In Drive mode, the 'Set API key' button must NOT be visible
    expect(screen.queryByTestId('btn-set-api-key')).toBeNull();
    expect(screen.queryByText(/Set API key/i)).toBeNull();
    expect(screen.getByText(/Folder must be shared as 'Anyone with the link'/i)).toBeTruthy();
  });

  it('shows Set API key button when API key is not configured', async () => {
    const handleStartJob = vi.fn();
    vi.mocked(api.getSettings).mockResolvedValue({
      drive_api_key_configured: false,
    } as any);

    render(<HomeScreen onStartJob={handleStartJob} isApiKeyConfigured={false} />);

    // In Drive mode without API key configured, the 'Set API key' button is visible
    expect(screen.getByTestId('btn-set-api-key')).toBeTruthy();
  });
});
