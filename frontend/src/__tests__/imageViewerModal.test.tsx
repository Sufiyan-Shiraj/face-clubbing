import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ImageViewerModal } from '../components/ImageViewerModal';
import { PhotoInfo, PersonCluster, UnrecognizedData } from '../types';

describe('ImageViewerModal - Unknown Face Boxes & Person Changing', () => {
  const mockPhotos: Record<string, PhotoInfo> = {
    p1: {
      photo_id: 'p1',
      file_name: 'test_photo_1.jpg',
      width: 1000,
      height: 800,
      thumb: '/thumbs/p1.jpg',
      faces: [
        { face_id: 'f_known', photo_id: 'p1', bbox: [100, 100, 200, 200], det_score: 0.95 },
        { face_id: 'f_unrec', photo_id: 'p1', bbox: [400, 300, 500, 420], det_score: 0.88 },
      ],
    },
  };

  const mockPeople: PersonCluster[] = [
    {
      id: 'person_001',
      label: 'Alice',
      face: '/faces/f_known.jpg',
      photo_ids: ['p1'],
      photos: ['p1'],
      photo_count: 1,
      faces: [
        { face_id: 'f_known', photo_id: 'p1', bbox: [100, 100, 200, 200], det_score: 0.95 },
      ],
      anchor_face_ids: ['f_known'],
    },
    {
      id: 'person_002',
      label: 'Bob',
      face: '/faces/bob.jpg',
      photo_ids: ['p2'],
      photos: ['p2'],
      photo_count: 3,
      faces: [],
      anchor_face_ids: ['f_bob'],
    },
  ];

  const mockUnrecognized: UnrecognizedData = {
    total_unrecognized_photos: 1,
    no_face_photos: [],
    faces: [
      {
        face_id: 'f_unrec',
        photo_id: 'p1',
        face: '/faces/f_unrec.jpg',
        rejection_reason: 'unattached_small',
        det_score: 0.88,
        bbox: [400, 300, 500, 420],
      },
    ],
  };

  it('renders bounding boxes for BOTH known and unknown faces', () => {
    render(
      <ImageViewerModal
        photoId="p1"
        photos={mockPhotos}
        people={mockPeople}
        unrecognized={mockUnrecognized}
        onClose={vi.fn()}
        onNavigatePhoto={vi.fn()}
      />
    );

    // Check title/tags rendered on overlay
    expect(screen.getByText('Alice')).toBeDefined();
    expect(screen.getByText('Unknown (unattached_small)')).toBeDefined();

    // Check the face count badge
    expect(screen.getByText('2 detected faces')).toBeDefined();
  });

  it('allows changing an unknown face to an existing person directly from Inspect Faces drawer', async () => {
    const onAssignFace = vi.fn();
    render(
      <ImageViewerModal
        photoId="p1"
        photos={mockPhotos}
        people={mockPeople}
        unrecognized={mockUnrecognized}
        onClose={vi.fn()}
        onNavigatePhoto={vi.fn()}
        onAssignFace={onAssignFace}
      />
    );

    // Open faces drawer
    const inspectBtn = screen.getByRole('button', { name: /Inspect Faces/i });
    fireEvent.click(inspectBtn);

    // Verify both faces are in drawer
    expect(screen.getByText('Faces in this Photo (2)')).toBeDefined();

    // Find the select dropdown for assigning f_unrec
    const selects = screen.getAllByRole('combobox');
    expect(selects.length).toBeGreaterThanOrEqual(2);

    // Select Bob (person_002) for the unrecognized face
    const unrecSelect = selects[1];
    fireEvent.change(unrecSelect, { target: { value: 'person_002' } });

    // Click assign button for f_unrec
    const assignButtons = screen.getAllByRole('button', { name: /Assign/i });
    fireEvent.click(assignButtons[1]);

    expect(onAssignFace).toHaveBeenCalledWith('f_unrec', 'person_002');
  });

  it('allows creating a new person for an unknown face', async () => {
    const onAssignFace = vi.fn();
    render(
      <ImageViewerModal
        photoId="p1"
        photos={mockPhotos}
        people={mockPeople}
        unrecognized={mockUnrecognized}
        onClose={vi.fn()}
        onNavigatePhoto={vi.fn()}
        onAssignFace={onAssignFace}
      />
    );

    // Open faces drawer
    fireEvent.click(screen.getByRole('button', { name: /Inspect Faces/i }));

    // Click "+ New" button for unknown face
    const newButtons = screen.getAllByTitle('Create a new person from this face');
    expect(newButtons.length).toBeGreaterThanOrEqual(1);
    fireEvent.click(newButtons[0]);

    expect(onAssignFace).toHaveBeenCalledWith('f_known', null);
  });

  it('allows detaching a known face to unknown', async () => {
    const onRemoveFace = vi.fn();
    render(
      <ImageViewerModal
        photoId="p1"
        photos={mockPhotos}
        people={mockPeople}
        unrecognized={mockUnrecognized}
        onClose={vi.fn()}
        onNavigatePhoto={vi.fn()}
        onRemoveFace={onRemoveFace}
      />
    );

    // Open faces drawer
    fireEvent.click(screen.getByRole('button', { name: /Inspect Faces/i }));

    // Click Detach button for the known face
    const detachBtn = screen.getByTitle('Detach face and move to unknown');
    fireEvent.click(detachBtn);

    expect(onRemoveFace).toHaveBeenCalledWith('person_001', 'f_known');
  });
});
