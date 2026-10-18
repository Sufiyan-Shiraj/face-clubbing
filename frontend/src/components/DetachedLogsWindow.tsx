import React, { useEffect, useRef, useState, useMemo } from 'react';
import ReactDOM from 'react-dom';
import {
  Terminal,
  Clock,
  Copy,
  Check,
  Search,
  X,
  Minimize2,
} from 'lucide-react';
import { JobStatus } from '../types';

export interface LogEntry {
  id: number;
  stage: string;
  message: string;
  percent: number;
}

export interface DetachedLogsWindowProps {
  isOpen: boolean;
  onClose: () => void;
  onDock: () => void;
  allLogs: LogEntry[];
  isRunning: boolean;
  status: JobStatus;
  elapsedSeconds: number;
  formatElapsedTime: (totalSecs: number) => string;
  theme?: string;
}

export const DetachedLogsWindow: React.FC<DetachedLogsWindowProps> = ({
  isOpen,
  onClose,
  onDock,
  allLogs,
  isRunning,
  status,
  elapsedSeconds,
  formatElapsedTime,
  theme = 't-dark',
}) => {
  const externalWindowRef = useRef<Window | null>(null);
  const [containerEl, setContainerEl] = useState<HTMLDivElement | null>(null);
  const [logSearchQuery, setLogSearchQuery] = useState<string>('');
  const [isCopied, setIsCopied] = useState<boolean>(false);
  const [stageFilter, setStageFilter] = useState<string>('all');
  const [autoScroll, setAutoScroll] = useState<boolean>(true);
  const terminalScrollRef = useRef<HTMLDivElement>(null);

  // Open and initialize detached window
  useEffect(() => {
    if (!isOpen) {
      if (externalWindowRef.current && !externalWindowRef.current.closed) {
        externalWindowRef.current.close();
      }
      externalWindowRef.current = null;
      setContainerEl(null);
      return;
    }

    // If window is already open and not closed, focus it
    if (externalWindowRef.current && !externalWindowRef.current.closed) {
      externalWindowRef.current.focus();
      return;
    }

    // Open new native detached window
    const width = 880;
    const height = 640;
    const left = Math.max(50, Math.floor((window.screen?.availWidth || 1200) / 2 - width / 2));
    const top = Math.max(50, Math.floor((window.screen?.availHeight || 800) / 2 - height / 2));
    const windowFeatures = `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes,status=no,toolbar=no,menubar=no,location=no`;

    const popup = window.open('', 'PhotoSorterDetachedLogs', windowFeatures);

    if (!popup || !popup.document) {
      // Popup blocked by browser settings
      alert(
        'Pop-up window was blocked by your browser.\n\nPlease enable pop-ups for this site to use the detached floating logs window, or use the in-page logs modal.'
      );
      onClose();
      return;
    }

    externalWindowRef.current = popup;

    // Set initial title with elapsed time in the name
    const initialElapsed = formatElapsedTime(elapsedSeconds);
    popup.document.title = `[${initialElapsed}] Engine Activity Log - CatLog`;

    // Clear popup document body
    popup.document.body.innerHTML = '';

    // Create mount root container
    const rootDiv = popup.document.createElement('div');
    rootDiv.id = 'detached-logs-root';
    rootDiv.style.height = '100vh';
    rootDiv.style.width = '100vw';
    rootDiv.style.display = 'flex';
    rootDiv.style.flexDirection = 'column';
    rootDiv.style.overflow = 'hidden';
    popup.document.body.appendChild(rootDiv);

    // Apply active theme class to html & body
    popup.document.documentElement.className = theme;
    popup.document.body.className = `${theme} antialiased`;

    // Clone parent stylesheets to detached window
    try {
      document.querySelectorAll('link[rel="stylesheet"], style').forEach((node) => {
        popup.document.head.appendChild(node.cloneNode(true));
      });
    } catch (e) {
      // Ignore stylesheet clone exceptions in restricted environments
    }

    // Inject base reset & scrollbar CSS
    const baseStyle = popup.document.createElement('style');
    baseStyle.textContent = `
      html, body {
        margin: 0;
        padding: 0;
        width: 100%;
        height: 100%;
        overflow: hidden;
        background: var(--bg, #141211);
        color: var(--text, #f5eedf);
        font-family: 'JetBrains Mono', monospace, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      }
      * { box-sizing: border-box; }
      ::-webkit-scrollbar { width: 8px; height: 8px; }
      ::-webkit-scrollbar-track { background: var(--panel, #1a1715); }
      ::-webkit-scrollbar-thumb { background: var(--line, #4e443e); border-radius: 4px; }
      ::-webkit-scrollbar-thumb:hover { background: var(--accent, #fa7175); }
    `;
    popup.document.head.appendChild(baseStyle);

    // Listen to close/unload on popup
    const handleUnload = () => {
      onClose();
    };
    popup.addEventListener('beforeunload', handleUnload);

    // Handle Escape key to close/dock
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    popup.addEventListener('keydown', handleKeyDown);

    setContainerEl(rootDiv);

    // Watch for window closure
    const pollTimer = setInterval(() => {
      if (popup.closed) {
        clearInterval(pollTimer);
        onClose();
      }
    }, 500);

    return () => {
      clearInterval(pollTimer);
      if (popup && !popup.closed) {
        popup.removeEventListener('beforeunload', handleUnload);
        popup.removeEventListener('keydown', handleKeyDown);
      }
    };
  }, [isOpen, onClose, theme]);

  // Update window title dynamically whenever elapsed time, stage, or logs change
  // This satisfies "it also need to show time elapsed in the name"
  useEffect(() => {
    if (!isOpen || !externalWindowRef.current || externalWindowRef.current.closed) return;
    const timeStr = formatElapsedTime(elapsedSeconds);
    const stageStr = isRunning
      ? (status.stage || 'Scanning')
      : (status.status === 'completed' ? 'Completed' : status.status || 'Ready');
    externalWindowRef.current.document.title = `[${timeStr}] ${stageStr} • Engine Activity Log (${allLogs.length}) - CatLog`;
  }, [isOpen, elapsedSeconds, isRunning, status.stage, status.status, allLogs.length, formatElapsedTime]);

  // Sync theme changes to detached window
  useEffect(() => {
    if (externalWindowRef.current && !externalWindowRef.current.closed) {
      externalWindowRef.current.document.documentElement.className = theme;
      externalWindowRef.current.document.body.className = `${theme} antialiased`;
    }
  }, [theme]);

  // Filter logs by search query and stage filter
  const filteredLogs = useMemo(() => {
    return allLogs.filter((log) => {
      if (stageFilter !== 'all') {
        const s = log.stage.toLowerCase();
        if (stageFilter === 'model' && !s.includes('model') && !s.includes('load')) return false;
        if (stageFilter === 'faces' && !s.includes('detect') && !s.includes('face') && !s.includes('scan')) return false;
        if (stageFilter === 'clustering' && !s.includes('cluster') && !s.includes('group')) return false;
        if (stageFilter === 'export' && !s.includes('export') && !s.includes('save') && !s.includes('gallery')) return false;
        if (stageFilter === 'errors' && !s.includes('err') && !s.includes('fail') && !s.includes('warn')) return false;
      }
      if (!logSearchQuery.trim()) return true;
      const q = logSearchQuery.toLowerCase();
      return log.stage.toLowerCase().includes(q) || log.message.toLowerCase().includes(q);
    });
  }, [allLogs, logSearchQuery, stageFilter]);

  // Auto-scroll to bottom of terminal
  useEffect(() => {
    if (autoScroll && terminalScrollRef.current) {
      terminalScrollRef.current.scrollTop = terminalScrollRef.current.scrollHeight;
    }
  }, [allLogs.length, autoScroll, filteredLogs.length]);

  // Copy all logs
  const handleCopyAll = () => {
    const text = allLogs
      .map((l, i) => `[${(i + 1).toString().padStart(4, '0')}] [${l.stage}] (${l.percent}%) ${l.message}`)
      .join('\n');
    navigator.clipboard.writeText(text).then(() => {
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    });
  };

  // Dock to main window handler
  const handleDockToMain = () => {
    if (externalWindowRef.current && !externalWindowRef.current.closed) {
      externalWindowRef.current.close();
    }
    externalWindowRef.current = null;
    onDock();
  };

  // Close detached window
  const handleCloseWindow = () => {
    if (externalWindowRef.current && !externalWindowRef.current.closed) {
      externalWindowRef.current.close();
    }
    externalWindowRef.current = null;
    onClose();
  };

  if (!isOpen || !containerEl) return null;

  return ReactDOM.createPortal(
    <div
      data-testid="detached-logs-window-root"
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        width: '100vw',
        background: 'var(--panel)',
        color: 'var(--text)',
        fontFamily: "'JetBrains Mono', monospace",
      }}
    >
      {/* Top Header Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '12px 18px',
          borderBottom: '2px solid var(--line)',
          background: 'var(--bg)',
          flexShrink: 0,
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Terminal className="w-5 h-5 text-[var(--accent)]" />
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontWeight: 800, fontSize: '15px', letterSpacing: '0.5px' }}>
                Engine Activity Log
              </span>

              {/* Time elapsed in the header/name */}
              <span
                data-testid="detached-elapsed-badge"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '3px 10px',
                  borderRadius: '4px',
                  border: '1px solid var(--line)',
                  background: 'var(--input)',
                  color: 'var(--accent-ink)',
                  fontSize: '12px',
                  fontWeight: 700,
                  boxShadow: '1px 1px 0px var(--line)',
                }}
                title="Time elapsed since scan started (also shown in window title bar)"
              >
                <Clock className="w-3.5 h-3.5 text-[var(--accent)]" />
                <span>{formatElapsedTime(elapsedSeconds)}</span>
              </span>

              <span
                style={{
                  padding: '3px 8px',
                  borderRadius: '4px',
                  border: '1px solid var(--line)',
                  background: 'var(--panel)',
                  color: 'var(--muted)',
                  fontSize: '11px',
                  fontWeight: 700,
                }}
              >
                {allLogs.length} events
              </span>

              {isRunning && (
                <span
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    fontSize: '12px',
                    fontWeight: 700,
                    color: 'var(--accent-ink)',
                  }}
                >
                  <span
                    style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      background: 'var(--accent)',
                      display: 'inline-block',
                      animation: 'pulse 1.5s infinite',
                    }}
                  />
                  Live Feed
                </span>
              )}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '2px' }}>
              Detached Window • Main window can be minimized safely while this remains active
            </div>
          </div>
        </div>

        {/* Header Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <button
            type="button"
            id="btn-detached-dock"
            data-testid="btn-detached-dock"
            onClick={handleDockToMain}
            className="btn sm"
            style={{ height: '32px', padding: '0 12px', fontSize: '12px', fontWeight: 600 }}
            title="Dock logs back into main window modal"
          >
            <Minimize2 className="w-3.5 h-3.5 mr-1 text-[var(--accent)]" />
            <span>Dock to Main</span>
          </button>

          <button
            type="button"
            id="btn-detached-copy"
            data-testid="btn-detached-copy"
            onClick={handleCopyAll}
            className="btn sm"
            style={{ height: '32px', padding: '0 12px', fontSize: '12px' }}
            title="Copy all logs to clipboard"
          >
            {isCopied ? (
              <>
                <Check className="w-3.5 h-3.5 text-green-500 mr-1" />
                <span>Copied!</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 mr-1 text-[var(--muted)]" />
                <span>Copy All</span>
              </>
            )}
          </button>

          <button
            type="button"
            id="btn-detached-close"
            data-testid="btn-detached-close"
            onClick={handleCloseWindow}
            className="btn sm"
            style={{ height: '32px', width: '32px', padding: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
            title="Close detached log window (Esc)"
          >
            <X className="w-4 h-4 text-[var(--muted)]" />
          </button>
        </div>
      </div>

      {/* Filter and Quick Chips Bar */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '8px 18px',
          borderBottom: '1px solid var(--line)',
          background: 'var(--panel)',
          gap: '10px',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, minWidth: '240px' }}>
          <Search className="w-4 h-4 text-[var(--muted)] flex-shrink-0" />
          <input
            type="text"
            id="detached-search-input"
            data-testid="detached-search-input"
            placeholder="Search logs by keyword or stage..."
            value={logSearchQuery}
            onChange={(e) => setLogSearchQuery(e.target.value)}
            style={{
              background: 'transparent',
              border: 'none',
              fontSize: '12px',
              color: 'var(--text)',
              fontFamily: 'inherit',
              outline: 'none',
              width: '100%',
            }}
          />
          {logSearchQuery && (
            <button
              type="button"
              onClick={() => setLogSearchQuery('')}
              style={{
                fontSize: '11px',
                color: 'var(--muted)',
                background: 'none',
                border: 'none',
                cursor: 'pointer',
              }}
            >
              Clear
            </button>
          )}
        </div>

        {/* Quick Filter Stage Chips */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          {[
            { id: 'all', label: 'All' },
            { id: 'faces', label: 'Faces' },
            { id: 'clustering', label: 'Clustering' },
            { id: 'export', label: 'Export' },
            { id: 'errors', label: 'Errors' },
          ].map((chip) => (
            <button
              key={chip.id}
              type="button"
              onClick={() => setStageFilter(chip.id)}
              style={{
                padding: '2px 8px',
                borderRadius: '3px',
                fontSize: '11px',
                fontWeight: stageFilter === chip.id ? 700 : 500,
                border: '1px solid var(--line)',
                background: stageFilter === chip.id ? 'var(--accent)' : 'var(--input)',
                color: stageFilter === chip.id ? 'var(--on-accent)' : 'var(--muted)',
                cursor: 'pointer',
              }}
            >
              {chip.label}
            </button>
          ))}

          <label
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '5px',
              fontSize: '11px',
              color: 'var(--muted)',
              cursor: 'pointer',
              marginLeft: '8px',
            }}
          >
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              style={{ cursor: 'pointer' }}
            />
            <span>Auto-scroll</span>
          </label>
        </div>
      </div>

      {/* Terminal Output Body */}
      <div
        id="detached-progress-updates-log"
        data-testid="detached-progress-updates-log"
        ref={terminalScrollRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '12px 18px',
          background: 'var(--input)',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
        }}
      >
        {filteredLogs.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', color: 'var(--muted)', fontSize: '13px' }}>
            {logSearchQuery || stageFilter !== 'all'
              ? 'No log entries match the current filter.'
              : 'No activity logged yet.'}
          </div>
        ) : (
          filteredLogs.map((log, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                justifyContent: 'space-between',
                gap: '12px',
                padding: '4px 6px',
                borderRadius: '4px',
                fontSize: '12px',
                lineHeight: '1.5',
                borderBottom: '1px solid rgba(255,255,255,0.03)',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', overflow: 'hidden' }}>
                <span
                  style={{
                    color: 'var(--muted)',
                    fontSize: '11px',
                    minWidth: '34px',
                    textAlign: 'right',
                    userSelect: 'none',
                    opacity: 0.6,
                  }}
                >
                  {(idx + 1).toString().padStart(3, '0')}.
                </span>

                <span
                  style={{
                    padding: '1px 6px',
                    borderRadius: '3px',
                    fontSize: '10px',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    background: 'var(--panel)',
                    color: 'var(--accent-ink)',
                    border: '1px solid var(--line)',
                    flexShrink: 0,
                    whiteSpace: 'nowrap',
                  }}
                >
                  {log.stage}
                </span>

                <span style={{ color: 'var(--text)', wordBreak: 'break-word' }}>
                  {log.message}
                </span>
              </div>

              <span
                style={{
                  color: 'var(--accent-ink)',
                  fontWeight: 700,
                  fontSize: '11px',
                  flexShrink: 0,
                  fontFamily: 'inherit',
                }}
              >
                {log.percent}%
              </span>
            </div>
          ))
        )}
      </div>

      {/* Footer Status Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '8px 18px',
          borderTop: '2px solid var(--line)',
          background: 'var(--bg)',
          fontSize: '11px',
          color: 'var(--muted)',
          flexShrink: 0,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <span>
            Showing <strong style={{ color: 'var(--text)' }}>{filteredLogs.length}</strong> of{' '}
            <strong style={{ color: 'var(--text)' }}>{allLogs.length}</strong> events
          </span>
          <span>•</span>
          <span>
            Stage: <strong style={{ color: 'var(--accent-ink)' }}>{status.stage || status.status}</strong>
          </span>
          <span>•</span>
          <span>
            Elapsed: <strong style={{ color: 'var(--text)' }}>{formatElapsedTime(elapsedSeconds)}</strong>
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ color: 'var(--muted)' }}>[Esc] to close</span>
          <button
            type="button"
            onClick={handleDockToMain}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--accent)',
              cursor: 'pointer',
              textDecoration: 'underline',
              fontSize: '11px',
              fontFamily: 'inherit',
            }}
          >
            Dock to main app
          </button>
        </div>
      </div>
    </div>,
    containerEl
  );
};
