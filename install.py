"""Install the shared skill for Codex, Claude Code or Google Antigravity."""
import argparse
from pathlib import Path
import shutil

NAME = 'progress-bubble'
SOURCE = Path(__file__).resolve().parent / 'skills' / NAME
AGENTS = ('codex', 'claude', 'antigravity')


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
    args = parser.parse_args()
    if args.project_root and args.scope != 'project':
        parser.error('--project-root requires --scope project')
    project = (args.project_root or Path.cwd()).resolve()
    agents = AGENTS if args.agent == 'all' else (args.agent,)
    targets = {}
    for agent in agents:
        target = skill_root(agent,args.scope,project,Path.home()) / NAME
        targets.setdefault(target,[]).append(agent)
    # Preflight every destination before copying anything. Never replace a skill.
    if not args.dry_run:
        for target in targets:
            if target.exists() or target.is_symlink():
                parser.error(f'Already exists: {target}. Back it up and move it before installing.')
    for target, owners in targets.items():
        if not args.dry_run:
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copytree(SOURCE,target,ignore=shutil.ignore_patterns(
                '__pycache__','*.pyc','graphify-out','*.tmp'))
        print(f"{','.join(owners)}: {target}")
    print('Preview only.' if args.dry_run else 'Installed. Reload skills or start a new agent session.')


if __name__ == '__main__':
    main()
