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
    <footer className="mt-auto py-8 border-t border-neutral-900 text-center text-xs text-neutral-500">
      <div className="max-w-7xl mx-auto px-4 space-y-1.5">
        <p className="font-medium text-neutral-400">
          {config.footer || 'Published with PhotoSorter'}
        </p>
        {formattedDate && (
          <p className="text-[11px] text-neutral-600">
            Exported on {formattedDate}
          </p>
        )}
      </div>
    </footer>
  );
};
