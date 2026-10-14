"""Independent CLI for the shared command service. Stdlib; no desktop or MCP dependency."""
import argparse
from pathlib import Path
from common import print_json, read_json
from command_service import CommandError, CommandService, Context, failure
from hub import Hub, ROOT


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace', '--coordinator-root', dest='workspace', type=Path, default=ROOT)
    p.add_argument('--config', type=Path)
    p.add_argument('--allow-remote-check', action='store_true')
    p.add_argument('--agent', action='store_true', help='Use the same restricted caller role as the desktop adapter')
    sub = p.add_subparsers(dest='action', required=True)
    execute = sub.add_parser('execute')
    execute.add_argument('--request', type=Path, required=True)
    for name in ('show', 'receipt', 'events', 'brief'):
        cmd = sub.add_parser(name)
        cmd.add_argument('--study', required=True)
        if name == 'receipt': cmd.add_argument('--request-id', required=True)
        if name == 'events':
            cmd.add_argument('--after-revision', type=int)
            cmd.add_argument('--after-sha256')
            cmd.add_argument('--limit', type=int, default=50)
    args = p.parse_args()
    try:
        hub = Hub(args.workspace, read_json(args.config)[0] if args.config else None)
        service = CommandService(hub)
        context = Context.local('agent' if args.agent else 'operator', args.allow_remote_check)
        if args.action == 'execute':
            result = service.execute(read_json(args.request, limit=64000)[0], context)
        elif args.action == 'show':
            result = service.query(args.study)
        elif args.action == 'brief':
            from study_context import brief
            result = brief(*hub.store.read(args.study))
        elif args.action == 'receipt':
            result = service.find_receipt(args.study, args.request_id, context)
            if result is None:
                result = {'committed': False, 'request_id': args.request_id, 'submitted_experiments': 0}
        else:
            if (args.after_revision is None) != (args.after_sha256 is None):
                raise CommandError('invalid_cursor', 'Provide both cursor revision and hash')
            after = None if args.after_revision is None else {'revision': args.after_revision, 'sha256': args.after_sha256}
            result = service.events(args.study, after, args.limit)
        print_json(result)
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print_json(failure(exc))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
