#!/usr/bin/env python3
"""Generate a synthetic goat scream sound."""
import numpy as np
import wave

# Parameters
sample_rate = 44100
duration = 1.2  # seconds

# Generate time array
t = np.linspace(0, duration, int(sample_rate * duration))

# Create a goat-like scream with frequency modulation
# Goats typically scream in 200-600 Hz range with vibrato
base_freq = 350
vibrato_freq = 8  # Hz
vibrato_depth = 100  # Hz

# Frequency modulation (creates the "bleating" effect)
freq = base_freq + vibrato_depth * np.sin(2 * np.pi * vibrato_freq * t)

# Generate the tone with frequency modulation
phase = 2 * np.pi * np.cumsum(freq) / sample_rate
wave_data = np.sin(phase)

# Add harmonics for more goat-like quality
wave_data += 0.5 * np.sin(2 * phase)
wave_data += 0.3 * np.sin(3 * phase)
wave_data += 0.2 * np.sin(4 * phase)

# Apply amplitude envelope (attack, sustain, decay)
attack = int(0.05 * sample_rate)
decay = int(0.3 * sample_rate)
envelope = np.ones_like(wave_data)
envelope[:attack] = np.linspace(0, 1, attack)
envelope[-decay:] = np.linspace(1, 0, decay)

wave_data *= envelope

# Add some noise for texture
noise = np.random.normal(0, 0.05, len(wave_data))
wave_data += noise

# Normalize to 16-bit range
wave_data = np.int16(wave_data / np.max(np.abs(wave_data)) * 32767 * 0.8)

# Write to WAV file
with wave.open('goat_scream.wav', 'w') as wav_file:
    wav_file.setnchannels(1)  # Mono
    wav_file.setsampwidth(2)  # 16-bit
    wav_file.setframerate(sample_rate)
    wav_file.writeframes(wave_data.tobytes())

print("✅ Generated goat_scream.wav")
