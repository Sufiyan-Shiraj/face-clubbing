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
      openFolderDialog: vi.fn(),
      browseFolder: vi.fn(),
    },
    api: {
      getRecentProjects: vi.fn(),
      openProject: vi.fn(),
      removeProject: vi.fn(),
      openFolderDialog: vi.fn(),
      browseFolder: vi.fn(),
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

  it('allows cleaning all missing projects with one click', async () => {
    vi.mocked(apiClient.getRecentProjects)
      .mockResolvedValueOnce(mockProjects)
      .mockResolvedValueOnce([mockProjects[0]]);
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
      expect(screen.getByText('Clean Missing (1)')).toBeDefined();
    });

    const cleanBtn = screen.getByTestId('clean-all-missing-btn');
    fireEvent.click(cleanBtn);

    await waitFor(() => {
      expect(apiClient.removeProject).toHaveBeenCalledWith('proj_02');
    });
  });

  it('triggers native system dialog to select folder and updates custom path input', async () => {
    vi.mocked(apiClient.getRecentProjects).mockResolvedValue(mockProjects);
    vi.mocked(apiClient.openFolderDialog).mockResolvedValue({
      selected: 'D:/Photos/Wedding2026/Wedding2026.work',
      cancelled: false,
    });

    render(
      <OpenProjectModal
        onClose={vi.fn()}
        onProjectOpened={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByTestId('btn-system-dialog')).toBeDefined();
    });

    const browseBtn = screen.getByTestId('btn-system-dialog');
    fireEvent.click(browseBtn);

    await waitFor(() => {
      expect(apiClient.openFolderDialog).toHaveBeenCalled();
      const input = screen.getByTestId('custom-project-path-input') as HTMLInputElement;
      expect(input.value).toBe('D:/Photos/Wedding2026/Wedding2026.work');
    });
  });

  it('toggles in-modal folder explorer, renders subfolders, and selects a directory', async () => {
    vi.mocked(apiClient.getRecentProjects).mockResolvedValue(mockProjects);
    vi.mocked(apiClient.browseFolder).mockResolvedValue({
      current_path: 'C:/Users/DELL/Pictures',
      parent_path: 'C:/Users/DELL',
      name: 'Pictures',
      exists: true,
      is_directory: true,
      directories: [
        { name: 'Trip2026.work', path: 'C:/Users/DELL/Pictures/Trip2026.work' },
        { name: 'FamilyPhotos', path: 'C:/Users/DELL/Pictures/FamilyPhotos' },
      ],
      shortcuts: [
        { label: 'Desktop', path: 'C:/Users/DELL/Desktop' },
      ],
    });

    render(
      <OpenProjectModal
        onClose={vi.fn()}
        onProjectOpened={vi.fn()}
      />
    );

    const toggleBtn = screen.getByTestId('toggle-explorer-btn');
    fireEvent.click(toggleBtn);

    await waitFor(() => {
      expect(apiClient.browseFolder).toHaveBeenCalled();
      expect(screen.getByText('Trip2026.work')).toBeDefined();
      expect(screen.getByText('Desktop')).toBeDefined();
    });

    // Clicking a subfolder selects it
    fireEvent.click(screen.getByText('Trip2026.work'));
    const input = screen.getByTestId('custom-project-path-input') as HTMLInputElement;
    expect(input.value).toBe('C:/Users/DELL/Pictures/Trip2026.work');
  });

  describe('Unexported Work Guard', () => {
    it('prompts unexported guard modal when opening project with unexported work', async () => {
      vi.mocked(apiClient.getRecentProjects).mockResolvedValue(mockProjects);

      render(
        <OpenProjectModal
          onClose={vi.fn()}
          onProjectOpened={vi.fn()}
          hasUnexportedWork={true}
          onNavigateToExport={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Event Alpha')).toBeDefined();
      });

      // Click open on project
      const openBtn = screen.getByTestId('open-project-btn-proj_01');
      fireEvent.click(openBtn);

      // Guard modal is shown instead of immediately opening
      expect(screen.getByTestId('unexported-guard-modal')).toBeDefined();
      expect(screen.getByText(/Unexported Work in Current Project/i)).toBeDefined();
      expect(apiClient.openProject).not.toHaveBeenCalled();

      // Cancel button dismisses modal without action
      const cancelBtn = screen.getByTestId('cancel-guard-btn');
      fireEvent.click(cancelBtn);

      expect(screen.queryByTestId('unexported-guard-modal')).toBeNull();
      expect(apiClient.openProject).not.toHaveBeenCalled();
    });

    it('navigates to Export screen when user clicks Export First', async () => {
      vi.mocked(apiClient.getRecentProjects).mockResolvedValue(mockProjects);
      const onNavigateToExport = vi.fn();

      render(
        <OpenProjectModal
          onClose={vi.fn()}
          onProjectOpened={vi.fn()}
          hasUnexportedWork={true}
          onNavigateToExport={onNavigateToExport}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Event Alpha')).toBeDefined();
      });

      fireEvent.click(screen.getByTestId('open-project-btn-proj_01'));
      expect(screen.getByTestId('unexported-guard-modal')).toBeDefined();

      const exportFirstBtn = screen.getByTestId('export-first-btn');
      fireEvent.click(exportFirstBtn);

      expect(onNavigateToExport).toHaveBeenCalledTimes(1);
      expect(screen.queryByTestId('unexported-guard-modal')).toBeNull();
    });

    it('discards and opens project when user clicks Discard & Open Project', async () => {
      vi.mocked(apiClient.getRecentProjects).mockResolvedValue(mockProjects);
      vi.mocked(apiClient.openProject).mockResolvedValue({
        success: true,
        message: 'Opened',
        project: mockProjects[0],
        people_count: 15,
        photos_count: 120,
        unrecognized_faces_count: 5,
        applied_edits_count: 0,
        read_only: false,
      });

      const onProjectOpened = vi.fn();
      const onClose = vi.fn();

      render(
        <OpenProjectModal
          onClose={onClose}
          onProjectOpened={onProjectOpened}
          hasUnexportedWork={true}
          onNavigateToExport={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Event Alpha')).toBeDefined();
      });

      fireEvent.click(screen.getByTestId('open-project-btn-proj_01'));
      expect(screen.getByTestId('unexported-guard-modal')).toBeDefined();

      const discardBtn = screen.getByTestId('discard-and-open-btn');
      fireEvent.click(discardBtn);

      await waitFor(() => {
        expect(apiClient.openProject).toHaveBeenCalledWith({ project_id: 'proj_01' });
        expect(onProjectOpened).toHaveBeenCalled();
        expect(onClose).toHaveBeenCalled();
      });
    });
  });
});
