import { useState, useRef } from 'react'
import { useTheme, ACCENT_PRESETS } from '../../contexts/ThemeContext'

export function AccentColorPicker() {
  const { accent, setAccent, customAccent, setCustomAccent } = useTheme()
  const [hexInput, setHexInput] = useState(customAccent || accent.value)
  const [isEditing, setIsEditing] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  function handlePresetClick(color: typeof ACCENT_PRESETS[0]) {
    setAccent(color)
    setHexInput(color.value)
    setIsEditing(false)
  }

  function handleHexSubmit() {
    const hex = hexInput.trim()
    if (/^#[0-9a-fA-F]{6}$/.test(hex)) {
      setCustomAccent(hex)
      setIsEditing(false)
    }
  }

  function handleHexChange(e: React.ChangeEvent<HTMLInputElement>) {
    let val = e.target.value
    if (!val.startsWith('#')) val = '#' + val
    setHexInput(val)
    setIsEditing(true)

    // Live preview as user types
    if (/^#[0-9a-fA-F]{6}$/.test(val)) {
      setCustomAccent(val)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter') handleHexSubmit()
    if (e.key === 'Escape') {
      setHexInput(customAccent || accent.value)
      setIsEditing(false)
      inputRef.current?.blur()
    }
  }

  function clearCustom() {
    setCustomAccent(null)
    setHexInput(accent.value)
    setIsEditing(false)
  }

  const isActive = (color: typeof ACCENT_PRESETS[0]) =>
    !isEditing && accent.value === color.value && !customAccent

  return (
    <div className="card animate-in animate-in-delay-2" style={{ marginBottom: 'var(--space-6)' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 'var(--space-5)' }}>
        <div style={{
          width: 14,
          height: 14,
          borderRadius: 'var(--radius-sm)',
          background: accent.value,
        }} />
        <h3 style={{
          fontSize: 10,
          fontWeight: 500,
          color: 'var(--text-muted)',
          letterSpacing: '0.12em',
          textTransform: 'uppercase',
        }}>
          BRAND COLOR
        </h3>
      </div>

      {/* Preset Swatches */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: 8,
        marginBottom: 'var(--space-4)',
      }}>
        {ACCENT_PRESETS.map((color) => (
          <button
            key={color.name}
            onClick={() => handlePresetClick(color)}
            title={color.name}
            aria-label={`Set accent color to ${color.name}`}
            style={{
              width: 36,
              height: 36,
              borderRadius: 'var(--radius-sm)',
              background: color.value,
              border: isActive(color)
                ? '2px solid var(--text-primary)'
                : '2px solid transparent',
              cursor: 'pointer',
              transition: 'all 150ms ease',
              outline: 'none',
              position: 'relative',
            }}
          >
            {isActive(color) && (
              <div style={{
                position: 'absolute',
                inset: 0,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              </div>
            )}
          </button>
        ))}
      </div>

      {/* Custom Hex Input */}
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <span style={{
            position: 'absolute',
            left: 12,
            top: '50%',
            transform: 'translateY(-50%)',
            color: 'var(--text-muted)',
            fontSize: 13,
            fontFamily: 'var(--font-mono)',
            pointerEvents: 'none',
          }}>
            #
          </span>
          <input
            ref={inputRef}
            type="text"
            value={hexInput.replace('#', '')}
            onChange={handleHexChange}
            onBlur={handleHexSubmit}
            onKeyDown={handleKeyDown}
            maxLength={6}
            placeholder="Custom hex"
            className="form-input form-input-mono"
            style={{
              paddingLeft: 24,
              height: 36,
              fontSize: 13,
            }}
          />
        </div>

        {/* Live preview swatch */}
        <div style={{
          width: 36,
          height: 36,
          borderRadius: 'var(--radius-sm)',
          background: /^#[0-9a-fA-F]{6}$/.test(hexInput) ? hexInput : accent.value,
          border: '1px solid var(--border-primary)',
          flexShrink: 0,
        }} />

        {customAccent && (
          <button
            onClick={clearCustom}
            className="btn btn-secondary"
            style={{ height: 36, fontSize: 12, padding: '0 12px', flexShrink: 0 }}
          >
            Reset
          </button>
        )}
      </div>

      <p style={{
        fontSize: 11,
        color: 'var(--text-muted)',
        marginTop: 'var(--space-3)',
        lineHeight: 1.5,
      }}>
        Choose a preset or enter a custom hex color. This color is used for buttons, links, active states, and accents throughout the app.
      </p>
    </div>
  )
}
