import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { OpenProjectModal } from '../components/OpenProjectModal';
import { ImageViewerModal } from '../components/ImageViewerModal';
import { Header } from '../components/Header';
import { apiClient } from '../api/client';
import { ProjectItem, PhotoInfo } from '../types';

vi.mock('../api/client', () => {
  return {
    apiClient: {
      getRecentProjects: vi.fn(),
      openProject: vi.fn(),
      removeProject: vi.fn(),
    },
    api: {
      getRecentProjects: vi.fn(),
      openProject: vi.fn(),
      removeProject: vi.fn(),
    },
  };
});

describe('Open Saved Project Feature', () => {
  const mockProjects: ProjectItem[] = [
    {
      id: 'proj_01',
      name: 'Event Alpha',
      work_dir: 'C:/photos/alpha.work',
      export_path: 'C:/photos/alpha_export',
      source_description: 'Local: C:/photos/alpha',
      last_opened: '2026-10-15T12:00:00Z',
      counts: { people: 15, photos: 120 },
      exists: true,
    },
    {
      id: 'proj_02',
      name: 'Deleted Project',
      work_dir: 'C:/photos/deleted.work',
      export_path: null,
      source_description: 'Drive folder 1A2B3C4D5E6F7G8H9I0',
      last_opened: '2026-10-10T08:30:00Z',
      counts: { people: 2, photos: 20 },
      exists: false,
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders recent projects list with name, source, and counts', async () => {
    vi.mocked(apiClient.getRecentProjects).mockResolvedValue(mockProjects);

    render(
      <OpenProjectModal
        onClose={vi.fn()}
        onProjectOpened={vi.fn()}
      />
    );

    // Initial loading state
    expect(screen.getByText(/Loading recent projects/i)).toBeDefined();

    // Loaded items
    await waitFor(() => {
      expect(screen.getByText('Event Alpha')).toBeDefined();
    });

    expect(screen.getByText('Local: C:/photos/alpha')).toBeDefined();
    expect(screen.getByText('15 people')).toBeDefined();
    expect(screen.getByText('120 photos')).toBeDefined();
    expect(screen.getByText('Deleted Project')).toBeDefined();
    expect(screen.getByText('Folder Missing')).toBeDefined();
  });

  it('handles clicking Open on a project successfully', async () => {
    vi.mocked(apiClient.getRecentProjects).mockResolvedValue(mockProjects);
    vi.mocked(apiClient.openProject).mockResolvedValue({
      success: true,
      message: 'Project opened successfully',
      project: mockProjects[0],
      people_count: 15,
      photos_count: 120,
      unrecognized_faces_count: 5,
      applied_edits_count: 2,
      read_only: false,
    });

    const onProjectOpened = vi.fn();
    const onClose = vi.fn();

    render(
      <OpenProjectModal
        onClose={onClose}
        onProjectOpened={onProjectOpened}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Event Alpha')).toBeDefined();
    });

    const openBtn = screen.getByTestId('open-project-btn-proj_01');
    fireEvent.click(openBtn);

    await waitFor(() => {
      expect(apiClient.openProject).toHaveBeenCalledWith({ project_id: 'proj_01' });
      expect(onProjectOpened).toHaveBeenCalled();
      expect(onClose).toHaveBeenCalled();
    });
  });

  it('handles moved/deleted folder (404) and offers removal from list', async () => {
    vi.mocked(apiClient.getRecentProjects).mockResolvedValue(mockProjects);
    vi.mocked(apiClient.openProject).mockRejectedValue(
      new Error("404: Work folder 'C:/photos/deleted.work' not found or was moved.")
    );
    vi.mocked(apiClient.removeProject).mockResolvedValue({
      success: true,
      message: 'Project removed from recent list',
    });

    render(
      <OpenProjectModal
        onClose={vi.fn()}
        onProjectOpened={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Deleted Project')).toBeDefined();
    });

    const openBtn = screen.getByTestId('open-project-btn-proj_02');
    fireEvent.click(openBtn);

    // Shows clear moved/deleted message
    await waitFor(() => {
      expect(screen.getByTestId('project-error-alert')).toBeDefined();
      expect(screen.getByText(/was moved or deleted on disk/i)).toBeDefined();
    });

    // Offer removal button appears
    const removeMissingBtn = screen.getByTestId('remove-missing-entry-btn');
    expect(removeMissingBtn).toBeDefined();

    fireEvent.click(removeMissingBtn);

    await waitFor(() => {
      expect(apiClient.removeProject).toHaveBeenCalledWith('proj_02');
      expect(screen.queryByText('Deleted Project')).toBeNull();
    });
  });

  it('blocks opening project while a scan is running (409)', async () => {
    vi.mocked(apiClient.getRecentProjects).mockResolvedValue(mockProjects);
    vi.mocked(apiClient.openProject).mockRejectedValue(
      new Error('409: Cannot open a project while a scan is running.')
    );

    render(
      <OpenProjectModal
        onClose={vi.fn()}
        onProjectOpened={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText('Event Alpha')).toBeDefined();
    });

    const openBtn = screen.getByTestId('open-project-btn-proj_01');
    fireEvent.click(openBtn);

    await waitFor(() => {
      expect(screen.getByText(/A scan is currently running/i)).toBeDefined();
    });
  });

  it('ImageViewerModal displays source missing banner and disabled download when source_exists is false', () => {
    const mockMissingPhoto: Record<string, PhotoInfo> = {
      p_missing: {
        photo_id: 'p_missing',
        file_name: 'missing_pic.jpg',
        width: 800,
        height: 600,
        thumb: '/thumbs/p_missing.jpg',
        download: '/api/photos/p_missing/download',
        source_exists: false,
        original_path: 'D:/non_existent/missing_pic.jpg',
        faces: [],
      },
    };

    render(
      <ImageViewerModal
        photoId="p_missing"
        photos={mockMissingPhoto}
        onClose={vi.fn()}
        onNavigatePhoto={vi.fn()}
      />
    );

    // Source missing badge in title bar
    expect(screen.getByTestId('source-missing-badge')).toBeDefined();
    expect(screen.getByText('Source missing')).toBeDefined();

    // Source missing floating banner
    expect(screen.getByTestId('source-missing-banner')).toBeDefined();
    expect(screen.getByText('Source photo missing or moved on disk')).toBeDefined();

    // Download button disabled
    const dlBtn = screen.getByTestId('download-missing-btn');
    expect(dlBtn).toBeDefined();
    expect((dlBtn as HTMLButtonElement).disabled).toBe(true);
  });

  it('Header trigger button invokes onOpenProject', () => {
    const onOpenProject = vi.fn();

    render(
      <Header
        activeTab="home"
        onTabChange={vi.fn()}
        peopleCount={10}
        unrecFacesCount={2}
        unrecPhotosCount={1}
        clusteredFacesCount={10}
        totalFacesCount={12}
        appliedEditsCount={0}
        onUndo={vi.fn()}
        onRefresh={vi.fn()}
        isRefreshing={false}
        theme="t-dark"
        onThemeChange={vi.fn()}
        onOpenProject={onOpenProject}
      />
    );

    const openLink = screen.getByTitle('Open saved project');
    fireEvent.click(openLink);

    expect(onOpenProject).toHaveBeenCalledTimes(1);
  });
});
