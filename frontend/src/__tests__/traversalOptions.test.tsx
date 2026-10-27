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
    verifyDriveFolder: vi.fn(),
  },
}));

describe('Folder & Subfolder Traversal Options', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.getSettings).mockResolvedValue({
      output_dir: 'export',
      scan_subfolders: true,
      max_subfolder_depth: 5,
      follow_shortcuts: false,
    } as any);
  });

  it('renders HomeScreen traversal options with correct defaults (subfolders=true, depth=5, shortcuts=false)', async () => {
    const handleStartJob = vi.fn();
    render(<HomeScreen onStartJob={handleStartJob} />);

    // Check disclosure button
    const toggleBtn = screen.getByTestId('toggle-scan-options-btn');
    expect(toggleBtn).toBeTruthy();

    // Elements should exist in DOM with correct default states
    const subfoldersCheckbox = screen.getByTestId('opt-scan-subfolders') as HTMLInputElement;
    const depthSelect = screen.getByTestId('opt-subfolder-depth') as HTMLSelectElement;
    const shortcutsCheckbox = screen.getByTestId('opt-shortcut-folders') as HTMLInputElement;

    expect(subfoldersCheckbox.checked).toBe(true);
    expect(depthSelect.value).toBe('5');
    expect(shortcutsCheckbox.checked).toBe(false);
  });

  it('passes customized traversal options to onStartJob when starting scan', async () => {
    const handleStartJob = vi.fn();
    render(<HomeScreen onStartJob={handleStartJob} folderPath="/photos/event2026" sourceMode="local" />);

    // Toggle subfolders off
    const subfoldersCheckbox = screen.getByTestId('opt-scan-subfolders');
    fireEvent.click(subfoldersCheckbox);

    // Toggle shortcut folders on
    const shortcutsCheckbox = screen.getByTestId('opt-shortcut-folders');
    fireEvent.click(shortcutsCheckbox);

    const startBtn = screen.getByTestId('start-job-btn');
    fireEvent.click(startBtn);

    await waitFor(() => {
      expect(handleStartJob).toHaveBeenCalledTimes(1);
      expect(handleStartJob).toHaveBeenCalledWith(
        '/photos/event2026',
        undefined,
        undefined,
        {
          scan_subfolders: false,
          max_subfolder_depth: 5,
          follow_shortcuts: true,
        }
      );
    });
  });

  it('renders Folder & Cloud Traversal card on SettingsScreen and saves updates', async () => {
    vi.mocked(api.updateSettings).mockResolvedValue({} as any);

    render(<SettingsScreen />);

    await waitFor(() => {
      expect(screen.getByText('Folder & Cloud Traversal')).toBeTruthy();
    });

    const subfoldersInput = screen.getByTestId('setting-scan-subfolders') as HTMLInputElement;
    expect(subfoldersInput.checked).toBe(true);

    const shortcutsInput = screen.getByTestId('setting-follow-shortcuts') as HTMLInputElement;
    expect(shortcutsInput.checked).toBe(false);

    // Toggle shortcut folders
    fireEvent.click(shortcutsInput);

    await waitFor(() => {
      expect(api.updateSettings).toHaveBeenCalledWith({ follow_shortcuts: true });
    });
  });
});
