import React from 'react';
import { ActiveTab } from '../types';
import { Folder, Settings as SettingsIcon, RotateCcw, RefreshCw, Plus } from 'lucide-react';

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
}) => {
  return (
    <div className="hdr">
      {/* Brand Logo matching screenshot */}
      <div
        className="logo"
        onClick={() => onTabChange('home')}
        title="Organizer"
      >
        <img
          src={
            theme === 't-paper'
              ? '/textures/logo-paper.png?v=uncut-v6'
              : theme === 't-navy'
              ? '/textures/logo-navy.png?v=uncut-v6'
              : '/textures/logo-dark.png?v=uncut-v6'
          }
          alt="Organizer"
          className="logo-img"
        />
      </div>

      {/* Right Controls: 3 Theme Dots, Open Saved Project, Minimal Settings */}
      <div className="hdr-r">
        {onThemeChange && (
          <div className="themes" title="Select Theme (Dark, Paper, Navy)">
            <button
              type="button"
              onClick={(e) => onThemeChange('t-dark', e)}
              className={`sw s-dark ${theme === 't-dark' ? 'on' : ''}`}
              aria-label="Dark theme"
              title="Dark theme"
            />
            <button
              type="button"
              onClick={(e) => onThemeChange('t-paper', e)}
              className={`sw s-paper ${theme === 't-paper' ? 'on' : ''}`}
              aria-label="Paper theme"
              title="Paper theme"
            />
            <button
              type="button"
              onClick={(e) => onThemeChange('t-navy', e)}
              className={`sw s-navy ${theme === 't-navy' ? 'on' : ''}`}
              aria-label="Navy theme"
              title="Navy theme"
            />
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

        {/* Minimal Settings Icon */}
        <button
          id="header-settings-btn"
          data-testid="header-settings-btn"
          type="button"
          onClick={() => onTabChange('settings')}
          className={`icon-btn ${activeTab === 'settings' ? 'on' : ''}`}
          aria-label="Settings"
          title="Settings"
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
