import React from 'react';
import { ActiveTab } from '../types';
import {
  Users,
  FolderOpen,
  Activity,
  Download,
  Settings as SettingsIcon,
  RotateCcw,
  RefreshCw,
  CheckCircle2,
} from 'lucide-react';

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
}

export const Header: React.FC<HeaderProps> = ({
  activeTab,
  onTabChange,
  peopleCount,
  unrecFacesCount,
  unrecPhotosCount,
  clusteredFacesCount,
  totalFacesCount,
  appliedEditsCount,
  onUndo,
  onRefresh,
  isRefreshing,
}) => {
  const invariantHolds =
    totalFacesCount > 0
      ? clusteredFacesCount + unrecFacesCount === totalFacesCount
      : true;

  const tabs: Array<{ id: ActiveTab; label: string; icon: React.ReactNode }> = [
    { id: 'home', label: 'Home', icon: <FolderOpen className="w-4 h-4" /> },
    { id: 'progress', label: 'Progress', icon: <Activity className="w-4 h-4" /> },
    { id: 'people', label: 'Review People', icon: <Users className="w-4 h-4" /> },
    { id: 'export', label: 'Export', icon: <Download className="w-4 h-4" /> },
    { id: 'settings', label: 'Settings', icon: <SettingsIcon className="w-4 h-4" /> },
  ];

  return (
    <header className="sticky top-0 z-40 glass-nav border-b border-neutral-800/80 bg-neutral-950/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Title */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <Users className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="text-base font-bold text-white tracking-tight flex items-center gap-2">
                PhotoSorter <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-400 font-medium border border-blue-500/30">Organizer</span>
              </span>
              <p className="text-[11px] text-neutral-400 hidden sm:block">Event Face Clustering & Review</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex items-center space-x-1 sm:space-x-2">
            {tabs.map((tab) => {
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  id={`tab-${tab.id}`}
                  onClick={() => onTabChange(tab.id)}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30 shadow-sm'
                      : 'text-neutral-400 hover:text-neutral-200 hover:bg-neutral-900 border border-transparent'
                  }`}
                >
                  {tab.icon}
                  <span className="hidden md:inline">{tab.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Actions & Metrics */}
          <div className="flex items-center gap-2.5">
            {/* Quick Stats Pill */}
            <div className="hidden lg:flex items-center gap-3 px-3 py-1.5 rounded-lg bg-neutral-900/80 border border-neutral-800 text-xs">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                <span className="text-neutral-400">People:</span>
                <strong data-testid="header-people-count" className="text-neutral-200 font-mono">{peopleCount}</strong>
              </div>
              <span className="text-neutral-700">|</span>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                <span className="text-neutral-400">Unrecognized:</span>
                <strong data-testid="header-unrec-faces-count" className="text-neutral-200 font-mono">{unrecFacesCount}f</strong>
                <span className="text-neutral-500 font-mono">({unrecPhotosCount}p)</span>
              </div>
              {totalFacesCount > 0 && (
                <>
                  <span className="text-neutral-700">|</span>
                  <div className="flex items-center gap-1 text-[11px] text-neutral-400" title={`Invariant: ${clusteredFacesCount} clustered + ${unrecFacesCount} unrecognized = ${totalFacesCount} total`}>
                    <CheckCircle2 className={`w-3.5 h-3.5 ${invariantHolds ? 'text-emerald-500' : 'text-red-500'}`} />
                    <span className="font-mono">{clusteredFacesCount}+{unrecFacesCount}={totalFacesCount}</span>
                  </div>
                </>
              )}
            </div>

            {/* Undo Button */}
            <button
              id="header-undo-btn"
              data-testid="undo-btn"
              onClick={onUndo}
              disabled={appliedEditsCount === 0}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                appliedEditsCount > 0
                  ? 'bg-neutral-800 text-neutral-200 border-neutral-700 hover:bg-neutral-700 hover:border-neutral-600 shadow-sm cursor-pointer'
                  : 'bg-neutral-900/50 text-neutral-500 border-neutral-800/50 cursor-not-allowed opacity-60'
              }`}
              title={appliedEditsCount > 0 ? `Undo last edit (${appliedEditsCount} applied)` : 'No edits to undo'}
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Undo</span>
              {appliedEditsCount > 0 && (
                <span className="ml-0.5 px-1.5 py-0.2 rounded-full bg-blue-500/30 text-blue-300 text-[10px] font-mono">
                  {appliedEditsCount}
                </span>
              )}
            </button>

            {/* Refresh Button */}
            <button
              id="header-refresh-btn"
              data-testid="refresh-btn"
              onClick={onRefresh}
              disabled={isRefreshing}
              className="p-1.5 rounded-lg text-neutral-400 hover:text-neutral-200 hover:bg-neutral-900 border border-neutral-800 transition-colors"
              title="Refresh from API"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin text-blue-400' : ''}`} />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
