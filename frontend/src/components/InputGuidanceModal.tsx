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
      className={`fixed inset-0 z-50 flex items-center justify-center p-4 ${theme}`}
      style={{
        background: 'rgba(0, 0, 0, 0.70)',
        backdropFilter: 'blur(6px)',
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="input-guidance-title"
      data-testid="input-guidance-modal"
      onClick={onClose}
    >
      <div
        className="w-full max-w-3xl max-h-[90vh] rounded-xl shadow-2xl flex flex-col overflow-hidden"
        style={{
          background: 'var(--bg)',
          color: 'var(--text)',
          border: '2px solid var(--line)',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.75), 4px 4px 0px var(--line)',
          fontFamily: 'inherit',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-6 py-4"
          style={{
            background: 'var(--panel)',
            borderBottom: '1.5px solid var(--line)',
          }}
        >
          <div className="flex items-center gap-3">
            <div
              className="w-9 h-9 rounded-lg flex items-center justify-center"
              style={{
                background: 'rgba(250, 113, 117, 0.15)',
                border: '1.5px solid var(--accent)',
                color: 'var(--accent)',
              }}
            >
              <HelpCircle className="w-5 h-5" />
            </div>
            <div>
              <h2
                id="input-guidance-title"
                data-testid="input-guidance-title"
                className="text-base font-bold tracking-tight"
                style={{ color: 'var(--text)' }}
              >
                How Do I Get My Photos In?
              </h2>
              <p className="text-xs" style={{ color: 'var(--muted)' }}>
                Step-by-step instructions for Google Drive, Google Photos, WhatsApp &amp; phone exports
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            data-testid="btn-close-guidance"
            aria-label="Close"
            className="p-1.5 rounded-lg transition-colors"
            style={{
              color: 'var(--muted)',
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
            }}
          >
            <X className="w-5 h-5 hover:opacity-80" />
          </button>
        </div>

        {/* Tab Navigation */}
        <div
          className="flex px-6 gap-2 pt-2"
          style={{
            background: 'rgba(0, 0, 0, 0.05)',
            borderBottom: '1.5px solid var(--line)',
          }}
        >
          <button
            type="button"
            data-testid="tab-photos"
            onClick={() => setActiveTab('photos')}
            className="flex items-center gap-2 px-3 py-2.5 text-xs font-semibold transition-all"
            style={{
              borderBottom: activeTab === 'photos' ? '2.5px solid var(--accent)' : '2.5px solid transparent',
              color: activeTab === 'photos' ? 'var(--accent)' : 'var(--muted)',
              background: 'none',
              cursor: 'pointer',
            }}
          >
            <Download className="w-4 h-4" />
            <span>Google Photos</span>
          </button>
          <button
            type="button"
            data-testid="tab-drive"
            onClick={() => setActiveTab('drive')}
            className="flex items-center gap-2 px-3 py-2.5 text-xs font-semibold transition-all"
            style={{
              borderBottom: activeTab === 'drive' ? '2.5px solid var(--accent)' : '2.5px solid transparent',
              color: activeTab === 'drive' ? 'var(--accent)' : 'var(--muted)',
              background: 'none',
              cursor: 'pointer',
            }}
          >
            <HardDrive className="w-4 h-4" />
            <span>Google Drive</span>
          </button>
          <button
            type="button"
            data-testid="tab-phone"
            onClick={() => setActiveTab('phone')}
            className="flex items-center gap-2 px-3 py-2.5 text-xs font-semibold transition-all"
            style={{
              borderBottom: activeTab === 'phone' ? '2.5px solid var(--accent)' : '2.5px solid transparent',
              color: activeTab === 'phone' ? 'var(--accent)' : 'var(--muted)',
              background: 'none',
              cursor: 'pointer',
            }}
          >
            <Smartphone className="w-4 h-4" />
            <span>Phone &amp; WhatsApp</span>
          </button>
          <button
            type="button"
            data-testid="tab-formats"
            onClick={() => setActiveTab('formats')}
            className="flex items-center gap-2 px-3 py-2.5 text-xs font-semibold transition-all"
            style={{
              borderBottom: activeTab === 'formats' ? '2.5px solid var(--accent)' : '2.5px solid transparent',
              color: activeTab === 'formats' ? 'var(--accent)' : 'var(--muted)',
              background: 'none',
              cursor: 'pointer',
            }}
          >
            <FileCheck className="w-4 h-4" />
            <span>Supported Formats</span>
          </button>
        </div>

        {/* Content Body */}
        <div
          className="p-6 overflow-y-auto space-y-4 max-h-[calc(90vh-140px)] text-xs"
          style={{ background: 'var(--bg)', color: 'var(--text)' }}
        >
          {/* TAB 1: Google Photos */}
          {activeTab === 'photos' && (
            <div data-testid="section-photos" id="guidance-content-photos" className="space-y-4" data-content-tab="photos">
              <div
                className="p-4 rounded-lg flex items-start gap-3"
                style={{
                  background: 'rgba(245, 158, 11, 0.12)',
                  border: '1.5px solid #f59e0b',
                }}
              >
                <AlertTriangle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <h3 className="font-bold text-xs" style={{ color: '#d97706' }}>
                    Google Photos Links Cannot Be Scanned Directly
                  </h3>
                  <p className="leading-relaxed" style={{ color: 'var(--text)', opacity: 0.95 }}>
                    Under Google&apos;s Photos Library API policy (updated March 2025), third-party applications
                    are prohibited from reading photo album contents via shared URL or API unless the album was
                    created by the app itself.
                  </p>
                </div>
              </div>

              <div className="space-y-3">
                <h4 className="text-sm font-bold" style={{ color: 'var(--text)' }}>
                  How to Export and Import in 3 Easy Steps:
                </h4>

                <div className="grid gap-3">
                  <div
                    className="p-3.5 rounded-lg flex items-start gap-3"
                    style={{
                      background: 'var(--panel)',
                      border: '1.5px solid var(--line)',
                    }}
                  >
                    <span
                      className="w-6 h-6 rounded-full font-bold flex items-center justify-center shrink-0 text-xs"
                      style={{
                        background: 'var(--accent)',
                        color: 'var(--on-accent, #ffffff)',
                      }}
                    >
                      1
                    </span>
                    <div className="space-y-1">
                      <p className="font-bold text-sm" style={{ color: 'var(--text)' }}>
                        Open your album in Google Photos
                      </p>
                      <p style={{ color: 'var(--muted)', lineHeight: 1.5 }}>
                        Go to <span className="font-mono font-semibold" style={{ color: 'var(--accent)' }}>photos.google.com</span> in your computer&apos;s browser
                        and open the album or event you want to sort.
                      </p>
                    </div>
                  </div>

                  <div
                    className="p-3.5 rounded-lg flex items-start gap-3"
                    style={{
                      background: 'var(--panel)',
                      border: '1.5px solid var(--line)',
                    }}
                  >
                    <span
                      className="w-6 h-6 rounded-full font-bold flex items-center justify-center shrink-0 text-xs"
                      style={{
                        background: 'var(--accent)',
                        color: 'var(--on-accent, #ffffff)',
                      }}
                    >
                      2
                    </span>
                    <div className="space-y-1">
                      <p className="font-bold text-sm" style={{ color: 'var(--text)' }}>
                        Download all photos as a ZIP archive
                      </p>
                      <p style={{ color: 'var(--muted)', lineHeight: 1.5 }}>
                        Click the <span className="font-bold" style={{ color: 'var(--text)' }}>three dots (⋮)</span> in the top-right corner
                        and choose <span className="font-bold" style={{ color: 'var(--text)' }}>&quot;Download all&quot;</span> (or press <kbd
                          style={{
                            background: 'var(--bg)',
                            border: '1.5px solid var(--line)',
                            color: 'var(--text)',
                            padding: '2px 6px',
                            borderRadius: '4px',
                            fontFamily: 'monospace',
                            fontWeight: 700,
                          }}
                        >Shift + D</kbd>).
                        Google Photos will bundle all full-resolution photos into a ZIP archive.
                      </p>
                    </div>
                  </div>

                  <div
                    className="p-3.5 rounded-lg flex items-start gap-3"
                    style={{
                      background: 'var(--panel)',
                      border: '1.5px solid var(--line)',
                    }}
                  >
                    <span
                      className="w-6 h-6 rounded-full font-bold flex items-center justify-center shrink-0 text-xs"
                      style={{
                        background: 'var(--accent)',
                        color: 'var(--on-accent, #ffffff)',
                      }}
                    >
                      3
                    </span>
                    <div className="space-y-1">
                      <p className="font-bold text-sm" style={{ color: 'var(--text)' }}>
                        Select the ZIP file in CatLog
                      </p>
                      <p style={{ color: 'var(--muted)', lineHeight: 1.5 }}>
                        On the Home Screen or in Add Source, choose <span className="font-bold" style={{ color: 'var(--text)' }}>&quot;Folder or Zip&quot;</span>,
                        select the downloaded <span className="font-mono font-semibold" style={{ color: 'var(--accent)' }}>.zip</span> file, and click <span className="font-bold" style={{ color: 'var(--text)' }}>Process Photos</span>.
                        CatLog will automatically unpack, index, and cluster all faces!
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              <div
                className="p-3 rounded-lg flex items-center gap-2"
                style={{
                  background: 'var(--panel)',
                  border: '1.5px solid var(--line)',
                  color: 'var(--muted)',
                }}
              >
                <Info className="w-4 h-4 shrink-0" style={{ color: 'var(--accent)' }} />
                <span>
                  Tip: If your album is over 5GB, Google Photos or Takeout splits it into multiple ZIP files. You can add each ZIP as a source in CatLog!
                </span>
              </div>
            </div>
          )}

          {/* TAB 2: Google Drive */}
          {activeTab === 'drive' && (
            <div data-testid="section-drive" className="space-y-4">
              <div className="space-y-2">
                <h4 className="text-sm font-bold" style={{ color: 'var(--text)' }}>
                  Google Drive Folder Import
                </h4>
                <p className="leading-relaxed" style={{ color: 'var(--muted)' }}>
                  CatLog supports direct Google Drive folder scanning using public links or an optional API key.
                </p>
              </div>

              <div className="grid gap-3">
                <div
                  className="p-3.5 rounded-lg space-y-1.5"
                  style={{
                    background: 'var(--panel)',
                    border: '1.5px solid var(--line)',
                  }}
                >
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span className="font-bold" style={{ color: 'var(--text)' }}>1. Ensure Link Sharing is Enabled</span>
                  </div>
                  <p className="pl-6" style={{ color: 'var(--muted)', lineHeight: 1.5 }}>
                    In Google Drive, right-click your photo folder &rarr; click <span className="font-bold" style={{ color: 'var(--text)' }}>Share</span> &rarr;
                    set General access to <span className="font-bold" style={{ color: 'var(--text)' }}>&quot;Anyone with the link can view&quot;</span>.
                  </p>
                </div>

                <div
                  className="p-3.5 rounded-lg space-y-1.5"
                  style={{
                    background: 'var(--panel)',
                    border: '1.5px solid var(--line)',
                  }}
                >
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span className="font-bold" style={{ color: 'var(--text)' }}>2. Copy &amp; Paste the Folder URL</span>
                  </div>
                  <p className="pl-6" style={{ color: 'var(--muted)', lineHeight: 1.5 }}>
                    Copy the link (e.g. <span className="font-mono font-semibold" style={{ color: 'var(--accent)' }}>https://drive.google.com/drive/folders/1A2b3C...</span>)
                    and paste it into the Drive tab on CatLog. CatLog verifies public access immediately.
                  </p>
                </div>

                <div
                  className="p-3.5 rounded-lg space-y-1.5"
                  style={{
                    background: 'var(--panel)',
                    border: '1.5px solid var(--line)',
                  }}
                >
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span className="font-bold" style={{ color: 'var(--text)' }}>3. Google Drive Image Quality Presets</span>
                  </div>
                  <p className="pl-6" style={{ color: 'var(--muted)', lineHeight: 1.5 }}>
                    CatLog defaults to <span className="font-bold" style={{ color: 'var(--text)' }}>Original</span> (full camera resolution), with options for
                    <span className="font-bold" style={{ color: 'var(--text)' }}> Best</span> (2000px),
                    <span className="font-bold" style={{ color: 'var(--text)' }}> Better</span> (1600px), or
                    <span className="font-bold" style={{ color: 'var(--text)' }}> Fast</span> (1000px).
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: Phone & WhatsApp */}
          {activeTab === 'phone' && (
            <div data-testid="section-phone" className="space-y-4">
              <div className="space-y-2">
                <h4 className="text-sm font-bold" style={{ color: 'var(--text)' }}>
                  Importing from WhatsApp &amp; Phone Backups
                </h4>
                <p className="leading-relaxed" style={{ color: 'var(--muted)' }}>
                  CatLog features automatic nested archive extraction — perfect for WhatsApp chat exports and multi-folder phone backups.
                </p>
              </div>

              <div className="grid gap-3">
                <div
                  className="p-3.5 rounded-lg space-y-2"
                  style={{
                    background: 'var(--panel)',
                    border: '1.5px solid var(--line)',
                  }}
                >
                  <div className="flex items-center gap-2">
                    <FolderArchive className="w-4 h-4" style={{ color: 'var(--accent)' }} />
                    <span className="font-bold" style={{ color: 'var(--text)' }}>WhatsApp Chat Export</span>
                  </div>
                  <p className="leading-relaxed" style={{ color: 'var(--muted)' }}>
                    1. On your phone, open the WhatsApp chat or group &rarr; tap the contact/group name at top.
                    <br />
                    2. Scroll down and tap <span className="font-bold" style={{ color: 'var(--text)' }}>Export Chat</span> &rarr; choose <span className="font-bold" style={{ color: 'var(--text)' }}>Attach Media</span>.
                    <br />
                    3. Send or AirDrop the generated <span className="font-mono font-semibold" style={{ color: 'var(--accent)' }}>WhatsApp Chat - Group.zip</span> to your computer.
                    <br />
                    4. Select the ZIP in CatLog. CatLog automatically unpacks any nested media archives (such as internal <span className="font-mono font-semibold" style={{ color: 'var(--accent)' }}>Media.zip</span>) and catalogs every photo!
                  </p>
                </div>

                <div
                  className="p-3.5 rounded-lg space-y-2"
                  style={{
                    background: 'var(--panel)',
                    border: '1.5px solid var(--line)',
                  }}
                >
                  <div className="flex items-center gap-2">
                    <Smartphone className="w-4 h-4" style={{ color: 'var(--accent)' }} />
                    <span className="font-bold" style={{ color: 'var(--text)' }}>iPhone (AirDrop / Cable)</span>
                  </div>
                  <p className="leading-relaxed" style={{ color: 'var(--muted)' }}>
                    AirDrop selected event photos directly to your computer Downloads folder, or connect via USB and export from the Photos app.
                    Select the folder in CatLog.
                  </p>
                </div>

                <div
                  className="p-3.5 rounded-lg space-y-2"
                  style={{
                    background: 'var(--panel)',
                    border: '1.5px solid var(--line)',
                  }}
                >
                  <div className="flex items-center gap-2">
                    <Smartphone className="w-4 h-4" style={{ color: 'var(--accent)' }} />
                    <span className="font-bold" style={{ color: 'var(--text)' }}>Android (USB / Google Drive)</span>
                  </div>
                  <p className="leading-relaxed" style={{ color: 'var(--muted)' }}>
                    Connect your Android phone via USB in <span className="font-bold" style={{ color: 'var(--text)' }}>File Transfer</span> mode and select your <span className="font-mono font-semibold" style={{ color: 'var(--accent)' }}>DCIM/Camera</span> folder, or upload the photos to Google Drive.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: Supported Formats */}
          {activeTab === 'formats' && (
            <div data-testid="section-formats" className="space-y-4">
              <div className="space-y-2">
                <h4 className="text-sm font-bold" style={{ color: 'var(--text)' }}>
                  Supported Image Formats &amp; Non-Image Handling
                </h4>
                <p className="leading-relaxed" style={{ color: 'var(--muted)' }}>
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
                  <div
                    key={item.ext}
                    className="p-3 rounded-lg text-center space-y-1"
                    style={{
                      background: 'var(--panel)',
                      border: '1.5px solid var(--line)',
                    }}
                  >
                    <span className="font-mono font-bold text-xs" style={{ color: 'var(--accent)' }}>{item.ext}</span>
                    <p className="text-[12px]" style={{ color: 'var(--muted)' }}>{item.desc}</p>
                  </div>
                ))}
              </div>

              <div
                className="p-3.5 rounded-lg space-y-2"
                style={{
                  background: 'var(--panel)',
                  border: '1.5px solid var(--line)',
                }}
              >
                <div className="flex items-center gap-2">
                  <Info className="w-4 h-4" style={{ color: 'var(--accent)' }} />
                  <span className="font-bold" style={{ color: 'var(--text)' }}>Safe Skipping of Non-Image Files</span>
                </div>
                <p className="leading-relaxed" style={{ color: 'var(--muted)' }}>
                  If your folder or ZIP includes videos (<span className="font-mono">.mp4</span>, <span className="font-mono">.mov</span>, <span className="font-mono">.avi</span>), documents (<span className="font-mono">.pdf</span>, <span className="font-mono">.docx</span>), or text files, CatLog <span className="font-bold" style={{ color: 'var(--text)' }}>safely skips them</span> without interrupting or failing the scan.
                  All skipped non-image files are tallied and reported transparently by count and extension in your scan summary and <span className="font-mono">manifest.json</span>.
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div
          className="px-6 py-3.5 flex items-center justify-between"
          style={{
            background: 'var(--panel)',
            borderTop: '1.5px solid var(--line)',
          }}
        >
          <span className="text-xs" style={{ color: 'var(--muted)' }}>
            CatLog Engine &bull; Safe, Local, Privacy-First Photo Clustering
          </span>
          <button
            type="button"
            data-testid="btn-guidance-got-it"
            id="btn-guidance-got-it"
            onClick={onClose}
            className="px-5 py-2 rounded-lg font-bold text-xs transition-transform active:scale-95 shadow-md"
            style={{
              background: 'var(--accent)',
              color: 'var(--on-accent, #ffffff)',
              border: 'none',
              cursor: 'pointer',
            }}
          >
            Got It
          </button>
        </div>
      </div>
    </div>
  );
};
