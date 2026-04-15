# 生成物目录约定

> 每个蒸馏的角色对应一个子目录。
> `slug` 遵循 Agent Skills 规范：仅小写字母、数字、连字符，与 `SKILL.md` 的 `name` 一致。

## 输入：角色设定目录

用户提供的角色设定目录：

```
<用户路径>/<角色名>/
├── wiki.md      # 完整Wiki风格设定（必需）
├── brief.md     # 第三人称简介（推荐）
└── prompt.md    # 第二人称角色扮演提示（可选）
```

### 读取顺序

1. **先读 `brief.md`**：快速了解角色定位、性格、经历
2. **再读 `wiki.md`**：深入提取详细设定、台词、关系等
3. **参考 `prompt.md`**（如有）：理解角色的第二人称视角

## 输出：蒸馏结果目录

```
<slug>/
├── SKILL.md          # 角色扮演入口 (< 100 行)
├── profile.md        # 角色档案（基本信息、世界观位置）
├── personality.md    # 性格与价值观
├── interaction.md    # 说话方式与台词
├── memory.md         # 背景故事
├── relations.md      # 人际关系网络
├── conflicts.md      # 设定冲突（如有）
├── manifest.json     # 元数据
└── sources/          # 源数据目录
    └── wiki.md       # Wiki原始设定
```

## `SKILL.md` frontmatter

```yaml
---
name: <slug>
description: "蒸馏<角色名>的角色扮演Skill。<简要描述>"
license: MIT
metadata: {"kit": "character-skill", "game": "<游戏名>", "evidence": "<evidence_stats>", "sources": ["<来源>"]}
---
```

- `name` 必须与目录名一致
- `metadata` 须为**单行 JSON**
- `evidence` 简要记录各维度的证据分布，如 `profile=5a; personality=10v+5a; interaction=20v; memory=8a; relations=15a+5i`
- `sources` 列出设定来源

## `manifest.json` 字段

```json
{
  "slug": "<slug>",
  "name": "<角色名>",
  "game": "<游戏名>",
  "built_at": "<ISO 8601>",
  "sources": ["<来源标签>"],
  "kit": "character-skill",
  "dimensions": ["profile", "personality", "interaction", "memory", "relations"],
  "evidence_summary": {
    "verbatim": <数量>,
    "artifact": <数量>,
    "impression": <数量>
  }
}
```

## 各文件用途

| 文件 | 内容 | 主要证据类型 |
|------|------|-------------|
| `profile.md` | 基本信息、世界观定位 | `artifact` |
| `personality.md` | 性格、价值观、动机 | `verbatim` + `artifact` |
| `interaction.md` | 说话方式、台词 | `verbatim` |
| `memory.md` | 背景故事、关键事件 | `artifact` |
| `relations.md` | 人际关系网络 | `artifact` + `impression` |
| `conflicts.md` | 设定冲突记录 | - |

## 质量自检

- [ ] `name` 与目录名一致且符合命名规则？
- [ ] 必需文件是否齐全？
- [ ] `metadata` 确实是单行 JSON？
- [ ] 每个维度文件都有证据标注？
- [ ] `SKILL.md` 正文 < 100 行？
