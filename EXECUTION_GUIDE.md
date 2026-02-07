# Step-by-Step Execution Guide for Assignment 2

## Complete Workflow - Execute in This Order

This guide shows exactly what to run and when. Share this with your teammates.

---

## Prerequisites

- Windows PC with PowerShell
- Python 3.8 or higher installed
- Internet connection for package downloads
- 8GB RAM minimum
- 2-3 hours for full execution

---

## STEP 1: Navigate to Project Directory

```powershell
cd "C:\Users\thomap22\OneDrive - Medtronic PLC\Documents\BITS\Semester 2\ML System Optimization\Assignment 2"
```

**Expected Output:** You should be in the project root directory

---

## STEP 2: Create Virtual Environment (Optional but Recommended)

```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1
```

**Expected Output:** 
```
(venv) PS C:\Users\thomap22\...\Assignment 2>
```

**Troubleshooting:** If you get execution policy error:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## STEP 3: Install Dependencies

```powershell
pip install -r requirements.txt
```

**Expected Output:** All packages installing (takes 2-5 minutes)
```
Collecting numpy==1.24.3
Collecting pandas==2.0.3
...
Successfully installed numpy-1.24.3 pandas-2.0.3 ...
```

---

## STEP 4: Validate Setup

```powershell
python validate_setup.py
```

**Expected Output:**
```
============================================================
DISTRIBUTED K-MEANS - PROJECT VALIDATION
============================================================
✅ Python 3.10.12
✅ numpy installed
✅ pandas installed
✅ scikit-learn installed
✅ pyspark installed
...
🎉 All validations passed!
```

**If any checks fail:** Install missing packages with `pip install <package-name>`

---

## STEP 5: Generate Test Dataset (Small - 10K records)

```powershell
python src/utils/data_generator.py `
  --num-samples 10000 `
  --num-features 10 `
  --num-clusters 5 `
  --output-dir data/test
```

**Expected Output:**
```
============================================================
Customer Segmentation Data Generator
============================================================
Number of samples: 10,000
Number of features: 10
Number of clusters: 5
============================================================

Generating data...
Data saved to: data/test/data.csv
```

**Verify:** Check that `data/test/data.csv` exists (should be ~800 KB)

---

## STEP 6: Run Baseline k-Means (Single-Node)

```powershell
python src/pyspark/kmeans_baseline.py `
  --input data/test/data.csv `
  --output results/test_baseline `
  --k 5 `
  --max-iterations 20
```

**Expected Output:**
```
============================================================
Baseline k-Means (Single-Node)
============================================================
Dataset size: 10,000 points
Dimensions: 10
Number of clusters (k): 5
============================================================

Training completed in 1.23 seconds
Iterations: 7
WCSS: 45,231.52

Centroids saved to: results/test_baseline/centroids.npy
Performance metrics saved to: results/test_baseline/performance_metrics.json
```

**Key Metrics to Note:**
- **Training time:** ~1-3 seconds
- **Iterations:** Usually 5-10
- **WCSS:** Note this number for comparison

---

## STEP 7: Run Distributed k-Means (4 Workers)

```powershell
python src/pyspark/kmeans_distributed.py `
  --input data/test/data.csv `
  --output results/test_distributed `
  --k 5 `
  --max-iterations 20 `
  --partitions 4 `
  --master "local[4]"
```

**Expected Output:**
```
============================================================
Distributed k-Means Configuration
============================================================
Dataset size: 10,000 points
Dimensions: 10
Number of clusters (k): 5
Number of partitions: 4
============================================================

Iteration  1 | Time: 0.421s | Centroid shift: 8.234521 | Network reduction: 625.0x
Iteration  2 | Time: 0.312s | Centroid shift: 2.451289 | Network reduction: 625.0x
...
Converged after 7 iterations!

Centroids saved to: results/test_distributed/centroids.npy
```

**Compare with Baseline:**
- For 10K records, distributed might be SLOWER (overhead)
- This is expected and documented in report
- Real benefits show up with larger datasets

---

## STEP 8: Generate Large Dataset (100K records)

```powershell
python src/utils/data_generator.py `
  --num-samples 100000 `
  --num-features 10 `
  --num-clusters 5 `
  --output-dir data/medium
```

**Expected Output:**
```
Generated data shape: (100000, 10)
Data saved to: data/medium/data.csv
```

**File size:** ~8 MB

---

## STEP 9: Run Baseline on Medium Dataset

```powershell
python src/pyspark/kmeans_baseline.py `
  --input data/medium/data.csv `
  --output results/medium_baseline `
  --k 5
```

**Expected Time:** 10-15 seconds

**Note the total_time** from the output - we'll compare this next.

---

## STEP 10: Run Distributed on Medium Dataset

```powershell
python src/pyspark/kmeans_distributed.py `
  --input data/medium/data.csv `
  --output results/medium_distributed `
  --k 5 `
  --partitions 4 `
  --master "local[4]"
```

**Expected Time:** 5-8 seconds (should be FASTER than baseline)

**Key Observation:** This is where you start seeing speedup benefits!

---

## STEP 11: Compare Results

```powershell
# View baseline metrics
Get-Content results/medium_baseline/performance_metrics.json

# View distributed metrics
Get-Content results/medium_distributed/performance_metrics.json
```

**What to Compare:**
- `total_time`: Distributed should be 1.5-2x faster
- `wcss`: Should be nearly identical (< 0.1% difference)
- `total_iterations`: Should be the same

---

## STEP 12: Generate Large Dataset (1M records) - OPTIONAL

**Warning:** This requires ~16GB RAM and takes 5-10 minutes

```powershell
python src/utils/data_generator.py `
  --num-samples 1000000 `
  --num-features 10 `
  --num-clusters 5 `
  --output-dir data/large
```

**Skip this if you have limited resources** - the medium dataset (100K) is sufficient to demonstrate the concepts.

---

## STEP 13: Run Speedup Experiments (Key Results)

```powershell
# Create experiment data directory
New-Item -ItemType Directory -Force -Path data/experiments

# Generate 500K dataset for experiments
python src/utils/data_generator.py `
  --num-samples 500000 `
  --num-features 10 `
  --num-clusters 5 `
  --output-dir data/experiments
```

**Then run speedup experiments:**

```powershell
# Test with 1 worker (baseline)
python src/pyspark/kmeans_distributed.py `
  --input data/experiments/data.csv `
  --output results/speedup_1worker `
  --k 5 `
  --partitions 1 `
  --master "local[1]"

# Test with 2 workers
python src/pyspark/kmeans_distributed.py `
  --input data/experiments/data.csv `
  --output results/speedup_2workers `
  --k 5 `
  --partitions 2 `
  --master "local[2]"

# Test with 4 workers
python src/pyspark/kmeans_distributed.py `
  --input data/experiments/data.csv `
  --output results/speedup_4workers `
  --k 5 `
  --partitions 4 `
  --master "local[4]"
```

**Expected Times (500K dataset):**
- 1 worker: ~60-80 seconds
- 2 workers: ~35-45 seconds (1.8x speedup)
- 4 workers: ~20-25 seconds (3.0x speedup)

**Record these times** - you'll need them for the report.

---

## STEP 14: Calculate Speedup and Efficiency

Create a simple comparison:

```powershell
# View all speedup results
Get-Content results/speedup_1worker/performance_metrics.json | Select-String "total_time"
Get-Content results/speedup_2workers/performance_metrics.json | Select-String "total_time"
Get-Content results/speedup_4workers/performance_metrics.json | Select-String "total_time"
```

**Calculate Speedup Manually:**
```
Speedup = Time_1worker / Time_Nworkers
Efficiency = Speedup / N × 100%

Example:
- 1 worker: 70s
- 4 workers: 22s
- Speedup = 70/22 = 3.18x
- Efficiency = 3.18/4 × 100% = 79.5%
```

---

## STEP 15: Run Tests for Validation

```powershell
# Install pytest if not already installed
pip install pytest

# Run correctness tests
pytest tests/test_correctness.py -v
```

**Expected Output:**
```
tests/test_correctness.py::TestKMeansCorrectness::test_data_generation PASSED
tests/test_correctness.py::TestKMeansCorrectness::test_cluster_balance PASSED
tests/test_correctness.py::TestKMeansCorrectness::test_baseline_convergence PASSED
...
======================== 10 passed in 15.23s ========================
```

**All tests should PASS.** If any fail, check error messages.

---

## STEP 16: Generate Visualizations (OPTIONAL)

**Note:** This requires experiment results from automated runner. For manual setup, skip to Step 17.

If you want to create plots manually:

```powershell
# Create a simple Python script to plot your manual results
# Or use the visualization.py with custom data
```

For assignment submission, you can include **screenshots** of your terminal outputs showing:
- Baseline runtime
- Distributed runtime
- Speedup calculation

---

## STEP 17: Generate Code Documentation PDF

```powershell
python generate_code_docs.py
```

**Expected Output:**
```
============================================================
Code Documentation Generated
============================================================
Output file: docs\code_documentation.txt
Total sections: 9
Total lines: 2,200
File size: 156.3 KB
============================================================
```

**Then convert to PDF:**

**Option 1 - Using VS Code:**
1. Open `docs/code_documentation.txt` in VS Code
2. Install "Markdown PDF" or "Print to PDF" extension
3. Right-click → "Export to PDF"

**Option 2 - Using Word:**
1. Open `docs/code_documentation.txt` in Notepad
2. Copy all content
3. Paste into Word
4. Format with Courier New font
5. Save as PDF

**Option 3 - Using Python:**
```powershell
pip install reportlab
# Then use a script to convert (or use online converter)
```

---

## STEP 18: Convert Report to PDF

The report is in `docs/Assignment2_Report.md`

**Option 1 - Using Pandoc (Best Quality):**
```powershell
# Install pandoc from https://pandoc.org/
pandoc docs/Assignment2_Report.md -o docs/Assignment2_Report.pdf
```

**Option 2 - Using VS Code:**
1. Open `docs/Assignment2_Report.md`
2. Install "Markdown PDF" extension
3. Right-click → "Markdown PDF: Export (pdf)"

**Option 3 - Using Online Converter:**
1. Go to https://www.markdowntopdf.com/
2. Upload `Assignment2_Report.md`
3. Download PDF

**Option 4 - Copy to Word:**
1. Open markdown file in VS Code
2. Press Ctrl+A, Ctrl+C
3. Paste into Word (formatting will be preserved)
4. Save as PDF

---

## STEP 19: Prepare GitHub Repository

```powershell
# Initialize git if not already done
git init

# Create .gitignore (already exists)
# Add all files
git add .

# Commit
git commit -m "Assignment 2: Distributed k-Means Implementation - Complete"

# Create GitHub repo and push
# (Do this on GitHub.com first, then:)
git remote add origin https://github.com/YOUR-USERNAME/distributed-kmeans-assignment2.git
git branch -M main
git push -u origin main
```

**Update FACING_SHEET.md** with your actual GitHub URL.

---

## STEP 20: Prepare Final Submission Package

Create a folder with these three deliverables:

```powershell
# Create submission folder
New-Item -ItemType Directory -Force -Path submission

# Copy deliverables
Copy-Item docs/Assignment2_Report.pdf submission/
Copy-Item docs/code_documentation.pdf submission/
Copy-Item FACING_SHEET.md submission/facing_sheet.txt

# Create a summary file
@"
Assignment 2 Submission - Group 51

Deliverables:
1. GitHub Repository: [YOUR URL HERE]
2. Code Documentation: code_documentation.pdf
3. Technical Report: Assignment2_Report.pdf

Team Members:
- Thomala Priyank Kumar (2024AC05058)
- Diya Roy (2024AC05018)
- Rag Singha (2024AC05771)
- Sayyad Saddamhusen M. (2024AC05017)
- Bhosale Abhishek M. (2024AC05766)

Submission Date: $(Get-Date -Format 'yyyy-MM-dd')
"@ | Out-File submission/README.txt
```

---

## VERIFICATION CHECKLIST

Before submission, verify:

- [ ] **Code runs successfully**
  - [ ] Baseline k-means works
  - [ ] Distributed k-means works
  - [ ] Tests pass

- [ ] **Results are correct**
  - [ ] WCSS values match between baseline and distributed
  - [ ] Speedup observed on medium/large datasets
  - [ ] All metrics collected

- [ ] **Deliverables ready**
  - [ ] GitHub repository created and pushed
  - [ ] Code documentation PDF generated
  - [ ] Technical report PDF generated
  - [ ] FACING_SHEET.md updated with GitHub URL

- [ ] **Documentation complete**
  - [ ] README.md has correct instructions
  - [ ] Report includes all sections (P0-P3)
  - [ ] Code is well-commented

---

## QUICK REFERENCE - Key Commands

```powershell
# Validate setup
python validate_setup.py

# Generate data (small)
python src/utils/data_generator.py --num-samples 10000 --output-dir data/test

# Run baseline
python src/pyspark/kmeans_baseline.py --input data/test/data.csv --output results/baseline --k 5

# Run distributed
python src/pyspark/kmeans_distributed.py --input data/test/data.csv --output results/distributed --k 5 --partitions 4 --master "local[4]"

# Run tests
pytest tests/test_correctness.py -v

# Generate docs
python generate_code_docs.py
```

---

## TIME ESTIMATES

| Task | Time Required |
|------|---------------|
| Setup (Steps 1-4) | 15-20 minutes |
| Small dataset testing (Steps 5-7) | 10 minutes |
| Medium dataset testing (Steps 8-11) | 15 minutes |
| Speedup experiments (Steps 12-14) | 30-45 minutes |
| Testing (Step 15) | 10 minutes |
| Documentation (Steps 17-18) | 30 minutes |
| GitHub setup (Step 19) | 15 minutes |
| **Total** | **2-3 hours** |

---

## TROUBLESHOOTING

### Issue: "pyspark not found"
```powershell
pip install pyspark==3.4.1
```

### Issue: "Java not found" when running Spark
**Solution:** PySpark includes a bundled JVM, but if needed:
```powershell
# Download Java 11 from https://adoptium.net/
# Install and restart PowerShell
```

### Issue: "Invalid maximum heap size" or "Could not create the Java Virtual Machine"
**Solution:** The default 2GB heap size is too large for your system. Edit `src/pyspark/kmeans_distributed.py` and reduce memory:
```python
# Change lines 451-452 from:
conf.set("spark.driver.memory", "2g")
conf.set("spark.executor.memory", "2g")

# To:
conf.set("spark.driver.memory", "1g")
conf.set("spark.executor.memory", "1g")
```
Or run with environment variable:
```powershell
$env:PYSPARK_DRIVER_MEMORY="1g"
python src/pyspark/kmeans_distributed.py ...
```

### Issue: Out of Memory during execution
**Solution:** Reduce dataset size or process in batches:
```powershell
# Use smaller datasets for testing
python src/utils/data_generator.py --num-samples 50000 --output-dir data/small
```

### Issue: Slow performance
**Solution:** 
- Make sure you're using the virtual environment
- Close other applications
- Use smaller datasets for testing
- Distributed benefits show only with 100K+ records

### Issue: Tests failing
**Solution:**
- Check that dependencies are installed: `pip list`
- Verify data was generated: check `data/` folders
- Run with verbose: `pytest -vv`

---

## TEAM COLLABORATION TIPS

**If working with teammates:**

1. **Divide tasks:**
   - Person 1: Run experiments and collect metrics
   - Person 2: Generate visualizations and format report
   - Person 3: Review code and run tests
   - Person 4: Prepare GitHub and documentation
   - Person 5: Final review and submission

2. **Share results:**
   - Create a shared folder for results files
   - Document all metrics in a spreadsheet
   - Take screenshots of successful runs

3. **Version control:**
   - Each person should test on their machine
   - Share the GitHub repository
   - Use branches for any code changes

---

## EXPECTED FINAL RESULTS

After completing all steps, you should have:

✅ **Working Implementation**
- Baseline k-means functioning
- Distributed k-means functioning
- Clear speedup demonstrated (2-3x on 4 workers)

✅ **Test Results**
- All correctness tests passing
- WCSS matching between implementations
- Performance metrics collected

✅ **Deliverables**
- GitHub repository with all code
- Code documentation PDF (~150 pages)
- Technical report PDF (~60 pages)
- Facing sheet with team details

✅ **Evidence of Execution**
- Terminal outputs showing successful runs
- Metrics files in results/ folders
- Performance comparison data

---

## FINAL NOTES

- **Don't skip the validation step** - it catches issues early
- **Start with small datasets** to verify everything works
- **Document any deviations** from expected behavior
- **Keep screenshots** of successful runs
- **Test on one machine first** before distributing to team

**Good luck with your submission!** 🎯

---

**Document Version:** 1.0  
**Last Updated:** January 24, 2026  
**For:** Assignment 2 - ML System Optimization  
**Team:** Group 51
