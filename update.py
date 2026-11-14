"""Fetch the latest repository version and update skills with automatic backups."""
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parent
    args = sys.argv[1:]
    if '--help' in args or '-h' in args:
        print('Usage: python update.py --agent codex|claude|antigravity|all [--scope project --project-root PATH] [--dry-run]')
        print('Pulls the latest Git version, then installs with backup. Reload skills after updating.')
        return 0
    if '--agent' not in args:
        print('Choose an agent, e.g. python update.py --agent codex', file=sys.stderr)
        return 2
    if '--dry-run' not in args:
        try:
            result = subprocess.run(['git', 'pull', '--ff-only'], cwd=root)
        except FileNotFoundError:
            print('Git is required. Install Git or download the latest repository and run install.py --update.', file=sys.stderr)
            return 1
        if result.returncode:
            print('Repository update failed; installed skills were not changed.', file=sys.stderr)
            return result.returncode
    return subprocess.run([sys.executable, str(root/'install.py'),
                           *args, '--update'], cwd=root).returncode


if __name__ == '__main__':
    sys.exit(main())
