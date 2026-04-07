#!/usr/bin/env python3
"""Pre-commit hook: prevent privado_mantenimiento/ from being committed."""

import subprocess
import sys


def main():
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"], capture_output=True, text=True
    )
    staged = result.stdout.strip().split("\n")
    offending = [f for f in staged if f.startswith("privado_mantenimiento/")]
    if offending:
        print("ERROR: privado_mantenimiento/ files detected in staging area:")
        for f in offending:
            print(f"  - {f}")
        print("\nThese files should NOT be committed. Run:")
        print("  git reset HEAD privado_mantenimiento/")
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
