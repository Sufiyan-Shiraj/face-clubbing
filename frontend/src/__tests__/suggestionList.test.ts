import { describe, it, expect, vi } from 'vitest';
import { RankedPairSuggestion } from '../types';

describe('Suggestion List & Review Logic', () => {
  const mockSuggestions: RankedPairSuggestion[] = [
    {
      person_a_id: 'mock_person_1',
      person_b_id: 'mock_person_2',
      person_a_anchors: ['f_101'],
      person_b_anchors: ['f_201'],
      distance: 0.52,
      confidence: 'medium',
      reason: 'centroid_band',
      person_a_photos: 5,
      person_b_photos: 4,
    },
    {
      person_a_id: 'mock_person_3',
      person_b_id: 'mock_person_4',
      person_a_anchors: ['f_301'],
      person_b_anchors: ['f_401'],
      distance: 0.68,
      confidence: 'low',
      reason: 'single_photo_extended',
      person_a_photos: 1,
      person_b_photos: 3,
    },
    {
      person_a_id: 'mock_person_5',
      person_b_id: 'mock_person_6',
      person_a_anchors: ['f_501'],
      person_b_anchors: ['f_601'],
      distance: 0.54,
      confidence: 'medium',
      reason: 'centroid_band',
      person_a_photos: 2,
      person_b_photos: 2,
    },
  ];

  const getPairKey = (idA: string, idB: string) => [idA, idB].sort().join(':::');

  it('filters out session-rejected suggestion pairs', () => {
    const rejectedPairs = new Set<string>();

    // Initially all 3 active
    let active = mockSuggestions.filter(
      (s) => !rejectedPairs.has(getPairKey(s.person_a_id, s.person_b_id))
    );
    expect(active.length).toBe(3);

    // Reject mock_person_1 <-> mock_person_2
    rejectedPairs.add(getPairKey('mock_person_1', 'mock_person_2'));
    active = mockSuggestions.filter(
      (s) => !rejectedPairs.has(getPairKey(s.person_a_id, s.person_b_id))
    );
    expect(active.length).toBe(2);
    expect(active.some((s) => s.person_a_id === 'mock_person_1' && s.person_b_id === 'mock_person_2')).toBe(false);

    // Rejection key is symmetric
    expect(rejectedPairs.has(getPairKey('mock_person_2', 'mock_person_1'))).toBe(true);
  });

  it('filters suggestions by confidence level', () => {
    const mediumOnly = mockSuggestions.filter((s) => s.confidence === 'medium');
    expect(mediumOnly.length).toBe(2);

    const lowOnly = mockSuggestions.filter((s) => s.confidence === 'low');
    expect(lowOnly.length).toBe(1);
    expect(lowOnly[0].person_a_id).toBe('mock_person_3');
  });

  it('invokes accept callback with correct person IDs', () => {
    const mockAccept = vi.fn();
    const handleAccept = (sug: RankedPairSuggestion) => {
      mockAccept(sug.person_a_id, sug.person_b_id);
    };

    handleAccept(mockSuggestions[0]);
    expect(mockAccept).toHaveBeenCalledWith('mock_person_1', 'mock_person_2');
  });

  it('invokes reject callback and updates rejectedPairs set', () => {
    const rejectedPairs = new Set<string>();
    const handleReject = (idA: string, idB: string) => {
      rejectedPairs.add(getPairKey(idA, idB));
    };

    handleReject('mock_person_3', 'mock_person_4');
    expect(rejectedPairs.has('mock_person_3:::mock_person_4')).toBe(true);
  });
});
