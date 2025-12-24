import os
import io
import numpy as np
import scipy.signal as signal
from gtts import gTTS
from pydub import AudioSegment

ASSETS_DIR = "assets"
if not os.path.exists(ASSETS_DIR):
    os.makedirs(ASSETS_DIR)

def get_digit_audio(digit, lang='English'):
    lang_code = 'en' if lang == 'English' else 'he' # 'iw' is technically hebrew code in some legacy, but 'he' is standard
    # gTTS uses 'iw' usually ? Let's check docs or try 'he'. 'he' is standard ISO.
    # Actually gTTS maps 'he' to 'iw' internally often.
    
    filename = os.path.join(ASSETS_DIR, f"{lang_code}_{digit}.mp3")
    
    if not os.path.exists(filename):
        text = str(digit)
        print(f"Generating audio for {digit} in {lang}...")
        try:
            tts = gTTS(text=text, lang=lang_code, slow=False)
            tts.save(filename)
        except Exception as e:
            print(f"Error generating TTS: {e}")
            return None
            
    return AudioSegment.from_mp3(filename)

def generate_noise(duration_ms):
    # Generating 1 second of noise to test
    sample_rate = 44100
    samples = np.random.normal(0, 1, int(sample_rate * duration_ms / 1000))
    
    # Simple lowpass to make it less harsh (LTASS-ish)
    b, a = signal.butter(1, 0.1, btype='low')
    samples = signal.lfilter(b, a, samples)
    
    # Normalize
    samples = samples / np.max(np.abs(samples)) * 0.5
    samples = (samples * 32767).astype(np.int16)
    
    return AudioSegment(
        samples.tobytes(), 
        frame_rate=sample_rate, 
        sample_width=2, 
        channels=1
    )

def test_pipeline():
    digit_seg = get_digit_audio(1, 'English')
    if not digit_seg:
        print("Failed to get digit audio")
        return

    noise = generate_noise(1000)
    
    # Mix
    combined = noise.overlay(digit_seg, position=100)
    output_path = "test_mix.mp3"
    combined.export(output_path, format="mp3")
    print(f"Exported {output_path}")

if __name__ == "__main__":
    test_pipeline()
