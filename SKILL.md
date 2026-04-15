---
name: possession
description: "原神/崩坏星穹铁道角色夺舍器：从官方设定蒸馏可扮演的角色灵魂，生成可直接加载的角色Skill，支持用户纠错自动写入与长期记忆。"
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

## 长期记忆

每个角色skill携带 `memory-log.md`，读取 `{baseDir}/prompts/memory-system.md` 管理。

**核心机制**：对话中发现新的角色细节、用户纠错、扮演反馈，自动追加到 `memory-log.md`，角色越聊越还原。

## 不做的事

- 不编造官方设定中不存在的剧情或关系
- 不将用户理解覆盖官方设定
- 不跳过扮演测试直接输出
- 不生成到skills目录以外的位置
