import React from 'react';

export type MascotPose = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8;

export interface MascotStickerProps {
  pose: MascotPose;
  theme?: string;
  className?: string;
  alt?: string;
  title?: string;
  style?: React.CSSProperties;
  width?: number | string;
  height?: number | string;
}

/**
 * Resolves the theme folder ('dark', 'navy', or 'paper') and pose index (1-8)
 * to a public static asset URL.
 */
export const getMascotUrl = (theme: string = 't-dark', pose: number = 1): string => {
  const themeFolder = theme === 't-navy' ? 'navy' : theme === 't-paper' ? 'paper' : 'dark';
  const clampedPose = Math.max(1, Math.min(8, Math.round(pose)));
  return `/mascot/${themeFolder}/pose${clampedPose}.png`;
};

export const MASCOT_POSE_LABELS: Record<MascotPose, string> = {
  1: 'Hello & Welcome',
  2: 'Looking Around & Investigating',
  3: 'Pointing to Action',
  4: 'Excited Celebration',
  5: 'Working Hard at Computer',
  6: 'Done & Verified',
  7: 'Leaving with Packed Bundle',
  8: 'Idle Resting Snooze',
};

export const MascotSticker: React.FC<MascotStickerProps> = ({
  pose,
  theme = 't-dark',
  className = '',
  alt,
  title,
  style,
  width,
  height,
}) => {
  const src = getMascotUrl(theme, pose);
  const defaultAlt = `Camera Cat Mascot - ${MASCOT_POSE_LABELS[pose] || `Pose ${pose}`}`;

  return (
    <img
      src={src}
      alt={alt || defaultAlt}
      title={title || MASCOT_POSE_LABELS[pose]}
      className={`object-contain select-none pointer-events-none ${className}`}
      style={{
        imageRendering: 'auto',
        ...style,
      }}
      width={width}
      height={height}
      loading="lazy"
    />
  );
};
