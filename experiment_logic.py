import random
import pandas as pd
from datetime import datetime

class ExperimentLogic:
    def __init__(self, subject_id, session_num, available_digits, age):
        self.subject_id = subject_id
        self.session_num = session_num
        self.available_digits = [int(d) for d in available_digits] # Ensure ints
        self.age = age
        self.trials = []
        self.practice_trials = []
        self.main_trials = []
        
    def generate_trials(self, loads=[2, 4, 6], snrs=[10, 5, 0], main_reps=22, num_practice=3, randomize=False):
        # Validate inputs
        valid_loads = [l for l in loads if l <= len(self.available_digits)]
        if not valid_loads:
            valid_loads = [min(3, len(self.available_digits))]
        
        # Define Sorted Conditions (Easy -> Hard)
        # SNR: 10 -> 0 (High SNR is easier)
        # Load: 2 -> 6 (Low Load is easier)
        sorted_conditions = []
        
        # User requested: 10/2 -> 10/4 -> 10/6 -> ...
        # So Outer Loop = SNR (10, 5, 0), Inner Loop = Load (2, 4, 6)
        
        # We need to sort the input lists to ensure order
        # User requested: SNR 10 -> 5 -> 0, Load 2 -> 4 -> 6
        _snrs = sorted(snrs, reverse=True) # 10, 5, 0
        _loads = sorted(valid_loads)      # 2, 4, 6
        
        for snr in _snrs:
            for load in _loads:
                sorted_conditions.append((load, snr))
        
        # Practice Block (Cycle through sorted conditions)
        self.practice_trials = []
        if sorted_conditions:
            import itertools
            practice_cycle = itertools.cycle(sorted_conditions)
            for i in range(num_practice):
                load, snr = next(practice_cycle)
                self.practice_trials.append(self._create_trial(i+1, "Practice", load, snr))
            
        # Main Block
        self.main_trials = []
        all_main_conds = []
        
        if randomize:
            # Full mix
            all_main_conds = sorted_conditions * main_reps
            random.shuffle(all_main_conds)
        else:
            # Blocked (Sequential by difficulty)
            for cond in sorted_conditions:
                all_main_conds.extend([cond] * main_reps)
        
        for i, (load, snr) in enumerate(all_main_conds):
            self.main_trials.append(self._create_trial(i+1, "Main", load, snr))
            
        return self.practice_trials, self.main_trials

    def _create_trial(self, num, block, load, snr):
        # Sequence
        seq = random.sample(self.available_digits, load)
        
        # Probe
        # 50% Match
        is_match = random.choice([True, False])
        
        if is_match:
            probe = random.choice(seq)
        else:
            remaining = [d for d in self.available_digits if d not in seq]
            if remaining:
                probe = random.choice(remaining)
            else:
                # Should not happen if load < available
                probe = random.choice([d for d in self.available_digits if d not in seq]) if [d for d in self.available_digits if d not in seq] else seq[0] # Fallback
                is_match = True # Force match if no lures possible
                
        return {
            'timestamp': str(datetime.now()),
            'subject_id': self.subject_id,
            'session': self.session_num,
            'block': block,
            'trial_num': num,
            'load': load,
            'snr': snr,
            'digits': seq,
            'probe': probe,
            'is_match': is_match,
            'response': None,
            'is_correct': None,
            'rt': None
        }

    def export_data(self, all_trials_data):
        """Converts list of trial dicts to CSV."""
        if not all_trials_data:
            # Return headers only
            cols = ['timestamp', 'subject_id', 'session', 'block', 'trial_num', 'load', 'snr', 'digits', 'probe', 'is_match', 'response', 'is_correct', 'rt']
            return pd.DataFrame(columns=cols).to_csv(index=False)
            
        df = pd.DataFrame(all_trials_data)
        # Flatten digits list
        if 'digits' in df.columns:
            df['digits'] = df['digits'].apply(lambda x: str(x))
            
        return df.to_csv(index=False)

    def save_trial(self, trial_data, filename):
        """Appends a single trial to a CSV file."""
        df = pd.DataFrame([trial_data])
        
        # Flatten digits list
        if 'digits' in df.columns:
            df['digits'] = df['digits'].apply(lambda x: str(x))

        import os
        # Check if file exists to determine if we need header
        header = not os.path.exists(filename)
        
        try:
            df.to_csv(filename, mode='a', header=header, index=False)
        except Exception as e:
            print(f"Error saving trial: {e}")

