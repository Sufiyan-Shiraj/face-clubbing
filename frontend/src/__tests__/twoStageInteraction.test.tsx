import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { HomeScreen, extractDriveFolderId } from '../components/HomeScreen';

describe('Organizer Two-Stage Interaction & Drive Folder ID Extraction', () => {
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

  it('transitions to Stage 2 upon entering a valid Google Drive link', () => {
    const handleStartJob = vi.fn();
    render(<HomeScreen onStartJob={handleStartJob} />);

    const driveInput = screen.getByTestId('input-drive-link') as HTMLInputElement;
    fireEvent.change(driveInput, {
      target: { value: 'https://drive.google.com/drive/folders/1aB2c3D4e5F6g7H8i9Jk?usp=sharing' },
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
    expect(screen.getByText('9aB2c3D4e5F6g7H8i9Jk')).toBeTruthy();

    // Drive Folder ID header
    expect(screen.getByText('DRIVE FOLDER ID')).toBeTruthy();

    // Detected drive link text
    expect(screen.getByText(/Detected Drive link\. Folder:/i)).toBeTruthy();
    expect(screen.getByText('9aB2c3D4e5F6g7H8i9Jk')).toBeTruthy();

    // Stage expanded class applied for upward shift
    const stageContainer = document.querySelector('.home-stage-container');
    expect(stageContainer?.classList.contains('stage-expanded')).toBe(true);

    // Face preview section revealed
    const facePreviewSection = document.querySelector('.faces-preview-section');
    expect(facePreviewSection?.classList.contains('visible')).toBe(true);
    expect(screen.getByText('Faces will appear here as the scan runs.')).toBeTruthy();

    // Submitting Scan folder works
    const scanBtn = screen.getByTestId('start-job-btn');
    fireEvent.click(scanBtn);
    expect(handleStartJob).toHaveBeenCalledTimes(1);
    expect(handleStartJob).toHaveBeenCalledWith(
      undefined,
      'https://drive.google.com/drive/folders/9aB2c3D4e5F6g7H8i9Jk?usp=sharing',
      undefined
    );
  });

  it('reverses to Initial State when Clear is clicked', () => {
    const handleStartJob = vi.fn();
    render(<HomeScreen onStartJob={handleStartJob} />);

    const driveInput = screen.getByTestId('input-drive-link') as HTMLInputElement;
    fireEvent.change(driveInput, {
      target: { value: 'https://drive.google.com/drive/folders/1aB2c3D4e5F6g7H8i9Jk?usp=sharing' },
    });

    expect(document.querySelector('.char-cells-row')).toBeTruthy();

    // Click Clear
    const clearBtn = screen.getByRole('button', { name: /Clear/i });
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

  it('switches between source modes without leaving stale Drive content', () => {
    const handleStartJob = vi.fn();
    render(<HomeScreen onStartJob={handleStartJob} />);

    // Enter Drive link
    const driveInput = screen.getByTestId('input-drive-link') as HTMLInputElement;
    fireEvent.change(driveInput, {
      target: { value: 'https://drive.google.com/drive/folders/1aB2c3D4e5F6g7H8i9Jk?usp=sharing' },
    });
    expect(document.querySelector('.char-cells-row')).toBeTruthy();

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
});
