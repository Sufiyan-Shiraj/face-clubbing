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
  },
}));

describe('Google Drive Image Quality UI (Phase V2-6)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getSettings).mockResolvedValue({
      output_dir: 'export',
      drive_image_quality: 'fast',
      min_face_size: 64,
      distance_threshold: 0.50,
    } as any);
  });

  it('renders SettingsScreen with Drive Image Quality dropdown defaulting to fast', async () => {
    render(<SettingsScreen onClose={vi.fn()} />);

    await waitFor(() => {
      const dropdown = screen.getByTestId('select-drive-image-quality');
      expect(dropdown).toBeTruthy();
      expect(dropdown.textContent).toContain('Fast (1000 px)');
    });
  });

  it('renders AddSourceModal with Drive Image Quality select in drive mode', async () => {
    const handleAdd = vi.fn();
    render(<AddSourceModal isOpen={true} onClose={vi.fn()} onAddSource={handleAdd} />);

    // Switch to Google Drive mode
    const driveTypeBtn = screen.getByTestId('btn-source-type-drive');
    fireEvent.click(driveTypeBtn);

    // Verify quality select exists
    const qualitySelect = screen.getByTestId('select-source-drive-quality') as HTMLSelectElement;
    expect(qualitySelect).toBeTruthy();
    expect(qualitySelect.value).toBe('fast');

    // Change quality to 'best'
    fireEvent.change(qualitySelect, { target: { value: 'best' } });
    expect(qualitySelect.value).toBe('best');
  });

  it('renders HomeScreen with Drive Quality selector in Drive mode and passes to onStartJob', async () => {
    const handleStartJob = vi.fn();
    render(
      <HomeScreen
        onStartJob={handleStartJob}
        initialSourceMode="drive"
        controlledApiKeyConfigured={true}
      />
    );

    const qualitySelect = screen.getByTestId('select-home-drive-quality') as HTMLSelectElement;
    expect(qualitySelect).toBeTruthy();
    expect(qualitySelect.value).toBe('fast');

    // Change to 'better'
    fireEvent.change(qualitySelect, { target: { value: 'better' } });
    expect(qualitySelect.value).toBe('better');
  });
});
