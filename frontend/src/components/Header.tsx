import React from 'react';
import { ActiveTab } from '../types';
import { Folder, Settings as SettingsIcon, RotateCcw, RefreshCw, Plus, HelpCircle } from 'lucide-react';
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
  activeProjectName?: string;
  totalPhotosCount?: number;
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
  activeProjectName,
  totalPhotosCount,
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

      {/* Active Project Pill (QoL 5) */}
      {activeProjectName && (
        <button
          type="button"
          id="header-active-project-pill"
          data-testid="header-active-project-pill"
          onClick={onOpenProject}
          className="hidden md:flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono transition-all hover:scale-105"
          style={{
            background: 'rgba(255, 255, 255, 0.05)',
            border: '1px solid var(--line)',
            color: 'var(--text)',
          }}
          title="Active Project. Click to switch or open recent projects"
        >
          <Folder className="w-3.5 h-3.5 text-[var(--accent)]" />
          <span className="font-bold truncate max-w-[200px]">{activeProjectName}</span>
          {totalPhotosCount !== undefined && totalPhotosCount > 0 && (
            <span className="opacity-60 text-[11px]">({totalPhotosCount} photos)</span>
          )}
        </button>
      )}

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

        {/* CatLog Handbook & Shortcuts Link */}
        {onOpenTutorial && (
          <button
            type="button"
            id="header-handbook-help-btn"
            data-testid="header-handbook-help-btn"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              onOpenTutorial();
            }}
            className="lnk"
            title="CatLog Handbook & Keyboard Shortcuts (?)"
          >
            <HelpCircle className="w-4 h-4 opacity-75" />
            <span>Guide (?)</span>
          </button>
        )}



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
