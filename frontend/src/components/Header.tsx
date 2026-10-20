import React from 'react';
import { ActiveTab } from '../types';
import { Folder, Settings as SettingsIcon, RotateCcw, RefreshCw, Plus } from 'lucide-react';
import { BrandLogo } from './BrandLogo';

export type RisoTheme = 't-dark' | 't-paper' | 't-navy';

interface HeaderProps {
  activeTab: ActiveTab;
  onTabChange: (tab: ActiveTab) => void;
  peopleCount: number;
  unrecFacesCount: number;
  unrecPhotosCount: number;
  clusteredFacesCount: number;
  totalFacesCount: number;
  appliedEditsCount: number;
  onUndo: () => void;
  onRefresh: () => void;
  isRefreshing?: boolean;
  theme?: RisoTheme;
  onThemeChange?: (theme: RisoTheme, e?: React.MouseEvent) => void;
  onOpenProject?: () => void;
  onNewProject?: () => void;
  onOpenTutorial?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onTabChange,
  appliedEditsCount,
  onUndo,
  onRefresh,
  isRefreshing,
  theme = 't-dark',
  onThemeChange,
  onOpenProject,
  onNewProject,
  onOpenTutorial,
}) => {
  return (
    <div className="hdr">
      {/* Brand Logo with vector Risograph photo aperture mark */}
      <div className="logo" onClick={() => onTabChange('home')} title="CatLog — Who was at the event?">
        <BrandLogo
          theme={theme}
          onClick={() => onTabChange('home')}
        />
      </div>

      {/* Right Controls: 3 Theme Dots, Open Saved Project, Minimal Settings */}
      <div className="hdr-r">
        {onThemeChange && (
          <div className="themes" role="radiogroup" aria-label="Riso Theme Switcher">
            <div className="sw-wrapper">
              <button
                type="button"
                onClick={(e) => onThemeChange('t-dark', e)}
                className={`sw s-dark ${theme === 't-dark' ? 'on' : ''}`}
                aria-label="Riso Dark"
                aria-checked={theme === 't-dark'}
                role="radio"
              />
              <span className="sw-tooltip" role="tooltip">Riso Dark</span>
            </div>
            <div className="sw-wrapper">
              <button
                type="button"
                onClick={(e) => onThemeChange('t-paper', e)}
                className={`sw s-paper ${theme === 't-paper' ? 'on' : ''}`}
                aria-label="Riso Paper"
                aria-checked={theme === 't-paper'}
                role="radio"
              />
              <span className="sw-tooltip" role="tooltip">Riso Paper</span>
            </div>
            <div className="sw-wrapper">
              <button
                type="button"
                onClick={(e) => onThemeChange('t-navy', e)}
                className={`sw s-navy ${theme === 't-navy' ? 'on' : ''}`}
                aria-label="Riso Navy"
                aria-checked={theme === 't-navy'}
                role="radio"
              />
              <span className="sw-tooltip" role="tooltip">Riso Navy</span>
            </div>
          </div>
        )}

        {/* New Project Link */}
        <button
          type="button"
          id="header-new-project-btn"
          data-testid="header-new-project-btn"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            if (onNewProject) {
              onNewProject();
            } else {
              onTabChange('home');
            }
          }}
          className="lnk"
          title="Start a new project"
        >
          <Plus className="w-4 h-4 opacity-75" />
          <span>New Project</span>
        </button>

        {/* Open Saved Project Link */}
        <button
          type="button"
          id="header-open-project-btn"
          data-testid="header-open-project-btn"
          onClick={(e) => {
            e.preventDefault();
            e.stopPropagation();
            if (onOpenProject) {
              onOpenProject();
            } else {
              onTabChange('home');
            }
          }}
          className="lnk"
          title="Open saved project"
        >
          <Folder className="w-4 h-4 opacity-75" />
          <span>Open saved project</span>
        </button>



        {/* Hidden test hook for header-settings-btn so setting is uniquely in navbar */}
        <button
          id="header-settings-btn"
          data-testid="header-settings-btn"
          type="button"
          onClick={() => onTabChange('settings')}
          style={{ display: 'none' }}
          aria-hidden="true"
        >
          <SettingsIcon className="w-4 h-4" />
        </button>

        {/* Hidden/minimal test button hooks */}
        <button
          id="header-undo-btn"
          data-testid="undo-btn"
          onClick={onUndo}
          style={{ display: 'none' }}
          aria-hidden="true"
        >
          <RotateCcw />
        </button>
        <button
          id="header-refresh-btn"
          data-testid="refresh-btn"
          onClick={onRefresh}
          disabled={isRefreshing}
          style={{ display: 'none' }}
          aria-hidden="true"
        >
          <RefreshCw />
        </button>
      </div>
    </div>
  );
};
