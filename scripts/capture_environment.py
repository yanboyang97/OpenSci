"""Inspect this interpreter locally; never installs packages or reads secrets."""
import argparse
from pathlib import Path
import platform
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import environment_record, print_json, write_json

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    record = environment_record()
    if args.out:
        write_json(args.out, record)
    print_json(record)

if __name__ == "__main__":
    main()
