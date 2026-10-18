import React from 'react';

export interface BrandLogoProps {
  title?: string;
  subtitle?: string;
  size?: 'sm' | 'md' | 'lg';
  showSubtitle?: boolean;
  onClick?: () => void;
}

export const BrandLogo: React.FC<BrandLogoProps> = ({
  title = 'CatLog',
  subtitle = 'Who was at the event?',
  size = 'md',
  showSubtitle = true,
  onClick,
}) => {
  const iconSize = size === 'sm' ? 28 : size === 'lg' ? 44 : 36;
  const titleSize = size === 'sm' ? '18px' : size === 'lg' ? '24px' : '20px';

  return (
    <div
      onClick={onClick}
      className="brand-logo-container"
      title={`${title} — ${subtitle}`}
      data-testid="brand-logo"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '10px',
        cursor: onClick ? 'pointer' : 'default',
        userSelect: 'none',
        textDecoration: 'none',
      }}
    >
      {/* CatLog Camera Cat Mascot Icon */}
      <div
        style={{
          width: `${iconSize}px`,
          height: `${iconSize}px`,
          minWidth: `${iconSize}px`,
          minHeight: `${iconSize}px`,
          maxWidth: `${iconSize}px`,
          maxHeight: `${iconSize}px`,
          overflow: 'hidden',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          borderRadius: '8px',
          background: 'var(--panel)',
          border: '1.5px solid var(--line)',
        }}
      >
        <img
          src="./catlog-icon.png"
          alt="CatLog"
          style={{
            width: '100%',
            height: '100%',
            maxWidth: '100%',
            maxHeight: '100%',
            objectFit: 'contain',
            display: 'block',
          }}
          onError={(e) => {
            // Fallback to SVG camera icon if png not found
            const target = e.currentTarget;
            target.style.display = 'none';
            if (target.parentElement) {
              target.parentElement.innerHTML = `
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/>
                  <circle cx="12" cy="13" r="3"/>
                </svg>
              `;
            }
          }}
        />
      </div>

      {/* Typography: Wordmark with tactile Risograph text-shadow */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          lineHeight: 1,
        }}
      >
        <h1
          style={{
            fontSize: titleSize,
            fontFamily: "'Outfit', 'Inter', system-ui, sans-serif",
            fontWeight: 900,
            color: 'var(--text)',
            letterSpacing: '-0.02em',
            textShadow: '1.5px 1.5px 0 var(--accent)',
            lineHeight: 1.1,
            margin: 0,
            padding: 0,
          }}
        >
          {title}
        </h1>

        {showSubtitle && (
          <span
            style={{
              fontSize: '10px',
              fontFamily: "'JetBrains Mono', monospace",
              fontWeight: 700,
              color: 'var(--muted)',
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
              marginTop: '2px',
            }}
          >
            {subtitle}
          </span>
        )}
      </div>
    </div>
  );
};
export default BrandLogo;
