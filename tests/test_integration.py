import unittest
import subprocess
import sys
import os
import json
from pathlib import Path

class TestIntegration(unittest.TestCase):
    def test_full_pipeline_dry_run(self):
        """Test the full pipeline using the newly added --dry-run flag."""
        # Ensure we are in the project root
        project_root = Path(__file__).parent.parent.absolute()
        
        # Run the pipeline with --dry-run
        result = subprocess.run(
            [sys.executable, "tools/run_pipeline.py", "--dry-run"],
            cwd=project_root,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        # Check if the pipeline completed successfully
        self.assertEqual(result.returncode, 0, f"Pipeline failed with stderr: {result.stderr}")
        self.assertIn("--- Pipeline Completed Successfully ---", result.stdout)
        
        # Verify that the intermediate files were created in .tmp
        from datetime import datetime
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        self.assertTrue((project_root / ".tmp" / f"newsletter_{date_str}.json").exists())
        self.assertTrue((project_root / ".tmp" / f"ai_content_{date_str}.json").exists())
        self.assertTrue((project_root / ".tmp" / f"drafts_{date_str}.json").exists())

if __name__ == '__main__':
    unittest.main()
