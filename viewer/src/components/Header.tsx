import React from 'react';
import { ViewerConfig } from '../types';
import { Users, Image as ImageIcon, Search, ArrowLeft, Sun, Moon, Compass } from 'lucide-react';

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
                className="touch-target p-2 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--bg-card-hover)] transition-colors focus:outline-none focus-visible:ring-2"
                title="Back to all people"
                aria-label="Back to all people"
              >
                <ArrowLeft className="w-5 h-5" />
              </button>
            )}

            {/* CatLog Brand Logo & Title */}
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-[var(--color-accent)] text-[var(--color-accent-text)] flex items-center justify-center font-bold text-base shadow-sm select-none">
                🐱
              </div>
              <div>
                <h1 className="text-lg sm:text-xl font-bold tracking-tight text-[var(--text-main)] flex items-center gap-2">
                  {config.title || 'CatLog Gallery'}
                </h1>
                {config.subtitle && (
                  <p className="text-xs text-[var(--text-muted)] line-clamp-1">
                    {config.subtitle}
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Right: Theme Switcher, Stats Badges & Search */}
          <div className="flex flex-wrap items-center justify-between md:justify-end gap-2.5 w-full md:w-auto">
            {/* Theme Selector (3 Themes: Dark, Paper, Navy) */}
            <div className="inline-flex items-center p-1 rounded-xl border border-[var(--border-color)] bg-[var(--bg-card)] gap-1" role="radiogroup" aria-label="Select theme">
              <button
                type="button"
                role="radio"
                aria-checked={theme === 't-dark'}
                onClick={() => onThemeChange('t-dark')}
                className={`touch-target px-2.5 py-1 text-xs font-medium rounded-lg transition-all ${
                  theme === 't-dark'
                    ? 'bg-[var(--color-accent)] text-[var(--color-accent-text)] shadow-sm'
                    : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'
                }`}
                title="Dark theme"
              >
                <Moon className="w-3.5 h-3.5 mr-1 inline" />
                <span>Dark</span>
              </button>

              <button
                type="button"
                role="radio"
                aria-checked={theme === 't-paper'}
                onClick={() => onThemeChange('t-paper')}
                className={`touch-target px-2.5 py-1 text-xs font-medium rounded-lg transition-all ${
                  theme === 't-paper'
                    ? 'bg-[var(--color-accent)] text-[var(--color-accent-text)] shadow-sm'
                    : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'
                }`}
                title="Paper theme"
              >
                <Sun className="w-3.5 h-3.5 mr-1 inline" />
                <span>Paper</span>
              </button>

              <button
                type="button"
                role="radio"
                aria-checked={theme === 't-navy'}
                onClick={() => onThemeChange('t-navy')}
                className={`touch-target px-2.5 py-1 text-xs font-medium rounded-lg transition-all ${
                  theme === 't-navy'
                    ? 'bg-[var(--color-accent)] text-[var(--color-accent-text)] shadow-sm'
                    : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'
                }`}
                title="Navy theme"
              >
                <Compass className="w-3.5 h-3.5 mr-1 inline" />
                <span>Navy</span>
              </button>
            </div>

            {/* Stats Badges */}
            <div className="flex items-center gap-1.5 text-xs font-semibold text-[var(--text-muted)]">
              <span className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)]">
                <Users className="w-3.5 h-3.5 text-[var(--color-accent)]" />
                <span>{totalPeople} People</span>
              </span>
              <span className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)]">
                <ImageIcon className="w-3.5 h-3.5 text-[var(--color-accent)]" />
                <span>{totalPhotos} Photos</span>
              </span>
            </div>

            {/* Search Input on Grid View */}
            {activeView === 'grid' && (
              <div className="relative w-full sm:w-56">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-dim)] pointer-events-none" />
                <input
                  type="text"
                  placeholder="Search..."
                  value={searchQuery}
                  onChange={(e) => onSearchChange(e.target.value)}
                  className="w-full h-11 pl-9 pr-3 text-sm bg-[var(--bg-card)] text-[var(--text-main)] placeholder-[var(--text-dim)] rounded-xl border border-[var(--border-color)] focus:outline-none focus:border-[var(--color-accent)] transition-all"
                />
              </div>
            )}
          </div>

        </div>
      </div>
    </header>
  );
};
export default Header;
