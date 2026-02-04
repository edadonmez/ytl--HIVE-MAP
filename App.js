/**
 * HIVE-MAP PRO - Search & Rescue Dashboard
 * Mission Critical Interface | Tactical HUD / Cyberpunk Theme
 * 
 * Uses Bluetooth RSSI for victim location & acoustic sensors for voice detection.
 */

import 'react-native-reanimated';
import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  View,
  Text,
  Pressable,
  Dimensions,
  Platform,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaView } from 'react-native-safe-area-context';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withTiming,
  withSequence,
  Easing,
} from 'react-native-reanimated';
import Svg, { Circle, Line, G } from 'react-native-svg';

const { width: SCREEN_WIDTH } = Dimensions.get('window');
const RADAR_SIZE = Math.min(SCREEN_WIDTH - 48, 320);
const RADAR_CENTER = RADAR_SIZE / 2;
const RADAR_RADIUS = RADAR_CENTER - 20;

// Design System
const COLORS = {
  background: '#050505',
  surface: '#0D0D0F',
  border: '#1A1A1E',
  neonGreen: '#00FF41',
  alertRed: '#FF3B30',
  electricBlue: '#00D4FF',
  muted: '#6B6B70',
  white: '#F5F5F5',
};

const FONT_FAMILY = Platform.OS === 'ios' ? 'Courier' : 'monospace';

// Generate polar to cartesian
const polarToCart = (angle, radius) => {
  const rad = (angle * Math.PI) / 180;
  return {
    x: RADAR_CENTER + radius * Math.cos(rad - Math.PI / 2),
    y: RADAR_CENTER + radius * Math.sin(rad - Math.PI / 2),
  };
};

// Mock blip generator
const generateBlips = () => {
  const blips = [];
  const victimCount = 1 + Math.floor(Math.random() * 2);
  const rescuerCount = 2 + Math.floor(Math.random() * 3);

  for (let i = 0; i < victimCount; i++) {
    blips.push({
      id: `v-${i}`,
      type: 'victim',
      angle: Math.random() * 360,
      dist: 0.8 + Math.random() * 2.4,
      rssi: -72 - Math.floor(Math.random() * 20),
    });
  }
  for (let i = 0; i < rescuerCount; i++) {
    blips.push({
      id: `r-${i}`,
      type: 'rescuer',
      angle: Math.random() * 360,
      dist: 0.5 + Math.random() * 2.0,
      rssi: -55 - Math.floor(Math.random() * 15),
    });
  }
  return blips;
};

// Initial mock data
const initialBlips = generateBlips();

export default function App() {
  const [blips, setBlips] = useState(initialBlips);
  const [waveformData, setWaveformData] = useState(
    Array(24).fill(0).map(() => 0.3 + Math.random() * 0.4)
  );
  const [voiceDetected, setVoiceDetected] = useState(false);
  const [voiceMatch, setVoiceMatch] = useState(0);
  const [telemetry, setTelemetry] = useState({
    lat: 41.0082,
    long: 28.9784,
    airQuality: 'Good',
    deviceCount: 12,
  });

  // Animation values
  const sweepRotation = useSharedValue(0);
  const statusOpacity = useSharedValue(1);
  const alertOpacity = useSharedValue(0);

  // Radar sweep animation - continuous 360° rotation
  useEffect(() => {
    sweepRotation.value = withRepeat(
      withTiming(360, { duration: 4000, easing: Easing.linear }),
      -1,
      false
    );
  }, []);

  // Status badge blink
  useEffect(() => {
    statusOpacity.value = withRepeat(
      withSequence(
        withTiming(0.4, { duration: 600 }),
        withTiming(1, { duration: 600 })
      ),
      -1,
      true
    );
  }, []);

  // Voice detection flash
  useEffect(() => {
    if (voiceDetected) {
      alertOpacity.value = withRepeat(
        withSequence(
          withTiming(1, { duration: 300 }),
          withTiming(0.3, { duration: 300 })
        ),
        4,
        true
      );
    } else {
      alertOpacity.value = withTiming(0);
    }
  }, [voiceDetected]);

  // Mock data refresh intervals
  useEffect(() => {
    const blipInterval = setInterval(() => setBlips(generateBlips()), 3000);

    const waveformInterval = setInterval(() => {
      const newWaveform = Array(24).fill(0).map(() => 0.2 + Math.random() * 0.7);
      setWaveformData(newWaveform);
      const maxVal = Math.max(...newWaveform);
      if (maxVal > 0.92) {
        setVoiceDetected(true);
        setVoiceMatch(Math.min(98, Math.floor(90 + maxVal * 10)));
      } else {
        setVoiceDetected(false);
      }
    }, 800);

    const telemetryInterval = setInterval(() => {
      setTelemetry((prev) => ({
        lat: prev.lat + (Math.random() - 0.5) * 0.0001,
        long: prev.long + (Math.random() - 0.5) * 0.0001,
        airQuality: Math.random() > 0.85 ? 'Poor' : 'Good',
        deviceCount: 10 + Math.floor(Math.random() * 6),
      }));
    }, 2000);

    return () => {
      clearInterval(blipInterval);
      clearInterval(waveformInterval);
      clearInterval(telemetryInterval);
    };
  }, []);

  const sweepAnimatedStyle = useAnimatedStyle(() => ({
    transform: [{ rotate: `${sweepRotation.value}deg` }],
  }));

  const statusAnimatedStyle = useAnimatedStyle(() => ({
    opacity: statusOpacity.value,
  }));

  const alertAnimatedStyle = useAnimatedStyle(() => ({
    opacity: alertOpacity.value,
  }));

  const primaryVictim = blips.find((b) => b.type === 'victim');

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <StatusBar style="light" />
      
      {/* ═══════════════════════════════════════════════════════════ */}
      {/* HEADER */}
      {/* ═══════════════════════════════════════════════════════════ */}
      <View style={styles.header}>
        <Text style={styles.appName}>HIVE-MAP PRO</Text>
        <View style={styles.headerRight}>
          <Animated.View style={[styles.statusBadge, statusAnimatedStyle]}>
            <View style={styles.statusDot} />
            <Text style={styles.statusText}>SCANNING... [NET-MESH: ACTIVE]</Text>
          </Animated.View>
          <View style={styles.icons}>
            <View style={styles.iconBox}>
              <Text style={styles.iconText}>📶</Text>
              <Text style={styles.iconLabel}>4G</Text>
            </View>
            <View style={styles.iconBox}>
              <Text style={styles.iconText}>🔋</Text>
              <Text style={styles.iconLabel}>87%</Text>
            </View>
          </View>
        </View>
      </View>

      {/* ═══════════════════════════════════════════════════════════ */}
      {/* RADAR - Main Visualizer */}
      {/* ═══════════════════════════════════════════════════════════ */}
      <View style={styles.radarSection}>
        <View style={styles.radarContainer}>
          <Svg width={RADAR_SIZE} height={RADAR_SIZE}>
            {/* Radar circles */}
            {[1, 2, 3, 4].map((ring) => (
              <Circle
                key={ring}
                cx={RADAR_CENTER}
                cy={RADAR_CENTER}
                r={RADAR_RADIUS * (ring / 4)}
                stroke={COLORS.border}
                strokeWidth={0.5}
                fill="none"
              />
            ))}

            {/* Cross lines */}
            <Line x1={RADAR_CENTER} y1={10} x2={RADAR_CENTER} y2={RADAR_SIZE - 10} stroke={COLORS.border} strokeWidth={0.5} />
            <Line x1={10} y1={RADAR_CENTER} x2={RADAR_SIZE - 10} y2={RADAR_CENTER} stroke={COLORS.border} strokeWidth={0.5} />

            {/* Blips */}
            {blips.map((blip) => {
              const radius = (blip.dist / 3.5) * RADAR_RADIUS;
              const pos = polarToCart(blip.angle, radius);
              const isVictim = blip.type === 'victim';
              const color = isVictim ? COLORS.alertRed : COLORS.neonGreen;

              return (
                <G key={blip.id}>
                  <Circle
                    cx={pos.x}
                    cy={pos.y}
                    r={isVictim ? 6 : 4}
                    fill={color}
                    stroke={COLORS.white}
                    strokeWidth={1}
                    strokeOpacity={0.5}
                  />
                </G>
              );
            })}
          </Svg>

          {/* Sweep rotation wrapper - Reanimated */}
          <Animated.View
            style={[
              styles.sweepWrapper,
              sweepAnimatedStyle,
              { width: RADAR_SIZE, height: RADAR_SIZE },
            ]}
            pointerEvents="none"
          >
            <Svg width={RADAR_SIZE} height={RADAR_SIZE} style={StyleSheet.absoluteFill}>
              <Line
                x1={RADAR_CENTER}
                y1={RADAR_CENTER}
                x2={RADAR_CENTER}
                y2={10}
                stroke={COLORS.electricBlue}
                strokeWidth={2}
                strokeOpacity={0.9}
              />
            </Svg>
          </Animated.View>

          {/* Floating label for primary victim */}
          {primaryVictim && (() => {
            const pos = polarToCart(primaryVictim.angle, (primaryVictim.dist / 3.5) * RADAR_RADIUS);
            return (
              <View style={[styles.floatingLabel, {
                left: Math.max(8, Math.min(RADAR_SIZE - 148, pos.x - 74)),
                top: Math.max(8, Math.min(RADAR_SIZE - 52, pos.y - 38)),
              }]}>
                <Text style={styles.floatingLabelText}>
                  DIST: {primaryVictim.dist.toFixed(1)}m | RSSI: {primaryVictim.rssi}dBm
                </Text>
              </View>
            );
          })()}

          {/* Radar labels */}
          <View style={styles.radarLabels}>
            <View style={styles.legendItem}>
              <View style={[styles.legendDot, { backgroundColor: COLORS.alertRed }]} />
              <Text style={styles.legendText}>VICTIM</Text>
            </View>
            <View style={styles.legendItem}>
              <View style={[styles.legendDot, { backgroundColor: COLORS.neonGreen }]} />
              <Text style={styles.legendText}>RESCUER</Text>
            </View>
          </View>
        </View>
      </View>

      {/* ═══════════════════════════════════════════════════════════ */}
      {/* SPECTRUM - Audio Waveform */}
      {/* ═══════════════════════════════════════════════════════════ */}
      <View style={styles.spectrumSection}>
        <Text style={styles.sectionTitle}>AUDIO SPECTRUM</Text>
        <View style={styles.waveformContainer}>
          {waveformData.map((val, i) => (
            <View
              key={i}
              style={[
                styles.waveformBar,
                {
                  height: Math.max(4, val * 48),
                  backgroundColor: val > 0.9 ? COLORS.alertRed : COLORS.electricBlue,
                },
              ]}
            />
          ))}
        </View>
        {voiceDetected && (
          <Animated.View style={[styles.voiceAlert, alertAnimatedStyle]}>
            <Text style={styles.voiceAlertText}>
              ⚠ HUMAN VOICE DETECTED ({voiceMatch}% MATCH)
            </Text>
          </Animated.View>
        )}
      </View>

      {/* ═══════════════════════════════════════════════════════════ */}
      {/* TELEMETRY PANEL */}
      {/* ═══════════════════════════════════════════════════════════ */}
      <View style={styles.telemetryPanel}>
        <View style={styles.telemetryGrid}>
          <View style={styles.telemetryItem}>
            <Text style={styles.telemetryLabel}>LAT</Text>
            <Text style={styles.telemetryValue}>{telemetry.lat.toFixed(5)}°</Text>
          </View>
          <View style={styles.telemetryItem}>
            <Text style={styles.telemetryLabel}>LONG</Text>
            <Text style={styles.telemetryValue}>{telemetry.long.toFixed(5)}°</Text>
          </View>
          <View style={styles.telemetryItem}>
            <Text style={styles.telemetryLabel}>AIR QUALITY</Text>
            <Text style={[styles.telemetryValue, { color: telemetry.airQuality === 'Good' ? COLORS.neonGreen : COLORS.alertRed }]}>
              {telemetry.airQuality}
            </Text>
          </View>
          <View style={styles.telemetryItem}>
            <Text style={styles.telemetryLabel}>DEVICE COUNT</Text>
            <Text style={styles.telemetryValue}>{telemetry.deviceCount}</Text>
          </View>
        </View>
      </View>

      {/* ═══════════════════════════════════════════════════════════ */}
      {/* ACTION BAR */}
      {/* ═══════════════════════════════════════════════════════════ */}
      <View style={styles.actionBar}>
        <Pressable
          style={({ pressed }) => [
            styles.emergencyButton,
            pressed && styles.emergencyButtonPressed,
          ]}
          onPress={() => {}}
        >
          <Text style={styles.emergencyButtonText}>EMERGENCY STOP</Text>
        </Pressable>
        <Pressable
          style={({ pressed }) => [
            styles.calibrateButton,
            pressed && styles.calibrateButtonPressed,
          ]}
          onPress={() => {}}
        >
          <Text style={styles.calibrateButtonText}>CALIBRATE</Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  appName: {
    fontFamily: FONT_FAMILY,
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.white,
    letterSpacing: 2,
  },
  headerRight: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.surface,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: COLORS.neonGreen,
  },
  statusDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: COLORS.neonGreen,
    marginRight: 8,
  },
  statusText: {
    fontFamily: FONT_FAMILY,
    fontSize: 11,
    color: COLORS.neonGreen,
    letterSpacing: 1,
  },
  icons: {
    flexDirection: 'row',
    gap: 8,
  },
  iconBox: {
    alignItems: 'center',
  },
  iconText: {
    fontSize: 14,
  },
  iconLabel: {
    fontFamily: FONT_FAMILY,
    fontSize: 9,
    color: COLORS.muted,
  },
  radarSection: {
    alignItems: 'center',
    paddingTop: 16,
    paddingBottom: 8,
  },
  radarContainer: {
    position: 'relative',
    width: RADAR_SIZE,
    height: RADAR_SIZE,
  },
  sweepWrapper: {
    position: 'absolute',
    top: 0,
    left: 0,
    justifyContent: 'center',
    alignItems: 'center',
  },
  floatingLabel: {
    position: 'absolute',
    backgroundColor: 'rgba(255, 59, 48, 0.9)',
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: COLORS.alertRed,
  },
  floatingLabelText: {
    fontFamily: FONT_FAMILY,
    fontSize: 10,
    color: COLORS.white,
    letterSpacing: 1,
  },
  radarLabels: {
    position: 'absolute',
    bottom: -28,
    right: 0,
    flexDirection: 'row',
    gap: 16,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  legendDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  legendText: {
    fontFamily: FONT_FAMILY,
    fontSize: 10,
    color: COLORS.muted,
    letterSpacing: 1,
  },
  spectrumSection: {
    marginHorizontal: 20,
    marginTop: 24,
    padding: 16,
    backgroundColor: COLORS.surface,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  sectionTitle: {
    fontFamily: FONT_FAMILY,
    fontSize: 11,
    color: COLORS.muted,
    letterSpacing: 2,
    marginBottom: 12,
  },
  waveformContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-between',
    height: 52,
    gap: 2,
  },
  waveformBar: {
    flex: 1,
    borderRadius: 2,
  },
  voiceAlert: {
    marginTop: 12,
    padding: 12,
    backgroundColor: 'rgba(255, 59, 48, 0.2)',
    borderRadius: 4,
    borderWidth: 1,
    borderColor: COLORS.alertRed,
    alignItems: 'center',
  },
  voiceAlertText: {
    fontFamily: FONT_FAMILY,
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.alertRed,
    letterSpacing: 1,
  },
  telemetryPanel: {
    marginHorizontal: 20,
    marginTop: 16,
    padding: 16,
    backgroundColor: COLORS.surface,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  telemetryGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 16,
  },
  telemetryItem: {
    flex: 1,
    minWidth: '45%',
  },
  telemetryLabel: {
    fontFamily: FONT_FAMILY,
    fontSize: 10,
    color: COLORS.muted,
    letterSpacing: 1,
    marginBottom: 4,
  },
  telemetryValue: {
    fontFamily: FONT_FAMILY,
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.electricBlue,
  },
  actionBar: {
    flexDirection: 'row',
    marginHorizontal: 20,
    marginTop: 20,
    marginBottom: 24,
    gap: 12,
  },
  emergencyButton: {
    flex: 1,
    backgroundColor: COLORS.alertRed,
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 59, 48, 0.5)',
  },
  emergencyButtonPressed: {
    opacity: 0.8,
  },
  emergencyButtonText: {
    fontFamily: FONT_FAMILY,
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.white,
    letterSpacing: 2,
  },
  calibrateButton: {
    flex: 1,
    backgroundColor: COLORS.surface,
    paddingVertical: 16,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.electricBlue,
  },
  calibrateButtonPressed: {
    opacity: 0.8,
  },
  calibrateButtonText: {
    fontFamily: FONT_FAMILY,
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.electricBlue,
    letterSpacing: 2,
  },
});
