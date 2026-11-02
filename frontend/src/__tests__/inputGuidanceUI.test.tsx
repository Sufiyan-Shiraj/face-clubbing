import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { HomeScreen, detectUnsupportedCloudLink } from '../components/HomeScreen';
import { AddSourceModal } from '../components/AddSourceModal';
import { InputGuidanceModal } from '../components/InputGuidanceModal';
import { api } from '../api/client';

vi.mock('../api/client', () => ({
  api: {
    addProjectSource: vi.fn(),
    checkDriveFolder: vi.fn(),
    getModelStatus: vi.fn().mockResolvedValue({
      installed: true,
      files_present: 2,
      total_files: 2,
      files: [],
      recommended_action: 'none',
      status: 'ready',
    }),
    getSettings: vi.fn().mockResolvedValue({
      drive_api_key: '',
    }),
  },
}));

describe('Phase V2-7: Input Guidance & Cloud Link Detection UI', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('detectUnsupportedCloudLink utility', () => {
    it('detects Google Photos share and app URLs', () => {
      const res = detectUnsupportedCloudLink('https://photos.google.com/share/AF1QipNxyz');
      expect(res).not.toBeNull();
      expect(res?.code).toBe('GOOGLE_PHOTOS_LINK');
      expect(res?.service).toBe('Google Photos');
      expect(res?.howToFix).toContain('Download all');

      const res2 = detectUnsupportedCloudLink('https://photos.app.goo.gl/abcdef123');
      expect(res2?.code).toBe('GOOGLE_PHOTOS_LINK');
    });

    it('detects Dropbox, OneDrive, iCloud, and Box', () => {
      expect(detectUnsupportedCloudLink('https://www.dropbox.com/scl/fo/abc/h')?.code).toBe('DROPBOX_LINK');
      expect(detectUnsupportedCloudLink('https://onedrive.live.com/?id=root')?.code).toBe('ONEDRIVE_LINK');
      expect(detectUnsupportedCloudLink('https://1drv.ms/f/s!abc')?.code).toBe('ONEDRIVE_LINK');
      expect(detectUnsupportedCloudLink('https://www.icloud.com/sharedalbum/#B0123')?.code).toBe('ICLOUD_LINK');
      expect(detectUnsupportedCloudLink('https://app.box.com/s/xyz')?.code).toBe('BOX_LINK');
    });

    it('returns null for valid Google Drive folder links', () => {
      expect(
        detectUnsupportedCloudLink('https://drive.google.com/drive/folders/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OIvE2up08')
      ).toBeNull();
      expect(detectUnsupportedCloudLink('1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OIvE2up08')).toBeNull();
    });
  });

  describe('HomeScreen Guidance & Cloud Link Validation', () => {
    it('opens InputGuidanceModal when "How do I get my photos in?" button is clicked', () => {
      render(<HomeScreen onStartJob={vi.fn()} />);

      const guidanceBtn = screen.getByTestId('btn-open-input-guidance');
      expect(guidanceBtn).toBeTruthy();

      fireEvent.click(guidanceBtn);

      const modal = screen.getByTestId('input-guidance-modal');
      expect(modal).toBeTruthy();
      expect(screen.getByTestId('input-guidance-title')).toBeTruthy();
    });

    it('warns user when Google Photos link is entered in Drive input', async () => {
      render(
        <HomeScreen
          onStartJob={vi.fn()}
          sourceMode="drive"
          driveLink="https://photos.google.com/share/AF1QipNxyz"
        />
      );

      const checkBtn = screen.getByTestId('btn-check-drive');
      fireEvent.click(checkBtn);

      await waitFor(() => {
        expect(
          screen.getByText(/Google Photos album links cannot be/i)
        ).toBeTruthy();
      });

      const photosGuideBtn = screen.getByTestId('btn-open-photos-guide');
      expect(photosGuideBtn).toBeTruthy();

      fireEvent.click(photosGuideBtn);

      expect(screen.getByTestId('input-guidance-modal')).toBeTruthy();
      expect(screen.getByTestId('section-photos')).toBeTruthy();
    });
  });

  describe('InputGuidanceModal Tab Navigation & Dismissal', () => {
    it('switches between all 4 tabs and renders relevant instructions', () => {
      const onClose = vi.fn();
      render(<InputGuidanceModal isOpen={true} onClose={onClose} defaultTab="photos" />);

      // Tab 1: Photos
      expect(screen.getByTestId('section-photos')).toBeTruthy();
      expect(screen.getByText(/Google Photos Links Cannot Be Scanned Directly/i)).toBeTruthy();

      // Tab 2: Drive
      fireEvent.click(screen.getByTestId('tab-drive'));
      expect(screen.getByTestId('section-drive')).toBeTruthy();
      expect(screen.getByText(/Anyone with the link/i)).toBeTruthy();

      // Tab 3: Phone & WhatsApp
      fireEvent.click(screen.getByTestId('tab-phone'));
      expect(screen.getByTestId('section-phone')).toBeTruthy();
      expect(screen.getAllByText(/WhatsApp/i).length).toBeGreaterThanOrEqual(1);

      // Tab 4: Formats
      fireEvent.click(screen.getByTestId('tab-formats'));
      expect(screen.getByTestId('section-formats')).toBeTruthy();
      expect(screen.getByText(/Apple High-Efficiency/i)).toBeTruthy();
      expect(screen.getByText(/Safe Skipping of Non-Image Files/i)).toBeTruthy();

      // Dismiss with Got it button
      fireEvent.click(screen.getByTestId('btn-guidance-got-it'));
      expect(onClose).toHaveBeenCalled();
    });

    it('closes on Escape key press', () => {
      const onClose = vi.fn();
      render(<InputGuidanceModal isOpen={true} onClose={onClose} />);

      fireEvent.keyDown(window, { key: 'Escape' });
      expect(onClose).toHaveBeenCalled();
    });
  });

  describe('AddSourceModal Cloud Link Detection & Guidance', () => {
    it('blocks Google Photos link and offers export guide button', async () => {
      render(
        <AddSourceModal
          onClose={vi.fn()}
          onSourceAdded={vi.fn()}
        />
      );

      const pathInput = screen.getByTestId('input-source-path');
      fireEvent.change(pathInput, {
        target: { value: 'https://photos.google.com/share/AF1QipNxyz' },
      });

      const submitBtn = screen.getByTestId('btn-submit-add-source');
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(
          screen.getByText(/Google Photos album links cannot be/i)
        ).toBeTruthy();
      });

      const guideBtn = screen.getByTestId('btn-add-source-photos-guide');
      expect(guideBtn).toBeTruthy();

      fireEvent.click(guideBtn);
      expect(screen.getByTestId('input-guidance-modal')).toBeTruthy();
    });

    it('opens guidance modal from the footer Import Guide button', () => {
      render(
        <AddSourceModal
          onClose={vi.fn()}
          onSourceAdded={vi.fn()}
        />
      );

      const importGuideBtn = screen.getByTestId('btn-add-source-guidance');
      expect(importGuideBtn).toBeTruthy();

      fireEvent.click(importGuideBtn);
      expect(screen.getByTestId('input-guidance-modal')).toBeTruthy();
    });
  });
});
