import subprocess
import tempfile
import argparse
from pathlib import Path
import shutil
import zipfile
import csv
import re
import matplotlib.pyplot as plt
from PIL import Image

def run_evo_traj(control, test):
    print("📈 Plotting trajectories (pose-based)...")
    subprocess.run([
        "evo_traj", "tum", control, test,
        "--plot", "--plot_mode", "xyz",
        "--ref", control
    ])

def run_evo_ape_index(control, test, n_to_align, zip_output):
    print("\n🧪 APE using pose index alignment (with synthetic timestamps):")
    result = subprocess.run([
        "evo_ape", "tum", control, test,
        "--align", "--correct_scale",
        "--n_to_align", str(n_to_align),
        "--save_results", zip_output
    ], capture_output=True, text=True)
    print(result.stdout)
    return result.stdout

def extract_ape_metrics(ape_output):
    metrics = {}
    for line in ape_output.splitlines():
        match = re.match(r"\s*(\w+)\s+([\d.]+)", line)
        if match:
            key, value = match.groups()
            metrics[key] = float(value)
    return metrics

def rewrite_with_synthetic_timestamps(in_path, out_path):
    with open(in_path, 'r') as f_in, open(out_path, 'w') as f_out:
        for i, line in enumerate(f_in):
            if line.strip() and not line.startswith("#"):
                parts = line.strip().split()
                if len(parts) == 8:
                    f_out.write(f"{float(i):.6f} {' '.join(parts[1:])}\n")

def save_metrics_to_csv(metrics, csv_path):
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Metric", "Value"])
        for key, value in metrics.items():
            writer.writerow([key, value])
    print(f"📁 APE metrics saved to: {csv_path}")

def extract_and_show_plot(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        plot_file = next((f for f in zip_ref.namelist() if f.endswith('.png')), None)
        if plot_file:
            zip_ref.extract(plot_file)
            print(f"🖼️ APE plot extracted: {plot_file}")
            img = Image.open(plot_file)
            plt.imshow(img)
            plt.title("APE Plot (Index-Aligned)")
            plt.axis('off')
            plt.show()
        else:
            print("⚠️ No PNG plot found in zip.")

def main(control, test, n_to_align):
    temp_dir = tempfile.mkdtemp()
    try:
        control = str(Path(control).resolve())
        test = str(Path(test).resolve())

        # ✅ Step 1: Plot actual trajectories
        run_evo_traj(control, test)

        # ✅ Step 2: Create and save synthetic timestamp files
        synthetic_control = Path("control_synthetic.txt")
        synthetic_test = Path("test_synthetic.txt")
        rewrite_with_synthetic_timestamps(control, synthetic_control)
        rewrite_with_synthetic_timestamps(test, synthetic_test)
        print(f"📝 Synthetic control saved to: {synthetic_control}")
        print(f"📝 Synthetic test saved to: {synthetic_test}")

        # ✅ Step 3: Run index-based APE
        zip_path = str(Path(temp_dir) / "ape_index.zip")
        ape_output = run_evo_ape_index(str(synthetic_control), str(synthetic_test), n_to_align, zip_path)

        # ✅ Step 4: Extract metrics
        metrics = extract_ape_metrics(ape_output)
        if not metrics:
            print("❌ Failed to extract APE metrics.")
            return

        # ✅ Step 5: Save metrics to CSV
        csv_path = "ape_metrics_index.csv"
        save_metrics_to_csv(metrics, csv_path)

        # ✅ Step 6: Extract and display plot
        extract_and_show_plot(zip_path)

        # ✅ Step 7: Summary
        print("\n📊 RMSE Summary:")
        print(f"   Index-based APE RMSE: {metrics.get('rmse', 'N/A')} m")
    finally:
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate SLAM trajectory using index-based APE and extract plot")
    parser.add_argument("control", help="Control (ground truth) TUM file")
    parser.add_argument("test", help="Test (SLAM output) TUM file")
    parser.add_argument("--n_to_align", type=int, default=50, help="Number of poses to align by index")
    args = parser.parse_args()

    main(args.control, args.test, args.n_to_align)