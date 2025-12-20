import subprocess
import sys
import time
import os

def run_phase(phase_name, script_name):
    """Run a single phase and handle errors"""
    print(f"\n{'='*60}")
    print(f"RUNNING {phase_name}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print(f"Warnings: {result.stderr}")
        
        elapsed = time.time() - start_time
        print(f"✓ {phase_name} completed in {elapsed:.1f}s")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ {phase_name} failed:")
        print(f"Error: {e.stderr}")
        print(f"Output: {e.stdout}")
        return False

def main():
    """Run all phases of the discount predictor pipeline"""
    print("🚀 STARTING DISCOUNT PREDICTOR PIPELINE")
    print("Multi-model approach with comprehensive analysis")
    
    # Check if we're in the right directory
    if not os.path.exists('phase1_data_understanding.py'):
        print("❌ Error: Run this script from the discount_predictor directory")
        return False
    
    phases = [
        ("PHASE 1: Data Understanding", "phase1_data_understanding.py"),
        ("PHASE 2: Preprocessing", "phase2_preprocessing.py"),
        ("PHASE 3: EDA", "phase3_eda.py"),
        ("PHASE 4: Modeling", "phase4_modeling.py"),
        ("PHASE 5: Evaluation", "phase5_evaluation.py"),
        ("PHASE 6: Final Prediction", "phase6_final_prediction.py"),
        ("PHASE 7: Submission Perfection", "phase7_submission_perfection.py"),
        ("PHASE 8: Score Boosting", "phase8_score_boosting.py")
    ]
    
    total_start = time.time()
    completed_phases = 0
    
    for phase_name, script_name in phases:
        if os.path.exists(script_name):
            success = run_phase(phase_name, script_name)
            if success:
                completed_phases += 1
            else:
                print(f"\n❌ Pipeline failed at {phase_name}")
                print(f"Completed {completed_phases}/{len(phases)} phases")
                return False
        else:
            print(f"⚠️  Skipping {phase_name} - {script_name} not found")
    
    total_elapsed = time.time() - total_start
    
    print(f"\n{'='*60}")
    print("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"Completed all {completed_phases} phases")
    print(f"Total time: {total_elapsed/60:.1f} minutes")
    
    # Show final outputs
    output_files = [
        'submission.csv',
        'final_submission.csv', 
        'perfect_submission.csv',
        'boosted_submission.csv'
    ]
    
    print("\n📁 Generated files:")
    for file in output_files:
        if os.path.exists(file):
            print(f"  ✓ {file}")
    
    print(f"{'='*60}")
    
    return True

if __name__ == "__main__":
    main()