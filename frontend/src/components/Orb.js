/**
 * Premium Breathing Particle Cloud Orb
 * 
 * A soft, organic voice blob that expands and shrinks like a living entity
 * - Particle cloud system (not a ring or loader)
 * - Continuous breathing animation
 * - Internal drift for organic feel
 * - State-driven expansion/shrinkage intensity
 * - Premium minimal aesthetic
 */

import React, { useEffect, useRef } from 'react';
import '../styles/Orb.css';

function Orb({ analyser, isPlaying, orbState = {} }) {
  const canvasRef = useRef(null);
  const animationIdRef = useRef(null);
  const particlesRef = useRef([]);
  
  const stateRef = useRef({
    // Breathing animation
    breathPhase: 0,
    breathScale: 1,
    
    // Pulse intensity (speaker-dependent)
    pulseIntensity: 0,
    glowRed: 0,
    
    // Audio reactivity
    avgEnergy: 0,
  });

  // Determine animation based on orbState type
  const orbType = orbState?.type || 'idle';

  // Log when animation type changes
  const prevOrbTypeRef = useRef(orbType);
  useEffect(() => {
    if (orbType !== prevOrbTypeRef.current) {
      console.debug(`🎤 Orb style: ${prevOrbTypeRef.current} → ${orbType}`);
      prevOrbTypeRef.current = orbType;
    }
  }, [orbType]);

  // Initialize particle cloud
  useEffect(() => {
    const particleCount = 180;  // Increased from 120
    const particles = [];
    
    for (let i = 0; i < particleCount; i++) {
      particles.push({
        angle: Math.random() * Math.PI * 2,
        radius: Math.random() * 50 + 15,  // Increased range
        vx: (Math.random() - 0.5) * 0.08,  // Increased drift
        vy: (Math.random() - 0.5) * 0.08,
        drift: Math.random() * 0.015,  // Increased drift speed
        driftAngle: Math.random() * Math.PI * 2,
      });
    }
    
    particlesRef.current = particles;
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);

    const centerX = rect.width / 2;
    const centerY = rect.height / 2;
    
    const dataArray = analyser ? new Uint8Array(analyser.frequencyBinCount) : null;

    const animate = () => {
      // Clear canvas to black
      ctx.fillStyle = '#000000';
      ctx.fillRect(0, 0, rect.width, rect.height);

      // Get audio energy if playing
      if (isPlaying && analyser && dataArray) {
        try {
          analyser.getByteFrequencyData(dataArray);
          const sum = dataArray.reduce((a, b) => a + b, 0);
          const avg = sum / dataArray.length;
          stateRef.current.avgEnergy += ((avg / 255) - stateRef.current.avgEnergy) * 0.1;
        } catch (err) {
          console.warn('Audio analysis:', err);
        }
      } else {
        stateRef.current.avgEnergy += (0 - stateRef.current.avgEnergy) * 0.08;
      }

      // STATE-DRIVEN BREATHING SYSTEM - POWERFUL AND RESPONSIVE
      let breathingSpeed = 0;
      let maxPulse = 0;
      let glowIntensity = 0;
      let audioBoost = 1;

      if (orbType === 'expand-pulse') {
        // AI SPEAKING: STRONGEST, MOST ENERGETIC BREATHING
        breathingSpeed = 0.08;  // Faster
        maxPulse = 0.7;  // Much larger expansion (±70%)
        glowIntensity = 1.2 + stateRef.current.avgEnergy * 0.5;  // Brighter
        audioBoost = 1 + stateRef.current.avgEnergy * 0.6;  // Audio heavily affects scale
      } else if (orbType === 'listening-ripple') {
        // CUSTOMER SPEAKING: STRONG RESPONSIVE BREATHING
        breathingSpeed = 0.05;  // Faster
        maxPulse = 0.5;  // Larger expansion (±50%)
        glowIntensity = 0.8 + stateRef.current.avgEnergy * 0.4;  // Responsive
        audioBoost = 1 + stateRef.current.avgEnergy * 0.4;
      } else if (orbType === 'soft-pulse') {
        // HUMAN AGENT: MODERATE STABLE BREATHING
        breathingSpeed = 0.035;  // Medium speed
        maxPulse = 0.35;  // Medium expansion (±35%)
        glowIntensity = 0.6 + stateRef.current.avgEnergy * 0.2;
        audioBoost = 1 + stateRef.current.avgEnergy * 0.2;
      } else {
        // IDLE: SUBTLE BUT PRESENT BREATHING
        breathingSpeed = 0.015;  // Slightly faster
        maxPulse = 0.15;  // Minimal but visible (±15%)
        glowIntensity = 0.25;
        audioBoost = 1;
      }

      // Update breathing animation with audio reactivity
      stateRef.current.breathPhase += breathingSpeed;
      const sinValue = Math.sin(stateRef.current.breathPhase);
      const audioReactiveScale = maxPulse * sinValue * audioBoost;
      stateRef.current.breathScale = 1 + audioReactiveScale;
      stateRef.current.glowRed += (Math.min(1, glowIntensity) - stateRef.current.glowRed) * 0.15;

      // Dampen when paused
      if (!isPlaying) {
        stateRef.current.breathScale += (1 - stateRef.current.breathScale) * 0.05;
        stateRef.current.glowRed *= 0.95;
      }

      // LAYER 1: Soft red glow halo (background)
      const haloGradient = ctx.createRadialGradient(centerX, centerY, 10, centerX, centerY, 120);
      haloGradient.addColorStop(0, `rgba(231, 0, 11, ${stateRef.current.glowRed * 0.3})`);
      haloGradient.addColorStop(0.4, `rgba(231, 0, 11, ${stateRef.current.glowRed * 0.15})`);
      haloGradient.addColorStop(1, 'rgba(231, 0, 11, 0)');
      ctx.fillStyle = haloGradient;
      ctx.beginPath();
      ctx.arc(centerX, centerY, 120, 0, Math.PI * 2);
      ctx.fill();

      // LAYER 2: Particle cloud (breathing)
      const particles = particlesRef.current;
      
      particles.forEach((particle, idx) => {
        // Update drift (organic motion)
        particle.driftAngle += particle.drift;
        const driftX = Math.cos(particle.driftAngle) * 0.5;  // Increased drift
        const driftY = Math.sin(particle.driftAngle) * 0.5;
        
        // Apply breathing scale with audio boost
        const scaledRadius = particle.radius * stateRef.current.breathScale;
        
        // Calculate particle position
        const x = centerX + Math.cos(particle.angle) * scaledRadius + driftX;
        const y = centerY + Math.sin(particle.angle) * scaledRadius + driftY;
        
        // Particle opacity and size vary with breathing - MORE DRAMATIC
        const opacityVariance = 0.4 + 0.4 * Math.sin(stateRef.current.breathPhase + idx * 0.08);
        const baseOpacity = 0.6 + stateRef.current.avgEnergy * 0.4;  // More audio reactive
        const particleOpacity = Math.min(1, baseOpacity * opacityVariance);
        
        const particleSize = 2 + Math.sin(stateRef.current.breathPhase * 0.6 + idx * 0.04) * 1.2;  // Larger particles
        
        // Draw particle (red accent)
        ctx.fillStyle = `rgba(231, 0, 11, ${particleOpacity})`;
        ctx.beginPath();
        ctx.arc(x, y, particleSize, 0, Math.PI * 2);
        ctx.fill();
      });

      // LAYER 3: Core bloom (inner glow expanding with breathing)
      const coreRadius = 40 * stateRef.current.breathScale;  // Larger core
      const coreGradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, coreRadius + 20);
      coreGradient.addColorStop(0, `rgba(231, 0, 11, ${stateRef.current.glowRed * 0.7})`);
      coreGradient.addColorStop(0.5, `rgba(231, 0, 11, ${stateRef.current.glowRed * 0.3})`);
      coreGradient.addColorStop(1, 'rgba(231, 0, 11, 0)');
      ctx.fillStyle = coreGradient;
      ctx.beginPath();
      ctx.arc(centerX, centerY, coreRadius + 20, 0, Math.PI * 2);
      ctx.fill();

      // LAYER 4: Center micro-core (white breathing dot) - LARGER
      const coreSize = 3 + 2.5 * Math.sin(stateRef.current.breathPhase * 0.8);  // Larger
      ctx.fillStyle = `rgba(255, 255, 255, ${0.6 + 0.4 * Math.sin(stateRef.current.breathPhase * 1.2)})`;
      ctx.beginPath();
      ctx.arc(centerX, centerY, coreSize, 0, Math.PI * 2);
      ctx.fill();

      animationIdRef.current = requestAnimationFrame(animate);
    };

    animationIdRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current);
      }
    };
  }, [analyser, isPlaying, orbType]);

  return (
    <canvas
      ref={canvasRef}
      className="orb-canvas"
      width={240}
      height={240}
    />
  );
}

export default Orb;
