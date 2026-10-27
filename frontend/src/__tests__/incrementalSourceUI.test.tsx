import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AddSourceModal } from '../components/AddSourceModal';
import { WhatChangedModal } from '../components/WhatChangedModal';
import { ReviewPeopleScreen } from '../components/ReviewPeopleScreen';
import { api } from '../api/client';
import { WhatChangedResponse, PersonCluster, PhotoInfo, UnrecognizedData, SuggestionsData } from '../types';

vi.mock('../api/client', () => ({
  api: {
    addProjectSource: vi.fn(),
    getWhatChanged: vi.fn(),
    undoLastSnapshot: vi.fn(),
    getProjectSnapshots: vi.fn(),
    selectFolderDialog: vi.fn(),
    selectFileDialog: vi.fn(),
  },
  apiClient: {
    addProjectSource: vi.fn(),
    getWhatChanged: vi.fn(),
    undoLastSnapshot: vi.fn(),
    getProjectSnapshots: vi.fn(),
  },
}));

const mockDiff: WhatChangedResponse = {
  generated_at: '2026-10-27T10:00:00Z',
  new_photos_count: 5,
  new_photo_ids: ['ph_new_1', 'ph_new_2', 'ph_new_3', 'ph_new_4', 'ph_new_5'],
  skipped_duplicate_photos: 2,
  new_people_count: 1,
  new_people_ids: ['person_bob'],
  joined_existing_count: 3,
  joined_existing: {
    person_alice: {
      person_name: 'Alice',
      new_faces_count: 3,
      new_photo_ids: ['ph_new_1', 'ph_new_2'],
    },
  },
  existing_people_membership_changed: 0,
  new_unrecognized_faces_count: 1,
  new_unrecognized_photos_count: 1,
};

const mockPhotos: Record<string, PhotoInfo> = {
  p1: { photo_id: 'p1', file_name: 'p1.jpg', source_id: 'src_01', source_label: 'Folder A' },
};

const mockPeople: PersonCluster[] = [
  {
    id: 'person_alice',
    label: 'Alice',
    face: '/faces/person_alice.jpg',
    photo_ids: ['p1'],
    photos: ['p1'],
    photo_count: 1,
    faces: [{ face_id: 'f_p1_0', photo_id: 'p1' }],
    anchor_face_ids: ['f_p1_0'],
  },
];

const mockUnrecognized: UnrecognizedData = {
  total_unrecognized_photos: 0,
  no_face_photos: [],
  faces: [],
};

const mockSuggestions: SuggestionsData = {
  maybe_groups_count: 0,
  maybe_groups: [],
  possibly_the_same_count: 0,
  possibly_the_same: [],
  ambiguous_faces_count: 0,
  ambiguous_faces: [],
};

describe('Incremental Source Ingestion & What Changed UI (Phase V2-3)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('AddSourceModal', () => {
    it('renders source type options and defaults to local folder with frozen mode checked', () => {
      render(<AddSourceModal onClose={vi.fn()} onSourceAdded={vi.fn()} />);

      expect(screen.getByTestId('add-source-modal-card')).toBeTruthy();
      expect(screen.getByTestId('btn-source-type-local')).toBeTruthy();
      expect(screen.getByTestId('btn-source-type-zip')).toBeTruthy();
      expect(screen.getByTestId('btn-source-type-drive')).toBeTruthy();
      expect(screen.getByTestId('input-source-path')).toBeTruthy();

      const checkbox = screen.getByTestId('checkbox-frozen-mode') as HTMLInputElement;
      expect(checkbox.checked).toBe(true);
    });

    it('allows toggling to Google Drive and shows API key input', () => {
      render(<AddSourceModal onClose={vi.fn()} onSourceAdded={vi.fn()} />);

      fireEvent.click(screen.getByTestId('btn-source-type-drive'));
      expect(screen.getByTestId('input-drive-api-key')).toBeTruthy();
    });

    it('submits incremental source with frozen mode invariant and calls onSourceAdded', async () => {
      const onSourceAdded = vi.fn();
      const onClose = vi.fn();
      vi.mocked(api.addProjectSource).mockResolvedValueOnce(mockDiff);

      render(<AddSourceModal onClose={onClose} onSourceAdded={onSourceAdded} />);

      const pathInput = screen.getByTestId('input-source-path');
      fireEvent.change(pathInput, { target: { value: 'C:/Event/Day2' } });

      const labelInput = screen.getByTestId('input-source-label');
      fireEvent.change(labelInput, { target: { value: 'Day 2 Camera' } });

      const submitBtn = screen.getByTestId('btn-submit-add-source');
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(api.addProjectSource).toHaveBeenCalledWith(
          expect.objectContaining({
            path_or_url: 'C:/Event/Day2',
            label: 'Day 2 Camera',
            kind: 'local',
          }),
          undefined,
          true
        );
        expect(onSourceAdded).toHaveBeenCalledWith(mockDiff);
        expect(onClose).toHaveBeenCalled();
      });
    });

    it('handles backend error gracefully and shows alert', async () => {
      vi.mocked(api.addProjectSource).mockRejectedValueOnce(new Error('Folder not accessible'));

      render(<AddSourceModal onClose={vi.fn()} onSourceAdded={vi.fn()} />);

      fireEvent.change(screen.getByTestId('input-source-path'), { target: { value: 'C:/Missing' } });
      fireEvent.click(screen.getByTestId('btn-submit-add-source'));

      await waitFor(() => {
        expect(screen.getByTestId('add-source-error-alert')).toBeTruthy();
        expect(screen.getByText('Folder not accessible')).toBeTruthy();
      });
    });
  });

  describe('WhatChangedModal', () => {
    it('renders structured diff metrics and frozen invariant banner', () => {
      render(
        <WhatChangedModal
          diff={mockDiff}
          onClose={vi.fn()}
          onUndoAddition={vi.fn()}
        />
      );

      expect(screen.getByTestId('frozen-invariant-badge')).toBeTruthy();
      expect(screen.getByText('Frozen Invariant Verified')).toBeTruthy();
      expect(screen.getByText('0 existing people membership changes')).toBeTruthy();

      expect(screen.getByTestId('stat-new-photos').textContent).toContain('+5');
      expect(screen.getByText('2 duplicates skipped')).toBeTruthy();
      expect(screen.getByTestId('stat-new-people').textContent).toContain('+1');
      expect(screen.getByTestId('stat-joined-existing').textContent).toContain('+3');
      expect(screen.getByTestId('stat-unrec-faces').textContent).toContain('+1');
      expect(screen.getByTestId('stat-membership-delta').textContent).toContain('0');

      // Sections
      expect(screen.getByTestId('section-new-people').textContent).toContain('person_bob');
      expect(screen.getByTestId('section-joined-existing').textContent).toContain('Alice');
    });

    it('triggers undo addition rollback flow with user confirmation', async () => {
      const onUndoAddition = vi.fn().mockResolvedValue(undefined);
      const onClose = vi.fn();

      render(
        <WhatChangedModal
          diff={mockDiff}
          onClose={onClose}
          onUndoAddition={onUndoAddition}
        />
      );

      // 1. Click Undo This Addition
      fireEvent.click(screen.getByTestId('btn-trigger-undo-addition'));

      // 2. Confirmation prompt appears
      expect(screen.getByTestId('confirm-undo-container')).toBeTruthy();
      expect(screen.getByText('Confirm Rollback to Pre-Addition Snapshot')).toBeTruthy();

      // 3. Confirm execution
      fireEvent.click(screen.getByTestId('btn-execute-undo'));

      await waitFor(() => {
        expect(onUndoAddition).toHaveBeenCalled();
        expect(onClose).toHaveBeenCalled();
      });
    });
  });

  describe('ReviewPeopleScreen Integration', () => {
    it('renders + Add Source button in the review header', () => {
      vi.mocked(api.getWhatChanged).mockResolvedValueOnce(null as any);

      render(
        <ReviewPeopleScreen
          people={mockPeople}
          photos={mockPhotos}
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

      expect(screen.getByTestId('btn-add-source')).toBeTruthy();
      expect(screen.getByText('+ Add Source')).toBeTruthy();
    });

    it('opens AddSourceModal when clicking + Add Source', () => {
      vi.mocked(api.getWhatChanged).mockResolvedValueOnce(null as any);

      render(
        <ReviewPeopleScreen
          people={mockPeople}
          photos={mockPhotos}
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

      fireEvent.click(screen.getByTestId('btn-add-source'));
      expect(screen.getByTestId('add-source-modal-card')).toBeTruthy();
    });

    it('renders What Changed button when a report exists and opens WhatChangedModal on click', async () => {
      vi.mocked(api.getWhatChanged).mockResolvedValueOnce(mockDiff);

      render(
        <ReviewPeopleScreen
          people={mockPeople}
          photos={mockPhotos}
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

      await waitFor(() => {
        expect(screen.getByTestId('btn-view-what-changed')).toBeTruthy();
      });

      fireEvent.click(screen.getByTestId('btn-view-what-changed'));
      expect(screen.getByTestId('what-changed-modal-card')).toBeTruthy();
    });
  });
});
