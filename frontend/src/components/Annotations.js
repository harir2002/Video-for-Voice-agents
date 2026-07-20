/**
 * Annotations Component
 * Renders feature labels and markers during playback based on timing
 * 
 * Priority System:
 * - PRIMARY FEATURE CHIP: ui_chip only (highest priority, always shown as main label)
 * - SUPPORTING ANNOTATIONS: breadcrumb, memory_strip, event_chip, metric_chip, etc. (shown in their positions)
 * 
 * Supported annotation types:
 * - ui_chip: Primary feature pill badge (ONLY one shown as main label)
 * - floating_chip: Compact helper chip (supporting)
 * - side_label: Side note label (supporting)
 * - metric_chip: Response time badge (supporting)
 * - event_chip: Event marker (supporting)
 * - breadcrumb: Journey trail (supporting)
 * - memory_strip: Context memory (supporting)
 */

import React, { useMemo } from 'react';
import '../styles/Annotations.css';

function Annotations({ currentTime, annotations = [], isPlaying }) {
  // Active annotations from the shared playback clock (times already real seconds)
  const activeAnnotations = useMemo(() => {
    if (!annotations || annotations.length === 0) return [];

    return annotations.filter((ann) => {
      if (ann.start == null || ann.end == null) return false;
      return currentTime >= ann.start && currentTime < ann.end;
    });
  }, [currentTime, annotations]);

  // Primary feature label: ui_chip wins over all other overlapping annotation types
  const primaryUiChip = useMemo(() => {
    if (activeAnnotations.length === 0) return null;

    const uiChips = activeAnnotations.filter((ann) => ann.type === 'ui_chip');
    if (uiChips.length === 0) return null;

    return uiChips.reduce((latest, current) => {
      return current.start > latest.start ? current : latest;
    });
  }, [activeAnnotations]);

  // Only render during playback so recording UI stays clean when idle
  if (!isPlaying || !primaryUiChip) {
    return null;
  }

  return (
    <div className="annotations-container">
      <div className="primary-feature-chip">
        <div className="chip ui-chip primary">
          <span className="chip-icon">✨</span>
          <span className="chip-text">{primaryUiChip.label}</span>
        </div>
      </div>
    </div>
  );
}

export default Annotations;
