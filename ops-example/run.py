"""Run all three steps for one sample: extract, verify, report.

Run it as `python run.py oyster_payroll_changes`. Running it again only sends documents that
are not in output/extractions.jsonl yet.
"""

import sys

import extract
import report
import verify

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python run.py <sample name>  (one of the folders in samples/)")
    sample = sys.argv[1]
    extract.run(sample)
    verify.run(sample)
    report.run(sample)
