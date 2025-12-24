# AuditoryMemoryTest

AuditoryMemoryTest is an auditory memory experiment application built with Streamlit.

## Features
- **Stimuli Control**: Select specific digits (1-9).
- **Languages**: English and Hebrew support (via Google TTS).
- **SNR Levels**: 10dB, 5dB, 0dB SNR conditions with speech-shaped noise.
- **Timing**: Configurable ISI and Retention phases.
- **Experiment Structure**: Practice block + Main experiment (198 trials).
- **Data Export**: CSV download.

## Installation

1. Install dependencies:
   ```bash
   pip install streamlit gTTS pydub numpy scipy pandas
   ```
2. Ensure **ffmpeg** is installed and receiving in your system PATH.
   - Windows: Download ffmpeg and add `bin` folder to Path.

## Running the App

```bash
streamlit run app.py
```

## Usage
1. Enter Subject ID and Session Number.
2. Select Stimuli and Language.
3. Use the **Calibration** tool to set physical volume (0dB SNR noise).
4. Start Experiment.
5. Follow the trials:
   - Fixation (+)
   - Noise Onset
   - Encoding (Digits)
   - Retention
   - Retrieval (Probe)
6. Download data at the end.

## Author & Contact

**AuditoryMemoryTest** is developed and maintained by **Eviatar Segev**.

**© 2025 All Rights Reserved.**

For inquiries, please contact: [eviatarsegev100@gmail.com](mailto:eviatarsegev100@gmail.com)
