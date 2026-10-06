import React, { useState } from 'react';
import { api } from '../api/client';
import { Download, CheckCircle2, Folder, ExternalLink, Globe, Github, Sparkles, Layers } from 'lucide-react';

interface ExportScreenProps {
  initialTitle?: string;
  initialSubtitle?: string;
  onRefreshStats?: () => void;
}

export const ExportScreen: React.FC<ExportScreenProps> = ({
  initialTitle = 'Face Clubbing Gallery',
  initialSubtitle = 'Auto-sorted face albums and photo gallery',
  onRefreshStats,
}) => {
  const [outputDir, setOutputDir] = useState('export');
  const [title, setTitle] = useState(initialTitle);
  const [subtitle, setSubtitle] = useState(initialSubtitle);
  const [includeMaybe, setIncludeMaybe] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [exportResult, setExportResult] = useState<{
    success: boolean;
    output_dir: string;
    files_exported: string[];
    people_count: number;
    photos_count: number;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async () => {
    setIsExporting(true);
    setError(null);
    try {
      const res = await api.exportBundle({
        output_dir: outputDir.trim() || 'export',
        title: title.trim(),
        subtitle: subtitle.trim(),
        include_maybe: includeMaybe,
      });
      setExportResult(res);
      if (onRefreshStats) onRefreshStats();
    } catch (err: any) {
      setError(err.message || 'Export failed');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fadeIn pb-20">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white tracking-tight flex items-center gap-2.5">
          <Download className="w-6 h-6 text-accent" />
          Export Static Web Bundle
        </h2>
        <p className="text-sm text-neutral-400 mt-1">
          Export the finalized public gallery bundle. The bundle contains strictly static files (config.json, people.json, faces/, thumbs/) ready to be hosted on any static web host with zero backend dependencies.
        </p>
      </div>

      {/* Configuration Card */}
      <div className="glass-card p-6 rounded-2xl space-y-5">
        <h3 className="text-base font-semibold text-white">Bundle Configuration</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-1.5">
              Output Directory
            </label>
            <div className="relative">
              <Folder className="w-4 h-4 text-neutral-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                id="export-output-dir-input"
                type="text"
                value={outputDir}
                onChange={(e) => setOutputDir(e.target.value)}
                placeholder="export"
                className="w-full pl-10 pr-4 py-2.5 bg-neutral-900 border border-neutral-800 rounded-xl text-neutral-200 text-sm focus:outline-none focus:border-accent"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-1.5">
              Gallery Title
            </label>
            <input
              id="export-title-input"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-4 py-2.5 bg-neutral-900 border border-neutral-800 rounded-xl text-neutral-200 text-sm focus:outline-none focus:border-accent"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold uppercase tracking-wider text-neutral-400 mb-1.5">
            Gallery Subtitle
          </label>
          <input
            id="export-subtitle-input"
            type="text"
            value={subtitle}
            onChange={(e) => setSubtitle(e.target.value)}
            className="w-full px-4 py-2.5 bg-neutral-900 border border-neutral-800 rounded-xl text-neutral-200 text-sm focus:outline-none focus:border-accent"
          />
        </div>

        <div className="flex items-center gap-3 pt-2">
          <input
            id="export-include-maybe-toggle"
            type="checkbox"
            checked={includeMaybe}
            onChange={(e) => setIncludeMaybe(e.target.checked)}
            className="w-4 h-4 rounded border-neutral-700 bg-neutral-900 text-accent focus:ring-accent"
          />
          <label htmlFor="export-include-maybe-toggle" className="text-xs text-neutral-300 select-none">
            Include <span className="font-semibold text-amber-400">"Possible matches"</span> (distance 0.50 – 0.60) in the exported viewer bundle
          </label>
        </div>

        {error && (
          <div className="p-3.5 rounded-xl bg-red-950/60 border border-red-800 text-red-300 text-xs">
            {error}
          </div>
        )}

        <div className="pt-2">
          <button
            id="export-bundle-btn"
            disabled={isExporting}
            onClick={handleExport}
            className={`w-full py-3 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all shadow-lg ${
              isExporting
                ? 'bg-neutral-800 text-neutral-500 cursor-not-allowed'
                : 'bg-accent text-white hover:brightness-110 shadow-accent/20 cursor-pointer'
            }`}
          >
            <Download className="w-4 h-4" />
            <span>{isExporting ? 'Exporting Bundle...' : 'Export Public Bundle'}</span>
          </button>
        </div>
      </div>

      {/* Export Result Summary */}
      {exportResult && (
        <div id="export-success-summary" className="glass-card p-6 rounded-2xl space-y-4 border border-emerald-500/40 bg-emerald-950/20 animate-scaleUp">
          <div className="flex items-center gap-3 text-emerald-400">
            <CheckCircle2 className="w-6 h-6 flex-shrink-0" />
            <div>
              <h3 className="text-base font-semibold text-white">Bundle Exported Successfully</h3>
              <p className="text-xs text-neutral-300 mt-0.5 font-mono">
                Location: {exportResult.output_dir}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
            <div className="p-3 rounded-xl bg-neutral-900/80 border border-neutral-800 text-center">
              <span className="text-xs text-neutral-400">People</span>
              <p id="export-stat-people" className="text-lg font-bold text-white mt-0.5">{exportResult.people_count}</p>
            </div>
            <div className="p-3 rounded-xl bg-neutral-900/80 border border-neutral-800 text-center">
              <span className="text-xs text-neutral-400">Photos</span>
              <p id="export-stat-photos" className="text-lg font-bold text-white mt-0.5">{exportResult.photos_count}</p>
            </div>
            <div className="p-3 rounded-xl bg-neutral-900/80 border border-neutral-800 text-center">
              <span className="text-xs text-neutral-400">Bundle Files</span>
              <p id="export-stat-files" className="text-lg font-bold text-white mt-0.5">{exportResult.files_exported.length}</p>
            </div>
            <div className="p-3 rounded-xl bg-neutral-900/80 border border-neutral-800 text-center">
              <span className="text-xs text-neutral-400">Hygiene</span>
              <p className="text-xs font-semibold text-emerald-400 mt-1.5">Zero Private Files</p>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-neutral-900/90 border border-neutral-800">
            <p className="text-xs text-neutral-400 mb-1">Exported Assets in Bundle:</p>
            <div className="flex flex-wrap gap-2">
              {exportResult.files_exported.map((f) => (
                <span
                  key={f}
                  className="px-2.5 py-1 rounded-lg bg-neutral-800 text-neutral-200 text-xs font-mono border border-neutral-700"
                >
                  {f}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Deployment & Publishing Guides */}
      <div className="space-y-4">
        <h3 className="text-lg font-bold text-white">Publishing Guides</h3>

        {/* GitHub Pages Guide */}
        <div className="glass-card p-6 rounded-2xl space-y-3 border border-neutral-800">
          <div className="flex items-center gap-2.5 text-white font-semibold">
            <Github className="w-5 h-5 text-neutral-300" />
            <h4>Publish to GitHub Pages</h4>
          </div>
          <p className="text-xs text-neutral-400">
            Host the exported gallery for free on GitHub Pages directly from your repository:
          </p>
          <div className="p-3 rounded-xl bg-neutral-950 font-mono text-xs text-neutral-300 space-y-1.5 overflow-x-auto border border-neutral-800/80">
            <p className="text-neutral-500"># 1. Switch to the gh-pages branch (or create it)</p>
            <p>git checkout -b gh-pages</p>
            <p className="text-neutral-500"># 2. Copy the exported bundle and built viewer</p>
            <p>cp -r export/* .</p>
            <p>cp -r viewer/dist/* .</p>
            <p className="text-neutral-500"># 3. Commit and push</p>
            <p>git add . &amp;&amp; git commit -m "Deploy Face Clubbing gallery"</p>
            <p>git push origin gh-pages</p>
          </div>
          <p className="text-xs text-neutral-500">
            In repository settings under <strong>Pages</strong>, select branch <strong>gh-pages</strong> and folder <strong>/ (root)</strong>.
          </p>
        </div>

        {/* Cloudflare Pages Guide */}
        <div className="glass-card p-6 rounded-2xl space-y-3 border border-neutral-800">
          <div className="flex items-center gap-2.5 text-white font-semibold">
            <Globe className="w-5 h-5 text-amber-400" />
            <h4>Publish to Cloudflare Pages</h4>
          </div>
          <p className="text-xs text-neutral-400">
            Deploy with global CDN distribution and instant worldwide caching:
          </p>
          <div className="p-3 rounded-xl bg-neutral-950 font-mono text-xs text-neutral-300 space-y-1.5 overflow-x-auto border border-neutral-800/80">
            <p className="text-neutral-500"># Option A: Deploy directly via Wrangler CLI</p>
            <p>npx wrangler pages deploy export/ --project-name photo-sorter</p>
            <p className="text-neutral-500"># Option B: Direct Drag-and-Drop</p>
            <p className="text-neutral-400">
              Navigate to dashboard.cloudflare.com &gt; Workers &amp; Pages &gt; Create &gt; Pages &gt; Upload assets &gt; Drag and drop the <span className="text-white font-semibold">export/</span> folder.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
