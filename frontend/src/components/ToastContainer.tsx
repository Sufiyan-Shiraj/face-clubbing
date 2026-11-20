import React, { useEffect, useState } from 'react';
import { Undo2, X, CheckCircle2, AlertTriangle, Info } from 'lucide-react';

export interface ToastItem {
  id: string;
  message: string;
  type?: 'success' | 'info' | 'warning' | 'error';
  undoAction?: () => void | Promise<void>;
  undoLabel?: string;
  duration?: number; // ms, defaults to 6000
}

interface ToastCardProps {
  toast: ToastItem;
  onDismiss: (id: string) => void;
  onUndo?: (toast: ToastItem) => void;
}

const ToastCard: React.FC<ToastCardProps> = ({ toast, onDismiss, onUndo }) => {
  const duration = toast.duration || 6000;
  const [progress, setProgress] = useState<number>(100);

  useEffect(() => {
    const startTime = Date.now();
    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, 100 - (elapsed / duration) * 100);
      setProgress(remaining);
      if (remaining <= 0) {
        clearInterval(interval);
        onDismiss(toast.id);
      }
    }, 50);

    return () => clearInterval(interval);
  }, [toast.id, duration, onDismiss]);

  const handleUndoClick = async () => {
    if (onUndo) {
      onUndo(toast);
    } else if (toast.undoAction) {
      await toast.undoAction();
    }
    onDismiss(toast.id);
  };

  const getBorderColor = () => {
    switch (toast.type) {
      case 'error':
        return '#ef4444';
      case 'warning':
        return '#f59e0b';
      case 'info':
        return '#3b82f6';
      case 'success':
      default:
        return 'var(--accent)';
    }
  };

  return (
    <div
      role="status"
      data-testid={`toast-${toast.id}`}
      className="relative overflow-hidden flex flex-col p-3 rounded shadow-2xl transition-all animate-in slide-in-from-bottom-5 duration-200"
      style={{
        background: 'var(--panel)',
        border: `1.5px solid ${getBorderColor()}`,
        color: 'var(--text)',
        minWidth: '300px',
        maxWidth: '420px',
        boxShadow: '0 20px 30px -10px rgba(0,0,0,0.65), 0 0 0 1px var(--line)',
        fontFamily: '"JetBrains Mono", monospace',
      }}
    >
      <div className="flex items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2">
          {toast.type === 'error' && <AlertTriangle className="w-4 h-4 text-red-500 shrink-0" />}
          {toast.type === 'warning' && <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />}
          {toast.type === 'info' && <Info className="w-4 h-4 text-blue-400 shrink-0" />}
          {(toast.type === 'success' || !toast.type) && <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />}
          <span className="font-semibold leading-snug">{toast.message}</span>
        </div>

        <div className="flex items-center gap-1.5 shrink-0">
          {(toast.undoAction || onUndo) && (
            <button
              type="button"
              data-testid={`toast-undo-btn-${toast.id}`}
              onClick={handleUndoClick}
              className="btn sm inline-flex items-center gap-1 px-2 py-0.5 font-bold"
              style={{
                background: 'rgba(234, 88, 12, 0.15)',
                borderColor: 'var(--accent)',
                color: 'var(--accent)',
                fontSize: '11px',
              }}
              title="Undo this operation (Ctrl+Z)"
            >
              <Undo2 className="w-3 h-3" />
              <span>{toast.undoLabel || 'Undo (Ctrl+Z)'}</span>
            </button>
          )}

          <button
            type="button"
            data-testid={`toast-dismiss-btn-${toast.id}`}
            onClick={() => onDismiss(toast.id)}
            className="p-1 rounded opacity-70 hover:opacity-100 transition-opacity"
            title="Dismiss notification"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Progress countdown bar */}
      <div className="w-full bg-[rgba(255,255,255,0.06)] h-1 rounded-full overflow-hidden mt-2">
        <div
          className="h-full rounded-full transition-all duration-75"
          style={{
            width: `${progress}%`,
            background: getBorderColor(),
          }}
        />
      </div>
    </div>
  );
};

export interface ToastContainerProps {
  toasts: ToastItem[];
  onDismiss: (id: string) => void;
  onUndo?: (toast: ToastItem) => void;
}

export const ToastContainer: React.FC<ToastContainerProps> = ({
  toasts,
  onDismiss,
  onUndo,
}) => {
  if (toasts.length === 0) return null;

  return (
    <div
      aria-live="polite"
      data-testid="toast-container"
      className="fixed bottom-5 right-5 z-[99990] flex flex-col gap-2 pointer-events-auto"
    >
      {toasts.map((toast) => (
        <ToastCard
          key={toast.id}
          toast={toast}
          onDismiss={onDismiss}
          onUndo={onUndo}
        />
      ))}
    </div>
  );
};
