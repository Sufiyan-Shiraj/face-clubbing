import React, { useEffect } from 'react';
import ReactDOM from 'react-dom';
import {
  AlertTriangle,
  AlertCircle,
  HelpCircle,
  X,
  ExternalLink,
  Trash2,
  Check,
  RefreshCw,
} from 'lucide-react';
import { MascotSticker } from './MascotSticker';
import { CopyDiagnosticsButton } from './CopyDiagnosticsButton';

export type DialogType = 'error' | 'confirm' | 'active-project' | 'saved-edits';

export interface DialogOptions {
  isOpen: boolean;
  type: DialogType;
  title?: string;
  subtitle?: string;
  message: string;
  details?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  exportLabel?: string;
  theme?: string;
  onConfirm?: () => void;
  onCancel?: () => void;
  onExportFirst?: () => void;
  onSecondaryAction?: () => void;
  secondaryLabel?: string;
}

export const CustomDialog: React.FC<DialogOptions> = ({
  isOpen,
  type,
  title,
  subtitle,
  message,
  details,
  confirmLabel,
  cancelLabel,
  exportLabel = 'Export First (Recommended)',
  theme = 't-dark',
  onConfirm,
  onCancel,
  onExportFirst,
  onSecondaryAction,
  secondaryLabel,
}) => {
  useEffect(() => {
    if (!isOpen) return;
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        if (onCancel) onCancel();
        else if (onConfirm) onConfirm();
      } else if (e.key === 'Enter' && type === 'error') {
        e.preventDefault();
        if (onConfirm) onConfirm();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onCancel, onConfirm, type]);

  if (!isOpen) return null;

  const defaultTitle =
    type === 'error'
      ? 'Action Failed'
      : type === 'active-project'
      ? 'Active Project in Progress'
      : type === 'saved-edits'
      ? 'Saved Edits Detected'
      : 'Please Confirm';

  const displayTitle = title || defaultTitle;

  const defaultConfirmLabel =
    type === 'error'
      ? 'Dismiss'
      : type === 'active-project'
      ? 'Discard & Proceed'
      : type === 'saved-edits'
      ? 'Keep Saved Edits'
      : 'Confirm';

  const displayConfirmLabel = confirmLabel || defaultConfirmLabel;

  const defaultCancelLabel = type === 'active-project' ? 'Keep Project' : 'Cancel';
  const displayCancelLabel = cancelLabel || defaultCancelLabel;

  const modalContent = (
    <div
      className={`fixed inset-0 z-[9999] flex items-center justify-center p-4 sm:p-6 ${theme}`}
      style={{
        background: 'rgba(0, 0, 0, 0.72)',
        backdropFilter: 'blur(5px)',
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="custom-dialog-title"
      data-testid="custom-dialog-overlay"
      onClick={(e) => {
        if (e.target === e.currentTarget && onCancel) {
          onCancel();
        }
      }}
    >
      <div
        className="relative w-full max-w-lg rounded-2xl border-2 p-6 space-y-5 shadow-2xl animate-in fade-in zoom-in-95 duration-150"
        style={{
          background: 'var(--bg)',
          borderColor: type === 'error' ? '#ef4444' : type === 'active-project' ? 'var(--accent)' : 'var(--line)',
          color: 'var(--text)',
          boxShadow: '6px 6px 0px var(--line)',
        }}
        onClick={(e) => e.stopPropagation()}
        data-testid="custom-dialog-container"
      >
        {/* Header with Icon, Title, and Mascot */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3.5">
            {/* Themed Icon Box */}
            <div
              className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{
                background:
                  type === 'error'
                    ? 'rgba(239, 68, 68, 0.18)'
                    : type === 'active-project'
                    ? 'rgba(245, 158, 11, 0.18)'
                    : 'rgba(250, 113, 117, 0.18)',
                border: `2px solid ${
                  type === 'error'
                    ? '#ef4444'
                    : type === 'active-project'
                    ? '#f59e0b'
                    : 'var(--accent)'
                }`,
                color:
                  type === 'error'
                    ? '#f87171'
                    : type === 'active-project'
                    ? '#fbbf24'
                    : 'var(--accent)',
              }}
            >
              {type === 'error' ? (
                <AlertCircle className="w-6 h-6 text-red-400" />
              ) : type === 'active-project' ? (
                <AlertTriangle className="w-6 h-6 text-amber-400" />
              ) : (
                <HelpCircle className="w-6 h-6" style={{ color: 'var(--accent)' }} />
              )}
            </div>

            <div>
              <h3
                id="custom-dialog-title"
                className="font-black text-base tracking-tight"
                style={{
                  fontFamily: "'Outfit', 'Inter', system-ui, sans-serif",
                  color: 'var(--text)',
                }}
              >
                {displayTitle}
              </h3>
              {subtitle ? (
                <p className="text-xs font-mono font-semibold mt-0.5" style={{ color: 'var(--muted)' }}>
                  {subtitle}
                </p>
              ) : type === 'active-project' ? (
                <p className="text-xs font-mono font-bold mt-0.5 text-amber-400">
                  Unexported Albums & Faces
                </p>
              ) : null}
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Mascot Accent */}
            <MascotSticker
              pose={type === 'error' ? 2 : type === 'active-project' ? 2 : 3}
              theme={theme}
              width={34}
              height={34}
            />

            {/* Close Button */}
            {onCancel && (
              <button
                type="button"
                onClick={onCancel}
                className="p-1 rounded-lg border border-transparent hover:border-[var(--line)] opacity-70 hover:opacity-100 transition-all ml-1"
                title="Close dialog (Escape)"
                data-testid="dialog-close-btn"
                style={{ color: 'var(--text)' }}
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Message Content */}
        <div className="space-y-3">
          <p
            className="text-xs sm:text-sm leading-relaxed whitespace-pre-line font-mono"
            style={{ color: 'var(--text)' }}
            data-testid="dialog-message"
          >
            {message}
          </p>

          {/* Optional expandable technical details */}
          {details && (
            <div
              className="p-3 rounded-lg border text-xs font-mono overflow-x-auto max-h-36"
              style={{
                background: 'var(--input)',
                borderColor: 'var(--line)',
                color: 'var(--muted)',
              }}
            >
              {details}
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="pt-2">
          {type === 'active-project' ? (
            <div className="flex flex-col gap-2.5">
              {onExportFirst && (
                <button
                  type="button"
                  data-testid="dialog-export-first-btn"
                  onClick={onExportFirst}
                  className="riso-btn-accent text-xs flex items-center justify-center gap-2 w-full font-bold"
                  style={{ height: '40px' }}
                >
                  <ExternalLink className="w-4 h-4" />
                  <span>{exportLabel}</span>
                </button>
              )}

              <div className="flex flex-col sm:flex-row items-center gap-2">
                <button
                  type="button"
                  data-testid="dialog-confirm-discard-btn"
                  onClick={onConfirm}
                  className="riso-btn-sec text-xs flex items-center justify-center gap-2 w-full sm:flex-1 font-bold"
                  style={{
                    height: '38px',
                    borderColor: '#ef4444',
                    color: '#f87171',
                  }}
                >
                  <Trash2 className="w-4 h-4" />
                  <span>{displayConfirmLabel}</span>
                </button>

                <button
                  type="button"
                  data-testid="dialog-cancel-btn"
                  onClick={onCancel}
                  className="riso-btn-sec text-xs w-full sm:w-auto font-bold px-4"
                  style={{ height: '38px' }}
                >
                  {displayCancelLabel}
                </button>
              </div>
            </div>
          ) : type === 'saved-edits' ? (
            <div className="flex flex-col sm:flex-row items-center justify-end gap-2.5">
              <button
                type="button"
                data-testid="dialog-cancel-btn"
                onClick={onCancel}
                className="riso-btn-sec text-xs w-full sm:w-auto font-bold px-4"
                style={{ height: '38px' }}
              >
                {displayCancelLabel}
              </button>

              {onSecondaryAction && (
                <button
                  type="button"
                  data-testid="dialog-secondary-btn"
                  onClick={onSecondaryAction}
                  className="riso-btn-sec text-xs w-full sm:w-auto font-bold px-4"
                  style={{
                    height: '38px',
                    borderColor: 'var(--line)',
                  }}
                >
                  {secondaryLabel || 'Start Fresh'}
                </button>
              )}

              <button
                type="button"
                data-testid="dialog-confirm-btn"
                onClick={onConfirm}
                className="riso-btn-accent text-xs flex items-center justify-center gap-2 w-full sm:w-auto px-5 font-bold"
                style={{ height: '38px' }}
              >
                <Check className="w-4 h-4" />
                <span>{displayConfirmLabel}</span>
              </button>
            </div>
          ) : type === 'confirm' ? (
            <div className="flex items-center justify-end gap-2.5">
              <button
                type="button"
                data-testid="dialog-cancel-btn"
                onClick={onCancel}
                className="riso-btn-sec text-xs font-bold px-4"
                style={{ height: '38px' }}
              >
                {displayCancelLabel}
              </button>

              <button
                type="button"
                data-testid="dialog-confirm-btn"
                onClick={onConfirm}
                className="riso-btn-accent text-xs font-bold px-5"
                style={{ height: '38px' }}
              >
                {displayConfirmLabel}
              </button>
            </div>
          ) : (
            /* Error / Alert Dismiss */
            <div className="flex items-center justify-between w-full gap-3">
              <CopyDiagnosticsButton variant="danger" showPrivacyHint={false} />
              <button
                type="button"
                data-testid="dialog-ok-btn"
                onClick={onConfirm || onCancel}
                className="riso-btn-accent text-xs font-bold px-6"
                style={{ height: '38px' }}
              >
                {displayConfirmLabel}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  if (typeof document !== 'undefined' && document.body) {
    return ReactDOM.createPortal(modalContent, document.body);
  }
  return modalContent;
};

export default CustomDialog;
