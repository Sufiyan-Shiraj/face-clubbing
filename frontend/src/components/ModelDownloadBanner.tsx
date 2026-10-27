import React, { useState, useEffect, useCallback } from 'react';
import { Download, RefreshCw, CheckCircle2, AlertTriangle, Cpu, Loader2 } from 'lucide-react';
import { api } from '../api/client';
import { ModelStatus } from '../types';

export interface ModelDownloadBannerProps {
  onStatusChange?: (status: ModelStatus) => void;
  className?: string;
  showCompactTriggerWhenInstalled?: boolean;
}

export const ModelDownloadBanner: React.FC<ModelDownloadBannerProps> = ({
  onStatusChange,
  className = '',
  showCompactTriggerWhenInstalled = true,
}) => {
  const [status, setStatus] = useState<ModelStatus | null>(null);
  const [isChecking, setIsChecking] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await api.getModelStatus();
      setStatus(res);
      onStatusChange?.(res);
      return res;
    } catch (err: any) {
      console.warn('Failed to load model status:', err);
      return null;
    }
  }, [onStatusChange]);

  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  // Poll while downloading
  useEffect(() => {
    if (!status?.is_downloading) return;
    const interval = setInterval(async () => {
      const res = await fetchStatus();
      if (res && !res.is_downloading && res.stage === 'completed') {
        setFeedback('Models verified and up to date!');
        setTimeout(() => setFeedback(null), 4000);
      }
    }, 600);
    return () => clearInterval(interval);
  }, [status?.is_downloading, fetchStatus]);

  const handleCheckUpdate = async (simulate = false) => {
    setIsChecking(true);
    setError(null);
    setFeedback(null);
    try {
      const res = await api.checkModelUpdates(simulate);
      const updatedStatus = await fetchStatus();
      if (res.update_available) {
        setFeedback(res.message || 'A new model update is available!');
      } else {
        setFeedback(res.message || 'Models are up to date.');
        setTimeout(() => setFeedback(null), 3500);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to check for model updates.');
    } finally {
      setIsChecking(false);
    }
  };

  const handleDownload = async () => {
    setError(null);
    setFeedback(null);
    try {
      const isUpdate = Boolean(status?.update_available);
      const res = await api.downloadModels(isUpdate);
      setStatus(res);
    } catch (err: any) {
      setError(err?.message || 'Failed to initiate model download.');
    }
  };

  // If models are already installed and no update is available and not downloading:
  // "check for the models if the models are there it becomes blank, but if the models hare not there then it shows"
  const isUpToDate = Boolean(status?.installed && !status?.update_available && !status?.is_downloading);

  if (!status) {
    return null;
  }

  // When up to date: render blank card, but keep subtle refresh trigger so user can check for updates at any time
  if (isUpToDate) {
    if (!showCompactTriggerWhenInstalled) return null;

    return (
      <div className={`model-status-clean-wrap flex items-center justify-between text-xs px-3 py-1.5 rounded-lg mb-3 ${className}`}
        style={{
          background: 'rgba(255, 255, 255, 0.02)',
          border: '1px solid var(--line)',
        }}
      >
        <div className="flex items-center gap-2 text-[var(--muted)]">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          <span>AI face models installed ({status.model_name || 'buffalo_l'})</span>
          {feedback && <span className="text-[var(--accent)] font-medium ml-1">({feedback})</span>}
        </div>
        <button
          type="button"
          id="check-models-update-btn"
          data-testid="check-models-update-btn"
          onClick={() => handleCheckUpdate(false)}
          disabled={isChecking}
          className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-[var(--muted)] hover:text-[var(--text)] hover:bg-[rgba(255,255,255,0.06)] transition-all font-medium"
          title="Check for model updates"
        >
          <RefreshCw className={`w-3 h-3 ${isChecking ? 'animate-spin text-[var(--accent)]' : ''}`} />
          <span>{isChecking ? 'Checking...' : 'Check updates'}</span>
        </button>
      </div>
    );
  }

  // When downloading: render live progress
  if (status.is_downloading) {
    const pct = status.percent ?? 0;
    const mbCur = status.current_bytes ? (status.current_bytes / (1024 * 1024)).toFixed(1) : '0.0';
    const mbTot = status.total_bytes ? (status.total_bytes / (1024 * 1024)).toFixed(1) : '288.6';

    return (
      <div
        id="model-download-banner"
        data-testid="model-download-banner"
        className={`p-4 rounded-xl mb-4 border transition-all ${className}`}
        style={{
          background: 'rgba(59, 130, 246, 0.06)',
          borderColor: 'rgba(59, 130, 246, 0.35)',
        }}
      >
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2.5">
            <Loader2 className="w-5 h-5 text-blue-400 animate-spin" />
            <div>
              <h4 className="text-sm font-semibold text-[var(--text)]">
                {status.update_available ? 'Updating Face Models...' : 'Downloading Face Models...'}
              </h4>
              <p className="text-xs text-[var(--muted)]">{status.message || 'Connecting to model repository...'}</p>
            </div>
          </div>
          <span className="text-xs font-mono font-bold text-blue-400">{pct.toFixed(1)}%</span>
        </div>

        <div className="w-full bg-[rgba(255,255,255,0.08)] h-2 rounded-full overflow-hidden mt-2">
          <div
            className="bg-gradient-to-r from-blue-500 to-indigo-500 h-full rounded-full transition-all duration-300"
            style={{ width: `${Math.max(pct, 2)}%` }}
          />
        </div>

        <div className="flex items-center justify-between text-[11px] text-[var(--muted)] mt-1.5 font-mono">
          <span>{mbCur} MB / {mbTot} MB</span>
          <span>InsightFace buffalo_l</span>
        </div>
      </div>
    );
  }

  // When models are missing OR update is available:
  const isUpdate = Boolean(status.update_available);

  return (
    <div
      id="model-download-banner"
      data-testid="model-download-banner"
      className={`p-4 rounded-xl mb-4 border transition-all shadow-lg ${className}`}
      style={{
        background: isUpdate ? 'rgba(234, 88, 12, 0.08)' : 'rgba(99, 102, 241, 0.08)',
        borderColor: isUpdate ? 'rgba(234, 88, 12, 0.4)' : 'rgba(99, 102, 241, 0.4)',
      }}
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-start gap-3">
          <div
            className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0 mt-0.5"
            style={{
              background: isUpdate ? 'rgba(234, 88, 12, 0.2)' : 'rgba(99, 102, 241, 0.2)',
              color: isUpdate ? '#fb923c' : '#818cf8',
            }}
          >
            {isUpdate ? <AlertTriangle className="w-5 h-5" /> : <Cpu className="w-5 h-5" />}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-semibold text-[var(--text)]">
                {isUpdate ? 'Face Recognition Models Update Available' : 'Face Recognition Models Required'}
              </h4>
              <span
                className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full"
                style={{
                  background: isUpdate ? 'rgba(234, 88, 12, 0.25)' : 'rgba(99, 102, 241, 0.25)',
                  color: isUpdate ? '#fdba74' : '#a5b4fc',
                }}
              >
                {isUpdate ? `v${status.latest_version || '1.1.0'}` : '~288 MB'}
              </span>
            </div>
            <p className="text-xs text-[var(--muted)] mt-1 leading-relaxed max-w-xl">
              {isUpdate
                ? 'A newer version of the buffalo_l deep learning weights is available upstream. Update to ensure optimal face recognition accuracy.'
                : 'InsightFace buffalo_l pack (5 ONNX neural weights, ~288 MB) is needed for face clustering. Download now in advance so your photo scans start instantly.'}
            </p>
            {feedback && <p className="text-xs text-[var(--accent)] font-medium mt-1">{feedback}</p>}
            {error && <p className="text-xs text-rose-400 font-medium mt-1">{error}</p>}
          </div>
        </div>

        <div className="flex items-center gap-2 self-end sm:self-center flex-shrink-0">
          <button
            type="button"
            id="check-models-update-btn"
            data-testid="check-models-update-btn"
            onClick={() => handleCheckUpdate(false)}
            disabled={isChecking}
            className="p-2 rounded-lg text-[var(--muted)] hover:text-[var(--text)] hover:bg-[rgba(255,255,255,0.08)] border border-[var(--line)] transition-all"
            title="Refresh / Check for updates"
          >
            <RefreshCw className={`w-4 h-4 ${isChecking ? 'animate-spin text-[var(--accent)]' : ''}`} />
          </button>

          <button
            type="button"
            id="download-models-btn"
            data-testid="download-models-btn"
            onClick={handleDownload}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg font-semibold text-xs text-white transition-all shadow-md hover:scale-[1.02] active:scale-[0.98]"
            style={{
              background: isUpdate
                ? 'linear-gradient(135deg, #ea580c, #c2410c)'
                : 'linear-gradient(135deg, var(--accent, #6366f1), #4338ca)',
            }}
          >
            <Download className="w-4 h-4" />
            <span>{isUpdate ? 'Update Models (~288 MB)' : 'Download Models (~288 MB)'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
