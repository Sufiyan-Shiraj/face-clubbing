import React, { useState } from 'react';
import { DiagnosticsReport } from '../types';

interface CopyDiagnosticsButtonProps {
  reportText?: string | null;
  className?: string;
  variant?: 'primary' | 'secondary' | 'danger' | 'outline' | 'subtle';
  buttonText?: string;
  onCopied?: () => void;
  showPrivacyHint?: boolean;
}

export const CopyDiagnosticsButton: React.FC<CopyDiagnosticsButtonProps> = ({
  reportText,
  className = '',
  variant = 'secondary',
  buttonText = 'Copy diagnostics',
  onCopied,
  showPrivacyHint = false,
}) => {
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleCopy = async () => {
    if (loading) return;
    setErrorMsg(null);
    let textToCopy = reportText;

    if (!textToCopy) {
      setLoading(true);
      try {
        const resp = await fetch('/api/diagnostics');
        if (!resp.ok) {
          throw new Error(`Failed to fetch diagnostics (HTTP ${resp.status})`);
        }
        const data: DiagnosticsReport = await resp.json();
        textToCopy = data.formatted_report;
      } catch (err: any) {
        console.error('Error fetching diagnostics:', err);
        setErrorMsg('Failed to fetch diagnostics');
        setLoading(false);
        return;
      } finally {
        setLoading(false);
      }
    }

    if (!textToCopy) {
      setErrorMsg('No diagnostics available');
      return;
    }

    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(textToCopy);
      } else {
        // Fallback for older webview / non-secure contexts
        const textarea = document.createElement('textarea');
        textarea.value = textToCopy;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
      }

      setCopied(true);
      if (onCopied) onCopied();
      setTimeout(() => setCopied(false), 2500);
    } catch (err) {
      console.error('Clipboard copy failed:', err);
      setErrorMsg('Could not copy to clipboard');
    }
  };

  const getVariantStyles = () => {
    if (copied) {
      return 'bg-emerald-600/20 text-emerald-300 border-emerald-500/50 hover:bg-emerald-600/30';
    }
    switch (variant) {
      case 'primary':
        return 'bg-blue-600 hover:bg-blue-500 text-white border-blue-500/50 shadow-sm';
      case 'danger':
        return 'bg-red-600/20 text-red-300 border-red-500/40 hover:bg-red-600/30';
      case 'outline':
        return 'bg-transparent text-gray-300 border-gray-600 hover:bg-gray-800 hover:text-white';
      case 'subtle':
        return 'bg-gray-800/60 text-gray-400 border-transparent hover:bg-gray-800 hover:text-gray-200';
      case 'secondary':
      default:
        return 'bg-gray-800 text-gray-200 border-gray-700 hover:bg-gray-700 hover:text-white';
    }
  };

  return (
    <div className="inline-flex flex-col items-start gap-1">
      <button
        type="button"
        id="copy-diagnostics-btn"
        onClick={handleCopy}
        disabled={loading}
        title="Copies a privacy-safe report with version, OS, settings hash, error code, and photo counts (zero paths, zero photos, zero API keys)"
        className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all duration-150 cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed ${getVariantStyles()} ${className}`}
      >
        {copied ? (
          <>
            <svg
              className="w-3.5 h-3.5 text-emerald-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
            </svg>
            <span className="font-semibold text-emerald-300">Copied Safe Report!</span>
          </>
        ) : loading ? (
          <>
            <svg
              className="w-3.5 h-3.5 animate-spin text-gray-400"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
            </svg>
            <span>Preparing diagnostics...</span>
          </>
        ) : (
          <>
            <svg
              className="w-3.5 h-3.5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"
              />
            </svg>
            <span>{buttonText}</span>
          </>
        )}
      </button>

      {errorMsg && <span className="text-[10px] text-red-400">{errorMsg}</span>}

      {showPrivacyHint && (
        <span className="text-[10px] text-gray-500">
          Privacy guarantee: zero file paths, zero URLs, zero API keys, and zero attendee photos.
        </span>
      )}
    </div>
  );
};
