import React from 'react';
import { ViewerConfig } from '../types';
import { MascotSticker } from './MascotSticker';

interface FooterProps {
  config: ViewerConfig;
  generatedAt?: string;
  theme?: string;
}

export const Footer: React.FC<FooterProps> = ({ config, generatedAt, theme = 't-dark' }) => {
  const formattedDate = generatedAt
    ? new Date(generatedAt).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    : null;

  return (
    <footer
      className="mt-auto py-8 border-t-2 border-[var(--line)] text-center text-xs font-mono"
      style={{
        background: 'var(--panel)',
      }}
    >
      <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <MascotSticker pose={6} theme={theme} width={28} height={28} />
          <p className="font-bold text-[var(--text)]">
            {config.footer || 'Published with CatLog — Who was at the event?'}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {formattedDate && (
            <span className="badge-chip text-[11px] text-[var(--muted)]">
              Exported {formattedDate}
            </span>
          )}
          <span className="badge-chip badge-accent text-[11px]">
            CatLog v0.1.0
          </span>
        </div>
      </div>
    </footer>
  );
};
export default Footer;
