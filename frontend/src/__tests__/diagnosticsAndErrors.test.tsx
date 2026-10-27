import React from 'react';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { CopyDiagnosticsButton } from '../components/CopyDiagnosticsButton';
import { ProgressScreen } from '../components/ProgressScreen';
import { JobStatus } from '../types';

describe('CopyDiagnosticsButton and Error Screens (Phase V2-1)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders CopyDiagnosticsButton and copies provided reportText to clipboard', async () => {
    const writeTextMock = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: {
        writeText: writeTextMock,
      },
    });

    const mockReport = 'CatLog Diagnostics Report\nVersion: 0.1.0\nSettings Hash: abcd1234abcd1234\n';
    const onCopiedMock = vi.fn();

    render(
      <CopyDiagnosticsButton
        reportText={mockReport}
        onCopied={onCopiedMock}
      />
    );

    const btn = screen.getByRole('button', { name: /copy diagnostics/i });
    expect(btn).toBeDefined();

    fireEvent.click(btn);

    await waitFor(() => {
      expect(writeTextMock).toHaveBeenCalledWith(mockReport);
      expect(onCopiedMock).toHaveBeenCalled();
      expect(screen.getByText(/copied safe report/i)).toBeDefined();
    });
  });

  it('fetches /api/diagnostics if reportText is not provided', async () => {
    const writeTextMock = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, {
      clipboard: {
        writeText: writeTextMock,
      },
    });

    const mockFetchedReport = 'CatLog Diagnostics Report\nFrom API\nCounts:\n  - Photos Ingested: 10\n';
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        formatted_report: mockFetchedReport,
      }),
    } as any);

    render(<CopyDiagnosticsButton />);

    const btn = screen.getByRole('button', { name: /copy diagnostics/i });
    fireEvent.click(btn);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/diagnostics');
      expect(writeTextMock).toHaveBeenCalledWith(mockFetchedReport);
    });
  });

  it('renders failure banner in ProgressScreen with classified error code and plain-language fix', () => {
    const failedStatus: JobStatus = {
      job_id: 'err_job_1',
      status: 'failed',
      stage: 'failed',
      current: 12,
      total: 50,
      percent: 24,
      message: 'Google Drive Quota Exceeded: HTTP 403 Rate Limit',
      error: 'Google Drive API quota or request rate limit exceeded (HTTP 403).',
      error_code: 'QUOTA_403',
      error_title: 'Google Drive Quota Exceeded',
      plain_language_fix: 'Enter your free Google Drive API key in Settings or wait a few minutes.',
      diagnostics_report: 'CatLog Diagnostics Report\nVersion: 0.1.0\nError Code: QUOTA_403\n',
    };

    render(
      <ProgressScreen
        status={failedStatus}
        progressHistory={[]}
        onCancelJob={vi.fn()}
        onGoToReview={vi.fn()}
        onNavigateHome={vi.fn()}
        onNavigateSettings={vi.fn()}
      />
    );

    const failureBanner = screen.getByTestId('scan-failure-banner');
    expect(failureBanner).toBeDefined();

    expect(screen.getByText(/\[QUOTA_403\]/i)).toBeDefined();
    expect(screen.getByRole('heading', { name: /Google Drive Quota Exceeded/i })).toBeDefined();
    expect(
      screen.getByText(/Enter your free Google Drive API key in Settings or wait a few minutes\./i)
    ).toBeDefined();

    const copyBtn = screen.getByRole('button', { name: /copy diagnostics/i });
    expect(copyBtn).toBeDefined();

    const settingsBtn = screen.getByRole('button', { name: /open settings/i });
    expect(settingsBtn).toBeDefined();
  });
});
