import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { HomeScreen } from '../components/HomeScreen';

describe('HomeScreen Native OS Picker & pywebview Bridge', () => {
  beforeEach(() => {
    delete (window as any).pywebview;
  });

  it('triggers native OS folder picker via window.pywebview.api.select_folder when present', async () => {
    const mockSelectFolder = vi.fn().mockResolvedValue('C:\\photos\\event_2026');
    (window as any).pywebview = {
      api: {
        select_folder: mockSelectFolder,
      },
    };

    const handleStartJob = vi.fn();
    render(<HomeScreen onStartJob={handleStartJob} />);

    const browseFolderBtn = screen.getByTestId('btn-browse-folder');
    expect(browseFolderBtn).toBeTruthy();

    fireEvent.click(browseFolderBtn);

    await waitFor(() => {
      expect(mockSelectFolder).toHaveBeenCalledWith('Select Photo Folder');
    });

    const input = screen.getByTestId('input-source-path') as HTMLInputElement;
    await waitFor(() => {
      expect(input.value).toBe('C:\\photos\\event_2026');
    });
  });

  it('triggers native OS file picker via window.pywebview.api.select_file when present', async () => {
    const mockSelectFile = vi.fn().mockResolvedValue('C:\\photos\\archive.zip');
    (window as any).pywebview = {
      api: {
        select_file: mockSelectFile,
      },
    };

    const handleStartJob = vi.fn();
    render(<HomeScreen onStartJob={handleStartJob} />);

    const browseFileBtn = screen.getByTestId('btn-browse-file');
    expect(browseFileBtn).toBeTruthy();

    fireEvent.click(browseFileBtn);

    await waitFor(() => {
      expect(mockSelectFile).toHaveBeenCalledWith('Select Zip Archive or File');
    });

    const input = screen.getByTestId('input-source-path') as HTMLInputElement;
    await waitFor(() => {
      expect(input.value).toBe('C:\\photos\\archive.zip');
    });
  });

  it('falls back gracefully when window.pywebview is undefined', () => {
    const createElementSpy = vi.spyOn(document, 'createElement');
    const handleStartJob = vi.fn();
    render(<HomeScreen onStartJob={handleStartJob} />);

    const browseFolderBtn = screen.getByTestId('btn-browse-folder');
    fireEvent.click(browseFolderBtn);

    expect(createElementSpy).toHaveBeenCalledWith('input');
    createElementSpy.mockRestore();
  });
});
