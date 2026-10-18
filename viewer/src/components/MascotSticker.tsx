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

export const getMascotUrl = (theme: string = 't-dark', pose: number = 1): string => {
  const themeFolder = theme === 't-navy' ? 'navy' : theme === 't-paper' ? 'paper' : 'dark';
  const clampedPose = Math.max(1, Math.min(8, Math.round(pose)));
  return `./mascot/${themeFolder}/pose${clampedPose}.png`;
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
  const defaultAlt = `CatLog Mascot - ${MASCOT_POSE_LABELS[pose] || `Pose ${pose}`}`;

  return (
    <img
      src={src}
      alt={alt || defaultAlt}
      title={title || MASCOT_POSE_LABELS[pose]}
      className={`select-none pointer-events-none ${className}`}
      style={{
        objectFit: 'contain',
        imageRendering: 'auto',
        ...style,
      }}
      width={width}
      height={height}
      onError={(e) => {
        // Hide if mascot sticker is not found
        (e.target as HTMLElement).style.display = 'none';
      }}
    />
  );
};
export default MascotSticker;
