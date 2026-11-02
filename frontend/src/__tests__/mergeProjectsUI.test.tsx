import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MergeProjectsModal } from '../components/MergeProjectsModal';
import { OpenProjectModal } from '../components/OpenProjectModal';
import { apiClient } from '../api/client';

vi.mock('../api/client', () => ({
  apiClient: {
    getRecentProjects: vi.fn(),
    mergeProjects: vi.fn(),
    openSavedProject: vi.fn(),
    removeRecentProject: vi.fn(),
    browseFolder: vi.fn(),
  },
}));

describe('MergeProjectsModal Component (Phase V2-4)', () => {
  const mockProjects = [
    {
      id: 'proj_alpha',
      name: 'Event Alpha',
      work_dir: 'C:/events/alpha.work',
      export_path: 'C:/events/alpha',
      source_description: 'Local Folder',
      counts: { photos: 40, people: 12 },
      last_opened: '2026-11-01T10:00:00Z',
    },
    {
      id: 'proj_beta',
      name: 'Event Beta',
      work_dir: 'C:/events/beta.work',
      export_path: 'C:/events/beta',
      source_description: 'Drive folder XYZ',
      counts: { photos: 65, people: 20 },
      last_opened: '2026-11-02T10:00:00Z',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
    (apiClient.getRecentProjects as any).mockResolvedValue(mockProjects);
  });

  it('renders modal with project selections and defaults', async () => {
    render(<MergeProjectsModal onClose={vi.fn()} onMergedSuccess={vi.fn()} />);

    expect(screen.getByText('Merge Two Projects')).toBeDefined();
    expect(screen.getByText(/Immutable Parent Projects Guarantee/i)).toBeDefined();

    await waitFor(() => {
      expect(screen.getByTestId('select-project-a')).toBeDefined();
      expect(screen.getByTestId('select-project-b')).toBeDefined();
    });

    const selectA = screen.getByTestId('select-project-a') as HTMLSelectElement;
    const selectB = screen.getByTestId('select-project-b') as HTMLSelectElement;

    expect(selectA.value).toBe('proj_alpha');
    expect(selectB.value).toBe('proj_beta');
    expect(screen.getByTestId('btn-confirm-merge')).toBeDefined();
  });

  it('executes merge with selected projects and custom name', async () => {
    const onMergedSuccess = vi.fn();
    (apiClient.mergeProjects as any).mockResolvedValue({
      success: true,
      project_name: 'Combined Alpha and Beta',
      work_dir: 'C:/events/merged.work',
      export_dir: 'C:/events/merged',
      total_photos: 105,
      shared_photos: 10,
      people_count: 28,
      unrecognized_faces: 4,
      unrecognized_photos: 2,
      edits_applied: 5,
      unapplied_edits: 0,
      conflicts_count: 0,
      conflicts: [],
    });

    render(<MergeProjectsModal onClose={vi.fn()} onMergedSuccess={onMergedSuccess} />);

    await waitFor(() => {
      expect(screen.getByTestId('btn-confirm-merge')).toBeDefined();
    });

    const nameInput = screen.getByTestId('merged-project-name-input');
    fireEvent.change(nameInput, { target: { value: 'Combined Alpha and Beta' } });

    fireEvent.click(screen.getByTestId('btn-confirm-merge'));

    await waitFor(() => {
      expect(apiClient.mergeProjects).toHaveBeenCalledWith({
        project_a_work_dir: 'C:/events/alpha.work',
        project_b_work_dir: 'C:/events/beta.work',
        new_project_name: 'Combined Alpha and Beta',
      });
    });

    expect(screen.getByText('Projects Merged Successfully!')).toBeDefined();
    expect(screen.getByText('105')).toBeDefined(); // Total photos
    expect(screen.getByText('28')).toBeDefined(); // People count
    expect(screen.getByText(/Zero conflicting names or conflicting face assignments detected/i)).toBeDefined();

    // Click Open Merged Project
    const openMergedBtn = screen.getByTestId('open-merged-project-btn');
    fireEvent.click(openMergedBtn);
    expect(onMergedSuccess).toHaveBeenCalledTimes(1);
  });

  it('displays flagged conflicts for user review if present', async () => {
    (apiClient.mergeProjects as any).mockResolvedValue({
      success: true,
      project_name: 'Combined Events',
      work_dir: 'C:/events/merged.work',
      export_dir: 'C:/events/merged',
      total_photos: 100,
      shared_photos: 5,
      people_count: 25,
      unrecognized_faces: 3,
      unrecognized_photos: 1,
      edits_applied: 4,
      unapplied_edits: 0,
      conflicts_count: 1,
      conflicts: [
        {
          conflict_type: 'name_conflict',
          description: "Conflicting names for individual: 'Alice' vs 'Alicia'",
          entity_id: 'f_001',
          val_a: 'Alice',
          val_b: 'Alicia',
          resolution_strategy: 'review_needed',
        },
      ],
    });

    render(<MergeProjectsModal onClose={vi.fn()} onMergedSuccess={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByTestId('btn-confirm-merge')).toBeDefined();
    });

    fireEvent.click(screen.getByTestId('btn-confirm-merge'));

    await waitFor(() => {
      expect(screen.getByTestId('merge-conflicts-section')).toBeDefined();
    });

    expect(screen.getByText(/Review Needed: 1 Conflicts Flagged/i)).toBeDefined();
    expect(screen.getByText(/Conflicting names for individual: 'Alice' vs 'Alicia'/i)).toBeDefined();
  });

  it('displays error alert when backend rejects merge due to incompatible settings', async () => {
    (apiClient.mergeProjects as any).mockRejectedValue(
      new Error('Cannot merge projects with different detection settings hashes: Project A has abc, Project B has xyz')
    );

    render(<MergeProjectsModal onClose={vi.fn()} onMergedSuccess={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByTestId('btn-confirm-merge')).toBeDefined();
    });

    fireEvent.click(screen.getByTestId('btn-confirm-merge'));

    await waitFor(() => {
      expect(screen.getByTestId('merge-error-alert')).toBeDefined();
    });

    expect(screen.getByText(/Cannot merge projects with different detection settings hashes/i)).toBeDefined();
  });

  it('OpenProjectModal header contains button triggering onOpenMergeProjects', async () => {
    const onOpenMergeProjects = vi.fn();
    render(
      <OpenProjectModal
        onClose={vi.fn()}
        onProjectOpened={vi.fn()}
        onOpenMergeProjects={onOpenMergeProjects}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('modal-open-merge-btn')).toBeDefined();
    });

    fireEvent.click(screen.getByTestId('modal-open-merge-btn'));
    expect(onOpenMergeProjects).toHaveBeenCalledTimes(1);
  });
});
