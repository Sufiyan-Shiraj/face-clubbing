import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { App } from '../App';
import { PhotoGallery } from '../components/PhotoGallery';
import { Header } from '../components/Header';
import { Footer } from '../components/Footer';
import { ViewerConfig, PersonCluster, PhotoInfo, PeopleData } from '../types';

describe('PhotoGallery Component Requirements', () => {
  const dummyPerson: PersonCluster = {
    id: 'p001',
    label: 'Alice Wonderland',
    face: 'faces/f001.jpg',
    photo_ids: ['ph001', 'ph002'],
    maybe_photos: [
      { photo_id: 'ph003', source_cluster: 'p005', distance: 0.52 },
    ],
  };

  const dummyPhotos: Record<string, PhotoInfo> = {
    ph001: { name: 'photo1.jpg', thumb: 'thumbs/th1.jpg', download: 'photos/photo1.jpg' },
    ph002: { name: 'photo2.jpg', thumb: 'thumbs/th2.jpg', download: null },
    ph003: { name: 'photo3.jpg', thumb: 'thumbs/th3.jpg', download: 'photos/photo3.jpg' },
  };

  it('Requirement 6: does NOT show "Possible matches" when includeMaybe is false', () => {
    render(
      <PhotoGallery
        person={dummyPerson}
        photos={dummyPhotos}
        includeMaybe={false}
        onBack={() => {}}
      />
    );

    expect(screen.queryByText(/Possible matches/i)).toBeNull();
  });

  it('Requirement 6: shows separate labelled "Possible matches" section when includeMaybe is true', () => {
    render(
      <PhotoGallery
        person={dummyPerson}
        photos={dummyPhotos}
        includeMaybe={true}
        onBack={() => {}}
      />
    );

    const matchesHeader = screen.getByText(/Possible matches/i);
    expect(matchesHeader).toBeTruthy();
  });

  it('Requirement 7: shows download button when download is present and hides when null', () => {
    const { container } = render(
      <PhotoGallery
        person={dummyPerson}
        photos={dummyPhotos}
        includeMaybe={false}
        onBack={() => {}}
      />
    );

    // Download links with href
    const downloadLinks = container.querySelectorAll('a[download]');
    // ph001 has download link, ph002 has null download
    expect(downloadLinks.length).toBe(1);
    expect(downloadLinks[0].getAttribute('href')).toBe('photos/photo1.jpg');
  });

  it('Requirement 10: supports person with photos alias and absent faces/merged_from', () => {
    const aliasPerson: PersonCluster = {
      id: 'p002',
      face: 'faces/f002.jpg',
      photo_ids: [],
      photos: ['ph001'],
    };

    render(
      <PhotoGallery
        person={aliasPerson}
        photos={dummyPhotos}
        includeMaybe={false}
        onBack={() => {}}
      />
    );

    expect(screen.getByText(/Confirmed Photos \(1\)/i)).toBeTruthy();
  });
});

describe('Requirement 12: Config Swap Look Changes Without Code Change', () => {
  it('updates header and footer branding when config is swapped', () => {
    const configA: ViewerConfig = {
      title: 'Annual Gala 2026',
      subtitle: 'Official Event Portraits',
      accent: '#2563eb',
      font: 'Inter',
      footer: 'Published with PhotoSorter by Host Club',
      show_labels: true,
      include_maybe: false,
    };

    const { rerender } = render(
      <div>
        <Header
          config={configA}
          totalPeople={10}
          totalPhotos={50}
          searchQuery=""
          onSearchChange={() => {}}
          activeView="grid"
          onBackToGrid={() => {}}
        />
        <Footer config={configA} />
      </div>
    );

    expect(screen.getByText('Annual Gala 2026')).toBeTruthy();
    expect(screen.getByText('Official Event Portraits')).toBeTruthy();
    expect(screen.getByText('Published with PhotoSorter by Host Club')).toBeTruthy();

    // Swap to config B with completely different theme and branding
    const configB: ViewerConfig = {
      title: 'Neon Nights Festival',
      subtitle: 'Electronic Music Festival 2026',
      accent: '#ec4899',
      font: 'Outfit',
      footer: 'Hosted by CyberArts Collective',
      show_labels: false,
      include_maybe: true,
    };

    rerender(
      <div>
        <Header
          config={configB}
          totalPeople={10}
          totalPhotos={50}
          searchQuery=""
          onSearchChange={() => {}}
          activeView="grid"
          onBackToGrid={() => {}}
        />
        <Footer config={configB} />
      </div>
    );

    expect(screen.queryByText('Annual Gala 2026')).toBeNull();
    expect(screen.getByText('Neon Nights Festival')).toBeTruthy();
    expect(screen.getByText('Electronic Music Festival 2026')).toBeTruthy();
    expect(screen.getByText('Hosted by CyberArts Collective')).toBeTruthy();
  });

  const dummyPeopleData: PeopleData = {
    version: 2,
    generated_at: '2026-10-06T00:00:00Z',
    people: [
      { id: 'p001', face: 'faces/f001.jpg', photo_ids: ['ph001', 'ph002'] },
      { id: 'p002', face: 'faces/f002.jpg', photo_ids: ['ph003'] },
    ],
    photos: {
      ph001: { name: '1.jpg', thumb: 'thumbs/1.jpg' },
      ph002: { name: '2.jpg', thumb: 'thumbs/2.jpg' },
      ph003: { name: '3.jpg', thumb: 'thumbs/3.jpg' },
    },
    unrecognized: {
      photo_ids: [],
      faces: [],
    },
  };

  it('loads two different config.json files through App code path and verifies title, accent, footer, and toggle differ', async () => {
    const configA: ViewerConfig = {
      title: 'Annual Gala 2026',
      subtitle: 'Official Event Portraits',
      accent: '#2563eb',
      font: 'Inter',
      footer: 'Published with PhotoSorter by Host Club',
      show_labels: true,
      include_maybe: false,
      hide_single_photo_default: false,
    };

    const configB: ViewerConfig = {
      title: 'Neon Nights Festival',
      subtitle: 'Electronic Music Festival 2026',
      accent: '#ec4899',
      font: 'Outfit',
      footer: 'Hosted by CyberArts Collective',
      show_labels: false,
      include_maybe: true,
      hide_single_photo_default: true,
    };

    // 1. Render App with Config A
    let currentConfig = configA;
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('config.json')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(currentConfig),
        });
      }
      if (url.includes('people.json')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(dummyPeopleData),
        });
      }
      return Promise.reject(new Error(`Unhandled fetch ${url}`));
    });
    vi.stubGlobal('fetch', fetchMock);

    const { unmount } = render(<App />);

    // Wait for App to load and render
    await waitFor(() => {
      expect(screen.getByText('Annual Gala 2026')).toBeTruthy();
    });

    const titleA = document.title;
    const accentA = document.documentElement.style.getPropertyValue('--color-accent');
    const footerA = screen.getByText('Published with PhotoSorter by Host Club').textContent;
    const switchA = screen.getByRole('switch');
    const toggleStateA = switchA.getAttribute('aria-checked');

    expect(titleA).toBe('Annual Gala 2026');
    expect(accentA).toBe('#2563eb');
    expect(footerA).toBe('Published with PhotoSorter by Host Club');
    expect(toggleStateA).toBe('false');

    unmount();

    // 2. Render App with Config B
    currentConfig = configB;
    render(<App />);

    await waitFor(() => {
      expect(screen.getByText('Neon Nights Festival')).toBeTruthy();
    });

    const titleB = document.title;
    const accentB = document.documentElement.style.getPropertyValue('--color-accent');
    const footerB = screen.getByText('Hosted by CyberArts Collective').textContent;
    const switchB = screen.getByRole('switch');
    const toggleStateB = switchB.getAttribute('aria-checked');

    expect(titleB).toBe('Neon Nights Festival');
    expect(accentB).toBe('#ec4899');
    expect(footerB).toBe('Hosted by CyberArts Collective');
    expect(toggleStateB).toBe('true');

    // Assert that the rendered properties differ between Config A and Config B
    expect(titleA).not.toBe(titleB);
    expect(accentA).not.toBe(accentB);
    expect(footerA).not.toBe(footerB);
    expect(toggleStateA).not.toBe(toggleStateB);
  });
});

