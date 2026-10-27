import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ReviewPeopleScreen } from '../components/ReviewPeopleScreen';
import { PeopleGrid } from '../components/PeopleGrid';
import { PersonModal } from '../components/PersonModal';
import { ImageViewerModal } from '../components/ImageViewerModal';
import { UnrecognizedTriage } from '../components/UnrecognizedTriage';
import { PersonCluster, PhotoInfo, UnrecognizedData, SuggestionsData } from '../types';

const mockPhotosMultiSource: Record<string, PhotoInfo> = {
  p1: {
    photo_id: 'p1',
    file_name: 'p1.jpg',
    source_id: 'src_01',
    source_label: 'Main Camera',
    thumb: '/thumbs/p1.jpg',
  },
  p2: {
    photo_id: 'p2',
    file_name: 'p2.jpg',
    source_id: 'src_02',
    source_label: 'Drive Cloud',
    thumb: '/thumbs/p2.jpg',
  },
  p3: {
    photo_id: 'p3',
    file_name: 'p3.jpg',
    source_id: 'src_01',
    source_label: 'Main Camera',
    thumb: '/thumbs/p3.jpg',
  },
};

const mockPeople: PersonCluster[] = [
  {
    id: 'person_1',
    label: 'Alice',
    face: '/faces/person_1.jpg',
    photo_ids: ['p1'],
    photos: ['p1'],
    photo_count: 1,
    faces: [{ face_id: 'f_p1_0', photo_id: 'p1' }],
    anchor_face_ids: ['f_p1_0'],
  },
  {
    id: 'person_2',
    label: 'Bob',
    face: '/faces/person_2.jpg',
    photo_ids: ['p2'],
    photos: ['p2'],
    photo_count: 1,
    faces: [{ face_id: 'f_p2_0', photo_id: 'p2' }],
    anchor_face_ids: ['f_p2_0'],
  },
  {
    id: 'person_3',
    label: 'Charlie',
    face: '/faces/person_3.jpg',
    photo_ids: ['p1', 'p2'],
    photos: ['p1', 'p2'],
    photo_count: 2,
    faces: [{ face_id: 'f_p1_1', photo_id: 'p1' }, { face_id: 'f_p2_1', photo_id: 'p2' }],
    anchor_face_ids: ['f_p1_1'],
  },
];

const mockUnrecognized: UnrecognizedData = {
  total_unrecognized_photos: 1,
  no_face_photos: ['p3'],
  faces: [
    {
      face_id: 'f_unrec_1',
      photo_id: 'p2',
      face: '/faces/unrec_1.jpg',
      rejection_reason: 'unattached',
    },
  ],
};

const mockSuggestions: SuggestionsData = {
  maybe_groups_count: 0,
  maybe_groups: [],
  possibly_the_same_count: 0,
  possibly_the_same: [],
  ambiguous_faces_count: 0,
  ambiguous_faces: [],
};

describe('Source Badging & Filtering in Gallery/Review Screen (Phase V2-2 Piece 3)', () => {
  it('renders source filter dropdown in ReviewPeopleScreen when multiple sources are present', () => {
    render(
      <ReviewPeopleScreen
        people={mockPeople}
        photos={mockPhotosMultiSource}
        unrecognized={mockUnrecognized}
        suggestions={mockSuggestions}
        selectedIds={new Set()}
        onToggleSelect={vi.fn()}
        onSelectAll={vi.fn()}
        onClearSelection={vi.fn()}
        onMergeSelected={vi.fn()}
        onAcceptSuggestion={vi.fn()}
        onRejectSuggestion={vi.fn()}
        rejectedPairs={new Set()}
        onAssignFace={vi.fn()}
        onRenamePerson={vi.fn()}
        onHidePerson={vi.fn()}
        onRemoveFace={vi.fn()}
        onRemovePhoto={vi.fn()}
      />
    );

    const select = screen.getByTestId('source-filter-select') as HTMLSelectElement;
    expect(select).toBeTruthy();
    expect(select.value).toBe('all');

    // Should contain options for All Sources and the two sources
    expect(screen.getByText(/All Sources \(3\)/i)).toBeTruthy();
    expect(screen.getByText(/Main Camera \(2\)/i)).toBeTruthy();
    expect(screen.getByText(/Drive Cloud \(1\)/i)).toBeTruthy();
  });

  it('filters people grid when a specific source is selected in source-filter-select', () => {
    render(
      <ReviewPeopleScreen
        people={mockPeople}
        photos={mockPhotosMultiSource}
        unrecognized={mockUnrecognized}
        suggestions={mockSuggestions}
        selectedIds={new Set()}
        onToggleSelect={vi.fn()}
        onSelectAll={vi.fn()}
        onClearSelection={vi.fn()}
        onMergeSelected={vi.fn()}
        onAcceptSuggestion={vi.fn()}
        onRejectSuggestion={vi.fn()}
        rejectedPairs={new Set()}
        onAssignFace={vi.fn()}
        onRenamePerson={vi.fn()}
        onHidePerson={vi.fn()}
        onRemoveFace={vi.fn()}
        onRemovePhoto={vi.fn()}
      />
    );

    // Initially all 3 people are shown
    expect(screen.getByText('Alice')).toBeTruthy();
    expect(screen.getByText('Bob')).toBeTruthy();
    expect(screen.getByText('Charlie')).toBeTruthy();

    // Select Drive Cloud
    const select = screen.getByTestId('source-filter-select') as HTMLSelectElement;
    fireEvent.change(select, { target: { value: 'src_02' } });

    // Now only Bob and Charlie should be shown (they appear in p2 which is src_02)
    expect(screen.queryByText('Alice')).toBeNull();
    expect(screen.getByText('Bob')).toBeTruthy();
    expect(screen.getByText('Charlie')).toBeTruthy();
  });

  it('does not render source filter select when all photos belong to a single source', () => {
    const singleSourcePhotos: Record<string, PhotoInfo> = {
      p1: { photo_id: 'p1', file_name: 'p1.jpg', source_id: 'src_01', source_label: 'Single Source' },
      p2: { photo_id: 'p2', file_name: 'p2.jpg', source_id: 'src_01', source_label: 'Single Source' },
    };

    render(
      <ReviewPeopleScreen
        people={mockPeople.slice(0, 2)}
        photos={singleSourcePhotos}
        unrecognized={mockUnrecognized}
        suggestions={mockSuggestions}
        selectedIds={new Set()}
        onToggleSelect={vi.fn()}
        onSelectAll={vi.fn()}
        onClearSelection={vi.fn()}
        onMergeSelected={vi.fn()}
        onAcceptSuggestion={vi.fn()}
        onRejectSuggestion={vi.fn()}
        rejectedPairs={new Set()}
        onAssignFace={vi.fn()}
        onRenamePerson={vi.fn()}
        onHidePerson={vi.fn()}
        onRemoveFace={vi.fn()}
        onRemovePhoto={vi.fn()}
      />
    );

    expect(screen.queryByTestId('source-filter-select')).toBeNull();
  });

  it('renders source badge chips on PeopleGrid cards', () => {
    render(
      <PeopleGrid
        people={mockPeople}
        photos={mockPhotosMultiSource}
        selectedIds={new Set()}
        onToggleSelect={vi.fn()}
        onSelectAll={vi.fn()}
        onClearSelection={vi.fn()}
        onMergeSelected={vi.fn()}
        onSelectPerson={vi.fn()}
      />
    );

    // Alice card should have "Main Camera" badge
    const aliceSources = screen.getByTestId('person-sources-person_1');
    expect(aliceSources.textContent).toContain('Main Camera');

    // Bob card should have "Drive Cloud" badge
    const bobSources = screen.getByTestId('person-sources-person_2');
    expect(bobSources.textContent).toContain('Drive Cloud');

    // Charlie card should have both "Main Camera" and "Drive Cloud"
    const charlieSources = screen.getByTestId('person-sources-person_3');
    expect(charlieSources.textContent).toContain('Main Camera');
    expect(charlieSources.textContent).toContain('Drive Cloud');
  });

  it('renders source badge on photo cards in PersonModal', () => {
    render(
      <PersonModal
        person={mockPeople[2]}
        photos={mockPhotosMultiSource}
        onClose={vi.fn()}
        onRename={vi.fn()}
        onHide={vi.fn()}
        onRemoveFace={vi.fn()}
        onRemovePhoto={vi.fn()}
        onOpenPhotoViewer={vi.fn()}
      />
    );

    const badgeP1 = screen.getByTestId('photo-source-badge-p1');
    expect(badgeP1.textContent).toContain('Main Camera');

    const badgeP2 = screen.getByTestId('photo-source-badge-p2');
    expect(badgeP2.textContent).toContain('Drive Cloud');
  });

  it('renders source badge in ImageViewerModal top navigation bar', () => {
    render(
      <ImageViewerModal
        photoId="p2"
        photos={mockPhotosMultiSource}
        onClose={vi.fn()}
        onNavigatePhoto={vi.fn()}
      />
    );

    const sourceBadge = screen.getByTestId('photo-source-badge');
    expect(sourceBadge.textContent).toContain('Drive Cloud');
  });

  it('renders source badges in UnrecognizedTriage for face cards and no-face photos', () => {
    render(
      <UnrecognizedTriage
        unrecognized={mockUnrecognized}
        ambiguousMap={{}}
        people={mockPeople}
        photos={mockPhotosMultiSource}
        onAssignFace={vi.fn()}
        onOpenPhotoViewer={vi.fn()}
      />
    );

    // Face card source badge for p2 (Drive Cloud)
    const faceBadge = screen.getByTestId('unrec-source-badge-p2');
    expect(faceBadge.textContent).toContain('Drive Cloud');

    // No-face photo card badge for p3 (Main Camera)
    const noFaceBadge = screen.getByTestId('unrec-no-face-source-badge-p3');
    expect(noFaceBadge.textContent).toContain('Main Camera');
  });
});
