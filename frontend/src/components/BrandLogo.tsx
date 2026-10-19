import React from 'react';
import { RisoTheme } from './Header';

export interface BrandLogoProps {
  theme?: RisoTheme;
  onClick?: () => void;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showSubtitle?: boolean;
}

export const BrandLogo: React.FC<BrandLogoProps> = ({
  theme = 't-dark',
  onClick,
  className = '',
  size = 'md',
  showSubtitle = true,
}) => {
  const iconSize = size === 'sm' ? 28 : size === 'lg' ? 44 : 36;
  const titleSize = size === 'sm' ? '18px' : size === 'lg' ? '24px' : '20px';

  return (
    <div
      className={`brand-logo-container ${className}`}
      onClick={onClick}
      title="CatLog — Who was at the event?"
      data-testid="brand-logo"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '10px',
        cursor: 'pointer',
        userSelect: 'none',
        textDecoration: 'none',
        position: 'relative',
      }}
    >
      {/* CatLog Camera Cat Mascot Icon - Constrained */}
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
        }}
      >
        <img
          src="/catlog-icon.png"
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
            (e.target as HTMLElement).style.display = 'none';
          }}
        />
      </div>

      {/* Typography: Single crisp brand wordmark with Riso print misregistration shadow */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          lineHeight: 1,
        }}
      >
        <span
          style={{
            fontSize: titleSize,
            fontFamily: "'Archivo Black', 'Inter', sans-serif",
            fontWeight: 900,
            color: 'var(--text)',
            letterSpacing: '-0.02em',
            textShadow: '1.5px 1.5px 0 var(--accent)',
            lineHeight: 1,
          }}
        >
          CatLog
        </span>

        {showSubtitle && (
          <span
            style={{
              fontSize: '12px',
              fontFamily: 'monospace',
              fontWeight: 700,
              color: 'var(--muted)',
              letterSpacing: '0.14em',
              marginTop: '3px',
              textTransform: 'uppercase',
            }}
          >
            WHO WAS AT THE EVENT?
          </span>
        )}
      </div>
    </div>
  );
};
