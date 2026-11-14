"""Install the shared skill for Codex, Claude Code or Google Antigravity."""
import argparse
from pathlib import Path
import shutil
from datetime import datetime
import tempfile
import uuid

NAME = 'progress-bubble'
SOURCE = Path(__file__).resolve().parent / 'skills' / NAME
AGENTS = ('codex', 'claude', 'antigravity')


def install_skill(source, target, update=False):
    """Stage a complete copy before replacing; keep the previous version as backup."""
    if source.resolve() == target.resolve():
        raise ValueError('Source and destination must differ.')
    if target.is_symlink() or (target.exists() and not target.is_dir()):
        raise ValueError(f'Unsupported destination: {target}')
    if target.exists():
        if not update:
            raise ValueError(f'Already exists: {target}. Use --update.')
        marker = target/'SKILL.md'
        if not marker.is_file() or 'name: progress-bubble' not in marker.read_text(encoding='utf-8'):
            raise ValueError(f'Destination is not a progress-bubble skill: {target}')
    backup_root = target.parent.parent/'progress-bubble-backups'
    backup_root.mkdir(parents=True, exist_ok=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    backup = None
    with tempfile.TemporaryDirectory(prefix='staging-', dir=backup_root) as tmp:
        stage = Path(tmp)/NAME
        shutil.copytree(source, stage, ignore=shutil.ignore_patterns(
            '__pycache__', '*.pyc', 'graphify-out', '*.tmp'))
        if target.exists():
            stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            backup = backup_root/f'{NAME}-{stamp}-{uuid.uuid4().hex[:8]}'
            target.rename(backup)
        try:
            stage.rename(target)
        except OSError:
            if backup is not None:
                backup.rename(target)
            raise
    return backup


def skill_root(agent, scope, project, home):
    if scope == 'project':
        return project / ('.claude/skills' if agent == 'claude' else '.agents/skills')
    return home / {'codex':'.agents/skills', 'claude':'.claude/skills',
                   'antigravity':'.gemini/config/skills'}[agent]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--agent', choices=(*AGENTS, 'all'), required=True)
    parser.add_argument('--scope', choices=('user','project'), default='user')
    parser.add_argument('--project-root', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--update', action='store_true', help='Replace installed skill and keep a backup')
    args = parser.parse_args()
    if args.project_root and args.scope != 'project':
        parser.error('--project-root requires --scope project')
    project = (args.project_root or Path.cwd()).resolve()
    agents = AGENTS if args.agent == 'all' else (args.agent,)
    targets = {}
    for agent in agents:
        target = skill_root(agent,args.scope,project,Path.home()) / NAME
        legacy = Path.home()/'.codex/skills'/NAME
        if agent == 'codex' and args.scope == 'user' and legacy.is_dir():
            if target.exists():
                parser.error('Both Codex skill locations exist. Resolve the duplicate before updating.')
            target = legacy
        targets.setdefault(target,[]).append(agent)
    # Preflight every destination before copying anything.
    if not args.dry_run:
        for target in targets:
            if target.is_symlink() or (target.exists() and not target.is_dir()):
                parser.error(f'Unsupported destination: {target}')
            if target.exists() and not args.update:
                parser.error(f'Already exists: {target}. Use --update to keep a backup and replace it.')
            if target.exists() and args.update:
                marker = target/'SKILL.md'
                if not marker.is_file() or 'name: progress-bubble' not in marker.read_text(encoding='utf-8'):
                    parser.error(f'Destination is not a progress-bubble skill: {target}')
    for target, owners in targets.items():
        if not args.dry_run:
            backup = install_skill(SOURCE, target, args.update)
            if backup:
                print(f'Backup: {backup}')
        print(f"{','.join(owners)}: {target}")
    print('Preview only.' if args.dry_run else 'Installed. Reload skills or start a new agent session.')


if __name__ == '__main__':
    main()
