<div align="center">

# 花火.skill

### 花导想变成谁，就变成谁。

### AI 化身角色灵魂，让 TA 在你面前活过来。

> “我可以变成任何人——但我选择变成你想见的那个 TA。”
>
> ——致敬《崩坏：星穹铁道》花火（Sparkle）

[![License MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![基于 夺舍skill](https://img.shields.io/badge/基于-夺舍skill-8A2BE2.svg)](https://github.com/Summer907/possession-skill)
[![支持游戏](https://img.shields.io/badge/支持游戏-原神_星铁-red.svg)](#支持游戏)

</div>

---

## 简介

花火.skill 是一个面向角色扮演的 Skill 生成器。

它从官方设定、角色台词、人物关系和剧情材料中提取角色信息，生成可被支持 Skills 的程序加载的角色 Skill，让 AI 更稳定地扮演指定角色。

本项目重构自 **夺舍.skill**，保留五维提取体系与证据分级机制，主要面向：

- 《原神》
- 《崩坏：星穹铁道》

---

## 支持游戏

| 游戏 | 代号 | Wiki 来源 |
|------|------|----------|
| 原神（Genshin Impact） | `genshin` | 萌娘百科 / BWIKI / Fandom |
| 崩坏：星穹铁道（Honkai: Star Rail） | `hsr` | 萌娘百科 / BWIKI / Fandom |

理论上也可以手动粘贴其他作品的设定材料进行蒸馏。

---

## 核心功能

### 1. 生成角色 Skill

示例：

```text
帮我夺舍芙宁娜
蒸馏卡芙卡
生成遐蝶的Skill
```

流程：

```text
Phase 1  接收角色设定（Wiki 获取 / 手动粘贴）
Phase 2  五维提取（profile / personality / interaction / memory / relations）
Phase 3  冲突检查（写入 conflicts.md）
Phase 4  生成角色 Skill 文件包
Phase 5  输出生成路径和加载方式
Phase 6  8 场景扮演测试
Phase 7  质量评分报告
```

### 2. 提示词提炼

示例：

```text
把芙宁娜的skill提炼成提示词
给我卡芙卡的提示词
```

会读取已生成的角色 Skill，整理成可复制到其他 AI 的角色提示词。

### 3. 用户纠错

示例：

```text
这个设定不对，芙宁娜的生日应该是10月13日
卡芙卡不是这样说话的，她更冷静
```

纠错会根据来源与证据级别处理：

```text
verbatim（角色原话）> artifact（官方设定）> user_impression（用户理解）
```

用户理解不会覆盖官方设定，只会作为补充或反馈记录。

---

## 关于长期记忆

请注意：**Skills 本身通常不提供全自动长期记忆写入能力。**

本项目可以在生成的角色 Skill 中附带一个可选的记忆目录和辅助脚本，用于给支持文件写入或脚本调用的运行时接入：

```text
memory/
├── events.jsonl
├── facts.json
├── relationship.json
├── corrections.jsonl
├── summaries.md
└── index.json
```

但这只是一个**可选的运行时辅助协议**，不是所有 Skills 程序都会自动使用它。

如果加载 Skill 的程序没有主动读写这些文件，或没有调用 `scripts/memory_runtime.py`，那么长期记忆不会自动增长。

适用场景：

- 运行时支持文件读写；
- 运行时支持调用 Python 脚本；
- 或平台开发者愿意按该文件结构自行接入。

不适用场景：

- Skill 目录只读且没有外部状态目录；
- 沙箱禁止文件写入；
- 沙箱禁止脚本调用；
- 程序只读取 `SKILL.md`，不支持任何持久化。

简单示例：

```bash
python3 scripts/memory_runtime.py record \
  --skill-dir "../xiadie-skill" \
  --role user \
  --content "以后叫我小灰毛" \
  --extract
```

沙箱或只读目录可使用外部状态目录：

```bash
python3 scripts/memory_runtime.py record \
  --skill-dir "/app/skills/xiadie-skill" \
  --memory-dir "/app/state/xiadie-skill-memory" \
  --role user \
  --content "以后叫我小灰毛" \
  --extract
```

如果你只使用普通 Skills 加载器，请把该功能理解为“可接入的辅助协议”，不要理解为内置自动记忆。

---

## 五维提取体系

每个角色会被整理为五个维度：

```text
profile       角色档案：基本信息、身份、世界观定位
personality   性格价值观：动机、核心矛盾、行为模式
interaction   说话方式：语气、称呼、口头禅、台词
memory        背景故事：关键事件、经历、创伤与转折
relations     人际关系：重要角色与情感联结
```

证据级别：

- `verbatim`：角色原话；
- `artifact`：官方设定 / 游戏内文本；
- `impression`：其他角色评价；
- `user_impression`：用户理解或补充。

---

## 生成结构

生成的角色 Skill 与本 Skill 平级存放：

```text
skill开发/
├── Sparkle.skills/
└── <slug>/
    ├── SKILL.md
    ├── profile.md
    ├── personality.md
    ├── interaction.md
    ├── memory.md
    ├── relations.md
    ├── conflicts.md
    ├── manifest.json
    ├── memory-log.md          # 可选：人类可读记录
    └── memory/                # 可选：运行时记忆辅助协议
        ├── events.jsonl
        ├── facts.json
        ├── relationship.json
        ├── corrections.jsonl
        ├── summaries.md
        └── index.json
```

---

## 项目结构

```text
Sparkle.skills/
├── SKILL.md
├── prompts/
│   ├── profile-extractor.md
│   ├── personality-extractor.md
│   ├── interaction-extractor.md
│   ├── memory-extractor.md
│   ├── relations-extractor.md
│   ├── skill-assembler.md
│   ├── correction-handler.md
│   ├── memory-system.md
│   ├── prompt-distiller.md
│   └── roleplay-tester.md
├── recipes/
│   ├── wiki-sources.md
│   ├── merge-policy.md
│   ├── quality-metrics.md
│   └── ...
├── scripts/
│   ├── fetch_wiki.py
│   ├── quality_check.py
│   ├── memory_runtime.py       # 可选记忆辅助 CLI
│   ├── memory_store.py
│   ├── memory_schema.py
│   └── ...
└── examples/
```

---

## 质量评分

| 维度 | 权重 | 说明 |
|------|------|------|
| 完整度 | 30% | 五维度覆盖情况 |
| 证据率 | 40% | verbatim + artifact 占比 |
| 冲突数 | 10% | 设定冲突数量 |
| 测试通过率 | 20% | 8 场景扮演测试结果 |

评级：

```text
≥ 0.85      优秀
0.70-0.84   良好
0.60-0.69   及格
< 0.60      不合格
```

---

## 致谢

本项目重构自 [possession-skill](https://github.com/Summer907/possession-skill)，致敬其「夺舍」理念与五维提取体系。

花导的变身能力给了这个项目新的名字——她能变成任何人，而这个工具能让 AI 变成你想见的那个 TA。

---

<div align="center">MIT License</div>
