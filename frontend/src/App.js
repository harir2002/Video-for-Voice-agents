/**
 * Voice Demo - Recording-Ready Player with Advanced Transcript Sync
 * 
 * Features:
 * - Precise transcript sync using uiStart (if available) or start time
 * - Orb animation driven by speaker type and persistent_ui settings
 * - Feature annotations rendered directly from JSON during playback
 */

import React, { useState, useRef, useEffect } from 'react';
import Orb from './components/Orb';
import Annotations from './components/Annotations';
import { normalizeTimelinePayload } from './utils/timelineTime';
import './styles/App.css';

function getSegmentDisplayTime(segment) {
  if (!segment) return 0;
  return segment.uiStart !== undefined ? segment.uiStart : segment.start;
}

/** Normalize speaker ids so "agent" gets the same chip/orb treatment as "human_agent". */
function normalizeSpeakerKey(speaker) {
  const raw = String(speaker || '')
    .trim()
    .toLowerCase()
    .replace(/[\s-]+/g, '_');

  if (raw === 'agent' || raw === 'human' || raw === 'humanagent' || raw === 'specialist') {
    return 'human_agent';
  }
  if (raw === 'bot' || raw === 'assistant' || raw === 'ai_agent' || raw === 'ai') {
    return 'ai';
  }
  if (raw === 'user' || raw === 'caller' || raw === 'customer') {
    return 'customer';
  }
  return raw || 'unknown';
}

function formatSpeakerLabel(speaker) {
  const key = normalizeSpeakerKey(speaker);
  if (key === 'human_agent') return 'agent';
  if (key === 'ai') return 'ai';
  if (key === 'customer') return 'customer';
  return String(speaker || 'speaker');
}

function App() {
  // Progressive reveal from the shared playback clock (word-by-word).
  // Works during play and while paused/seeking so UI stays on the same clock.
  const getRevealedText = (segment, time) => {
    if (!segment) return '';

    const displayTime = getSegmentDisplayTime(segment);
    const segmentDuration = Math.max(0, segment.end - displayTime);
    const elapsed = time - displayTime;

    if (elapsed < 0) return '';
    if (segmentDuration <= 0 || elapsed >= segmentDuration) return segment.text;

    const progress = elapsed / segmentDuration;
    const words = segment.text.split(/\s+/).filter(Boolean);
    const wordsToShow = Math.max(1, Math.ceil(words.length * progress));
    return words.slice(0, wordsToShow).join(' ');
  };
  // Audio State
  const [audioFile, setAudioFile] = useState(null);
  const [audioUrl, setAudioUrl] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);

  // Transcript State (times stored as real seconds after mm.ss normalization)
  const [transcript, setTranscript] = useState([]);
  const [activeSegment, setActiveSegment] = useState(null);
  const [previousSegments, setPreviousSegments] = useState([]);
  // eslint-disable-next-line no-unused-vars
  const [orbBehavior, setOrbBehavior] = useState(null);

  // Annotations State
  const [annotations, setAnnotations] = useState([]);

  // UI visibility state
  const [showUI, setShowUI] = useState(true);
  const [showSettings, setShowSettings] = useState(true);
  const [transcriptJson, setTranscriptJson] = useState('');
  const [error, setError] = useState(null);

  // Refs
  const audioRef = useRef(null);
  const animationFrameRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const transcriptDisplayRef = useRef(null);

  // Initialize Web Audio API on first play
  useEffect(() => {
    const audioElement = audioRef.current;
    if (!audioElement) return;

    const initAudio = () => {
      try {
        if (!audioContextRef.current) {
          const AudioContext = window.AudioContext || window.webkitAudioContext;
          audioContextRef.current = new AudioContext();
        }

        if (!analyserRef.current && audioContextRef.current) {
          const analyser = audioContextRef.current.createAnalyser();
          analyser.fftSize = 256;
          
          try {
            const source = audioContextRef.current.createMediaElementAudioSource(audioElement);
            source.connect(analyser);
            analyser.connect(audioContextRef.current.destination);
          } catch (err) {
            console.warn('Audio source already connected');
          }
          
          analyserRef.current = analyser;
        }
      } catch (err) {
        console.error('Web Audio API init:', err);
      }
    };

    audioElement.addEventListener('play', initAudio, { once: true });
    return () => {
      audioElement.removeEventListener('play', initAudio);
    };
  }, []);

  // Transcript sync from the shared audio clock (times already real seconds)
  useEffect(() => {
    if (!transcript || !transcript.length) {
      setActiveSegment(null);
      setPreviousSegments([]);
      return;
    }

    const findActiveSegment = (time) => {
      let active = null;
      let latestDisplayTime = -1;

      for (const seg of transcript) {
        if (!seg) continue;
        const displayTime = getSegmentDisplayTime(seg);

        // Current line only: future lines stay hidden until their window starts
        if (time >= displayTime && time < seg.end) {
          if (displayTime >= latestDisplayTime) {
            active = seg;
            latestDisplayTime = displayTime;
          }
        }
      }

      return active;
    };

    const findCompletedSegments = (time) => {
      return transcript
        .filter((seg) => seg && seg.end <= time)
        .sort((a, b) => a.end - b.end);
    };

    const active = findActiveSegment(currentTime);
    const completed = findCompletedSegments(currentTime);

    setActiveSegment(active);
    setPreviousSegments(completed);
  }, [currentTime, transcript]);

  // Keep the newest transcript line in view as history grows
  useEffect(() => {
    const el = transcriptDisplayRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [previousSegments, activeSegment, currentTime]);

  // Main sync loop - update every frame for real-time sync
  useEffect(() => {
    if (!audioRef.current) return;

    const syncLoop = () => {
      if (audioRef.current) {
        setCurrentTime(audioRef.current.currentTime);
        setIsPlaying(!audioRef.current.paused);
      }
      animationFrameRef.current = requestAnimationFrame(syncLoop);
    };

    animationFrameRef.current = requestAnimationFrame(syncLoop);
    
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  // Handle audio file upload
  const handleAudioUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setError(null);
    const url = URL.createObjectURL(file);
    setAudioUrl(url);
    setAudioFile(file.name);
    
    if (audioRef.current) {
      audioRef.current.src = url;
    }
  };

  // Extract transcript / annotations / orb behavior from demo JSON shapes
  const applyTimelineData = (data, { updateTextarea = false } = {}) => {
    let transcriptArray = [];
    if (Array.isArray(data)) {
      transcriptArray = data;
    } else if (data.transcript && Array.isArray(data.transcript)) {
      transcriptArray = data.transcript;
    } else if (data.segments && Array.isArray(data.segments)) {
      transcriptArray = data.segments;
    }

    const annotationsData = (!Array.isArray(data) && data.annotations) || [];
    const orbBehaviorData = (!Array.isArray(data) && data.persistent_ui?.orb_behavior) || null;

    // Convert mm.ss → real seconds once so all consumers share one clock.
    // Keep the source JSON (mm.ss) in the textarea — do not write converted seconds back.
    const normalized = normalizeTimelinePayload({
      transcript: transcriptArray,
      annotations: annotationsData,
    });

    setTranscript(normalized.transcript);
    setOrbBehavior(orbBehaviorData);
    setAnnotations(normalized.annotations);
    setError(null);

    if (updateTextarea) {
      setTranscriptJson(JSON.stringify(data, null, 2));
    }

    if (normalized.transcript.length > 0) {
      console.log(
        `✅ Loaded ${normalized.transcript.length} segments (mm.ss → seconds). First:`,
        normalized.transcript[0]
      );
    }
  };

  // Handle transcript file upload
  const handleTranscriptUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) {
      console.warn('❌ No file selected');
      return;
    }

    console.log(`📂 Loading transcript file: ${file.name}`);
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const data = JSON.parse(event.target.result);
        applyTimelineData(data, { updateTextarea: true });
      } catch (err) {
        console.error('❌ JSON parse error:', err);
        setError('Invalid JSON format');
      }
    };
    reader.readAsText(file);
  };

  // Handle transcript paste
  const handleTranscriptPaste = () => {
    if (!transcriptJson.trim()) {
      console.warn('⚠️ Transcript textarea is empty');
      setError('Paste or enter transcript JSON first');
      return;
    }

    try {
      console.log('📝 Parsing pasted JSON...');
      const data = JSON.parse(transcriptJson);
      applyTimelineData(data);
    } catch (err) {
      console.error('❌ JSON parse error:', err);
      setError('Invalid JSON format. Check syntax and try again.');
    }
  };

  // Load sample data (times authored as mm.ss, converted at ingest)
  const loadSampleData = () => {
    console.log('📥 Loading sample data...');
    const sampleData = {
      persistent_ui: {
        orb_behavior: {
          ai: { type: "expand-pulse" },
          customer: { type: "listening-ripple" },
          human_agent: { type: "soft-pulse" }
        }
      },
      annotations: [
        {
          "id": "ann-1",
          "type": "ui_chip",
          "label": "Feature: Multiturn Guidance",
          "start": 0.00,
          "end": 0.06,
          "position": "top-right"
        },
        {
          "id": "ann-2",
          "type": "ui_chip",
          "label": "Feature: Predefined FAQ Retrieved",
          "start": 0.12,
          "end": 0.19,
          "position": "top-right"
        },
        {
          "id": "ann-3",
          "type": "ui_chip",
          "label": "Feature: Query Context Switch",
          "start": 0.18,
          "end": 0.24,
          "position": "top-center"
        },
        {
          "id": "ann-4",
          "type": "ui_chip",
          "label": "Feature: Context Window Retained",
          "start": 0.35,
          "end": 0.48,
          "position": "top-right"
        },
        {
          "id": "ann-5",
          "type": "ui_chip",
          "label": "Feature: Interruption Handled",
          "start": 0.55,
          "end": 1.00,
          "position": "top-center"
        },
        {
          "id": "ann-6",
          "type": "ui_chip",
          "label": "Feature: Human Handoff",
          "start": 1.09,
          "end": 1.14,
          "position": "top-right"
        }
      ],
      transcript: [
        {
          "id": "seg-1",
          "start": 0.00,
          "end": 0.06,
          "speaker": "ai",
          "text": "Welcome to Godrej Capital. I'm here to help you find the perfect financial solution."
        },
        {
          "id": "seg-2",
          "start": 0.06,
          "end": 0.12,
          "speaker": "customer",
          "text": "Haan ji, namaste. Main apke paas loan ke bare mein poochna chahta hoon."
        },
        {
          "id": "seg-3",
          "start": 0.12,
          "end": 0.18,
          "speaker": "ai",
          "text": "Bilkul! What type of loan are you looking for? Business, personal, or property-based?"
        },
        {
          "id": "seg-4",
          "start": 0.18,
          "end": 0.24,
          "speaker": "customer",
          "text": "Meri nai business hai. Business loan chahiye mujhe."
        },
        {
          "id": "seg-5",
          "start": 0.24,
          "end": 0.32,
          "speaker": "ai",
          "text": "Great! Business loans are perfect for new ventures. How long has your business been operating?"
        },
        {
          "id": "seg-6",
          "start": 0.32,
          "end": 0.35,
          "speaker": "customer",
          "text": "Approximately 2 years."
        },
        {
          "id": "seg-7",
          "start": 0.35,
          "end": 0.43,
          "speaker": "ai",
          "text": "Perfect! With 2 years of operation, you're eligible for our business loan program. What's your approximate annual revenue?"
        },
        {
          "id": "seg-8",
          "start": 0.43,
          "end": 0.47,
          "speaker": "customer",
          "text": "Around 5 lakhs per year."
        },
        {
          "id": "seg-9",
          "start": 0.47,
          "end": 0.55,
          "speaker": "ai",
          "text": "Excellent! Based on your profile, you could qualify for up to 25 lakhs. Would you like to proceed with the application?"
        },
        {
          "id": "seg-10",
          "start": 0.55,
          "end": 0.59,
          "speaker": "customer",
          "text": "Haan, bilkul. Aage kya karna hoga?"
        },
        {
          "id": "seg-11",
          "start": 0.59,
          "end": 1.09,
          "speaker": "ai",
          "text": "I'll connect you with our loan specialist who can guide you through the process. They'll collect the necessary documents and help you complete the application."
        },
        {
          "id": "seg-12",
          "start": 1.09,
          "end": 1.13,
          "speaker": "human_agent",
          "text": "Hello! I'm Rajesh from our loan team. I see you're interested in a business loan for your startup."
        },
        {
          "id": "seg-13",
          "start": 1.13,
          "end": 1.22,
          "speaker": "human_agent",
          "text": "We'll process your application and you should hear back within 5-7 business days. In the meantime, please gather your business registration and financial documents."
        }
      ]
    };

    applyTimelineData(sampleData, { updateTextarea: true });
    console.log(`✅ Sample data loaded (${sampleData.annotations.length} annotations)`);
  };

  // Playback controls
  const handlePlayPause = () => {
    if (audioRef.current) {
      if (audioRef.current.paused) {
        audioRef.current.play();
        setShowSettings(false);
      } else {
        audioRef.current.pause();
      }
    }
  };

  const handleSeek = (time) => {
    if (audioRef.current) {
      audioRef.current.currentTime = time;
    }
  };

  const handleRestart = () => {
    if (audioRef.current) {
      audioRef.current.currentTime = 0;
      setCurrentTime(0);
    }
  };

  const handleLoadedMetadata = () => {
    setDuration(audioRef.current.duration);
  };

  const formatTime = (seconds) => {
    if (isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Calculate orb state based on active segment (real-second window)
  const getOrbState = () => {
    if (!activeSegment || !orbBehavior) {
      return { type: 'idle', speaker: 'none', progress: 0 };
    }

    const speakerKey = normalizeSpeakerKey(activeSegment.speaker);
    const speakerBehavior =
      orbBehavior[speakerKey] ||
      orbBehavior[activeSegment.speaker] ||
      (speakerKey === 'human_agent' ? orbBehavior.human_agent : null);

    if (!speakerBehavior) {
      return { type: 'idle', speaker: speakerKey, progress: 0 };
    }

    const displayTime = getSegmentDisplayTime(activeSegment);
    const segmentDuration = Math.max(0.001, activeSegment.end - displayTime);
    const elapsed = currentTime - displayTime;
    const progress = Math.max(0, Math.min(1, elapsed / segmentDuration));

    return {
      type: speakerBehavior.type,
      speaker: speakerKey,
      progress: progress,
      segmentId: activeSegment.id
    };
  };

  return (
    <div className="app">
      {/* Hidden audio element */}
      <audio
        ref={audioRef}
        onLoadedMetadata={handleLoadedMetadata}
        crossOrigin="anonymous"
      />

      {/* Status bar - top right */}
      {showUI && (
        <div className="status-bar">
          <span className="status-item">● Connected</span>
          <span className="status-item">Premium Recorder</span>
        </div>
      )}

      {/* Hide UI button - always visible */}
      <button
        className="toggle-ui-btn"
        onClick={() => setShowUI(!showUI)}
        title={showUI ? "Hide UI (cleaner recording)" : "Show UI"}
      >
        {showUI ? '⊣' : '⊢'}
      </button>

      {/* Settings panel - collapsible side button */}
      {showUI && (
        <div className={`settings-panel ${showSettings ? '' : 'collapsed'}`}>
        <div className="settings-header">
          <button
            className="toggle-settings"
            onClick={() => setShowSettings(!showSettings)}
            title={showSettings ? 'Hide Settings' : 'Show Settings'}
          >
            {showSettings ? '✕' : '⚙️'} Data & Settings
          </button>
        </div>

        {showSettings && (
          <div className="settings-content">
            {/* Audio Upload */}
            <div className="setting-group">
              <label>📁 Audio File</label>
              <input
                type="file"
                accept=".mp3,.wav,.m4a,.ogg,.webm"
                onChange={handleAudioUpload}
                className="file-input"
              />
              {audioFile && <span className="file-name">✓ {audioFile}</span>}
            </div>

            {/* Transcript Upload */}
            <div className="setting-group">
              <label>📝 Transcript JSON File</label>
              <input
                type="file"
                accept=".json"
                onChange={handleTranscriptUpload}
                className="file-input"
              />
            </div>

            {/* Transcript Paste */}
            <div className="setting-group">
              <label>Or Paste Transcript JSON</label>
              <textarea
                value={transcriptJson}
                onChange={(e) => setTranscriptJson(e.target.value)}
                placeholder='{"transcript":[{"start":0.09,"end":0.15,"speaker":"ai","text":"..."}],"annotations":[{"type":"ui_chip","start":0.09,"end":0.20,"label":"..."}]}'
                className="transcript-textarea"
              />
              <button onClick={handleTranscriptPaste} className="btn-paste">
                Apply JSON
              </button>
            </div>

            {/* Sample Data */}
            <div className="setting-group">
              <button onClick={loadSampleData} className="btn-sample">
                Load Sample Data (for testing)
              </button>
            </div>

            {/* Error Message */}
            {error && <div className="error-message">⚠️ {error}</div>}

            {/* Status */}
            <div className="settings-status">
              {audioFile && <span className="status-ok">✓ Audio loaded</span>}
              {transcript.length > 0 && (
                <span className="status-ok">✓ Transcript loaded ({transcript.length} lines)</span>
              )}
            </div>
          </div>
        )}
        </div>
      )}

      {/* Main content area */}
      <div className="main-content">
        {/* Transcript display — completed lines stay visible; current reveals progressively */}
        <div className="transcript-display" ref={transcriptDisplayRef}>
          {previousSegments.map((seg) => {
            const speakerKey = normalizeSpeakerKey(seg.speaker);
            return (
              <div
                key={seg.id || `${seg.speaker}-${seg.start}`}
                className={`transcript-line previous speaker-${speakerKey}`}
              >
                <span className="speaker-label">{formatSpeakerLabel(seg.speaker)}</span>
                <p>{seg.text}</p>
              </div>
            );
          })}
          {activeSegment ? (
            <div className={`transcript-line active speaker-${normalizeSpeakerKey(activeSegment.speaker)}`}>
              <span className="speaker-label">{formatSpeakerLabel(activeSegment.speaker)}</span>
              <p>{getRevealedText(activeSegment, currentTime)}</p>
            </div>
          ) : (
            previousSegments.length === 0 && (
              <div className="transcript-placeholder">
                {transcript.length === 0 ? 'Load transcript to begin' : 'Ready to play'}
              </div>
            )
          )}
        </div>

        {/* Circular Orb with speaker-driven animation */}
        <div className="orb-wrapper">
          <Orb 
            analyser={analyserRef.current} 
            isPlaying={isPlaying}
            orbState={getOrbState()}
          />
        </div>
      </div>

      {/* Feature Annotations */}
      <Annotations 
        currentTime={currentTime}
        annotations={annotations}
        isPlaying={isPlaying}
      />

      {/* Bottom controls */}
      <div className="controls">
        <button
          className="control-btn restart"
          onClick={handleRestart}
          disabled={!audioUrl}
          title="Restart"
        >
          ⟲
        </button>

        <button
          className="control-btn play"
          onClick={handlePlayPause}
          disabled={!audioUrl}
          title="Play/Pause"
        >
          {isPlaying ? '⏸' : '▶'}
        </button>

        <div className="progress-container">
          <input
            type="range"
            min="0"
            max={duration || 0}
            value={currentTime}
            onChange={(e) => handleSeek(parseFloat(e.target.value))}
            className="progress-slider"
            disabled={!audioUrl}
          />
          <span className="time-display">
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>
        </div>
      </div>
    </div>
  );
}

export default App;
