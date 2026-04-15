<div align="center">

# 花火.skill

### 花导想变成谁，就变成谁。

### AI化身角色灵魂，让TA在你面前活过来。

> "我可以变成任何人——但我选择变成你想见的那个TA。"
>
> ——致敬崩坏：星穹铁道 花火（Sparkle）

[![License MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![基于 夺舍skill](https://img.shields.io/badge/基于-夺舍skill-8A2BE2.svg)](https://github.com/Summer907/possession-skill)
[![支持游戏](https://img.shields.io/badge/支持游戏-原神_星铁-red.svg)](#支持游戏)
[![长期记忆](https://img.shields.io/badge/长期记忆-越聊越还原-blue.svg)](#长期记忆系统)

</div>

---

## 为什么叫「花火」？

花火是崩坏：星穹铁道中拥有**变身成他人**的能力——她可以完美模拟任何人的外貌、声音、行为举止，让对方信以为真。

这正是本项目的核心理念：**从官方设定中提取角色灵魂，让AI完美化身为TA。**

本项目重构自**夺舍.skill**，保留其五维提取体系与证据分级机制，专注于**原神**与**崩坏：星穹铁道**两款游戏，并新增：

- **纠错自动写入**：用户纠错后自动更新角色skill文件，无需手动操作
- **长期记忆系统**：每个角色携带 `memory-log.md`，越聊越还原
- **提示词提炼**：一键将角色skill提炼为可直接粘贴的提示词
- **平级输出**：生成的角色skill与本skill平级存放，AI可直接加载

---

## 支持游戏(理论上支持所有游戏)

| 游戏 | 代号 | Wiki来源 |
|------|------|---------|
| 原神（Genshin Impact） | `genshin` | 萌娘百科 / BWIKI / Fandom |
| 崩坏：星穹铁道（Honkai: Star Rail） | `hsr` | 萌娘百科 / BWIKI / Fandom |

---

## 核心功能

### 1. 角色夺舍（生成角色Skill）

对AI说：
```
帮我夺舍芙宁娜
蒸馏卡芙卡
生成符玄的Skill
```

AI会引导你选择游戏和Wiki来源，自动获取设定，完成五维提取，生成可加载的角色skill目录。

**完整流程：**

```
Phase 1  接收角色设定（Wiki自动获取 / 手动粘贴）
Phase 2  五维分维度提取（profile / personality / interaction / memory / relations）
Phase 3  冲突检查（不同来源设定矛盾记录到 conflicts.md）
Phase 4  生成Skill文件包
Phase 5  告知用户生成路径与加载方式
Phase 6  8场景扮演测试（通过率 ≥ 70% 为合格）
Phase 7  质量评分报告（完整度 / 证据率 / 冲突数 / 测试通过率）
```

---

### 2. 提示词提炼

对AI说：
```
把芙宁娜的skill提炼成提示词
给我卡芙卡的提示词
```

AI读取已生成的角色skill，输出包含以下7个章节的完整提示词，可直接粘贴到任意AI的系统提示位置：

| 章节 | 内容 |
|------|------|
| 角色简介 | 身份、世界观定位、核心标签 |
| 核心指令 | 扮演规则，防止OOC |
| 深层内核记忆 | 最影响角色行为的底层经历与动机 |
| 表层人格与语言风格 | 性格关键词、说话方式、标志性台词 |
| 专属称呼体系 | 角色如何称呼各对象、自称方式 |
| 绝对禁区 | 官方设定中的底线与触发点 |
| 对话示例 | 3组场景对话，基于verbatim台词构造 |

---

### 3. 用户纠错（自动写入）

对AI说：
```
这个设定不对，芙宁娜的生日应该是10月13日
卡芙卡不是这样说话的，她更冷静
```

**纠错流程：**

1. AI识别纠错涉及的维度和条目
2. 询问来源（官方Wiki / 游戏内文本 / 角色台词 / 个人理解）
3. 验证来源，标注证据级别
4. 展示修改预览（diff）
5. 确认后**自动写入**对应skill文件 + memory-log.md

**证据级别优先级：**

```
verbatim（角色原话）> artifact（官方设定）> user_impression（用户理解）
```

`user_impression` 不覆盖官方设定，追加到末尾标注「用户补充」。

---

### 4. 长期记忆系统

每个角色skill携带独立的 `memory-log.md`，以下情况自动追加：

| 触发 | 类型 |
|------|------|
| 用户纠错并确认 | `correction` |
| 对话中发现新角色细节 | `discovery` |
| 扮演测试反馈 | `feedback` |
| 用户补充印象 | `impression` |

积累 ≥ 20 条时，AI提示批量合并到维度文件。**角色越聊越还原。**

---

## 五维提取体系

每个角色从官方设定中提取五个维度，每条标注证据级别：

```
profile       角色档案：基本信息、世界观定位、核心标签
personality   性格价值观：动机、核心矛盾、行为模式
interaction   说话方式：口头禅、标志性台词、对话场景
memory        背景故事：关键事件、成长经历、创伤与转折
relations     人际关系：重要角色与情感联结
```

**证据级别：**
- `verbatim` — 角色原话台词（最高权重）
- `artifact` — 官方Wiki / 游戏内文本
- `impression` — 其他角色的评价

矛盾的设定**不强行统一**，记录在 `conflicts.md`。

---

## 生成结构

生成的角色skill与本skill**平级**存放：

```
skill开发/
├── Sparkle.skills/        ← 本skill
└── <slug>/                ← 生成的角色skill（平级）
    ├── SKILL.md           # 角色扮演入口，AI加载即可化身TA
    ├── profile.md         # 角色档案
    ├── personality.md     # 性格与价值观
    ├── interaction.md     # 说话方式与台词
    ├── memory.md          # 背景故事
    ├── relations.md       # 人际关系
    ├── memory-log.md      # 长期记忆日志（自动积累）
    ├── conflicts.md       # 设定冲突记录
    └── manifest.json      # 元数据与质量评分
```

---

## 项目结构

```
Sparkle.skills/
├── SKILL.md                      # 主入口
├── prompts/                      # LLM Prompt模板
│   ├── profile-extractor.md      # 角色档案提取
│   ├── personality-extractor.md  # 性格提取
│   ├── interaction-extractor.md  # 互动风格提取
│   ├── memory-extractor.md       # 背景故事提取
│   ├── relations-extractor.md    # 人际关系提取
│   ├── skill-assembler.md        # Skill组装器
│   ├── correction-handler.md     # 纠错处理器（自动写入）
│   ├── memory-system.md          # 长期记忆系统
│   ├── prompt-distiller.md       # 提示词提炼器
│   └── roleplay-tester.md        # 扮演测试器
├── recipes/                      # 方法论文档
│   ├── wiki-sources.md           # Wiki数据源配置
│   ├── merge-policy.md           # 设定冲突处理策略
│   ├── quality-metrics.md        # 质量评分标准
│   └── ...
├── scripts/                      # Python辅助脚本
│   ├── fetch_wiki.py             # Wiki内容获取
│   ├── quality_check.py          # 质量评分检查
│   └── ...
└── examples/                     # 示例角色skill
    └── sparkle-demo/             # 花火示例
```

---

## 质量评分

每次生成后自动计算综合评分：

| 维度 | 权重 | 说明 |
|------|------|------|
| 完整度 | 30% | 五维度覆盖情况 |
| 证据率 | 40% | verbatim + artifact 占比 |
| 冲突数 | 10% | 设定冲突数量 |
| 测试通过率 | 20% | 8场景扮演测试结果 |

评级：`≥0.85` 优秀 / `0.70-0.84` 良好 / `0.60-0.69` 及格 / `<0.60` 不合格

---

## 致谢

本项目重构自 [possession-skill](https://github.com/Summer907/possession-skill)，致敬其「夺舍」理念与五维提取体系。

花导的变身能力给了这个项目新的名字——她能变成任何人，而这个工具能让AI变成你想见的那个TA。

[QQ交流群](https://qun.qq.com/universal-share/share?ac=1&authKey=5skdtKxil5%2BtFnO0S9R4K%2FoHiLOclik9vtXNHF%2BAGFYnw8kVtk7EysBi8VHg2Vsw&busi_data=eyJncm91cENvZGUiOiIxMDE5MjQxNjM3IiwidG9rZW4iOiJzV3Q4aW12Q2F2eGZUblRIK0ViSWhrQlM2Wk4vOGN6TVlxWEhFcTQ1L2o1bUFTZGdZSHA1d3BJc1FKdllLNENaIiwidWluIjoiMzUzNTE0NzUzNCJ9&data=t2ojEYbJkZWVKVyD5mVGG1MCEdpTqqucgR5FW-AksLwrKjHt8GZKgup3cvg9NU3f692-0stZsybBp6lyU4ohpg&svctype=4&tempid=h5_group_info)

---

<div align="center">MIT License</div>
