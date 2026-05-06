# -*- coding: utf-8 -*-
"""Portable file-backed memory store for generated character Skills.

No framework dependency. Storage layout under a character Skill directory:

memory/
  events.jsonl          raw chronological events, append-only
  facts.json            stable user/character/relationship facts
  relationship.json     compact relationship state
  corrections.jsonl     character correction records
  summaries.md          compressed long-term summaries
  index.json            metadata and counters
memory-log.md           human-readable audit log
"""
from __future__ import annotations

import json
import re
import uuid
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from memory_schema import now_iso, default_index, default_facts, default_relationship


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def append_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def read_jsonl(path: Path, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    if limit is not None:
        lines = lines[-limit:]
    out = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


class SkillMemoryStore:
    def __init__(self, skill_dir: str | Path):
        self.skill_dir = Path(skill_dir)
        self.memory_dir = self.skill_dir / "memory"
        self.events_path = self.memory_dir / "events.jsonl"
        self.facts_path = self.memory_dir / "facts.json"
        self.relationship_path = self.memory_dir / "relationship.json"
        self.corrections_path = self.memory_dir / "corrections.jsonl"
        self.summaries_path = self.memory_dir / "summaries.md"
        self.index_path = self.memory_dir / "index.json"
        self.human_log_path = self.skill_dir / "memory-log.md"

    def init(self, character: str = "unknown", game: str = "unknown") -> None:
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        if not self.index_path.exists():
            write_json(self.index_path, default_index(character, game))
        if not self.facts_path.exists():
            write_json(self.facts_path, default_facts())
        if not self.relationship_path.exists():
            write_json(self.relationship_path, default_relationship())
        if not self.events_path.exists():
            self.events_path.write_text("", encoding="utf-8")
        if not self.corrections_path.exists():
            self.corrections_path.write_text("", encoding="utf-8")
        if not self.summaries_path.exists():
            self.summaries_path.write_text("# 长期摘要\n\n", encoding="utf-8", newline="\n")
        if not self.human_log_path.exists():
            self.human_log_path.write_text(
                f"# {character} 长期记忆日志\n\n"
                f"## 元数据\n- 角色：{character}\n- 游戏：{game}\n- 创建时间：{now_iso()}\n- 最后更新：{now_iso()}\n- 记录条数：0\n\n"
                f"## 记忆条目\n\n（暂无记录，对话中将自动积累）\n",
                encoding="utf-8", newline="\n"
            )
        self.recount()

    def recount(self) -> Dict[str, Any]:
        index = read_json(self.index_path, default_index())
        facts = read_json(self.facts_path, default_facts())
        relationship = read_json(self.relationship_path, default_relationship())
        index["updated_at"] = now_iso()
        index["stats"] = {
            "events": len(read_jsonl(self.events_path)),
            "facts": self._count_facts(facts),
            "relationship_events": len(relationship.get("shared_history", [])),
            "corrections": len(read_jsonl(self.corrections_path)),
            "summaries": len(re.findall(r"^##\s+", self.summaries_path.read_text(encoding="utf-8") if self.summaries_path.exists() else "", re.M)),
        }
        write_json(self.index_path, index)
        return index

    def _count_facts(self, facts: Dict[str, Any]) -> int:
        count = 0
        def walk(x: Any):
            nonlocal count
            if isinstance(x, dict):
                for v in x.values(): walk(v)
            elif isinstance(x, list):
                count += len(x)
        walk(facts)
        return count

    def record_event(self, role: str, content: str, session_id: str = "default", speaker: Optional[str] = None, importance: float = 0.3, tags: Optional[List[str]] = None) -> Dict[str, Any]:
        self.init_if_needed()
        event = {
            "id": str(uuid.uuid4()),
            "time": now_iso(),
            "session_id": session_id,
            "role": role,
            "speaker": speaker or role,
            "content": content,
            "importance": importance,
            "tags": tags or []
        }
        append_jsonl(self.events_path, event)
        self.recount()
        return event

    def init_if_needed(self) -> None:
        if not self.index_path.exists():
            self.init()

    def upsert_fact(self, category: str, field: str, value: Any, source_event_id: Optional[str] = None, confidence: float = 0.8) -> Dict[str, Any]:
        self.init_if_needed()
        facts = read_json(self.facts_path, default_facts())
        if category not in facts or not isinstance(facts.get(category), dict):
            facts[category] = {}
        if field not in facts[category]:
            facts[category][field] = []
        item = {
            "value": value,
            "confidence": confidence,
            "source_event_id": source_event_id,
            "updated_at": now_iso()
        }
        target = facts[category][field]
        if isinstance(target, list):
            if not any(x.get("value") == value if isinstance(x, dict) else x == value for x in target):
                target.append(item)
        else:
            facts[category][field] = item
        write_json(self.facts_path, facts)
        self.append_human_log("事实记忆", "fact", f"{category}.{field} = {value}", source_event_id)
        self.recount()
        return item

    def set_relationship(self, field: str, value: Any, source_event_id: Optional[str] = None) -> None:
        self.init_if_needed()
        rel = read_json(self.relationship_path, default_relationship())
        if field in {"tone", "user_calls_character", "boundaries", "shared_history"}:
            rel.setdefault(field, [])
            if value not in rel[field]:
                rel[field].append(value)
        else:
            rel[field] = value
        rel["updated_at"] = now_iso()
        write_json(self.relationship_path, rel)
        self.append_human_log("关系记忆", "relationship", f"{field} = {value}", source_event_id)
        self.recount()

    def add_correction(self, dimension: str, content: str, source_event_id: Optional[str] = None, status: str = "pending_merge") -> Dict[str, Any]:
        self.init_if_needed()
        item = {
            "id": str(uuid.uuid4()),
            "time": now_iso(),
            "dimension": dimension,
            "content": content,
            "source_event_id": source_event_id,
            "status": status
        }
        append_jsonl(self.corrections_path, item)
        self.append_human_log("角色纠错", "correction", f"[{dimension}] {content}", source_event_id)
        self.recount()
        return item

    def append_summary(self, title: str, content: str) -> None:
        self.init_if_needed()
        with self.summaries_path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(f"\n## {title}\n- 时间：{now_iso()}\n\n{content.strip()}\n")
        self.append_human_log("长期摘要", "summary", title, None)
        self.recount()

    def append_human_log(self, title: str, typ: str, content: str, source_event_id: Optional[str]) -> None:
        if not self.human_log_path.exists():
            self.init_if_needed()
        text = self.human_log_path.read_text(encoding="utf-8")
        text = text.replace("\n（暂无记录，对话中将自动积累）\n", "\n")
        n = len(re.findall(r"^###\s+\[(\d+)\]", text, re.M)) + 1
        entry = (
            f"\n### [{n}] {title}\n"
            f"- 时间：{now_iso()}\n"
            f"- 类型：{typ}\n"
            f"- 内容：{content}\n"
            f"- 来源事件：{source_event_id or 'manual'}\n"
            f"- 是否已写入skill：否\n"
        )
        text = text.rstrip() + "\n" + entry + "\n"
        text = re.sub(r"^- 最后更新：.*$", f"- 最后更新：{now_iso()}", text, flags=re.M)
        text = re.sub(r"^- 记录条数：\d+\s*$", f"- 记录条数：{n}", text, flags=re.M)
        self.human_log_path.write_text(text, encoding="utf-8", newline="\n")


    def list_memories(self, kind: str = "all", limit: int = 50) -> Dict[str, Any]:
        self.init_if_needed()
        data: Dict[str, Any] = {}
        if kind in {"all", "events"}:
            data["events"] = read_jsonl(self.events_path, limit=limit)
        if kind in {"all", "facts"}:
            data["facts"] = read_json(self.facts_path, default_facts())
        if kind in {"all", "relationship"}:
            data["relationship"] = read_json(self.relationship_path, default_relationship())
        if kind in {"all", "corrections"}:
            data["corrections"] = read_jsonl(self.corrections_path, limit=limit)
        if kind in {"all", "summaries"}:
            data["summaries"] = self.summaries_path.read_text(encoding="utf-8") if self.summaries_path.exists() else ""
        if kind in {"all", "index"}:
            data["index"] = self.recount()
        return data

    def search(self, keyword: str, limit: int = 50) -> Dict[str, Any]:
        self.init_if_needed()
        keyword_l = keyword.lower()
        result: Dict[str, Any] = {"events": [], "facts": [], "relationship": [], "corrections": [], "summaries": []}
        for e in read_jsonl(self.events_path):
            if keyword_l in json.dumps(e, ensure_ascii=False).lower():
                result["events"].append(e)
        result["events"] = result["events"][-limit:]

        def walk(prefix: str, obj: Any):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    walk(f"{prefix}.{k}" if prefix else str(k), v)
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    walk(f"{prefix}[{i}]", v)
            else:
                if keyword_l in str(obj).lower():
                    result["facts"].append({"path": prefix, "value": obj})
        walk("", read_json(self.facts_path, default_facts()))
        walk_rel = read_json(self.relationship_path, default_relationship())
        for k, v in walk_rel.items():
            if keyword_l in json.dumps(v, ensure_ascii=False).lower():
                result["relationship"].append({"field": k, "value": v})
        for c in read_jsonl(self.corrections_path):
            if keyword_l in json.dumps(c, ensure_ascii=False).lower():
                result["corrections"].append(c)
        summaries = self.summaries_path.read_text(encoding="utf-8") if self.summaries_path.exists() else ""
        for para in re.split(r"\n(?=##\s+)", summaries):
            if keyword_l in para.lower():
                result["summaries"].append(para.strip())
        return result

    def delete_event(self, event_id: str) -> int:
        self.init_if_needed()
        events = read_jsonl(self.events_path)
        kept = [e for e in events if e.get("id") != event_id]
        if len(kept) == len(events):
            return 0
        self.events_path.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in kept), encoding="utf-8", newline="\n")
        self.append_human_log("删除记忆", "delete", f"删除事件 {event_id}", None)
        self.recount()
        return len(events) - len(kept)

    def clear(self, keep_summaries: bool = False) -> None:
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        character = read_json(self.index_path, default_index()).get("character", "unknown")
        game = read_json(self.index_path, default_index()).get("game", "unknown")
        old_summaries = self.summaries_path.read_text(encoding="utf-8") if keep_summaries and self.summaries_path.exists() else "# 长期摘要\n\n"
        write_json(self.index_path, default_index(character, game))
        write_json(self.facts_path, default_facts())
        write_json(self.relationship_path, default_relationship())
        self.events_path.write_text("", encoding="utf-8")
        self.corrections_path.write_text("", encoding="utf-8")
        self.summaries_path.write_text(old_summaries, encoding="utf-8", newline="\n")
        self.human_log_path.write_text(
            f"# {character} 长期记忆日志\n\n## 元数据\n- 角色：{character}\n- 游戏：{game}\n- 创建时间：{now_iso()}\n- 最后更新：{now_iso()}\n- 记录条数：0\n\n## 记忆条目\n\n（暂无记录，对话中将自动积累）\n",
            encoding="utf-8", newline="\n"
        )
        self.recount()

    def export(self, output: Optional[str | Path] = None) -> Dict[str, Any]:
        self.init_if_needed()
        data = self.list_memories("all", limit=10_000)
        if output:
            write_json(Path(output), data)
        return data

    def auto_summarize(self, threshold: int = 80, keep_recent: int = 30) -> bool:
        """Deterministic compression: summarize older events into summaries.md.

        Raw events are not deleted by default because the principle is to record every
        event. This method adds a compact summary when event count reaches threshold.
        Runtimes may decide whether to prune old events externally.
        """
        self.init_if_needed()
        events = read_jsonl(self.events_path)
        if len(events) < threshold:
            return False
        older = events[:-keep_recent] if keep_recent > 0 else events
        if not older:
            return False
        first = older[0].get("time", "unknown")
        last = older[-1].get("time", "unknown")
        user_points = []
        assistant_points = []
        for e in older[-min(len(older), 60):]:
            content = str(e.get("content", "")).replace("\n", " ").strip()
            if not content:
                continue
            short = content[:120]
            if e.get("role") == "user":
                user_points.append(short)
            elif e.get("role") == "assistant":
                assistant_points.append(short)
        summary = [f"时间范围：{first} 至 {last}", "", "### 用户侧重点"]
        summary += [f"- {x}" for x in user_points[-20:]] or ["- （无）"]
        summary += ["", "### 角色回复侧重点"]
        summary += [f"- {x}" for x in assistant_points[-20:]] or ["- （无）"]
        self.append_summary(f"自动摘要 {first} ~ {last}", "\n".join(summary))
        return True

    def build_context(self, query: str = "", recent: int = 12) -> str:
        self.init_if_needed()
        facts = read_json(self.facts_path, default_facts())
        rel = read_json(self.relationship_path, default_relationship())
        events = read_jsonl(self.events_path, limit=recent)
        summaries = self.summaries_path.read_text(encoding="utf-8") if self.summaries_path.exists() else ""
        lines = ["## 长期记忆上下文", ""]
        calls = rel.get("character_calls_user")
        if calls:
            lines.append(f"- 角色通常称呼用户为：{calls}")
        ucc = rel.get("user_calls_character") or []
        if ucc:
            lines.append(f"- 用户对角色的称呼：{', '.join(map(str, ucc))}")
        tone = rel.get("tone") or []
        if tone:
            lines.append(f"- 互动语气偏好：{', '.join(map(str, tone))}")
        bounds = rel.get("boundaries") or []
        if bounds:
            lines.append(f"- 用户边界/禁区：{', '.join(map(str, bounds))}")
        prefs = facts.get("user", {}).get("preferences", [])
        if prefs:
            lines.append("- 用户偏好：" + "; ".join(str(x.get("value", x)) for x in prefs[-8:]))
        shared = rel.get("shared_history") or []
        if shared:
            lines.append("- 共同经历：" + "; ".join(map(str, shared[-8:])))
        if summaries.strip():
            tail = "\n".join(summaries.strip().splitlines()[-30:])
            lines += ["", "### 长期摘要摘录", tail]
        if events:
            lines += ["", "### 最近事件"]
            for e in events:
                c = str(e.get("content", "")).replace("\n", " ")[:160]
                lines.append(f"- [{e.get('role')}] {c}")
        return "\n".join(lines).strip() + "\n"
