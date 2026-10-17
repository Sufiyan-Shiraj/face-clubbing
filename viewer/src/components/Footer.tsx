import React from 'react';
import { ViewerConfig } from '../types';

interface FooterProps {
  config: ViewerConfig;
  generatedAt?: string;
}

export const Footer: React.FC<FooterProps> = ({ config, generatedAt }) => {
  const formattedDate = generatedAt
    ? new Date(generatedAt).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      })
    : null;

  return (
    <footer className="mt-auto py-6 border-t border-[var(--border-color)] text-center text-xs text-[var(--text-dim)]">
      <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
        <p className="font-semibold text-[var(--text-muted)]">
          {config.footer || 'Published with CatLog'}
        </p>
        {formattedDate && (
          <p className="text-[11px] text-[var(--text-dim)]">
            Exported {formattedDate}
          </p>
        )}
      </div>
    </footer>
  );
};
export default Footer;
