#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
Memory manager for character skills.

Provides a small, deterministic file-backed long-term memory system for
Sparkle.skills generated character skills.

Usage examples:
  python scripts/memory_manager.py init --skill-dir D:\skills\sparkle-hsr --name 花火 --game hsr
  python scripts/memory_manager.py append --skill-dir D:\skills\sparkle-hsr --title 用户专属称呼 --type feedback --dimension interaction --content 用户希望被称为“小灰毛”。 --evidence user_impression
  python scripts/memory_manager.py list --skill-dir D:\skills\sparkle-hsr
  python scripts/memory_manager.py count --skill-dir D:\skills\sparkle-hsr
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Iterable, Optional

CST = timezone(timedelta(hours=8))
VALID_TYPES = {"correction", "discovery", "feedback", "impression"}
VALID_DIMENSIONS = {"profile", "personality", "interaction", "memory", "relations"}
VALID_EVIDENCE = {"verbatim", "artifact", "impression", "user_impression"}


def now_iso() -> str:
    return datetime.now(CST).replace(microsecond=0).isoformat()


def memory_path(skill_dir: Path) -> Path:
    return skill_dir / "memory-log.md"


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def normalize_space(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())


def infer_name_game(skill_dir: Path) -> tuple[str, str]:
    skill_md = skill_dir / "SKILL.md"
    text = read_text(skill_md)
    name = skill_dir.name
    game = "unknown"
    m = re.search(r"^#\s+(.+?)\s*$", text, re.M)
    if m:
        name = m.group(1).strip()
    gm = re.search(r'"game"\s*:\s*"([^"]+)"', text)
    if gm:
        game = gm.group(1).strip()
    return name, game


def entry_count(text: str) -> int:
    return len(re.findall(r"^###\s+\[(\d+)\]", text, re.M))


def next_index(text: str) -> int:
    nums = [int(x) for x in re.findall(r"^###\s+\[(\d+)\]", text, re.M)]
    return (max(nums) + 1) if nums else 1


def ensure_log(skill_dir: Path, name: Optional[str] = None, game: Optional[str] = None) -> Path:
    path = memory_path(skill_dir)
    if path.exists():
        return path
    inferred_name, inferred_game = infer_name_game(skill_dir)
    name = name or inferred_name
    game = game or inferred_game
    text = f"""# {name} 长期记忆日志

## 元数据
- 角色：{name}
- 游戏：{game}
- 创建时间：{now_iso()}
- 最后更新：{now_iso()}
- 记录条数：0

## 记忆条目

（暂无记录，对话中将自动积累）
"""
    write_text(path, text)
    return path


def update_metadata(text: str, count: int, updated_at: Optional[str] = None) -> str:
    updated_at = updated_at or now_iso()
    if re.search(r"^- 最后更新：.*$", text, re.M):
        text = re.sub(r"^- 最后更新：.*$", f"- 最后更新：{updated_at}", text, flags=re.M)
    else:
        text = text.replace("## 记忆条目", f"- 最后更新：{updated_at}\n\n## 记忆条目", 1)
    if re.search(r"^- 记录条数：\d+\s*$", text, re.M):
        text = re.sub(r"^- 记录条数：\d+\s*$", f"- 记录条数：{count}", text, flags=re.M)
    else:
        text = text.replace("## 记忆条目", f"- 记录条数：{count}\n\n## 记忆条目", 1)
    return text


def existing_contents(text: str) -> set[str]:
    return {normalize_space(m.group(1)) for m in re.finditer(r"^- 内容：(.+?)\s*$", text, re.M)}


def remove_empty_placeholder(text: str) -> str:
    return text.replace("\n（暂无记录，对话中将自动积累）\n", "\n")


def append_memory(
    skill_dir: Path,
    title: str,
    mem_type: str,
    dimension: str,
    content: str,
    evidence: str,
    written: str = "否",
    when: Optional[str] = None,
    no_dedupe: bool = False,
) -> tuple[bool, str]:
    if mem_type not in VALID_TYPES:
        raise ValueError(f"invalid type: {mem_type}; expected one of {sorted(VALID_TYPES)}")
    if dimension not in VALID_DIMENSIONS:
        raise ValueError(f"invalid dimension: {dimension}; expected one of {sorted(VALID_DIMENSIONS)}")
    if evidence not in VALID_EVIDENCE:
        raise ValueError(f"invalid evidence: {evidence}; expected one of {sorted(VALID_EVIDENCE)}")
    if written not in {"是", "否"}:
        raise ValueError("written must be 是 or 否")

    path = ensure_log(skill_dir)
    text = read_text(path)
    norm = normalize_space(content)
    if not no_dedupe and norm in existing_contents(text):
        return False, "duplicate: same 内容 already exists"

    idx = next_index(text)
    when = when or now_iso()
    entry = f"""### [{idx}] {title.strip()}
- 时间：{when}
- 类型：{mem_type}
- 维度：{dimension}
- 内容：{content.strip()}
- 证据级别：{evidence}
- 是否已写入skill：{written}
"""
    text = remove_empty_placeholder(text).rstrip() + "\n\n" + entry + "\n"
    text = update_metadata(text, entry_count(text), when)
    write_text(path, text)
    return True, f"appended #{idx}"


def mark_written(skill_dir: Path, index: Optional[int] = None) -> int:
    path = ensure_log(skill_dir)
    text = read_text(path)
    changed = 0
    if index is None:
        new_text, changed = re.subn(r"^- 是否已写入skill：否\s*$", "- 是否已写入skill：是", text, flags=re.M)
    else:
        pattern = rf"(###\s+\[{index}\][\s\S]*?^- 是否已写入skill：)否(\s*$)"
        new_text, changed = re.subn(pattern, rf"\1是\2", text, count=1, flags=re.M)
    if changed:
        new_text = update_metadata(new_text, entry_count(new_text))
        write_text(path, new_text)
    return changed


def cmd_init(args: argparse.Namespace) -> int:
    path = ensure_log(Path(args.skill_dir), args.name, args.game)
    print(str(path))
    return 0


def cmd_append(args: argparse.Namespace) -> int:
    ok, msg = append_memory(
        Path(args.skill_dir), args.title, args.type, args.dimension,
        args.content, args.evidence, args.written, args.time, args.no_dedupe,
    )
    print(msg)
    return 0 if ok else 2


def cmd_list(args: argparse.Namespace) -> int:
    path = ensure_log(Path(args.skill_dir))
    text = read_text(path)
    print(text)
    return 0


def cmd_count(args: argparse.Namespace) -> int:
    path = ensure_log(Path(args.skill_dir))
    print(entry_count(read_text(path)))
    return 0


def cmd_mark_written(args: argparse.Namespace) -> int:
    changed = mark_written(Path(args.skill_dir), args.index)
    print(f"updated {changed} entr{'y' if changed == 1 else 'ies'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Manage memory-log.md for a character skill")
    sub = p.add_subparsers(dest="command", required=True)

    pi = sub.add_parser("init", help="create memory-log.md if missing")
    pi.add_argument("--skill-dir", required=True)
    pi.add_argument("--name")
    pi.add_argument("--game")
    pi.set_defaults(func=cmd_init)

    pa = sub.add_parser("append", help="append one memory entry")
    pa.add_argument("--skill-dir", required=True)
    pa.add_argument("--title", required=True)
    pa.add_argument("--type", required=True, choices=sorted(VALID_TYPES))
    pa.add_argument("--dimension", required=True, choices=sorted(VALID_DIMENSIONS))
    pa.add_argument("--content", required=True)
    pa.add_argument("--evidence", required=True, choices=sorted(VALID_EVIDENCE))
    pa.add_argument("--written", default="否", choices=["是", "否"])
    pa.add_argument("--time")
    pa.add_argument("--no-dedupe", action="store_true")
    pa.set_defaults(func=cmd_append)

    pl = sub.add_parser("list", help="print memory-log.md")
    pl.add_argument("--skill-dir", required=True)
    pl.set_defaults(func=cmd_list)

    pc = sub.add_parser("count", help="print memory entry count")
    pc.add_argument("--skill-dir", required=True)
    pc.set_defaults(func=cmd_count)

    pm = sub.add_parser("mark-written", help="mark one or all entries as written into skill files")
    pm.add_argument("--skill-dir", required=True)
    pm.add_argument("--index", type=int)
    pm.set_defaults(func=cmd_mark_written)
    return p


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
