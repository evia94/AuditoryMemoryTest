import streamlit as st
import os
import time
import base64
import pandas as pd
from audio_manager import create_trial_audio, get_calibration_audio, get_digit_b64
from experiment_logic import ExperimentLogic

# Page Setup
st.set_page_config(
    page_title="AuditoryMemoryTest",
    page_icon="👂",
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
        text-align: center;
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
    .feedback-text {
        font-size: 60px;
        font-weight: bold;
    }
    .btn-container {
        width: 100%; 
        max-width: 400px;
        margin-top: 20px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        font-size: 20px !important;
        font-weight: bold;
        color: #000000 !important;
        background-color: #FFFFFF !important;
        border: 2px solid #000000 !important;
    }
    /* Restoration for Primary Actions (Start Buttons) */
    .stButton>button[kind="primary"] {
        background-color: #FF4B4B !important;
        color: white !important;
        border: none !important;
    }
    .stButton>button[kind="primary"]:hover {
        background-color: #FF0000 !important;
        color: white !important;
    }
    .stButton>button:hover {
        background-color: #E0E0E0 !important;
        border-color: #000000 !important;
    }
    .stButton>button:active {
        background-color: #CCCCCC !important;
    }
    /* Hide Audio Player */
    audio {
        display: none;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
st.sidebar.title("⚙️ AuditoryMemoryTest Config")

# 1. Subject Info
with st.sidebar.expander("👤 Subject & Session", expanded=True):
    subject_id = st.text_input("Subject ID", "SUB001")
    age = st.number_input("Age", 18, 99, 25)
    session_num = st.number_input("Session Number", 1, 10, 1)

# 2. Stimuli & Language
digits_avail = []
with st.sidebar.expander("🎛️ Stimuli & Language", expanded=False):
    st.write("Selected Digits:")
    cols = st.columns(3)
    for i in range(1, 10):
        with cols[(i-1)%3]:
            if st.checkbox(f"{i}", value=True, key=f"digit_{i}"):
                digits_avail.append(i)
    
    lang = st.radio("Language", ["English", "Hebrew", "Arabic", "Amharic"], index=1)
    
    # Test Voice
    if st.button("🔊 Test Voice (Digit '1')"):
        test_digit_b64 = get_digit_b64(1, lang)
        if test_digit_b64:
            st.markdown(f'<audio autoplay><source src="data:audio/mp3;base64,{test_digit_b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)
        else:
            st.error("Could not generate audio.")

if not digits_avail:
    st.sidebar.error("Select at least one digit.")
    st.stop()

# 3. Timing
with st.sidebar.expander("⏱️ Timing", expanded=False):
    isi = st.slider("Inter-Stimulus Interval (sec)", 0.1, 2.0, 0.8, 0.1)
    retention = st.slider("Retention Phase (sec)", 0.5, 5.0, 2.0, 0.5)

# 4. Calibration
with st.sidebar.expander("📢 Calibration & Noise", expanded=False):
    calib_snr = st.select_slider("Select Noise Level (SNR equivalents)", options=[10, 5, 0], value=0)
    
    st.write("---")
    st.caption("Continuous Noise Only")
    if st.button(f"Play Noise Only ({calib_snr}dB SNR Level)"):
        calib_b64 = get_calibration_audio(snr_db=calib_snr, duration_sec=10)
        audio_html = f'<audio autoplay controls><source src="data:audio/mp3;base64,{calib_b64}" type="audio/mp3"></audio>'
        st.markdown(f"Playing {calib_snr}dB SNR Noise...")
        st.markdown(audio_html, unsafe_allow_html=True)

    st.write("---")
    st.caption("Noise + Digits Preview")
    if st.button(f"Play Digits + Noise ({calib_snr}dB)"):
        # Create a dummy trial audio with current settings
        # Using a fixed sequence "1, 2, 3" if available, else random
        demo_digits = [d for d in [1, 2, 3] if d in digits_avail]
        if not demo_digits:
            demo_digits = digits_avail[:3]
            
        b64_demo, _ = create_trial_audio(
            digits_list=demo_digits,
            snr_db=calib_snr,
            isi_ms=int(isi * 1000),
            retention_ms=1000, # Short retention for demo
            lang=lang,
            noise_onset_ms=1000 # Short onset
        )
        audio_html = f'<audio autoplay controls><source src="data:audio/mp3;base64,{b64_demo}" type="audio/mp3"></audio>'
        st.markdown(f"Playing Demo: {demo_digits} at {calib_snr}dB SNR...")
        st.markdown(audio_html, unsafe_allow_html=True)

    st.write("---")
    num_practice = st.number_input("Number of Practice Trials", 0, 20, 1)
    randomize_order = st.checkbox("Randomize Trial Order (Main Exp)", value=False, help="Check to shuffle. Uncheck for structured order (0->5->10 SNR)")

# 5. Data Output
with st.sidebar.expander("📂 Data Output", expanded=False):
    st.info("Tip: To save to **Google Drive**, paste the path to your local Drive folder (e.g., `G:\\My Drive\\Experiment_Data`).")
    output_dir = st.text_input("Output Path (Local)", value="data")
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
        except:
            pass 

# 6. About
st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style="text-align: center; color: #666; font-size: 0.85em;">
        <b>© 2025 All Rights Reserved.</b><br>
        Developed by <b>Eviatar Segev</b><br>
        <a href="mailto:eviatarsegev100@gmail.com" style="color: #666; text-decoration: none;">eviatarsegev100@gmail.com</a>
    </div>
    """, 
    unsafe_allow_html=True
)

# --- Session State ---
if 'status' not in st.session_state:
    st.session_state.status = 'SETUP' # SETUP, PRACTICE, MAIN, DONE
    st.session_state.exp_logic = None
    st.session_state.trial_list = []
    st.session_state.current_trial_idx = 0
    st.session_state.results = []
    st.session_state.phase = 'IDLE' # IDLE, FIXATION, AUDITORY, RESPONSE, FEEDBACK
    st.session_state.last_correct = False
    st.session_state.start_time = 0

def start_experiment():
    logic = ExperimentLogic(subject_id, session_num, digits_avail, age)
    # Generate trials: 3 Loads (2,4,6) x 3 SNRs x 22 Reps = 198 trials
    practice, main = logic.generate_trials(
        loads=[2,4,6], 
        snrs=[10,5,0], 
        main_reps=22, 
        num_practice=num_practice,
        randomize=randomize_order
    )
    
    st.session_state.exp_logic = logic
    st.session_state.practice_trials = practice
    st.session_state.main_trials = main
    st.session_state.trial_list = practice
    st.session_state.status = 'PRACTICE'
    st.session_state.current_trial_idx = 0
    st.session_state.phase = 'IDLE'

def submit_response(response_bool, rt):
    current_trial = st.session_state.trial_list[st.session_state.current_trial_idx]
    
    is_correct = (current_trial['is_match'] == response_bool)
    
    current_trial['response'] = 'Yes' if response_bool else 'No'
    current_trial['is_correct'] = is_correct
    current_trial['rt'] = rt
    
    # Autosave
    try:
        if st.session_state.exp_logic:
            # Use stored ID/Session from the running experiment logic
            s_id = st.session_state.exp_logic.subject_id
            s_num = st.session_state.exp_logic.session_num
            
            # Ensure directory exists or try to create it again just in case
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Save single trial
            part_filename = os.path.join(output_dir, f"AuditoryMemoryTest_{s_id}_sess{s_num}.csv")
            st.session_state.exp_logic.save_trial(current_trial, part_filename)
                
            # Visual confirmation
            # st.toast(f"✅ Trial {len(st.session_state.results)} Saved!", icon="💾")
            
    except PermissionError:
        st.error(f"⚠️ Could not save to {part_filename}. Please close the file if it is open!")
    except Exception as e:
        st.error(f"Autosave failed: {e}")

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
        elif st.session_state.status == 'MAIN':
            st.session_state.status = 'DONE'
    else:
        st.session_state.phase = 'IDLE'

# --- Main Layout ---

st.title("🧠 AuditoryMemoryTest")

if st.session_state.status == 'SETUP':
    st.write("### Welcome to the AuditoryMemoryTest Experiment")
    st.write("Please configure the experiment settings in the sidebar.")
    st.info("""
    **Experiment Procedure:**
    1.  **Fixation**: A cross (+) appears on the screen.
    2.  **Noise Onset**: Background noise begins (2 seconds).
    3.  **Encoding**: You will hear a sequence of digits.
    4.  **Retention**: A brief pause while holding the sequence in memory.
    5.  **Retrieval**: A probe digit appears with audio. Decide if it matched one of the digits in the sequence.
    
    **Structure:**
    - **Practice Block**: A few trials to get familiar with the interface (Data saved as 'Practice').
    - **Main Experiment**: 198 trials (The actual test).
    """)
    st.write("Note: Ensure your audio volume is comfortable using the Calibration tool.")
    st.write(f"Number of available digits: {len(digits_avail)}")
    
    if st.button("Start Experiment (Starts with Practice)", type="primary"):
        start_experiment()
        st.rerun()

elif st.session_state.status == 'MAIN_READY':
    st.success("✅ Practice Block Completed.")
    st.info("You are now conducting the **Main Experiment**. Data will be recorded for analysis.")
    st.markdown(f"### Ready for Main Experiment ({len(st.session_state.main_trials)} trials)?")
    if st.button("🚀 Start Main Experiment", type="primary"):
        st.session_state.status = 'MAIN'
        st.session_state.phase = 'IDLE'
        st.rerun()

elif st.session_state.status == 'DONE':
    st.success("🎉 Experiment Completed Successfully!")
    
    if st.session_state.exp_logic:
        # Final Save
        try:
            csv_data = st.session_state.exp_logic.export_data(st.session_state.results)
            
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Save final local copy
            final_filename = os.path.join(output_dir, f"AuditoryMemoryTest_{subject_id}_sess{session_num}_final.csv")
            with open(final_filename, "w", newline='') as f:
                f.write(csv_data)
                
            st.success(f"Data saved locally to: {final_filename}")
                
            st.download_button(
                label="📥 Download Data as CSV",
                data=csv_data,
                file_name=os.path.basename(final_filename),
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"Error saving data: {e}")
            
        # Summary
        main_results = [r for r in st.session_state.results if r['block'] == 'Main']
        if main_results:
            correct_count = sum(1 for r in main_results if r.get('is_correct'))
            total = len(main_results)
            st.metric("Main Experiment Accuracy", f"{correct_count}/{total} ({correct_count/total*100:.1f}%)")

elif st.session_state.status in ['PRACTICE', 'MAIN']:
    # INFO BAR
    trial_count = len(st.session_state.trial_list)
    current = st.session_state.current_trial_idx + 1
    prog = current / trial_count
    
    col_info1, col_info2 = st.columns([3,1])
    with col_info1:
        st.progress(prog)
        if st.session_state.status == 'PRACTICE':
            # High contrast custom warning
            st.markdown(f"""
            <div style="background-color: #FFA500; color: #000000; padding: 10px; border-radius: 5px; font-weight: bold; text-align: center; margin-bottom: 10px;">
                ⚠️ PRACTICE MODE | Trial {current} of {trial_count}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info(f"📊 **MAIN EXPERIMENT** | Trial {current} of {trial_count}")
        
    # Get Current Trial Data
    trial = st.session_state.trial_list[st.session_state.current_trial_idx]
    
    # CONTAINER
    placeholder = st.empty()
    
    with placeholder.container():
        
        if st.session_state.phase == 'IDLE':
            st.markdown(f"""
            <div class='experiment-container'>
                <h2>Trial {current}</h2>
                <p>Press Start to begin.</p>
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns([1,2,1])
            with c2:
                if st.button("Start Trial", type="primary", use_container_width=True):
                    st.session_state.phase = 'FIXATION'
                    st.rerun()

        elif st.session_state.phase == 'FIXATION':
            st.markdown("""
            <div class='experiment-container'>
                <div class='fixation'>+</div>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(1.0) # Baseline
            st.session_state.phase = 'AUDITORY'
            st.rerun()
            
        elif st.session_state.phase == 'AUDITORY':
            # Visual: Fixation + "Listen"
            st.markdown("""
            <div class='experiment-container'>
                <div class='fixation'>+</div>
                <p>Listening...</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Generate Audio
            # We memoize? No, params change.
            # But creating audio takes time (~1s). 
            # Ideally generated before? 
            # We'll do it JIT.
            
            b64_audio, duration_ms = create_trial_audio(
                digits_list=trial['digits'],
                snr_db=trial['snr'],
                isi_ms=int(isi * 1000),
                retention_ms=int(retention * 1000),
                lang=lang,
                noise_onset_ms=2000
            )
            
            # Autoplay
            audio_html = f'<audio autoplay><source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3"></audio>'
            st.markdown(audio_html, unsafe_allow_html=True)
            
            # Wait for audio to finish
            time.sleep(duration_ms / 1000 + 0.2)
            
            st.session_state.phase = 'RESPONSE'
            st.session_state.start_time = time.time()
            st.rerun()
            
        elif st.session_state.phase == 'RESPONSE':
            # Display Probe
            probe_digit = trial['probe']
            
            st.markdown(f"""
            <div class='experiment-container'>
                <div class='probe-text'>? {probe_digit}</div>
            </div>
            """, unsafe_allow_html=True)
            
            # Audio Probe (One time)
            # Use a query param or state hack to ensure it doesn't loop?
            # 'autoplay' plays once per DOM insertion. Rerun is a DOM insertion.
            # But the component below is re-rendered.
            probe_b64 = get_digit_b64(probe_digit, lang)
            if probe_b64:
                audio_html = f'<audio autoplay><source src="data:audio/mp3;base64,{probe_b64}" type="audio/mp3"></audio>'
                st.markdown(audio_html, unsafe_allow_html=True)
            
            st.markdown("### Was this digit in the sequence?")
            
            c1, c2 = st.columns(2)
            with c1:
                # YES
                if st.button("YES (Match)", type="primary", use_container_width=True):
                    submit_response(True, time.time() - st.session_state.start_time)
                    st.rerun()
            with c2:
                # NO
                if st.button("NO (Non-Match)", type="primary", use_container_width=True):
                    submit_response(False, time.time() - st.session_state.start_time)
                    st.rerun()

        elif st.session_state.phase == 'FEEDBACK':
            is_correct = st.session_state.last_correct
            text = "Correct!" if is_correct else "Incorrect"
            color = "#28a745" if is_correct else "#dc3545"
            
            st.markdown(f"""
            <div class='experiment-container'>
                <div class='feedback-text' style='color:{color}'>{text}</div>
            </div>
            """, unsafe_allow_html=True)
            
            time.sleep(1.0) # Show feedback for 1s
            next_trial()
            st.rerun()
