import { describe, it, expect, vi } from 'vitest';

describe('Undo Control Logic', () => {
  it('determines when undo action is available', () => {
    const isUndoAvailable = (editsCount: number) => editsCount > 0;

    expect(isUndoAvailable(0)).toBe(false);
    expect(isUndoAvailable(1)).toBe(true);
    expect(isUndoAvailable(5)).toBe(true);
  });

  it('triggers onUndo callback when undo is clicked', () => {
    const mockUndoHandler = vi.fn();
    const handleUndoClick = (appliedCount: number, onUndo: () => void) => {
      if (appliedCount > 0) {
        onUndo();
      }
    };

    // When 0 edits
    handleUndoClick(0, mockUndoHandler);
    expect(mockUndoHandler).not.toHaveBeenCalled();

    // When edits exist
    handleUndoClick(2, mockUndoHandler);
    expect(mockUndoHandler).toHaveBeenCalledTimes(1);
  });

  it('updates edits count on successful undo response', () => {
    let appliedEdits = 3;

    // Simulate undo response
    const onUndoSuccess = () => {
      appliedEdits = Math.max(0, appliedEdits - 1);
    };

    onUndoSuccess();
    expect(appliedEdits).toBe(2);

    onUndoSuccess();
    expect(appliedEdits).toBe(1);

    onUndoSuccess();
    expect(appliedEdits).toBe(0);

    onUndoSuccess();
    expect(appliedEdits).toBe(0);
  });
});
