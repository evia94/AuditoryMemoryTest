import streamlit as st
import time
import base64
import pandas as pd
from audio_manager import create_trial_audio, get_calibration_audio
from experiment_logic import ExperimentLogic

# Page Setup
st.set_page_config(
    page_title="AuditoryMemoryTest",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Aesthetics
st.markdown("""
<style>
    .stApp {
        background-color: #f5f5f5;
        color: #000000;
    }
    .big-font {
        font-size: 50px !important;
        font-weight: bold;
        text-align: center;
        color: #333;
    }
    .experiment-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 60vh;
        background-color: white;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        padding: 2rem;
    }
    .fixation {
        font-size: 100px;
        color: black;
    }
    .probe-text {
        font-size: 80px;
        font-weight: bold;
        color: black;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        font-size: 18px;
    }
    /* Hide Audio Player */
    audio {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.title("🛠️ Setup & Config")

subject_id = st.sidebar.text_input("Subject ID", "SUB001")
age = st.sidebar.number_input("Age", 18, 99, 25)
session_num = st.sidebar.number_input("Session Number", 1, 10, 1)

st.sidebar.subheader("Stimuli Control")
digits_avail = []
cols = st.sidebar.columns(3)
for i in range(1, 10):
    with cols[(i-1)%3]:
        if st.checkbox(f"{i}", value=True, key=f"digit_{i}"):
            digits_avail.append(i)

if not digits_avail:
    st.sidebar.error("Select at least one digit.")
    st.stop()

lang = st.sidebar.radio("Language", ["English", "Hebrew"])

st.sidebar.subheader("Timing (sec)")
isi = st.sidebar.slider("Inter-Stimulus Interval", 0.1, 2.0, 0.8, 0.1)
retention = st.sidebar.slider("Retention Phase", 0.5, 5.0, 2.0, 0.5)

st.sidebar.subheader("Calibration")
if st.sidebar.button("Play Calibration Noise (5s)"):
    calib_b64 = get_calibration_audio()
    audio_html = f'<audio autoplay><source src="data:audio/mp3;base64,{calib_b64}" type="audio/mp3"></audio>'
    st.sidebar.markdown(audio_html, unsafe_allow_html=True)

# --- Session State ---
if 'status' not in st.session_state:
    st.session_state.status = 'SETUP' # SETUP, PRACTICE, MAIN, DONE
    st.session_state.exp_logic = None
    st.session_state.trial_list = []
    st.session_state.current_trial_idx = 0
    st.session_state.results = []
    st.session_state.phase = 'IDLE' # IDLE, FIXATION, PLAYING, RESPONSE, FEEDBACK

def start_experiment():
    logic = ExperimentLogic(subject_id, session_num, digits_avail, age)
    # Generate blocks
    practice, main = logic.generate_trials()
    # Combine or separate?
    # Logic: Run Practice -> Setup/Intermission? -> Main
    # We'll just load Practice first.
    st.session_state.exp_logic = logic
    st.session_state.practice_trials = practice
    st.session_state.main_trials = main
    st.session_state.trial_list = practice
    st.session_state.status = 'PRACTICE'
    st.session_state.current_trial_idx = 0
    st.session_state.phase = 'IDLE'

def submit_response(response_bool, rt):
    # Log Data
    current_trial = st.session_state.trial_list[st.session_state.current_trial_idx]
    
    # Correctness
    # Probe is match?
    # User said YES (True) or NO (False)
    # Correct if (is_match and YES) or (not is_match and NO)
    is_correct = (current_trial['is_match'] == response_bool)
    
    current_trial['response'] = 'Yes' if response_bool else 'No'
    current_trial['is_correct'] = is_correct
    current_trial['rt'] = rt
    
    st.session_state.results.append(current_trial)
    
    # Save to file immediately
    import os
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # Use stored ID/Session from the running experiment logic to avoid sidebar changes affecting filename
    if st.session_state.exp_logic:
        s_id = st.session_state.exp_logic.subject_id
        s_num = st.session_state.exp_logic.session_num
        filename = f"data/AuditoryMemoryTest_{s_id}_sess{s_num}.csv"
        st.session_state.exp_logic.save_trial(current_trial, filename)

    
    # Feedback
    st.session_state.last_correct = is_correct
    st.session_state.phase = 'FEEDBACK'

def next_trial():
    st.session_state.current_trial_idx += 1
    if st.session_state.current_trial_idx >= len(st.session_state.trial_list):
        if st.session_state.status == 'PRACTICE':
            st.session_state.status = 'MAIN_READY'
            st.session_state.current_trial_idx = 0
            st.session_state.trial_list = st.session_state.main_trials
            st.session_state.phase = 'IDLE'
        else:
            st.session_state.status = 'DONE'
    else:
        st.session_state.phase = 'IDLE'

# --- Main Interface ---

st.title("🧠 AuditoryMemoryTest")

if st.session_state.status == 'SETUP':
    st.info("Configure settings in the sidebar and click Start.")
    if st.button("Start Experiment", type="primary"):
        start_experiment()
        st.rerun()

elif st.session_state.status == 'MAIN_READY':
    st.success("Practice Completed.")
    st.markdown("### Ready for Main Experiment?")
    st.write(f"Trials: {len(st.session_state.main_trials)}")
    if st.button("Start Main Experiment", type="primary"):
        st.session_state.status = 'MAIN'
        st.rerun()

elif st.session_state.status == 'DONE':
    st.success("Experiment Completed!")
    
    # Export
    if st.session_state.exp_logic:
        csv_data = st.session_state.exp_logic.export_data(st.session_state.results)
        st.download_button(
            label="Download Data CSV",
            data=csv_data,
            file_name=f"AuditoryMemoryTest_{subject_id}_sess{session_num}.csv",
            mime="text/csv"
        )
        
elif st.session_state.status in ['PRACTICE', 'MAIN']:
    # Progress
    trial_count = len(st.session_state.trial_list)
    current = st.session_state.current_trial_idx + 1
    prog = current / trial_count
    st.progress(prog)
    st.caption(f"{st.session_state.status} Block: Trial {current} of {trial_count}")
    
    trial = st.session_state.trial_list[st.session_state.current_trial_idx]
    
    # PHASE LOGIC
    
    if st.session_state.phase == 'IDLE':
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            st.markdown("<div class='experiment-container'><h2>Ready?</h2></div>", unsafe_allow_html=True)
            if st.button("Start Trial"):
                st.session_state.phase = 'FIXATION'
                st.rerun()
                
    elif st.session_state.phase == 'FIXATION':
        # Show fixation for 1s then move to Audio
        placeholder = st.empty()
        placeholder.markdown("<div class='experiment-container'><div class='fixation'>+</div></div>", unsafe_allow_html=True)
        time.sleep(1.0) # Baseline
        st.session_state.phase = 'AUDITORY'
        st.rerun()
        
    elif st.session_state.phase == 'AUDITORY':
        # Generate Audio
        placeholder = st.empty()
        placeholder.markdown("<div class='experiment-container'><div class='fixation'>+</div><p>Listen...</p></div>", unsafe_allow_html=True)
        
        # Audio Params
        # Noise Onset (2s) -> Encoding (Digits + ISI) -> Retention (retention_sec)
        # We need to calculate precise duration to sleep
        
        digits = trial['digits']
        snr = trial['snr']
        
        # Estimate Duration
        # Average digit duration ~0.5s? 
        # We generate it, so we can know exactly, but `create_trial_audio` returns b64.
        # Ideally `create_trial_audio` returns duration too.
        # Re-calc for sleep:
        # We don't know exact duration of TTS without checking files.
        # But we can approximate or update `create_trial_audio` to return duration.
        # For now, I'll trust the audio plays and we just show "Retrieve" button enabled after a safe margin?
        # NO, user wants precise timing.
        # I should update `create_trial_audio` to return `duration_ms`.
        
        # Temporary: Assuming ~600ms per digit + ISI
        # Let's fix this properly by reading the files in `create_trial_audio`.
        # I will assume I can update `audio_manager` quickly or just use a helper here?
        # I'll update the call below.
        
        # For now, let's call it and assume I fix it or make a best guess.
        # To avoid editing audio_manager again immediately, I'll check if I can get duration from pydub object
        # but the function returns b64.
        # I'll edit audio_manager to return (b64, duration_ms).
        
        # WAIT: I can't edit it inside this thought block. 
        # I will assume I edit it next.
        pass
        
    elif st.session_state.phase == 'RESPONSE':
        # Retrieval
        st.markdown(f"<div class='experiment-container'><div class='probe-text'>? {trial['probe']}</div></div>", unsafe_allow_html=True)
        
        # Play Probe Audio ONCE
        # But st.audio re-runs?
        # Use a flag "probe_played"?
        # Or Just autoplay it.
        
        c1, c2 = st.columns(2)
        start_time = time.time() # Rough RT
        
        with c1:
            if st.button("YES (Match)", type="primary"):
                submit_response(True, time.time() - st.session_state.start_time)
                st.rerun()
        with c2:
            if st.button("NO (Non-Match)"):
                submit_response(False, time.time() - st.session_state.start_time)
                st.rerun()
                
    elif st.session_state.phase == 'FEEDBACK':
        color = "green" if st.session_state.last_correct else "red"
        text = "Correct!" if st.session_state.last_correct else "Incorrect"
        st.markdown(f"<div class='experiment-container'><h1 style='color:{color}'>{text}</h1></div>", unsafe_allow_html=True)
        time.sleep(1.0)
        next_trial()
        st.rerun()

