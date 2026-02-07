"""
Script to generate code documentation for PDF submission.

This creates a formatted text file with all source code
organized by module, suitable for PDF conversion.

Authors: Group 51
"""

import os
from pathlib import Path
from datetime import datetime


class CodeDocumentationGenerator:
    """Generate formatted code documentation for PDF export."""
    
    def __init__(self, project_root: str, output_file: str = "docs/code_documentation.txt"):
        """Initialize documentation generator."""
        self.project_root = Path(project_root)
        self.output_file = Path(output_file)
        self.code_sections = []
        
    def add_file(self, filepath: Path, section_name: str = None):
        """Add a source file to documentation."""
        if not filepath.exists():
            print(f"Warning: File not found: {filepath}")
            return
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Determine section name
        if section_name is None:
            section_name = str(filepath.relative_to(self.project_root))
        
        # Count lines
        num_lines = len(content.split('\n'))
        
        self.code_sections.append({
            'name': section_name,
            'path': str(filepath.relative_to(self.project_root)),
            'content': content,
            'lines': num_lines
        })
    
    def scan_directory(self, directory: Path, pattern: str = "*.py"):
        """Recursively scan directory for source files."""
        for filepath in sorted(directory.rglob(pattern)):
            # Skip __pycache__ and test files
            if '__pycache__' in str(filepath) or filepath.name.startswith('test_'):
                continue
            
            self.add_file(filepath)
    
    def generate_documentation(self):
        """Generate formatted documentation."""
        output = []
        
        # Header
        output.append("="*80)
        output.append("DISTRIBUTED K-MEANS CLUSTERING - CODE DOCUMENTATION")
        output.append("="*80)
        output.append("")
        output.append("Course: ML System Optimization")
        output.append("Assignment: Assignment 2")
        output.append("Group: 51")
        output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("")
        output.append("="*80)
        output.append("")
        
        # Table of Contents
        output.append("TABLE OF CONTENTS")
        output.append("-"*80)
        output.append("")
        
        for idx, section in enumerate(self.code_sections, 1):
            output.append(f"{idx:2d}. {section['name']} ({section['lines']} lines)")
        
        output.append("")
        output.append(f"Total: {sum(s['lines'] for s in self.code_sections):,} lines of code")
        output.append("")
        output.append("="*80)
        output.append("")
        output.append("")
        
        # Code sections
        for idx, section in enumerate(self.code_sections, 1):
            output.append("#"*80)
            output.append(f"# {idx}. {section['name']}")
            output.append(f"# File: {section['path']}")
            output.append(f"# Lines: {section['lines']}")
            output.append("#"*80)
            output.append("")
            
            # Add line numbers to code
            lines = section['content'].split('\n')
            for line_num, line in enumerate(lines, 1):
                output.append(f"{line_num:4d} | {line}")
            
            output.append("")
            output.append("")
            output.append("")
        
        # Footer
        output.append("="*80)
        output.append("END OF CODE DOCUMENTATION")
        output.append("="*80)
        
        return '\n'.join(output)
    
    def save_documentation(self):
        """Save documentation to file."""
        # Ensure output directory exists
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate content
        content = self.generate_documentation()
        
        # Save to file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n{'='*60}")
        print("Code Documentation Generated")
        print(f"{'='*60}")
        print(f"Output file: {self.output_file}")
        print(f"Total sections: {len(self.code_sections)}")
        print(f"Total lines: {sum(s['lines'] for s in self.code_sections):,}")
        print(f"File size: {os.path.getsize(self.output_file) / 1024:.1f} KB")
        print(f"{'='*60}\n")
        
        print("To convert to PDF, you can:")
        print("1. Open in VS Code and use 'Print to PDF' extension")
        print("2. Use a command-line tool: enscript or a2ps")
        print("3. Import into Word/Google Docs and export as PDF")
        print("")


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate code documentation for PDF submission'
    )
    parser.add_argument('--project-root', type=str, default='.',
                       help='Project root directory')
    parser.add_argument('--output', type=str, 
                       default='docs/code_documentation.txt',
                       help='Output file path')
    
    args = parser.parse_args()
    
    print("\nGenerating Code Documentation...")
    print("="*60)
    
    # Initialize generator
    generator = CodeDocumentationGenerator(args.project_root, args.output)
    
    # Add specific files in order
    project_root = Path(args.project_root)
    
    # Core implementation files
    print("Adding PySpark implementation files...")
    generator.add_file(project_root / "src/pyspark/kmeans_distributed.py", 
                      "1. PySpark Distributed k-Means Implementation")
    generator.add_file(project_root / "src/pyspark/kmeans_baseline.py",
                      "2. Baseline Single-Node Implementation")
    generator.add_file(project_root / "src/pyspark/run_experiment.py",
                      "3. Experiment Runner")
    
    # Hadoop implementation
    print("Adding Hadoop MapReduce files...")
    generator.add_file(project_root / "src/hadoop/mapper.py",
                      "4. Hadoop Mapper")
    generator.add_file(project_root / "src/hadoop/combiner.py",
                      "5. Hadoop Combiner")
    generator.add_file(project_root / "src/hadoop/reducer.py",
                      "6. Hadoop Reducer")
    
    # Utility files
    print("Adding utility files...")
    generator.add_file(project_root / "src/utils/data_generator.py",
                      "7. Data Generation Utility")
    generator.add_file(project_root / "src/utils/visualization.py",
                      "8. Visualization and Plotting")
    
    # Test files
    print("Adding test files...")
    generator.add_file(project_root / "tests/test_correctness.py",
                      "9. Correctness Tests")
    
    # Generate and save
    generator.save_documentation()
    
    print("\nNext steps:")
    print(f"1. Review the generated file: {args.output}")
    print("2. Convert to PDF using your preferred method")
    print("3. Include in assignment submission")


if __name__ == "__main__":
    main()
