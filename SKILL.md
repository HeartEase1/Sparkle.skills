---
name: possession
description: "原神/崩坏星穹铁道角色夺舍器：从官方设定蒸馏可扮演的角色灵魂，生成可直接加载的角色Skill，支持用户纠错辅助与可选记忆协议。"
license: MIT
metadata: {"kit_version": "3", "games": ["genshin", "hsr"], "dimensions": ["profile","personality","interaction","memory","relations"]}
---

# 夺舍

## 语言

根据用户**第一条消息**的语言，全程使用同一语言。

## 何时激活

- 用户要「夺舍/蒸馏角色」「做角色扮演」「生成XX的Skill」
- 用户提供原神或崩坏星穹铁道角色名，希望生成可加载的角色Skill


## 支持游戏

| 游戏 | 代号 | Wiki来源 |
|------|------|---------|
| 原神（Genshin Impact） | genshin | 萌娘百科 / BWIKI / Fandom |
| 崩坏：星穹铁道（Honkai: Star Rail） | hsr | 萌娘百科 / BWIKI / Fandom |

## 路径约定

- 本Skill所在目录记为 **`{skillsDir}`**（即本skill的父目录）
- **生成物写入 `{skillsDir}/<slug>/`**（与本skill平级，AI可直接加载）
- 例：本skill在 `/a/Sparkle.skills/`，则生成到 `/a/<slug>/`
- `slug`：小写字母、数字、连字符，与最终 `SKILL.md` 的 `name` 一致

## 操作顺序

### Phase 1：接收角色设定

#### Step 1.1：选择游戏

```
请选择游戏：
  [A] 原神（Genshin Impact）
  [B] 崩坏：星穹铁道（Honkai: Star Rail）
```

#### Step 1.2：选择Wiki来源

```
请选择Wiki来源：
  [1] 萌娘百科（中文首选）
  [2] BWIKI（严谨准确）
  [3] Fandom（英文）
  [4] 手动粘贴设定材料
```

选择[1]-[3]时，读取 `{baseDir}/recipes/wiki-sources.md` 拼接URL，用WebFetch获取内容。

#### Step 1.3：角色设定材料应包含

- 基本信息、角色故事/背景、语音台词、人物关系、官方评述

### Phase 2：分维度提取

按以下维度依次提取，每条标注证据级别：`verbatim` / `artifact` / `impression`

| 维度 | Prompt |
|------|--------|
| profile | `prompts/profile-extractor.md` |
| personality | `prompts/personality-extractor.md` |
| interaction | `prompts/interaction-extractor.md` |
| memory | `prompts/memory-extractor.md` |
| relations | `prompts/relations-extractor.md` |

### Phase 3：冲突检查

读取 `{baseDir}/recipes/merge-policy.md`，矛盾项写入 `conflicts.md`。

### Phase 4：生成Skill

读取 `{baseDir}/prompts/skill-assembler.md`，生成以下文件结构：

```
skills/<slug>/
├── SKILL.md          # 角色扮演入口（AI可直接加载）
├── profile.md
├── personality.md
├── interaction.md
├── memory.md
├── relations.md
├── memory-log.md     # 长期记忆日志（对话中自动更新）
├── conflicts.md
└── manifest.json
```

### Phase 5：告知用户

- 生成路径：`skills/<slug>/`
- 加载方式：将 `skills/<slug>/` 目录加入AI的Skill加载路径即可
- 各维度证据覆盖度、设定冲突提示

### Phase 6：扮演测试

读取 `{baseDir}/prompts/roleplay-tester.md`，执行8场景测试。
- 通过率 ≥ 70%：测试通过
- 通过率 < 70%：提示补充设定材料

### Phase 7：质量报告

读取 `{baseDir}/recipes/quality-metrics.md`，生成质量评分报告，更新 `manifest.json`。

## 提示词提炼

用户说「把XX提炼成提示词」「给我XX的提示词」时，读取 `{baseDir}/prompts/prompt-distiller.md` 处理。

输出包含7个章节：角色简介、核心指令、深层内核记忆、表层人格与语言风格、专属称呼体系、绝对禁区、对话示例。

## 用户纠错

用户对角色设定有异议时，读取 `{baseDir}/prompts/correction-handler.md` 处理。

**核心机制**：纠错验证后**自动写入**对应角色的skill文件，无需用户手动操作。

## 可选记忆辅助协议

生成的角色 Skill 可附带 `memory/` 目录与 `memory-log.md`，用于给支持文件写入或脚本调用的运行时接入。

**重要限制**：Skills 本身通常不支持全自动长期记忆写入。如果加载程序没有主动读写 `memory/`，也没有调用 `{baseDir}/scripts/memory_runtime.py`，记忆不会自动增长。

本功能应作为“可选运行时辅助协议”理解，不作为内置自动长期记忆宣传。

读取 `{baseDir}/prompts/memory-system.md` 获取最小接入方式。

## 不做的事

- 不编造官方设定中不存在的剧情或关系
- 不将用户理解覆盖官方设定
- 不跳过扮演测试直接输出
- 不生成到skills目录以外的位置


### 全局记忆原则

本 Skill 的长期记忆是**角色全局记忆**，不做多用户隔离。所有接入同一个角色 Skill 的程序和用户共享同一份 `memory/`，使该角色拥有连续统一的经历，而不是每个用户一套割裂记忆。

### 记忆管理命令

查看：

```cmd
python "{baseDir}\scripts\memory_runtime.py" list --skill-dir "{skillsDir}\{slug}" --kind all --limit 50
```

搜索：

```cmd
python "{baseDir}\scripts\memory_runtime.py" search --skill-dir "{skillsDir}\{slug}" --keyword "小灰毛"
```

删除单条事件：

```cmd
python "{baseDir}\scripts\memory_runtime.py" delete --skill-dir "{skillsDir}\{slug}" --event-id "事件ID"
```

导出：

```cmd
python "{baseDir}\scripts\memory_runtime.py" export --skill-dir "{skillsDir}\{slug}" --output "memory-export.json"
```

清空：

```cmd
python "{baseDir}\scripts\memory_runtime.py" clear --skill-dir "{skillsDir}\{slug}" --yes
```

### 自动摘要压缩策略

运行时可在记录消息时启用自动摘要：

```cmd
python "{baseDir}\scripts\memory_runtime.py" record --skill-dir "{skillsDir}\{slug}" --role user --content "{消息}" --extract --auto-summary --summary-threshold 80 --keep-recent 30
```

策略：

- 当 `events.jsonl` 事件数达到阈值时，自动把较早事件压缩进 `summaries.md`。
- 默认保留最近 30 条事件作为近期上下文。
- 原始事件默认不删除，保证“每一件事”仍可追溯。
- 回复前使用 `context` 命令时，只注入结构化事实、关系状态、长期摘要摘录和最近事件，避免上下文爆炸。
