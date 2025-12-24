import os
import io
import random
import numpy as np
from pydub import AudioSegment
from gtts import gTTS
import scipy.signal as signal
import base64

ASSETS_DIR = "assets"
if not os.path.exists(ASSETS_DIR):
    os.makedirs(ASSETS_DIR)

def get_digit_audio(digit, lang='English'):
    """Returns an AudioSegment for the digit."""
    # Map full names to gTTS codes
    lang_map = {
        'English': 'en',
        'Hebrew': 'iw',
        'Arabic': 'ar',
        'Amharic': 'am'
    }
    
    lang_code = lang_map.get(lang, 'en')
    file_prefix = lang_code
    
    filename = os.path.join(ASSETS_DIR, f"{file_prefix}_{digit}.mp3")
    
    if not os.path.exists(filename):
        text = str(digit)
        print(f"Generating {filename} with lang={lang_code}...")
        try:
            tts = gTTS(text=text, lang=lang_code, slow=False)
            tts.save(filename)
        except Exception as e:
            print(f"Error generating {text}: {e}")
            return None
            
    return AudioSegment.from_mp3(filename)

def generate_speech_shaped_noise(duration_ms):
    """Generates noise with a spectrum similar to speech (LTASS approximation)."""
    sample_rate = 44100
    # Generate white noise
    num_samples = int(sample_rate * duration_ms / 1000)
    white_noise = np.random.normal(0, 1, num_samples)
    
    # 2nd order Butterworth lowpass at 1kHz to approximate speech shape roll-off
    b, a = signal.butter(2, 1000 / (sample_rate / 2), btype='low')
    shaped_noise = signal.lfilter(b, a, white_noise)
    
    # Normalize to avoid clipping and generally fit 16-bit
    # Target RMS? We will adjust later. Just normalize peak to 0.5
    max_val = np.max(np.abs(shaped_noise))
    if max_val > 0:
        shaped_noise = shaped_noise / max_val * 0.5
        
    shaped_noise = (shaped_noise * 32767).astype(np.int16)
    
    audio = AudioSegment(
        shaped_noise.tobytes(), 
        frame_rate=sample_rate,
        sample_width=2, 
        channels=1
    )
    return audio

def create_trial_audio(digits_list, snr_db, isi_ms, retention_ms, lang='English', noise_onset_ms=2000):
    """
    Creates phase audio:
    timeline: [Noise (2s)] [Digit1][ISI][Digit2][ISI]... [Retention(Noise)]
    Note: The noise is continuous throughout.
    
    Returns: base64 encoded audio string (mp3).
    """
    
    # 1. Load Speech Segments
    speech_segments = []
    for d in digits_list:
        seg = get_digit_audio(d, lang)
        if seg is None:
            # Fallback
            seg = AudioSegment.silent(duration=500)
        speech_segments.append(seg)
    
    # Create speech track
    # Speech starts at noise_onset_ms
    # Sequence: D1 + Silence(ISI) + D2 + Silence(ISI) ... 
    # Use overlay on a silent track? Or concatenation?
    # Concat is easier for the speech stream.
    
    speech_stream = AudioSegment.empty()
    silence_isi = AudioSegment.silent(duration=isi_ms)
    
    for i, seg in enumerate(speech_segments):
        speech_stream += seg
        if i < len(speech_segments) - 1:
            speech_stream += silence_isi
            
    # 2. Generate Background Noise
    # Total duration = noise_onset_ms + speech_stream_duration + retention_ms
    total_duration = noise_onset_ms + len(speech_stream) + retention_ms
    
    noise_track = generate_speech_shaped_noise(total_duration)
    
    # 3. Adjust Levels for SNR
    # SNR = 20 * log10(RMS_signal / RMS_noise)
    # We fix Speech at -20 dBFS usually.
    target_speech_dbfs = -20.0
    
    if len(speech_stream) > 0:
        speech_stream = speech_stream.apply_gain(target_speech_dbfs - speech_stream.dBFS)
    
        # RMS_noise = RMS_signal / 10^(SNR/20)
        # dB_noise = dB_signal - SNR
        target_noise_dbfs = target_speech_dbfs - snr_db
        
        # Adjust noise gain
        noise_track = noise_track.apply_gain(target_noise_dbfs - noise_track.dBFS)
        
        # 4. Overlay
        # Overlay speech onto noise at silence offset
        full_audio = noise_track.overlay(speech_stream, position=noise_onset_ms)
    else:
        # Just noise (e.g. calibration or emtpy trial?)
        # Set noise to target level based on 0dB assumption if speech were there?
        # User said "Calibration: Play continuous LTASS noise at 0dB SNR level". 
        # This implies Noise Level calculated as if SNR was 0.
        # So Target Noise = Target Speech (-20) - 0 = -20 dBFS.
        target_noise_dbfs = -20.0
        noise_track = noise_track.apply_gain(target_noise_dbfs - noise_track.dBFS)
        full_audio = noise_track
        
    # Export
    buf = io.BytesIO()
    full_audio.export(buf, format="mp3")
    b64_data = base64.b64encode(buf.getvalue()).decode()
    
    return b64_data, total_duration

def get_digit_b64(digit, lang='English'):
    """Returns base64 audio for a single digit."""
    seg = get_digit_audio(digit, lang)
    if seg:
        buf = io.BytesIO()
        seg.export(buf, format="mp3")
        return base64.b64encode(buf.getvalue()).decode()
    return ""

def get_calibration_audio(snr_db=0, duration_sec=10):
    """Returns base64 audio for calibration (continuous noise at specified SNR level)."""
    # Note: SNR level implies the noise level relative to a theoretical speech level of -20 dBFS.
    # If SNR is 0dB, Noise is -20 dBFS.
    # If SNR is 10dB, Noise is -30 dBFS.
    
    noise = generate_speech_shaped_noise(duration_sec * 1000)
    target_speech_dbfs = -20.0
    target_noise_dbfs = target_speech_dbfs - snr_db
    
    noise = noise.apply_gain(target_noise_dbfs - noise.dBFS)
    
    buf = io.BytesIO()
    noise.export(buf, format="mp3")
    return base64.b64encode(buf.getvalue()).decode()
