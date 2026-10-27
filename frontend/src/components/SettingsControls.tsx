import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Check } from 'lucide-react';

export interface DropdownOption {
  value: number;
  label: string;
  badge?: string;
  desc?: string;
}

interface CustomDropdownProps {
  id: string;
  value: number;
  onChange: (value: number) => void;
  options: DropdownOption[];
  label: string;
}

export const CustomDropdown: React.FC<CustomDropdownProps> = ({
  id,
  value,
  onChange,
  options,
  label,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  const selectedOption = options.find((opt) => opt.value === value) || options[0];

  useEffect(() => {
    const handleOutsideClick = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleOutsideClick);
    }
    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
    };
  }, [isOpen]);

  const handleSelect = (val: number) => {
    onChange(val);
    setIsOpen(false);
  };

  return (
    <div className="relative space-y-1.5" ref={containerRef}>
      <label
        htmlFor={id}
        className="block text-sm font-bold uppercase tracking-wider text-[var(--muted)] font-mono"
      >
        {label}
      </label>

      {/* Hidden native select for test and form automation compatibility */}
      <select
        id={id}
        data-testid={id}
        value={value}
        onChange={(e) => onChange(parseInt(e.target.value, 10))}
        className="sr-only"
        aria-hidden="true"
        tabIndex={-1}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label} {opt.desc ? `(${opt.desc})` : ''}
          </option>
        ))}
      </select>

      {/* Custom Tactile Risograph Dropdown Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-4 py-2.5 rounded bg-[var(--input)] border-2 border-[var(--panel-border)] shadow-[2px_2px_0px_var(--line)] hover:border-[var(--accent)] hover:shadow-[2px_2px_0px_var(--accent)] transition-all text-left cursor-pointer group"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <div className="flex items-center gap-2.5 min-w-0">
          <span className="text-base font-black font-mono text-[var(--text)]">
            {selectedOption.label}
          </span>
          {selectedOption.desc && (
            <span className="text-sm font-mono text-[var(--muted)] truncate">
              {selectedOption.desc}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          {selectedOption.badge && (
            <span className="settings-badge accent text-xs font-bold px-2.5 py-0.5">
              {selectedOption.badge}
            </span>
          )}
          <ChevronDown
            className={`w-4 h-4 text-[var(--muted)] group-hover:text-[var(--accent)] transition-transform duration-200 ${
              isOpen ? 'rotate-180 text-[var(--accent)]' : ''
            }`}
          />
        </div>
      </button>

      {/* Popover Menu Options */}
      {isOpen && (
        <div
          className="absolute left-0 right-0 top-full mt-1.5 z-50 rounded bg-[var(--panel)] border-2 border-[var(--panel-border)] shadow-[4px_4px_0px_var(--line)] py-1.5 animate-fadeIn overflow-hidden"
          role="listbox"
        >
          {options.map((opt) => {
            const isSelected = opt.value === value;
            return (
              <div
                key={opt.value}
                onClick={() => handleSelect(opt.value)}
                className={`flex items-center justify-between px-4 py-2.5 cursor-pointer transition-colors text-sm font-mono ${
                  isSelected
                    ? 'bg-[var(--accent)] text-[var(--on-accent)] font-bold'
                    : 'text-[var(--text)] hover:bg-[var(--input)] hover:text-[var(--accent)]'
                }`}
                role="option"
                aria-selected={isSelected}
              >
                <div className="flex items-center gap-2.5">
                  <span
                    className={`w-4 h-4 rounded-sm flex items-center justify-center flex-shrink-0 ${
                      isSelected
                        ? 'text-[var(--on-accent)]'
                        : 'text-transparent'
                    }`}
                  >
                    <Check className="w-3.5 h-3.5 stroke-[3]" />
                  </span>
                  <span className="font-extrabold text-base">{opt.label}</span>
                  {opt.desc && (
                    <span
                      className={`text-sm ${
                        isSelected ? 'opacity-90' : 'text-[var(--muted)]'
                      }`}
                    >
                      {opt.desc}
                    </span>
                  )}
                </div>

                {opt.badge && (
                  <span
                    className={`text-xs px-2.5 py-0.5 rounded font-extrabold tracking-wider ${
                      isSelected
                        ? 'bg-[rgba(0,0,0,0.25)] text-white'
                        : 'settings-badge text-xs'
                    }`}
                  >
                    {opt.badge}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

// ============================================================================
// Custom Tactile Risograph Checkbox
// ============================================================================
interface CustomCheckboxProps {
  id: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  title: string;
  subtitle: string;
  'data-testid'?: string;
}

export const CustomCheckbox: React.FC<CustomCheckboxProps> = ({
  id,
  checked,
  onChange,
  title,
  subtitle,
  'data-testid': dataTestId,
}) => {
  return (
    <label
      htmlFor={id}
      className={`settings-toggle-card ${checked ? 'active' : ''} select-none cursor-pointer group`}
      style={{ padding: '16px 20px' }}
    >
      {/* Hidden input for automation and native behavior */}
      <input
        id={id}
        data-testid={dataTestId || id}
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="sr-only"
      />

      {/* Custom Tactile Checkbox Box */}
      <div
        className={`w-6 h-6 rounded flex items-center justify-center border-2 transition-all flex-shrink-0 ${
          checked
            ? 'bg-[var(--accent)] border-[var(--text)] shadow-[2px_2px_0px_var(--line)] scale-105'
            : 'bg-[var(--input)] border-[var(--panel-border)] shadow-[2px_2px_0px_var(--line)] group-hover:border-[var(--accent)]'
        }`}
        aria-hidden="true"
      >
        {checked && (
          <Check className="w-4 h-4 text-[var(--on-accent)] stroke-[3] animate-scaleUp" />
        )}
      </div>

      {/* Label Content */}
      <div className="flex-1 min-w-0 pr-2">
        <div className="flex items-center gap-2">
          <p className="text-base font-extrabold text-[var(--text)] uppercase tracking-wide group-hover:text-[var(--accent)] transition-colors">
            {title}
          </p>
        </div>
        <p className="text-sm text-[var(--muted)] leading-snug mt-1 font-mono">
          {subtitle}
        </p>
      </div>

      {/* Status Pill Badge */}
      <div className="flex-shrink-0">
        {checked ? (
          <span className="settings-badge accent text-xs font-bold px-3 py-1">
            ACTIVE
          </span>
        ) : (
          <span className="settings-badge text-xs font-bold px-3 py-1 text-[var(--muted)]">
            OFF
          </span>
        )}
      </div>
    </label>
  );
};
