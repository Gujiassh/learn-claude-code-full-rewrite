from __future__ import annotations

import argparse
from pathlib import Path

from .context_governance import ContextGovernor
from .observability import ObservabilityHub
from .task_board import TaskBoard


def default_data_root() -> Path:
    return Path.cwd() / ".rewrite_data"


def cmd_task(args: argparse.Namespace) -> int:
    board = TaskBoard(default_data_root() / "task_board.json")
    if args.task_action == "add":
        deps = [x for x in args.deps.split(",") if x] if args.deps else []
        item = board.add_task(args.task_id, args.title, deps)
        print(f"[ok] added {item.task_id}")
        return 0
    if args.task_action == "list":
        rows = board.list_tasks()
        print(f"[ok] tasks={len(rows)}")
        for row in rows:
            print(
                f"- {row.task_id} {row.status} deps={','.join(row.deps)} assignee={row.assignee}"
            )
        return 0
    if args.task_action == "claim":
        row = board.claim_next_ready(args.assignee)
        if row is None:
            print("[ok] no ready task")
            return 0
        print(f"[ok] claimed {row.task_id} by {row.assignee}")
        return 0
    if args.task_action == "complete":
        row = board.complete(args.task_id)
        print(f"[ok] completed {row.task_id}")
        return 0
    raise ValueError("invalid task action")


def cmd_context(args: argparse.Namespace) -> int:
    path = default_data_root() / "context.json"
    gov = ContextGovernor.load(path)
    if args.context_action == "add":
        gov.add(args.role, args.content)
        gov.save(path)
        print("[ok] context updated")
        return 0
    if args.context_action == "show":
        rows = gov.model_messages()
        print(f"[ok] rows={len(rows)}")
        for row in rows:
            print(f"- {row['role']}: {row['content']}")
        return 0
    raise ValueError("invalid context action")


def cmd_observe(_: argparse.Namespace) -> int:
    hub = ObservabilityHub()
    hub.record("health.check", status="ok", duration_ms=1.0)
    root = default_data_root()
    hub.save_json(root / "metrics.json")
    hub.save_markdown(root / "metrics.md")
    print("[ok] observability report exported")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rewrite-agent")
    sub = parser.add_subparsers(dest="command", required=True)

    task_parser = sub.add_parser("task")
    task_sub = task_parser.add_subparsers(dest="task_action", required=True)

    task_add = task_sub.add_parser("add")
    task_add.add_argument("task_id")
    task_add.add_argument("title")
    task_add.add_argument("--deps", default="")

    task_sub.add_parser("list")

    task_claim = task_sub.add_parser("claim")
    task_claim.add_argument("assignee")

    task_complete = task_sub.add_parser("complete")
    task_complete.add_argument("task_id")

    context_parser = sub.add_parser("context")
    context_sub = context_parser.add_subparsers(dest="context_action", required=True)

    context_add = context_sub.add_parser("add")
    context_add.add_argument("role")
    context_add.add_argument("content")

    context_sub.add_parser("show")

    sub.add_parser("observe")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "task":
        return cmd_task(args)
    if args.command == "context":
        return cmd_context(args)
    if args.command == "observe":
        return cmd_observe(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
