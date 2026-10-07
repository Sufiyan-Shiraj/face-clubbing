import { describe, it, expect } from 'vitest';
import { PersonCluster } from '../types';

describe('Merge Selection Logic', () => {
  const mockPeople: PersonCluster[] = [
    {
      id: 'mock_person_1',
      label: null,
      face: 'faces/f_1.jpg',
      photo_ids: ['ph1', 'ph2'],
      photos: ['ph1', 'ph2'],
      photo_count: 2,
      faces: [
        { face_id: 'f_face_101', photo_id: 'ph1' },
        { face_id: 'f_face_102', photo_id: 'ph2' },
      ],
      anchor_face_ids: ['f_face_101', 'f_face_102'],
    },
    {
      id: 'mock_person_2',
      label: 'Alice',
      face: 'faces/f_2.jpg',
      photo_ids: ['ph3'],
      photos: ['ph3'],
      photo_count: 1,
      faces: [{ face_id: 'f_face_201', photo_id: 'ph3' }],
      anchor_face_ids: ['f_face_201'],
    },
    {
      id: 'mock_person_3',
      label: null,
      face: 'faces/f_3.jpg',
      photo_ids: ['ph4'],
      photos: ['ph4'],
      photo_count: 1,
      faces: [{ face_id: 'f_face_301', photo_id: 'ph4' }],
      anchor_face_ids: ['f_face_301'],
    },
  ];

  it('correctly toggles selection in a Set', () => {
    let selected = new Set<string>();

    // Toggle on mock_person_1
    selected = new Set(selected).add('mock_person_1');
    expect(selected.has('mock_person_1')).toBe(true);
    expect(selected.size).toBe(1);

    // Toggle on mock_person_2
    selected = new Set(selected).add('mock_person_2');
    expect(selected.has('mock_person_2')).toBe(true);
    expect(selected.size).toBe(2);

    // Toggle off mock_person_1
    const next = new Set(selected);
    next.delete('mock_person_1');
    selected = next;
    expect(selected.has('mock_person_1')).toBe(false);
    expect(selected.size).toBe(1);
  });

  it('determines when merge button is eligible (>= 2 people)', () => {
    const isEligible = (set: Set<string>) => set.size >= 2;

    expect(isEligible(new Set())).toBe(false);
    expect(isEligible(new Set(['mock_person_1']))).toBe(false);
    expect(isEligible(new Set(['mock_person_1', 'mock_person_2']))).toBe(true);
    expect(isEligible(new Set(['mock_person_1', 'mock_person_2', 'mock_person_3']))).toBe(true);
  });

  it('constructs merge edit payload with strictly face ID anchors, zero cluster IDs', () => {
    const selectedIds = new Set(['mock_person_1', 'mock_person_2']);
    const selectedPeople = mockPeople.filter((p) => selectedIds.has(p.id));

    // Extract anchors
    const anchors = selectedPeople.map((p) => p.anchor_face_ids);
    expect(anchors).toEqual([['f_face_101', 'f_face_102'], ['f_face_201']]);

    // Build the payload
    const payload = {
      op: 'merge',
      anchors: anchors,
    };

    const serialized = JSON.stringify(payload);
    // Working Rule: No cluster IDs (\bp\d{3}\b) in anything persisted or sent as edit anchor
    expect(serialized).not.toMatch(/\bp\d{3}\b/);
    expect(serialized).toContain('f_face_101');
    expect(serialized).toContain('f_face_201');
  });

  it('supports selecting all and clearing selection', () => {
    // Select all
    let selected = new Set(mockPeople.map((p) => p.id));
    expect(selected.size).toBe(3);

    // Clear
    selected = new Set();
    expect(selected.size).toBe(0);
  });
});
