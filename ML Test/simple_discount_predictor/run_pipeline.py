import subprocess
import sys
import time

def run_phase(phase_name, script_name):
    """Run a single phase and handle errors"""
    print(f"\n{'='*50}")
    print(f"RUNNING {phase_name}")
    print(f"{'='*50}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, check=True)
        print(result.stdout)
        
        elapsed = time.time() - start_time
        print(f"✓ {phase_name} completed in {elapsed:.1f}s")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ {phase_name} failed:")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Run all phases of the simplified discount predictor"""
    print("🚀 STARTING SIMPLE DISCOUNT PREDICTOR")
    print("Using optimized Random Forest model only")
    
    phases = [
        ("PHASE 1: Data Loading", "phase1_data_loading.py"),
        ("PHASE 2: Preprocessing", "phase2_preprocessing.py"),
        ("PHASE 3: EDA", "phase3_eda.py"),
        ("PHASE 4: Model Training", "phase4_model_training.py"),
        ("PHASE 5: Evaluation", "phase5_evaluation.py"),
        ("PHASE 6: Prediction", "phase6_prediction.py")
    ]
    
    total_start = time.time()
    
    for phase_name, script_name in phases:
        success = run_phase(phase_name, script_name)
        if not success:
            print(f"\n❌ Pipeline failed at {phase_name}")
            return False
    
    total_elapsed = time.time() - total_start
    
    print(f"\n{'='*50}")
    print("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"Total time: {total_elapsed:.1f}s")
    print("📁 Check submission.csv for final predictions")
    print(f"{'='*50}")
    
    return True

if __name__ == "__main__":
    main()