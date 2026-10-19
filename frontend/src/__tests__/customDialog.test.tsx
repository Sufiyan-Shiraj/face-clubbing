import React from 'react';
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CustomDialog } from '../components/CustomDialog';

describe('CustomDialog Component', () => {
  it('does not render when isOpen is false', () => {
    const { container } = render(
      <CustomDialog
        isOpen={false}
        type="error"
        message="Something went wrong"
      />
    );
    expect(container.firstChild).toBeNull();
  });

  it('renders error dialog with message, icon, and dismiss button', () => {
    const onConfirm = vi.fn();
    render(
      <CustomDialog
        isOpen={true}
        type="error"
        title="Merge Failed"
        message="Cannot merge these people clusters"
        details="Error 500: Server traceback details"
        onConfirm={onConfirm}
        theme="t-dark"
      />
    );

    expect(screen.getByText('Merge Failed')).toBeDefined();
    expect(screen.getByText('Cannot merge these people clusters')).toBeDefined();
    expect(screen.getByText('Error 500: Server traceback details')).toBeDefined();

    const okBtn = screen.getByTestId('dialog-ok-btn');
    expect(okBtn.textContent).toContain('Dismiss');
    fireEvent.click(okBtn);
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });

  it('closes error dialog on Escape key', () => {
    const onCancel = vi.fn();
    render(
      <CustomDialog
        isOpen={true}
        type="error"
        message="Network error"
        onCancel={onCancel}
      />
    );

    fireEvent.keyDown(window, { key: 'Escape' });
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('renders active-project guard with Export First, Discard, and Keep buttons', () => {
    const onExportFirst = vi.fn();
    const onConfirm = vi.fn();
    const onCancel = vi.fn();

    render(
      <CustomDialog
        isOpen={true}
        type="active-project"
        message="You have an active project with unexported work. Opening another project will replace your current workspace."
        onExportFirst={onExportFirst}
        onConfirm={onConfirm}
        onCancel={onCancel}
        theme="t-navy"
      />
    );

    expect(screen.getByText('Active Project in Progress')).toBeDefined();
    expect(screen.getByText('Unexported Albums & Faces')).toBeDefined();

    const exportBtn = screen.getByTestId('dialog-export-first-btn');
    expect(exportBtn.textContent).toContain('Export First (Recommended)');
    fireEvent.click(exportBtn);
    expect(onExportFirst).toHaveBeenCalledTimes(1);

    const discardBtn = screen.getByTestId('dialog-confirm-discard-btn');
    expect(discardBtn.textContent).toContain('Discard & Proceed');
    fireEvent.click(discardBtn);
    expect(onConfirm).toHaveBeenCalledTimes(1);

    const cancelBtn = screen.getByTestId('dialog-cancel-btn');
    expect(cancelBtn.textContent).toContain('Keep Project');
    fireEvent.click(cancelBtn);
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('renders saved-edits dialog with Keep, Start Fresh, and Cancel options', () => {
    const onConfirm = vi.fn();
    const onSecondaryAction = vi.fn();
    const onCancel = vi.fn();

    render(
      <CustomDialog
        isOpen={true}
        type="saved-edits"
        title="Saved Edits Detected"
        subtitle="12 edits from previous scan"
        message="Would you like to keep saved edits or start fresh?"
        onConfirm={onConfirm}
        onSecondaryAction={onSecondaryAction}
        onCancel={onCancel}
        theme="t-paper"
      />
    );

    expect(screen.getByText('Saved Edits Detected')).toBeDefined();
    expect(screen.getByText('12 edits from previous scan')).toBeDefined();

    const keepBtn = screen.getByTestId('dialog-confirm-btn');
    expect(keepBtn.textContent).toContain('Keep Saved Edits');
    fireEvent.click(keepBtn);
    expect(onConfirm).toHaveBeenCalledTimes(1);

    const freshBtn = screen.getByTestId('dialog-secondary-btn');
    expect(freshBtn.textContent).toContain('Start Fresh');
    fireEvent.click(freshBtn);
    expect(onSecondaryAction).toHaveBeenCalledTimes(1);

    const cancelBtn = screen.getByTestId('dialog-cancel-btn');
    expect(cancelBtn.textContent).toContain('Cancel');
    fireEvent.click(cancelBtn);
    expect(onCancel).toHaveBeenCalledTimes(1);
  });
});
