import React, { useEffect, useState } from 'react';
import {
  X,
  HelpCircle,
  FolderArchive,
  HardDrive,
  Smartphone,
  FileCheck,
  Download,
  AlertTriangle,
  ExternalLink,
  CheckCircle2,
  Info,
} from 'lucide-react';

export interface InputGuidanceModalProps {
  isOpen: boolean;
  onClose: () => void;
  defaultTab?: 'photos' | 'drive' | 'phone' | 'formats';
  theme?: string;
}

export const InputGuidanceModal: React.FC<InputGuidanceModalProps> = ({
  isOpen,
  onClose,
  defaultTab = 'photos',
  theme = 't-dark',
}) => {
  const [activeTab, setActiveTab] = useState<'photos' | 'drive' | 'phone' | 'formats'>(defaultTab);

  useEffect(() => {
    setActiveTab(defaultTab);
  }, [defaultTab]);

  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in"
      role="dialog"
      aria-modal="true"
      aria-labelledby="input-guidance-title"
      data-testid="input-guidance-modal"
    >
      <div
        className="w-full max-w-3xl max-h-[90vh] bg-panel border border-border rounded-xl shadow-2xl flex flex-col overflow-hidden text-text"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-panel">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-accent/15 border border-accent/30 flex items-center justify-center text-accent">
              <HelpCircle className="w-5 h-5" />
            </div>
            <div>
              <h2
                id="input-guidance-title"
                data-testid="input-guidance-title"
                className="text-base font-semibold tracking-tight text-text"
              >
                How Do I Get My Photos In?
              </h2>
              <p className="text-xs text-muted">
                Step-by-step instructions for Google Drive, Google Photos, WhatsApp & phone exports
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            data-testid="btn-close-guidance"
            aria-label="Close"
            className="p-2 rounded-lg hover:bg-bg/60 text-muted hover:text-text transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-border bg-bg/40 px-6 gap-2 pt-2">
          <button
            type="button"
            data-testid="tab-photos"
            onClick={() => setActiveTab('photos')}
            className={`flex items-center gap-2 px-3 py-2.5 text-xs font-medium border-b-2 transition-all ${
              activeTab === 'photos'
                ? 'border-accent text-accent'
                : 'border-transparent text-muted hover:text-text'
            }`}
          >
            <Download className="w-4 h-4" />
            Google Photos
          </button>
          <button
            type="button"
            data-testid="tab-drive"
            onClick={() => setActiveTab('drive')}
            className={`flex items-center gap-2 px-3 py-2.5 text-xs font-medium border-b-2 transition-all ${
              activeTab === 'drive'
                ? 'border-accent text-accent'
                : 'border-transparent text-muted hover:text-text'
            }`}
          >
            <HardDrive className="w-4 h-4" />
            Google Drive
          </button>
          <button
            type="button"
            data-testid="tab-phone"
            onClick={() => setActiveTab('phone')}
            className={`flex items-center gap-2 px-3 py-2.5 text-xs font-medium border-b-2 transition-all ${
              activeTab === 'phone'
                ? 'border-accent text-accent'
                : 'border-transparent text-muted hover:text-text'
            }`}
          >
            <Smartphone className="w-4 h-4" />
            Phone & WhatsApp
          </button>
          <button
            type="button"
            data-testid="tab-formats"
            onClick={() => setActiveTab('formats')}
            className={`flex items-center gap-2 px-3 py-2.5 text-xs font-medium border-b-2 transition-all ${
              activeTab === 'formats'
                ? 'border-accent text-accent'
                : 'border-transparent text-muted hover:text-text'
            }`}
          >
            <FileCheck className="w-4 h-4" />
            Supported Formats
          </button>
        </div>

        {/* Content Body */}
        <div className="p-6 overflow-y-auto space-y-4 max-h-[calc(90vh-140px)] text-xs">
          {/* TAB 1: Google Photos */}
          {activeTab === 'photos' && (
            <div data-testid="section-photos" id="guidance-content-photos" className="space-y-4 animate-fade-in" data-content-tab="photos">
              <div className="p-3.5 rounded-lg border border-amber-500/30 bg-amber-500/10 flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <h3 className="font-semibold text-amber-400 text-xs">
                    Google Photos Links Cannot Be Scanned Directly
                  </h3>
                  <p className="text-muted leading-relaxed">
                    Under Google's Photos Library API policy (updated March 2025), third-party applications
                    are prohibited from reading photo album contents via shared URL or API unless the album was
                    created by the app itself.
                  </p>
                </div>
              </div>

              <div className="space-y-3">
                <h4 className="text-sm font-semibold text-text">How to Export and Import in 3 Easy Steps:</h4>

                <div className="grid gap-3">
                  <div className="p-3.5 rounded-lg border border-border bg-bg/50 flex items-start gap-3">
                    <span className="w-6 h-6 rounded-full bg-accent/20 text-accent font-bold flex items-center justify-center shrink-0 text-xs">
                      1
                    </span>
                    <div className="space-y-1">
                      <p className="font-medium text-text">Open your album in Google Photos</p>
                      <p className="text-muted">
                        Go to <span className="font-mono text-accent">photos.google.com</span> in your computer's browser
                        and open the album or event you want to sort.
                      </p>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-lg border border-border bg-bg/50 flex items-start gap-3">
                    <span className="w-6 h-6 rounded-full bg-accent/20 text-accent font-bold flex items-center justify-center shrink-0 text-xs">
                      2
                    </span>
                    <div className="space-y-1">
                      <p className="font-medium text-text">Download all photos as a ZIP archive</p>
                      <p className="text-muted">
                        Click the <span className="font-semibold text-text">three dots (⋮)</span> in the top-right corner
                        and choose <span className="font-semibold text-text">"Download all"</span> (or press <kbd className="px-1.5 py-0.5 rounded bg-panel border border-border font-mono">Shift + D</kbd>).
                        Google Photos will bundle all full-resolution photos into a ZIP archive.
                      </p>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-lg border border-border bg-bg/50 flex items-start gap-3">
                    <span className="w-6 h-6 rounded-full bg-accent/20 text-accent font-bold flex items-center justify-center shrink-0 text-xs">
                      3
                    </span>
                    <div className="space-y-1">
                      <p className="font-medium text-text">Select the ZIP file in CatLog</p>
                      <p className="text-muted">
                        On the Home Screen or in Add Source, choose <span className="font-semibold text-text">"Folder or Zip"</span>,
                        select the downloaded <span className="font-mono text-accent">.zip</span> file, and click <span className="font-semibold text-text">Process Photos</span>.
                        CatLog will automatically unpack, index, and cluster all faces!
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="p-3 rounded-lg border border-border bg-panel flex items-center gap-2 text-muted">
                <Info className="w-4 h-4 text-accent shrink-0" />
                <span>
                  Tip: If your album is over 5GB, Google Photos or Takeout splits it into multiple ZIP files. You can add each ZIP as a source in CatLog!
                </span>
              </div>
            </div>
          )}

          {/* TAB 2: Google Drive */}
          {activeTab === 'drive' && (
            <div data-testid="section-drive" className="space-y-4 animate-fade-in">
              <div className="space-y-2">
                <h4 className="text-sm font-semibold text-text">Google Drive Folder Import</h4>
                <p className="text-muted leading-relaxed">
                  CatLog supports direct Google Drive folder scanning using public links or an optional API key.
                </p>
              </div>

              <div className="grid gap-3">
                <div className="p-3.5 rounded-lg border border-border bg-bg/50 space-y-1.5">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span className="font-medium text-text">1. Ensure Link Sharing is Enabled</span>
                  </div>
                  <p className="text-muted pl-6">
                    In Google Drive, right-click your photo folder &rarr; click <span className="font-semibold text-text">Share</span> &rarr;
                    set General access to <span className="font-semibold text-text">"Anyone with the link can view"</span>.
                  </p>
                </div>

                <div className="p-3.5 rounded-lg border border-border bg-bg/50 space-y-1.5">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span className="font-medium text-text">2. Copy & Paste the Folder URL</span>
                  </div>
                  <p className="text-muted pl-6">
                    Copy the link (e.g. <span className="font-mono text-accent">https://drive.google.com/drive/folders/1A2b3C...</span>)
                    and paste it into the Drive tab on CatLog. CatLog verifies public access immediately.
                  </p>
                </div>

                <div className="p-3.5 rounded-lg border border-border bg-bg/50 space-y-1.5">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span className="font-medium text-text">3. Google Drive Image Quality Presets</span>
                  </div>
                  <p className="text-muted pl-6">
                    In Settings, choose between <span className="font-semibold text-text">Fast</span> (quick thumbnails),
                    <span className="font-semibold text-text"> Better</span> (balanced 1600px), or
                    <span className="font-semibold text-text"> Best</span> (full original resolution).
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: Phone & WhatsApp */}
          {activeTab === 'phone' && (
            <div data-testid="section-phone" className="space-y-4 animate-fade-in">
              <div className="space-y-2">
                <h4 className="text-sm font-semibold text-text">Importing from WhatsApp & Phone Backups</h4>
                <p className="text-muted leading-relaxed">
                  CatLog features automatic nested archive extraction — perfect for WhatsApp chat exports and multi-folder phone backups.
                </p>
              </div>

              <div className="grid gap-3">
                <div className="p-3.5 rounded-lg border border-border bg-bg/50 space-y-2">
                  <div className="flex items-center gap-2">
                    <FolderArchive className="w-4 h-4 text-accent" />
                    <span className="font-semibold text-text">WhatsApp Chat Export</span>
                  </div>
                  <p className="text-muted leading-relaxed">
                    1. On your phone, open the WhatsApp chat or group &rarr; tap the contact/group name at top.
                    <br />
                    2. Scroll down and tap <span className="font-semibold text-text">Export Chat</span> &rarr; choose <span className="font-semibold text-text">Attach Media</span>.
                    <br />
                    3. Send or AirDrop the generated <span className="font-mono text-accent">WhatsApp Chat - Group.zip</span> to your computer.
                    <br />
                    4. Select the ZIP in CatLog. CatLog automatically unpacks any nested media archives (such as internal <span className="font-mono text-accent">Media.zip</span>) and catalogs every photo!
                  </p>
                </div>

                <div className="p-3.5 rounded-lg border border-border bg-bg/50 space-y-2">
                  <div className="flex items-center gap-2">
                    <Smartphone className="w-4 h-4 text-accent" />
                    <span className="font-semibold text-text">iPhone (AirDrop / Cable)</span>
                  </div>
                  <p className="text-muted leading-relaxed">
                    AirDrop selected event photos directly to your Mac Downloads folder, or connect via USB and use the Photos or Image Capture app.
                    Point CatLog to the folder containing your photos.
                  </p>
                </div>

                <div className="p-3.5 rounded-lg border border-border bg-bg/50 space-y-2">
                  <div className="flex items-center gap-2">
                    <Smartphone className="w-4 h-4 text-accent" />
                    <span className="font-semibold text-text">Android (USB / Google Drive)</span>
                  </div>
                  <p className="text-muted leading-relaxed">
                    Connect your Android phone via USB in <span className="font-semibold text-text">File Transfer</span> mode and select your <span className="font-mono text-accent">DCIM/Camera</span> folder, or upload the photos to Google Drive.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: Supported Formats */}
          {activeTab === 'formats' && (
            <div data-testid="section-formats" className="space-y-4 animate-fade-in">
              <div className="space-y-2">
                <h4 className="text-sm font-semibold text-text">Supported Image Formats & Non-Image Handling</h4>
                <p className="text-muted leading-relaxed">
                  CatLog supports all standard and modern mobile camera image formats with native HEIC/HEIF decoding.
                </p>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                {[
                  { ext: '.JPG / .JPEG', desc: 'Standard JPEG' },
                  { ext: '.PNG', desc: 'Lossless PNG' },
                  { ext: '.WEBP', desc: 'Modern WebP' },
                  { ext: '.HEIC / .HEIF', desc: 'Apple High-Efficiency' },
                  { ext: '.BMP', desc: 'Bitmap' },
                  { ext: '.TIFF / .TIF', desc: 'High-Bit TIFF' },
                  { ext: '.ZIP', desc: 'Direct Archive' },
                  { ext: 'Nested ZIP', desc: 'WhatsApp & Takeout' },
                ].map((item) => (
                  <div key={item.ext} className="p-3 rounded-lg border border-border bg-bg/50 text-center space-y-1">
                    <span className="font-mono font-bold text-accent text-xs">{item.ext}</span>
                    <p className="text-[12px] text-muted">{item.desc}</p>
                  </div>
                ))}
              </div>

              <div className="p-3.5 rounded-lg border border-border bg-panel space-y-2">
                <div className="flex items-center gap-2">
                  <Info className="w-4 h-4 text-accent" />
                  <span className="font-semibold text-text">Safe Skipping of Non-Image Files</span>
                </div>
                <p className="text-muted leading-relaxed">
                  If your folder or ZIP includes videos (<span className="font-mono">.mp4</span>, <span className="font-mono">.mov</span>, <span className="font-mono">.avi</span>), documents (<span className="font-mono">.pdf</span>, <span className="font-mono">.docx</span>), or text files, CatLog <span className="font-semibold text-text">safely skips them</span> without interrupting or failing the scan.
                  All skipped non-image files are tallied and reported transparently by count and extension in your scan summary and <span className="font-mono">manifest.json</span>.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 border-t border-border bg-panel flex items-center justify-between">
          <span className="text-xs text-muted">
            CatLog Engine &bull; Safe, Local, Privacy-First Photo Clustering
          </span>
          <button
            type="button"
            data-testid="btn-guidance-got-it"
            id="btn-guidance-got-it"
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-accent text-white font-medium text-xs hover:bg-accent/90 transition-colors shadow-sm"
          >
            Got It
          </button>
        </div>
      </div>
    </div>
  );
};
