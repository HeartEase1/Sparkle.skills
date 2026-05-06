# -*- coding: utf-8 -*-
"""Skill-native portable long-term memory CLI.

Any Skills-compatible program can integrate by calling this script or by reading
/writing the documented files in memory/.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from memory_store import SkillMemoryStore


def extract_rules(store: SkillMemoryStore, event_id: str, text: str) -> int:
    """Rule-based portable extractor for common RP memory triggers.

    This baseline extractor intentionally has no LLM dependency. It catches
    explicit memories, nicknames, relationship preferences, boundaries,
    corrections, projects and important shared events.
    """
    n = 0
    raw = text.strip()

    def clean(v: str) -> str:
        return v.strip().strip('“”"\' ，。！？!?')

    # Character -> user nickname
    patterns = [
        r"(?:以后|之后|以后都|以后就)?(?:叫我|喊我|称呼我)[：: ]*([^，。！？!?,\s]+)",
        r"你(?:以后|之后|以后都|以后就)?(?:叫我|喊我|称呼我)[：: ]*([^，。！？!?,\s]+)",
        r"我(?:的)?(?:名字|昵称|称呼)是[：: ]*([^，。！？!?,\s]+)",
    ]
    for pat in patterns:
        m = re.search(pat, raw)
        if m:
            name = clean(m.group(1))
            if name:
                store.set_relationship("character_calls_user", name, event_id)
                store.upsert_fact("user", "preferred_names", name, event_id, 0.95)
                n += 1
                break

    # User -> character nickname
    m = re.search(r"我(?:以后|之后|以后都|以后就)?(?:叫你|喊你|称呼你)[：: ]*([^，。！？!?,\s]+)", raw)
    if m:
        name = clean(m.group(1))
        if name:
            store.set_relationship("user_calls_character", name, event_id)
            store.upsert_fact("character", "user_calls_character", name, event_id, 0.9)
            n += 1

    # Explicit remember clauses. Try to capture content after trigger.
    for pat in [r"(?:请|帮我)?记住[：: ]*(.+)", r"记一下[：: ]*(.+)", r"别忘了[：: ]*(.+)"]:
        m = re.search(pat, raw)
        if m:
            val = clean(m.group(1))
            if val:
                store.upsert_fact("misc", "manual_memories", val, event_id, 0.85)
                n += 1
                break

    # Preferences and dislikes
    pref_patterns = [
        (r"我喜欢(.+)", "like"),
        (r"我不喜欢(.+)", "dislike"),
        (r"我希望(.+)", "wish"),
        (r"以后别(.+)", "avoid"),
        (r"不要(.+)", "avoid"),
        (r"可以(.+)", "allow"),
    ]
    for pat, label in pref_patterns:
        m = re.search(pat, raw)
        if m:
            val = clean(m.group(1))
            if val:
                field = "boundaries" if label in {"avoid"} else "preferences"
                store.upsert_fact("user", field, {"type": label, "content": val}, event_id, 0.75)
                if field == "boundaries":
                    store.set_relationship("boundaries", val, event_id)
                n += 1

    # Tone / relationship style
    tone_keywords = ["暧昧", "调侃", "温柔", "毒舌", "撒娇", "严肃", "轻松", "骚一点", "甜一点", "坏一点"]
    hits = [k for k in tone_keywords if k in raw]
    if hits and any(k in raw for k in ["语气", "风格", "说话", "回复", "叫", "互动"]):
        tone = "、".join(hits)
        store.set_relationship("tone", tone, event_id)
        store.upsert_fact("character", "style_preferences", tone, event_id, 0.75)
        n += 1

    # Corrections / OOC feedback
    if any(k in raw for k in ["纠正一下", "不是这样", "设定错了", "你说错了", "不应该", "OOC", "ooc", "不像"]):
        dim = "other"
        if any(k in raw for k in ["语气", "说话", "台词", "称呼"]): dim = "interaction"
        elif any(k in raw for k in ["性格", "动机", "价值观"]): dim = "personality"
        elif any(k in raw for k in ["关系", "对谁", "人际"]): dim = "relations"
        elif any(k in raw for k in ["过去", "背景", "经历", "剧情"]): dim = "memory"
        store.add_correction(dim, raw, event_id)
        n += 1

    # Projects / persistent tasks
    if any(k in raw for k in ["项目", "开发", "代码", "插件", "Skill", "skills", "系统"]):
        if any(k in raw for k in ["我在", "我要", "想做", "正在", "继续", "完善"]):
            store.upsert_fact("user", "projects", raw, event_id, 0.65)
            n += 1

    # Shared important events
    if any(k in raw for k in ["我们", "刚才", "之前", "上次", "以后", "长期", "依赖", "难受"]):
        store.set_relationship("shared_history", raw[:180], event_id)
        n += 1

    return n

def cmd_init(args):
    store = SkillMemoryStore(args.skill_dir)
    store.init(args.character, args.game)
    print(store.memory_dir)
    return 0


def cmd_record(args):
    store = SkillMemoryStore(args.skill_dir)
    event = store.record_event(args.role, args.content, args.session_id, args.speaker, args.importance, args.tags or [])
    extracted = extract_rules(store, event["id"], args.content) if args.extract else 0
    summarized = store.auto_summarize(args.summary_threshold, args.keep_recent) if args.auto_summary else False
    print(f"event_id={event['id']} extracted={extracted} summarized={int(bool(summarized))}")
    return 0


def cmd_remember(args):
    store = SkillMemoryStore(args.skill_dir)
    store.upsert_fact(args.category, args.field, args.value, None, args.confidence)
    print("remembered")
    return 0


def cmd_relation(args):
    store = SkillMemoryStore(args.skill_dir)
    store.set_relationship(args.field, args.value, None)
    print("relationship-updated")
    return 0


def cmd_correction(args):
    store = SkillMemoryStore(args.skill_dir)
    item = store.add_correction(args.dimension, args.content, None)
    print(item["id"])
    return 0


def cmd_summary(args):
    store = SkillMemoryStore(args.skill_dir)
    store.append_summary(args.title, args.content)
    print("summary-added")
    return 0


def cmd_context(args):
    store = SkillMemoryStore(args.skill_dir)
    print(store.build_context(args.query, args.recent))
    return 0


def cmd_stats(args):
    store = SkillMemoryStore(args.skill_dir)
    print(store.recount())
    return 0



def cmd_list(args):
    import json
    store = SkillMemoryStore(args.skill_dir)
    print(json.dumps(store.list_memories(args.kind, args.limit), ensure_ascii=False, indent=2))
    return 0


def cmd_search(args):
    import json
    store = SkillMemoryStore(args.skill_dir)
    print(json.dumps(store.search(args.keyword, args.limit), ensure_ascii=False, indent=2))
    return 0


def cmd_delete(args):
    store = SkillMemoryStore(args.skill_dir)
    if args.event_id:
        print(f"deleted={store.delete_event(args.event_id)}")
    else:
        print("error: currently delete requires --event-id", file=sys.stderr)
        return 1
    return 0


def cmd_clear(args):
    store = SkillMemoryStore(args.skill_dir)
    if not args.yes:
        print("refusing to clear without --yes", file=sys.stderr)
        return 1
    store.clear(args.keep_summaries)
    print("cleared")
    return 0


def cmd_export(args):
    import json
    store = SkillMemoryStore(args.skill_dir)
    data = store.export(args.output)
    if args.output:
        print(args.output)
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def cmd_auto_summary(args):
    store = SkillMemoryStore(args.skill_dir)
    print(f"summarized={int(store.auto_summarize(args.threshold, args.keep_recent))}")
    return 0

def build_parser():
    p = argparse.ArgumentParser(description="Portable Skill-native long-term memory runtime")
    sub = p.add_subparsers(dest="cmd", required=True)
    pi = sub.add_parser("init")
    pi.add_argument("--skill-dir", required=True)
    pi.add_argument("--character", default="unknown")
    pi.add_argument("--game", default="unknown")
    pi.set_defaults(func=cmd_init)

    pr = sub.add_parser("record")
    pr.add_argument("--skill-dir", required=True)
    pr.add_argument("--role", required=True, choices=["user", "assistant", "system", "manual"])
    pr.add_argument("--content", required=True)
    pr.add_argument("--session-id", default="default")
    pr.add_argument("--speaker")
    pr.add_argument("--importance", type=float, default=0.3)
    pr.add_argument("--tags", nargs="*")
    pr.add_argument("--extract", action="store_true", help="run baseline rule-based memory extraction")
    pr.add_argument("--auto-summary", action="store_true", help="run deterministic auto summary after recording")
    pr.add_argument("--summary-threshold", type=int, default=80)
    pr.add_argument("--keep-recent", type=int, default=30)
    pr.set_defaults(func=cmd_record)

    pm = sub.add_parser("remember")
    pm.add_argument("--skill-dir", required=True)
    pm.add_argument("--category", required=True)
    pm.add_argument("--field", required=True)
    pm.add_argument("--value", required=True)
    pm.add_argument("--confidence", type=float, default=0.8)
    pm.set_defaults(func=cmd_remember)

    prel = sub.add_parser("relation")
    prel.add_argument("--skill-dir", required=True)
    prel.add_argument("--field", required=True)
    prel.add_argument("--value", required=True)
    prel.set_defaults(func=cmd_relation)

    pc = sub.add_parser("correction")
    pc.add_argument("--skill-dir", required=True)
    pc.add_argument("--dimension", default="other")
    pc.add_argument("--content", required=True)
    pc.set_defaults(func=cmd_correction)

    ps = sub.add_parser("summary")
    ps.add_argument("--skill-dir", required=True)
    ps.add_argument("--title", required=True)
    ps.add_argument("--content", required=True)
    ps.set_defaults(func=cmd_summary)

    px = sub.add_parser("context")
    px.add_argument("--skill-dir", required=True)
    px.add_argument("--query", default="")
    px.add_argument("--recent", type=int, default=12)
    px.set_defaults(func=cmd_context)

    pst = sub.add_parser("stats")
    pst.add_argument("--skill-dir", required=True)
    pst.set_defaults(func=cmd_stats)


    pl = sub.add_parser("list", help="list stored memories")
    pl.add_argument("--skill-dir", required=True)
    pl.add_argument("--kind", default="all", choices=["all", "events", "facts", "relationship", "corrections", "summaries", "index"])
    pl.add_argument("--limit", type=int, default=50)
    pl.set_defaults(func=cmd_list)

    psea = sub.add_parser("search", help="search memories by keyword")
    psea.add_argument("--skill-dir", required=True)
    psea.add_argument("--keyword", required=True)
    psea.add_argument("--limit", type=int, default=50)
    psea.set_defaults(func=cmd_search)

    pd = sub.add_parser("delete", help="delete one memory event")
    pd.add_argument("--skill-dir", required=True)
    pd.add_argument("--event-id")
    pd.set_defaults(func=cmd_delete)

    pcl = sub.add_parser("clear", help="clear all memory files; requires --yes")
    pcl.add_argument("--skill-dir", required=True)
    pcl.add_argument("--yes", action="store_true")
    pcl.add_argument("--keep-summaries", action="store_true")
    pcl.set_defaults(func=cmd_clear)

    pe = sub.add_parser("export", help="export all memories as JSON")
    pe.add_argument("--skill-dir", required=True)
    pe.add_argument("--output")
    pe.set_defaults(func=cmd_export)

    pas = sub.add_parser("auto-summary", help="create deterministic summary when threshold is reached")
    pas.add_argument("--skill-dir", required=True)
    pas.add_argument("--threshold", type=int, default=80)
    pas.add_argument("--keep-recent", type=int, default=30)
    pas.set_defaults(func=cmd_auto_summary)

    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
