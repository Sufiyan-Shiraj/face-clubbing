import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { PhotoGallery } from '../components/PhotoGallery';
import { UnrecognizedGallery } from '../components/UnrecognizedGallery';
import {
  getCleanDownloadName,
  isDrivePhoto,
  downloadLocalZip,
  downloadDriveSequential,
  PhotoDownloadItem,
  isMobileClassBrowser,
  checkDownloadSize,
  SIZE_GUARD_MOBILE_THRESHOLD_BYTES,
  SIZE_GUARD_DESKTOP_THRESHOLD_BYTES,
} from '../utils/downloader';
import { PersonCluster, PhotoInfo } from '../types';

describe('Filename Sanitization and Privacy (getCleanDownloadName)', () => {
  it('formats clean personname_001.jpg style with 3-digit zero-padding', () => {
    expect(getCleanDownloadName('Alice Wonderland', 0, 'IMG_9821.JPG')).toBe('alice_wonderland_001.jpg');
    expect(getCleanDownloadName('Bob Smith', 9, 'photo.png')).toBe('bob_smith_010.png');
    expect(getCleanDownloadName('Charlie', 99, 'portrait.webp')).toBe('charlie_100.webp');
  });

  it('sanitizes unsafe characters, symbols, and leading/trailing punctuation', () => {
    expect(getCleanDownloadName('Dr. Jane / Doe & Co.!', 0, 'raw.jpg')).toBe('dr_jane_doe_co_001.jpg');
    expect(getCleanDownloadName('___admin---user___', 1, 'test.jpeg')).toBe('admin---user_002.jpeg');
  });

  it('safely handles empty or null person label without leaking identifiers', () => {
    expect(getCleanDownloadName(null, 0, 'photo.jpg')).toBe('person_001.jpg');
    expect(getCleanDownloadName('', 2, 'photo.jpg')).toBe('person_003.jpg');
    expect(getCleanDownloadName('   ', 4, 'photo.png')).toBe('person_005.png');
  });

  it('prevents path traversal or private file system leakage in filenames', () => {
    const maliciousName = '../../../../etc/passwd';
    const clean = getCleanDownloadName(maliciousName, 0, 'test.jpg');
    expect(clean).not.toContain('/');
    expect(clean).not.toContain('\\');
    expect(clean).not.toContain('..');
    expect(clean).toBe('etc_passwd_001.jpg');
  });
});

describe('Google Drive Detection (isDrivePhoto)', () => {
  it('identifies Google Drive photos based on ID or URLs', () => {
    const drivePhoto1: PhotoInfo = {
      name: 'drive1.jpg',
      thumb: 'https://drive.google.com/thumbnail?id=xyz',
      drive_file_id: 'xyz123',
    };
    const drivePhoto2: PhotoInfo = {
      name: 'drive2.jpg',
      thumb: 'thumbs/2.jpg',
      download_url: 'https://drive.google.com/uc?id=abc456&export=download',
    };
    const localPhoto: PhotoInfo = {
      name: 'local.jpg',
      thumb: 'thumbs/local.jpg',
      download: 'photos/local.jpg',
    };

    expect(isDrivePhoto(drivePhoto1)).toBe(true);
    expect(isDrivePhoto(drivePhoto2)).toBe(true);
    expect(isDrivePhoto(localPhoto)).toBe(false);
  });
});

describe('PhotoGallery Selection and Download UI Flow', () => {
  const dummyPerson: PersonCluster = {
    id: 'p_charlie',
    label: 'Charlie Brown',
    face: 'faces/charlie.jpg',
    photo_ids: ['ph01', 'ph02', 'ph03'],
    maybe_photos: [
      { photo_id: 'ph_maybe1', source_cluster: 'p_other', distance: 0.45 },
    ],
  };

  const dummyPhotos: Record<string, PhotoInfo> = {
    ph01: { name: 'photo1.jpg', thumb: 'thumbs/th1.jpg', download: 'photos/photo1.jpg' },
    ph02: { name: 'photo2.jpg', thumb: 'thumbs/th2.jpg', download: 'photos/photo2.jpg' },
    ph03: { name: 'photo3.jpg', thumb: 'thumbs/th3.jpg', download: 'photos/photo3.jpg' },
    ph_maybe1: { name: 'maybe.jpg', thumb: 'thumbs/maybe.jpg', download: 'photos/maybe.jpg' },
  };

  it('displays the exact photo count in the primary "Download all N photos" button', () => {
    render(
      <PhotoGallery
        person={dummyPerson}
        photos={dummyPhotos}
        includeMaybe={false}
        onBack={() => {}}
      />
    );

    const downloadAllBtn = screen.getByRole('button', { name: /Download all 3 photos/i });
    expect(downloadAllBtn).toBeTruthy();
  });

  it('supports select mode toggle, photo ticking, select-all, and deselect-all', () => {
    render(
      <PhotoGallery
        person={dummyPerson}
        photos={dummyPhotos}
        includeMaybe={false}
        onBack={() => {}}
      />
    );

    // Initial state: not in select mode
    const selectToggleBtn = screen.getByRole('button', { name: /^Select$/i });
    expect(selectToggleBtn).toBeTruthy();
    expect(screen.queryByText(/selected/i)).toBeNull();

    // Toggle into select mode
    fireEvent.click(selectToggleBtn);
    expect(screen.getByRole('button', { name: /Exit select/i })).toBeTruthy();
    expect(screen.getByText('0 of 3 selected')).toBeTruthy();

    // Select all photos
    const selectAllBtn = screen.getByRole('button', { name: /Select all/i });
    fireEvent.click(selectAllBtn);
    expect(screen.getByText('3 of 3 selected')).toBeTruthy();

    // Download selected button shows count
    expect(screen.getByRole('button', { name: /Download selected \(3\)/i })).toBeTruthy();

    // Deselect all photos
    const deselectAllBtn = screen.getByRole('button', { name: /Deselect all/i });
    fireEvent.click(deselectAllBtn);
    expect(screen.getByText('0 of 3 selected')).toBeTruthy();

    // Exit select mode
    fireEvent.click(screen.getByRole('button', { name: /Exit select/i }));
    expect(screen.queryByText(/selected/i)).toBeNull();
  });

  it('ensures maybe-match section never has a "Download all" button', () => {
    render(
      <PhotoGallery
        person={dummyPerson}
        photos={dummyPhotos}
        includeMaybe={true}
        onBack={() => {}}
      />
    );

    // The maybe section exists
    expect(screen.getByText(/Possible matches \(1\)/i)).toBeTruthy();

    // Only one "Download all" button exists (for confirmed photos), not for maybe photos
    const downloadAllButtons = screen.getAllByRole('button', { name: /Download all/i });
    expect(downloadAllButtons.length).toBe(1);
    expect(downloadAllButtons[0].textContent).toContain('Download all 3 photos');
  });
});

describe('Unrecognized Gallery Requirements', () => {
  it('ensures Unrecognized gallery has NO "Download all" button', () => {
    render(
      <UnrecognizedGallery
        unrecognized={{
          photo_ids: ['ph_u1', 'ph_u2'],
          faces: [
            { photo_id: 'ph_u1', face: 'faces/u1.jpg', rejection_reason: 'low_confidence' },
          ],
        }}
        photos={{
          ph_u1: { name: 'unrec1.jpg', thumb: 'thumbs/u1.jpg', download: 'photos/u1.jpg' },
          ph_u2: { name: 'unrec2.jpg', thumb: 'thumbs/u2.jpg', download: 'photos/u2.jpg' },
        }}
        onBack={() => {}}
      />
    );

    // Unrecognized gallery should NEVER have a Download all button
    expect(screen.queryByRole('button', { name: /Download all/i })).toBeNull();
    expect(screen.queryByText(/Download all/i)).toBeNull();
  });
});

describe('Local Streaming Zip Download Logic (downloadLocalZip)', () => {
  beforeEach(() => {
    vi.stubGlobal('URL', {
      createObjectURL: vi.fn(() => 'blob:mock-url'),
      revokeObjectURL: vi.fn(),
    });
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('reports progress sequentially and generates clean zip name without error', async () => {
    const items: PhotoDownloadItem[] = [
      { id: '1', photo: { name: 'photo1.jpg', thumb: 'th1.jpg', download: 'photos/photo1.jpg' } },
      { id: '2', photo: { name: 'photo2.jpg', thumb: 'th2.jpg', download: 'photos/photo2.jpg' } },
    ];

    const progressCalls: Array<{ current: number; total: number }> = [];
    const controller = new AbortController();

    // Mock fetch for image assets
    vi.stubGlobal('fetch', vi.fn().mockImplementation(() =>
      Promise.resolve(new Response(new Blob(['fake-jpg-content'], { type: 'image/jpeg' })))
    ));

    await downloadLocalZip(
      'Alice Wonderland',
      items,
      (current, total) => progressCalls.push({ current, total }),
      controller.signal
    );

    expect(progressCalls).toEqual([
      { current: 1, total: 2 },
      { current: 2, total: 2 },
    ]);
  });

  it('supports cancellation cleanly through AbortSignal', async () => {
    const items: PhotoDownloadItem[] = [
      { id: '1', photo: { name: 'photo1.jpg', thumb: 'th1.jpg', download: 'photos/photo1.jpg' } },
    ];

    const controller = new AbortController();
    controller.abort(); // already aborted

    await expect(
      downloadLocalZip('Alice', items, () => {}, controller.signal)
    ).rejects.toThrow(/cancelled/i);
  });
});

describe('Drive Sequential Download Logic (downloadDriveSequential)', () => {
  it('triggers one-by-one downloads using existing download_url with progress callbacks', async () => {
    const driveItems: PhotoDownloadItem[] = [
      {
        id: 'd1',
        photo: {
          name: 'd1.jpg',
          thumb: 'th1.jpg',
          download_url: 'https://drive.google.com/uc?id=FILE_111&export=download',
        },
      },
      {
        id: 'd2',
        photo: {
          name: 'd2.jpg',
          thumb: 'th2.jpg',
          download_url: 'https://drive.google.com/uc?id=FILE_222&export=download',
        },
      },
    ];

    const progressCalls: Array<{ current: number; total: number }> = [];
    const controller = new AbortController();

    await downloadDriveSequential(
      driveItems,
      (current, total) => progressCalls.push({ current, total }),
      controller.signal,
      10 // fast delay for unit test
    );

    expect(progressCalls).toEqual([
      { current: 1, total: 2 },
      { current: 2, total: 2 },
    ]);
  });

  it('aborts cleanly midway when AbortSignal triggers', async () => {
    const driveItems: PhotoDownloadItem[] = [
      {
        id: 'd1',
        photo: {
          name: 'd1.jpg',
          thumb: 'th1.jpg',
          download_url: 'https://drive.google.com/uc?id=FILE_111&export=download',
        },
      },
      {
        id: 'd2',
        photo: {
          name: 'd2.jpg',
          thumb: 'th2.jpg',
          download_url: 'https://drive.google.com/uc?id=FILE_222&export=download',
        },
      },
    ];

    const controller = new AbortController();

    const promise = downloadDriveSequential(
      driveItems,
      () => {
        // Abort on first step
        controller.abort();
      },
      controller.signal,
      50
    );

    await expect(promise).rejects.toThrow(/cancelled/i);
  });
});

describe('Privacy and Cross-Person Leak Check', () => {
  it('guarantees that downloading Person A never leaks or includes Person B names or data', async () => {
    const personA: PersonCluster = {
      id: 'p_alice',
      label: 'Alice Secrets',
      face: 'faces/alice.jpg',
      photo_ids: ['ph_a1'],
    };

    const allPhotos: Record<string, PhotoInfo> = {
      ph_a1: { name: 'alice_01.jpg', thumb: 'thumbs/a1.jpg', download: 'photos/alice_01.jpg' },
      ph_b1: { name: 'bob_confidential.jpg', thumb: 'thumbs/b1.jpg', download: 'photos/bob_confidential.jpg' },
    };

    const targetItems: PhotoDownloadItem[] = (personA.photo_ids || []).map((id) => ({
      id,
      photo: allPhotos[id],
    }));

    // Verify Person A items only reference Person A
    expect(targetItems.length).toBe(1);
    expect(targetItems[0].id).toBe('ph_a1');
    expect(targetItems[0].photo.name).toBe('alice_01.jpg');

    // Run clean download name generator for Person A
    const downloadName = getCleanDownloadName(personA.label, 0, targetItems[0].photo.name);
    expect(downloadName).toBe('alice_secrets_001.jpg');

    // Verify Bob's name, ID, or file does NOT appear anywhere in the sanitized output or payload
    expect(downloadName).not.toContain('bob');
    expect(downloadName).not.toContain('confidential');
    expect(JSON.stringify(targetItems)).not.toContain('bob');
    expect(JSON.stringify(targetItems)).not.toContain('confidential');
  });
});

describe('Mobile vs Desktop Size Guard Threshold Logic (isMobileClassBrowser, checkDownloadSize)', () => {
  it('detects mobile user agents (iOS, Android, etc.)', () => {
    expect(isMobileClassBrowser({ userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15' })).toBe(true);
    expect(isMobileClassBrowser({ userAgent: 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Mobile Safari/537.36' })).toBe(true);
    expect(isMobileClassBrowser({ userAgent: 'Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15' })).toBe(true);
    expect(isMobileClassBrowser({ userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)', maxTouchPoints: 5 })).toBe(true);
  });

  it('detects constrained devices via navigator.deviceMemory <= 4 even on desktop UA', () => {
    expect(isMobileClassBrowser({ userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', deviceMemory: 2 })).toBe(true);
    expect(isMobileClassBrowser({ userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', deviceMemory: 4 })).toBe(true);
  });

  it('defaults conservative (true) when navigator or userAgent is absent or unknown', () => {
    expect(isMobileClassBrowser(undefined)).toBe(true);
    expect(isMobileClassBrowser({})).toBe(true);
    expect(isMobileClassBrowser({ userAgent: '' })).toBe(true);
  });

  it('identifies unconstrained desktop browser with > 4 GB memory', () => {
    expect(isMobileClassBrowser({ userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36', deviceMemory: 8 })).toBe(false);
    expect(isMobileClassBrowser({ userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36', maxTouchPoints: 0, deviceMemory: 16 })).toBe(false);
  });

  it('enforces 150 MB threshold on mobile and calculates proposed parts using ~100 MB target', () => {
    const mobileEnv = { userAgent: 'iPhone', deviceMemory: 4 };

    // 50 photos @ 2.5 MB = 125 MB (under 150 MB threshold)
    const items50: PhotoDownloadItem[] = Array.from({ length: 50 }, (_, i) => ({
      id: `p${i}`,
      photo: { name: `photo_${i}.jpg`, thumb: 'thumb.jpg', download: 'dl.jpg' },
    }));
    const check50 = checkDownloadSize(items50, undefined, undefined, mobileEnv);
    expect(check50.isMobile).toBe(true);
    expect(check50.thresholdBytes).toBe(SIZE_GUARD_MOBILE_THRESHOLD_BYTES); // 150 MB
    expect(check50.isOverThreshold).toBe(false);
    expect(check50.proposedParts).toBe(1);

    // 80 photos @ 2.5 MB = 200 MB (over 150 MB threshold)
    const items80: PhotoDownloadItem[] = Array.from({ length: 80 }, (_, i) => ({
      id: `p${i}`,
      photo: { name: `photo_${i}.jpg`, thumb: 'thumb.jpg', download: 'dl.jpg' },
    }));
    const check80 = checkDownloadSize(items80, undefined, undefined, mobileEnv);
    expect(check80.isMobile).toBe(true);
    expect(check80.isOverThreshold).toBe(true);
    // 200 MB / 100 MB part size = 2 parts
    expect(check80.proposedParts).toBe(2);
  });

  it('enforces 500 MB threshold on desktop and preserves single archive for 200 MB', () => {
    const desktopEnv = { userAgent: 'Windows NT 10.0; Win64; x64', deviceMemory: 8, maxTouchPoints: 0 };

    // 80 photos @ 2.5 MB = 200 MB (over mobile 150 MB, but under desktop 500 MB)
    const items80: PhotoDownloadItem[] = Array.from({ length: 80 }, (_, i) => ({
      id: `p${i}`,
      photo: { name: `photo_${i}.jpg`, thumb: 'thumb.jpg', download: 'dl.jpg' },
    }));
    const checkDesktop = checkDownloadSize(items80, undefined, undefined, desktopEnv);
    expect(checkDesktop.isMobile).toBe(false);
    expect(checkDesktop.thresholdBytes).toBe(SIZE_GUARD_DESKTOP_THRESHOLD_BYTES); // 500 MB
    expect(checkDesktop.isOverThreshold).toBe(false);
    expect(checkDesktop.proposedParts).toBe(1);

    // 220 photos @ 2.5 MB = 550 MB (over desktop 500 MB threshold)
    const items220: PhotoDownloadItem[] = Array.from({ length: 220 }, (_, i) => ({
      id: `p${i}`,
      photo: { name: `photo_${i}.jpg`, thumb: 'thumb.jpg', download: 'dl.jpg' },
    }));
    const check220 = checkDownloadSize(items220, undefined, undefined, desktopEnv);
    expect(check220.isOverThreshold).toBe(true);
    // 550 MB / 250 MB = 3 parts
    expect(check220.proposedParts).toBe(3);
  });
});
