#!/usr/bin/env python
"""
Quick validation script to ensure everything works.

Run this after setting up the project to verify installation.

Authors: Group 51
"""

import sys
import subprocess
import importlib.util
from pathlib import Path


def check_python_version():
    """Check Python version is 3.8+."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8+ required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_package(package_name, import_name=None):
    """Check if a Python package is installed."""
    if import_name is None:
        import_name = package_name
    
    spec = importlib.util.find_spec(import_name)
    if spec is None:
        print(f"❌ {package_name} not installed")
        return False
    print(f"✅ {package_name} installed")
    return True


def check_dependencies():
    """Check all required dependencies."""
    print("\n" + "="*60)
    print("Checking Dependencies")
    print("="*60)
    
    required = [
        ('numpy', 'numpy'),
        ('pandas', 'pandas'),
        ('scikit-learn', 'sklearn'),
        ('pyspark', 'pyspark'),
        ('matplotlib', 'matplotlib'),
        ('seaborn', 'seaborn'),
        ('pytest', 'pytest'),
    ]
    
    all_installed = True
    for package, import_name in required:
        if not check_package(package, import_name):
            all_installed = False
    
    if not all_installed:
        print("\n⚠️  Some packages missing. Install with:")
        print("   pip install -r requirements.txt")
        return False
    
    return True


def check_project_structure():
    """Check if project structure is correct."""
    print("\n" + "="*60)
    print("Checking Project Structure")
    print("="*60)
    
    required_paths = [
        'src/pyspark/kmeans_distributed.py',
        'src/pyspark/kmeans_baseline.py',
        'src/pyspark/run_experiment.py',
        'src/hadoop/mapper.py',
        'src/hadoop/combiner.py',
        'src/hadoop/reducer.py',
        'src/utils/data_generator.py',
        'src/utils/visualization.py',
        'tests/test_correctness.py',
        'requirements.txt',
        'README.md',
    ]
    
    all_exist = True
    for path in required_paths:
        if Path(path).exists():
            print(f"✅ {path}")
        else:
            print(f"❌ {path} missing")
            all_exist = False
    
    return all_exist


def run_quick_test():
    """Run a quick functionality test."""
    print("\n" + "="*60)
    print("Running Quick Functionality Test")
    print("="*60)
    
    try:
        # Test data generation
        print("\n1. Testing data generation...")
        subprocess.run([
            sys.executable,
            'src/utils/data_generator.py',
            '--num-samples', '100',
            '--num-features', '5',
            '--num-clusters', '3',
            '--output-dir', 'data/test_validation'
        ], check=True, capture_output=True)
        print("   ✅ Data generation works")
        
        # Check if data was created
        if Path('data/test_validation/data.csv').exists():
            print("   ✅ Data file created successfully")
        else:
            print("   ❌ Data file not found")
            return False
        
        # Test baseline k-means
        print("\n2. Testing baseline k-means...")
        subprocess.run([
            sys.executable,
            'src/pyspark/kmeans_baseline.py',
            '--input', 'data/test_validation/data.csv',
            '--output', 'results/test_validation',
            '--k', '3',
            '--max-iterations', '10'
        ], check=True, capture_output=True)
        print("   ✅ Baseline k-means works")
        
        # Check if results were created
        if Path('results/test_validation/centroids.npy').exists():
            print("   ✅ Results saved successfully")
        else:
            print("   ❌ Results not saved")
            return False
        
        print("\n✅ All quick tests passed!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Test failed with error:")
        print(f"   {e}")
        if e.output:
            print(f"   Output: {e.output.decode()}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False


def run_unit_tests():
    """Run unit tests if pytest is available."""
    print("\n" + "="*60)
    print("Running Unit Tests")
    print("="*60)
    
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pytest',
            'tests/test_correctness.py',
            '-v'
        ], capture_output=True, text=True)
        
        print(result.stdout)
        
        if result.returncode == 0:
            print("\n✅ All unit tests passed!")
            return True
        else:
            print("\n⚠️  Some tests failed. See output above.")
            return False
            
    except Exception as e:
        print(f"❌ Could not run tests: {e}")
        print("   Make sure pytest is installed: pip install pytest")
        return False


def main():
    """Main validation function."""
    print("\n" + "="*60)
    print("DISTRIBUTED K-MEANS - PROJECT VALIDATION")
    print("="*60)
    
    results = {
        'Python Version': check_python_version(),
        'Dependencies': check_dependencies(),
        'Project Structure': check_project_structure(),
        'Quick Test': run_quick_test(),
        'Unit Tests': run_unit_tests()
    }
    
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check:20s}: {status}")
    
    all_passed = all(results.values())
    
    print("="*60)
    
    if all_passed:
        print("\n🎉 All validations passed!")
        print("\nYour project is ready. Next steps:")
        print("1. Generate larger datasets:")
        print("   python src/utils/data_generator.py --num-samples 100000 --output-dir data/large")
        print("\n2. Run distributed k-means:")
        print("   spark-submit --master local[4] src/pyspark/kmeans_distributed.py \\")
        print("     --input data/large/data.csv --output results/large --k 5")
        print("\n3. Run experiments:")
        print("   python src/pyspark/run_experiment.py --experiment-type speedup")
        print("\n4. Generate visualizations:")
        print("   python src/utils/visualization.py --results-dir results/experiments")
    else:
        print("\n⚠️  Some validations failed.")
        print("Please fix the issues above before proceeding.")
        print("\nCommon fixes:")
        print("- Install missing packages: pip install -r requirements.txt")
        print("- Ensure you're in the project root directory")
        print("- Check that all files were created properly")
    
    print("")
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
