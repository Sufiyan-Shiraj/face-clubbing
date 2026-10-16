import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { UnrecognizedTriage } from '../components/UnrecognizedTriage';
import { PersonCluster, PhotoInfo, UnrecognizedData } from '../types';

describe('Revamped Unrecognized Triage & Image Viewer', () => {
  const mockPeople: PersonCluster[] = [
    {
      id: 'person_alice',
      label: 'Alice Smith',
      face: 'faces/person_alice.jpg',
      photo_ids: ['ph1', 'ph2'],
      photos: ['ph1', 'ph2'],
      photo_count: 2,
      faces: [
        { face_id: 'f101', photo_id: 'ph1' },
        { face_id: 'f102', photo_id: 'ph2' },
      ],
      anchor_face_ids: ['f101'],
    },
    {
      id: 'person_bob',
      label: 'Bob Jones',
      face: 'faces/person_bob.jpg',
      photo_ids: ['ph3'],
      photos: ['ph3'],
      photo_count: 1,
      faces: [{ face_id: 'f201', photo_id: 'ph3' }],
      anchor_face_ids: ['f201'],
    },
  ];

  const mockPhotos: Record<string, PhotoInfo> = {
    ph1: { photo_id: 'ph1', file_name: 'group_photo.jpg', width: 1920, height: 1080 },
    ph2: { photo_id: 'ph2', file_name: 'portrait.jpg', width: 800, height: 1200 },
    ph3: { photo_id: 'ph3', file_name: 'party.jpg', width: 2048, height: 1536 },
    ph_unrec_1: { photo_id: 'ph_unrec_1', file_name: 'conference.jpg', width: 1920, height: 1080 },
    ph_unrec_2: { photo_id: 'ph_unrec_2', file_name: 'stage.jpg', width: 1920, height: 1080 },
  };

  const mockUnrecognized: UnrecognizedData = {
    total_unrecognized_photos: 2,
    no_face_photos: ['ph_noface_1'],
    faces: [
      {
        face_id: 'f_unrec_1',
        photo_id: 'ph_unrec_1',
        face: 'faces/f_unrec_1.jpg',
        rejection_reason: 'ambiguous',
        det_score: 0.88,
      },
      {
        face_id: 'f_unrec_2',
        photo_id: 'ph_unrec_2',
        face: 'faces/f_unrec_2.jpg',
        rejection_reason: 'unattached_profile',
        det_score: 0.75,
      },
    ],
  };

  it('renders unrecognized faces grid with triage controls', () => {
    const onAssignFace = vi.fn();
    const onOpenPhotoViewer = vi.fn();

    render(
      <UnrecognizedTriage
        unrecognized={mockUnrecognized}
        ambiguousMap={{}}
        people={mockPeople}
        photos={mockPhotos}
        onAssignFace={onAssignFace}
        onOpenPhotoViewer={onOpenPhotoViewer}
      />
    );

    expect(screen.getByTestId('unrec-faces-grid')).toBeTruthy();
    expect(screen.getByTestId('unrec-face-card-f_unrec_1')).toBeTruthy();
    expect(screen.getByTestId('unrec-face-card-f_unrec_2')).toBeTruthy();
  });

  it('displays the target person preview when a person is selected in batch picker so user knows if correct to merge', async () => {
    render(
      <UnrecognizedTriage
        unrecognized={mockUnrecognized}
        ambiguousMap={{}}
        people={mockPeople}
        photos={mockPhotos}
        onAssignFace={vi.fn()}
        onOpenPhotoViewer={vi.fn()}
      />
    );

    const select = document.getElementById('batch-target-person-select') as HTMLSelectElement;
    expect(select).toBeTruthy();

    // Select Alice
    fireEvent.change(select, { target: { value: 'person_alice' } });

    // Verify preview card appears with Alice Smith
    const previewCard = document.getElementById('batch-target-person-preview');
    expect(previewCard).toBeTruthy();
    expect(previewCard?.textContent).toContain('Alice Smith');
    expect(previewCard?.textContent).toContain('2 photos');
  });

  it('allows multi-selecting faces and clicking one button to add them all', async () => {
    const onAssignMultipleFaces = vi.fn().mockResolvedValue(undefined);

    render(
      <UnrecognizedTriage
        unrecognized={mockUnrecognized}
        ambiguousMap={{}}
        people={mockPeople}
        photos={mockPhotos}
        onAssignFace={vi.fn()}
        onAssignMultipleFaces={onAssignMultipleFaces}
        onOpenPhotoViewer={vi.fn()}
      />
    );

    // 1. Select Bob Jones as target
    const targetSelect = document.getElementById('batch-target-person-select') as HTMLSelectElement;
    fireEvent.change(targetSelect, { target: { value: 'person_bob' } });

    // 2. Select both faces using Select All Filtered button
    const selectAllBtn = screen.getByText(/Select All Filtered/i);
    fireEvent.click(selectAllBtn);

    const selectedBadge = document.getElementById('batch-selected-count');
    expect(selectedBadge?.textContent).toContain('2 items selected');

    // 3. Click the one button to add them all
    const batchAssignBtn = screen.getByTestId('batch-assign-btn');
    expect(batchAssignBtn.textContent).toContain('Add 2 Selected to Bob Jones');
    fireEvent.click(batchAssignBtn);

    expect(onAssignMultipleFaces).toHaveBeenCalledTimes(1);
    expect(onAssignMultipleFaces).toHaveBeenCalledWith(['f_unrec_1', 'f_unrec_2'], 'person_bob');
  });

  it('renders individual card target preview when a person is chosen in card dropdown', () => {
    render(
      <UnrecognizedTriage
        unrecognized={mockUnrecognized}
        ambiguousMap={{}}
        people={mockPeople}
        photos={mockPhotos}
        onAssignFace={vi.fn()}
        onOpenPhotoViewer={vi.fn()}
      />
    );

    const cardSelects = screen.getAllByTestId('assign-target-select');
    fireEvent.change(cardSelects[0], { target: { value: 'person_alice' } });

    // Verify card preview exists
    const cardPreview = document.getElementById('selected-person-preview-f_unrec_1');
    expect(cardPreview).toBeTruthy();
    expect(cardPreview?.textContent).toContain('Alice Smith');
    expect(cardPreview?.textContent).toContain('Compare');
  });
});
