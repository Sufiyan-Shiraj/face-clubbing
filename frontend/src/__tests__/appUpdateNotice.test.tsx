import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AppUpdateBanner } from '../components/AppUpdateBanner';
import { api } from '../api/client';

vi.mock('../api/client', () => ({
  api: {
    checkAppUpdate: vi.fn(),
  },
}));

describe('AppUpdateBanner Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders nothing in banner mode when no update is available', async () => {
    vi.mocked(api.checkAppUpdate).mockResolvedValue({
      current_version: '0.1.0-rc1',
      latest_version: '0.1.0-rc1',
      update_available: false,
      release_name: '',
      release_url: '',
      release_notes: '',
      published_at: '',
      checked_online: true,
      error: null,
    });

    const { container } = render(<AppUpdateBanner variant="banner" />);
    await waitFor(() => {
      expect(api.checkAppUpdate).toHaveBeenCalled();
    });

    expect(screen.queryByTestId('app-update-notice-banner')).toBeNull();
  });

  it('renders top notice banner when a newer version is available and allows dismissing', async () => {
    vi.mocked(api.checkAppUpdate).mockResolvedValue({
      current_version: '0.1.0-rc1',
      latest_version: '0.2.0',
      update_available: true,
      release_name: 'CatLog v0.2.0: Distribution',
      release_url: 'https://github.com/Sufiyan-Shiraj/face-clubbing/releases/tag/v0.2.0',
      release_notes: 'New release with Inno Setup',
      published_at: '2026-11-03T12:00:00Z',
      checked_online: true,
      error: null,
    });

    render(<AppUpdateBanner variant="banner" />);
    await waitFor(() => {
      expect(screen.getByTestId('app-update-notice-banner')).toBeDefined();
    });

    expect(screen.getByText(/A new version of CatLog/i)).toBeDefined();
    expect(screen.getByText('v0.2.0')).toBeDefined();

    const link = screen.getByTestId('banner-view-github-release-link');
    expect(link.getAttribute('href')).toBe('https://github.com/Sufiyan-Shiraj/face-clubbing/releases/tag/v0.2.0');

    // Dismiss banner
    fireEvent.click(screen.getByTestId('btn-dismiss-app-update-banner'));
    expect(screen.queryByTestId('app-update-notice-banner')).toBeNull();
  });

  it('renders in settings screen and displays check for update button', async () => {
    vi.mocked(api.checkAppUpdate).mockResolvedValue({
      current_version: '0.1.0-rc1',
      latest_version: '0.1.0-rc1',
      update_available: false,
      release_name: '',
      release_url: '',
      release_notes: '',
      published_at: '',
      checked_online: true,
      error: null,
    });

    render(<AppUpdateBanner variant="settings" />);
    await waitFor(() => {
      expect(screen.getByText(/CatLog Updates/i)).toBeDefined();
    });

    expect(screen.getByText(/0.1.0-rc1/)).toBeDefined();
    const checkBtn = screen.getByTestId('btn-check-app-update');
    expect(checkBtn).toBeDefined();

    // Trigger manual check
    fireEvent.click(checkBtn);
    expect(api.checkAppUpdate).toHaveBeenCalledTimes(2);
  });
});

