
import json

print("Checking imports...")
try:
    print("Importing xrtm.data.core...")
    print("OK.")

    print("Importing xrtm.eval.core.evaluator...")
    # This might fail if xrtm-eval uses old xrtm-data paths
    print("OK.")

    print("Importing xrtm.train.simulation.backtester...")
    print("OK.")

    print("Importing xrtm.train.metrics...")
    from xrtm.train.metrics import Evaluator
    print("OK.")

except Exception as e:
    print(f"Import Failed: {e}")
    # Print traceback?
    import sys
    import traceback
    traceback.print_exc()
    sys.exit(1)

def verify_eval():
    samples = [
        {
            "prior_alpha": 2.0, "prior_beta": 2.0, # Mean 0.5
            "target_alpha": 8.0, "target_beta": 2.0, # Mean 0.8
        },
        {
            "prior_alpha": 5.0, "prior_beta": 5.0, # Mean 0.5
            "target_alpha": 5.0, "target_beta": 5.0, # Mean 0.5
        }
    ]

    evaluator = Evaluator()
    metrics = evaluator.compute_metrics(samples)

    print("Metrics:")
    print(json.dumps(metrics, indent=2))

    if "kl_divergence" in metrics and "brier_score" in metrics:
        print("VERIFICATION_SUCCESS")
    else:
        print("VERIFICATION_FAILED")

if __name__ == "__main__":
    verify_eval()
