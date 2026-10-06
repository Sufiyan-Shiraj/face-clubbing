import React from 'react';
import { ViewerConfig } from '../types';
import { Users, Image as ImageIcon, Search, ArrowLeft } from 'lucide-react';

interface HeaderProps {
  config: ViewerConfig;
  totalPeople: number;
  totalPhotos: number;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  activeView: 'grid' | 'person' | 'unrecognized';
  onBackToGrid: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  config,
  totalPeople,
  totalPhotos,
  searchQuery,
  onSearchChange,
  activeView,
  onBackToGrid,
}) => {
  return (
    <header className="sticky top-0 z-30 glass-nav transition-all duration-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 sm:py-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 sm:gap-4">
          
          {/* Left: Title, Logo, & Navigation */}
          <div className="flex items-center gap-3.5">
            {activeView !== 'grid' && (
              <button
                onClick={onBackToGrid}
                className="p-2 -ml-2 rounded-xl text-neutral-400 hover:text-white hover:bg-neutral-800/80 transition-colors focus:outline-none focus:ring-2 focus:ring-accent"
                title="Back to All People"
                aria-label="Back to All People"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
            )}

            {config.logo && (
              <img
                src={config.logo}
                alt="Event Logo"
                className="w-10 h-10 object-contain rounded-lg"
              />
            )}

            <div>
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-white flex items-center gap-2">
                {config.title || 'Event Gallery'}
              </h1>
              {config.subtitle && (
                <p className="text-xs sm:text-sm text-neutral-400 mt-0.5 line-clamp-1">
                  {config.subtitle}
                </p>
              )}
            </div>
          </div>

          {/* Right: Badges and Search (only on grid view) */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between md:justify-end gap-2.5 sm:gap-3 w-full md:w-auto">
            {/* Stats Badges */}
            <div className="flex items-center gap-2 text-xs font-medium text-neutral-300 flex-shrink-0">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-neutral-900 border border-neutral-800 shadow-sm">
                <Users className="w-3.5 h-3.5 text-accent" />
                <span>{totalPeople} People</span>
              </span>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-neutral-900 border border-neutral-800 shadow-sm">
                <ImageIcon className="w-3.5 h-3.5 text-accent" />
                <span>{totalPhotos} Photos</span>
              </span>
            </div>

            {/* Search Bar - Responsive full width on mobile, w-64 on desktop, never clipped */}
            {activeView === 'grid' && (
              <div className="relative w-full sm:w-64 max-w-full">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400 pointer-events-none" />
                <input
                  type="text"
                  placeholder="Search person or ID..."
                  value={searchQuery}
                  onChange={(e) => onSearchChange(e.target.value)}
                  className="w-full box-border pl-9 pr-3.5 py-1.5 text-sm bg-neutral-900/90 text-neutral-100 placeholder-neutral-500 rounded-xl border border-neutral-800 focus:outline-none focus:border-accent focus:ring-1 focus:ring-accent transition-all"
                />
              </div>
            )}
          </div>

        </div>
      </div>
    </header>
  );
};

