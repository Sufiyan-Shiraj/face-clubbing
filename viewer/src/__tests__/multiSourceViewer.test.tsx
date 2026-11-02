import { describe, it, expect } from 'vitest';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { PhotoGallery } from '../components/PhotoGallery';
import { PeopleGrid } from '../components/PeopleGrid';
import { PhotoModal } from '../components/PhotoModal';
import { PersonCluster, PhotoInfo } from '../types';

describe('Phase V2-5: Multi-Source Viewer Features', () => {
  const dummyPerson: PersonCluster = {
    id: 'p_multitest',
    label: 'Jordan Smith',
    face: 'faces/f_jordan.jpg',
    photo_ids: ['ph_loc_1', 'ph_drv_2', 'ph_loc_3'],
    maybe_photos: [],
  };

  const dummyPhotos: Record<string, PhotoInfo> = {
    ph_loc_1: {
      name: 'IMG_1001.jpg',
      thumb: 'thumbs/ph_loc_1.jpg',
      download: null,
      source_id: 'src_camera',
      source_label: 'Camera SD',
      album: 'Day 1 Morning',
      folder_path: 'Day 1 Morning',
    },
    ph_drv_2: {
      name: 'GDRIVE_2002.jpg',
      thumb: 'thumbs/ph_drv_2.jpg',
      download: 'https://drive.google.com/uc?id=DriveId2002&export=download',
      drive_file_id: 'DriveId2002',
      drive_url: 'https://drive.google.com/file/d/DriveId2002/view',
      source_id: 'src_drive',
      source_label: 'Drive Cloud',
      album: 'Reception Evening',
      folder_path: 'Reception Evening',
    },
    ph_loc_3: {
      name: 'IMG_1003.jpg',
      thumb: 'thumbs/ph_loc_3.jpg',
      download: null,
      source_id: 'src_camera',
      source_label: 'Camera SD',
      album: 'Day 1 Morning',
      folder_path: 'Day 1 Morning',
    },
  };

  it('renders source and album badges on photo cards in PhotoGallery', () => {
    render(
      <PhotoGallery
        person={dummyPerson}
        photos={dummyPhotos}
        includeMaybe={false}
        onBack={() => {}}
      />
    );

    // Source badges
    const sourceBadge = screen.getByTestId('photo-source-badge-ph_loc_1');
    expect(sourceBadge).toBeDefined();
    expect(sourceBadge.textContent).toContain('Camera SD');

    const driveSourceBadge = screen.getByTestId('photo-source-badge-ph_drv_2');
    expect(driveSourceBadge.textContent).toContain('Drive Cloud');

    // Album badges
    const albumBadgeLoc = screen.getByTestId('photo-album-badge-ph_loc_1');
    expect(albumBadgeLoc.textContent).toContain('Day 1 Morning');

    const albumBadgeDrv = screen.getByTestId('photo-album-badge-ph_drv_2');
    expect(albumBadgeDrv.textContent).toContain('Reception Evening');
  });

  it('filters gallery photos by album using gallery-album-filter-select', () => {
    render(
      <PhotoGallery
        person={dummyPerson}
        photos={dummyPhotos}
        includeMaybe={false}
        onBack={() => {}}
      />
    );

    const albumSelect = screen.getByTestId('gallery-album-filter-select') as HTMLSelectElement;
    expect(albumSelect).toBeDefined();
    expect(albumSelect.value).toBe('all');

    // Filter to Reception Evening
    fireEvent.change(albumSelect, { target: { value: 'Reception Evening' } });
    expect(albumSelect.value).toBe('Reception Evening');

    // Only ph_drv_2 should be visible
    expect(screen.queryByTestId('photo-album-badge-ph_drv_2')).not.toBeNull();
    expect(screen.queryByTestId('photo-album-badge-ph_loc_1')).toBeNull();
    expect(screen.queryByTestId('photo-album-badge-ph_loc_3')).toBeNull();

    // Primary download button text updates to reflect 1 photo
    expect(screen.getByText('Download 1 photo')).toBeDefined();
  });

  it('renders album badge in PhotoModal header', () => {
    render(
      <PhotoModal
        photo={dummyPhotos['ph_drv_2']}
        photoId="ph_drv_2"
        hasPrev={false}
        hasNext={false}
        onPrev={() => {}}
        onNext={() => {}}
        onClose={() => {}}
        personLabel="Jordan Smith"
      />
    );

    const modalAlbumBadge = screen.getByTestId('modal-photo-album-badge');
    expect(modalAlbumBadge).toBeDefined();
    expect(modalAlbumBadge.textContent).toContain('Reception Evening');

    const modalSourceBadge = screen.getByTestId('modal-photo-source-badge');
    expect(modalSourceBadge.textContent).toContain('Drive Cloud');
  });

  it('supports album filtering in PeopleGrid toolbar', () => {
    const personA: PersonCluster = {
      id: 'p_01',
      label: 'Alice',
      face: 'faces/p_01.jpg',
      photo_ids: ['ph_loc_1'],
    };
    const personB: PersonCluster = {
      id: 'p_02',
      label: 'Bob',
      face: 'faces/p_02.jpg',
      photo_ids: ['ph_drv_2'],
    };

    render(
      <PeopleGrid
        people={[personA, personB]}
        unrecognized={{ photo_ids: [], faces: [] }}
        photos={dummyPhotos}
        searchQuery=""
        onSelectPerson={() => {}}
        onSelectUnrecognized={() => {}}
      />
    );

    const albumSelect = screen.getByTestId('album-filter-select') as HTMLSelectElement;
    expect(albumSelect).toBeDefined();

    // Select Day 1 Morning -> only Alice has photo in Day 1 Morning
    fireEvent.change(albumSelect, { target: { value: 'Day 1 Morning' } });
    expect(screen.getByText('Alice')).toBeDefined();
    expect(screen.queryByText('Bob')).toBeNull();

    // Select Reception Evening -> only Bob has photo in Reception Evening
    fireEvent.change(albumSelect, { target: { value: 'Reception Evening' } });
    expect(screen.getByText('Bob')).toBeDefined();
    expect(screen.queryByText('Alice')).toBeNull();
  });

  it('virtualizes large photo galleries with windowed batch rendering', () => {
    // Generate 120 synthetic photos
    const largePhotos: Record<string, PhotoInfo> = {};
    const largePhotoIds: string[] = [];
    for (let i = 0; i < 120; i++) {
      const pid = `ph_bulk_${i}`;
      largePhotoIds.push(pid);
      largePhotos[pid] = {
        name: `Photo_${i}.jpg`,
        thumb: `thumbs/${pid}.jpg`,
        download: null,
        album: i < 60 ? 'BatchA' : 'BatchB',
      };
    }

    const largePerson: PersonCluster = {
      id: 'p_bulk',
      label: 'Bulk VIP',
      face: 'faces/p_bulk.jpg',
      photo_ids: largePhotoIds,
    };

    render(
      <PhotoGallery
        person={largePerson}
        photos={largePhotos}
        includeMaybe={false}
        onBack={() => {}}
      />
    );

    // Initial batch is 60 items
    const loadMoreBtn = screen.getByTestId('btn-load-more-photos');
    expect(loadMoreBtn).toBeDefined();
    expect(loadMoreBtn.textContent).toContain('Load more photos (60 of 120)');

    // Clicking load more increments batch by 48 -> 108
    fireEvent.click(loadMoreBtn);
    expect(loadMoreBtn.textContent).toContain('Load more photos (108 of 120)');

    // Clicking load more again completes all 120 photos, removing the button
    fireEvent.click(loadMoreBtn);
    expect(screen.queryByTestId('btn-load-more-photos')).toBeNull();
  });
});
