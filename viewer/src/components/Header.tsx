import React from 'react';
import { ViewerConfig } from '../types';
import { Users, Image as ImageIcon, Search, ArrowLeft, X } from 'lucide-react';
import { BrandLogo } from './BrandLogo';

export type ViewerTheme = 't-dark' | 't-paper' | 't-navy';

interface HeaderProps {
  config: ViewerConfig;
  totalPeople: number;
  totalPhotos: number;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  activeView: 'grid' | 'person' | 'unrecognized';
  onBackToGrid: () => void;
  theme?: ViewerTheme;
  onThemeChange?: (newTheme: ViewerTheme) => void;
}

export const Header: React.FC<HeaderProps> = ({
  config,
  totalPeople,
  totalPhotos,
  searchQuery,
  onSearchChange,
  activeView,
  onBackToGrid,
  theme = 't-dark',
  onThemeChange = () => {},
}) => {
  return (
    <header className="sticky top-0 z-30 glass-nav transition-all duration-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          
          {/* Left: Brand Identity & Back Navigation */}
          <div className="flex items-center gap-3">
            {activeView !== 'grid' && (
              <button
                onClick={onBackToGrid}
                className="btn-tactile btn-sm"
                title="Back to all people"
                aria-label="Back to all people"
                style={{ padding: '8px 12px' }}
              >
                <ArrowLeft className="w-4 h-4" />
                <span className="hidden sm:inline">Back</span>
              </button>
            )}

            {/* Official CatLog Brand Logo & Title */}
            <BrandLogo
              title={config.title || 'CatLog'}
              subtitle={config.subtitle || 'Public Photo Gallery'}
              onClick={activeView !== 'grid' ? onBackToGrid : undefined}
            />
          </div>

          {/* Right: Stats Badges & Search */}
          <div className="flex flex-wrap items-center justify-between md:justify-end gap-2.5 w-full md:w-auto">
            {/* Stats Badges */}
            <div className="flex items-center gap-1.5 text-xs font-semibold text-[var(--text)]">
              <span className="badge-chip">
                <Users className="w-3.5 h-3.5 text-[var(--accent)]" />
                <span>{totalPeople} People</span>
              </span>
              <span className="badge-chip">
                <ImageIcon className="w-3.5 h-3.5 text-[var(--accent)]" />
                <span>{totalPhotos} Photos</span>
              </span>
            </div>

            {/* Search Input on Grid View */}
            {activeView === 'grid' && (
              <div className="relative w-full sm:w-56">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--muted)] pointer-events-none" />
                <input
                  type="text"
                  placeholder="Search people..."
                  value={searchQuery}
                  onChange={(e) => onSearchChange(e.target.value)}
                  className="w-full h-10 pl-9 pr-8 text-sm font-mono bg-[var(--input)] text-[var(--text)] placeholder-[var(--muted)] rounded-lg border-2 border-[var(--line)] focus:outline-none focus:border-[var(--accent)] shadow-[2px_2px_0px_var(--line)] transition-all"
                />
                {searchQuery && (
                  <button
                    onClick={() => onSearchChange('')}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[var(--muted)] hover:text-[var(--text)] p-0.5"
                    title="Clear search"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            )}
          </div>

        </div>
      </div>
    </header>
  );
};
export default Header;
