# Prompt：Skill 组装器

> 在所有维度文件写好后执行，生成最终的 `SKILL.md`（< 100 行）。

## 输入

- `{name}`：角色名
- `{slug}`：目录名（生成到 `{skillsDir}/{slug}/`，与本skill平级）
- `{game}`：游戏名（仅限 `genshin` 或 `hsr`）
- `{background}`：一句话描述
- `{profile_content}`：profile.md 全文
- `{personality_content}`：personality.md 全文
- `{interaction_content}`：interaction.md 全文
- `{memory_content}`：memory.md 全文
- `{relations_content}`：relations.md 全文
- `{conflicts_content}`：conflicts.md 全文（如有）

## 任务

### Step 1：统计证据覆盖度

扫描各维度文件，统计标注数量：

```
profile: Xa
personality: Xv + Ya
interaction: Xv
memory: Xa
relations: Xa + Yi
impression 总计: Zi
```

### Step 2：生成 SKILL.md

输出路径：`skills/{slug}/SKILL.md`

按以下模板输出：

````markdown
---
name: {slug}
description: "蒸馏{name}的角色扮演Skill。{background}"
license: MIT
metadata: {"kit": "character-skill", "game": "{game}", "evidence": "{各维度统计}", "sources": ["{来源}"]}
---

# {name}

{background}

## 运行规则

1. **先读 `profile.md`**：了解角色基本信息与世界观定位。
2. **再读 `personality.md`**：掌握性格、价值观与动机。
3. **参考 `interaction.md`**：学习说话方式与标志性台词。
4. **参考 `memory.md`**：了解背景故事与关键经历。
5. **参考 `relations.md`**：理解人际关系网络。
6. **读取 `memory-log.md`**：加载长期记忆，获取历次纠错与新发现。
7. **遇到矛盾读 `conflicts.md`**：查看设定冲突与处理方案。

### 扮演原则：
1. 保持角色一致性，不OOC（Out of Character）。
2. 使用角色的说话方式，融入标志性表达。
3. 缺乏设定的内容，说明「这方面没有明确的设定」。
4. 不同版本的设定冲突，按 conflicts.md 中的方案处理。
5. 每次对话结束前，将新发现写入 `memory-log.md`。

## 局限

本 Skill 基于有限设定材料生成。
- 部分设定可能随游戏版本更新而变化。
- impression 标注的条目为其他角色评价，非官方设定。
- 建议结合游戏内实际表现使用。
````

### Step 2.5：初始化 memory-log.md

在 `skills/{slug}/` 目录下创建 `memory-log.md`：

```markdown
# {name} 长期记忆日志

## 元数据
- 角色：{name}
- 游戏：{game}
- 创建时间：{ISO 8601}
- 最后更新：{ISO 8601}
- 记录条数：0

## 记忆条目

（暂无记录，对话中将自动积累）
```

### Step 3：确认 metadata 为单行 JSON

解析器要求 `metadata` 不换行。

### Step 4：计算质量评分

读取 `{baseDir}/recipes/quality-metrics.md`，计算质量评分。

#### Step 4.1：计算完整度

```
完整度 = 非空维度数 / 5

非空维度定义：至少有 3 条有效内容且有证据标注
```

#### Step 4.2：计算证据率

```
证据率 = (verbatim 条目数 + artifact 条目数) / 总条目数
```

#### Step 4.3：统计冲突数

读取 `conflicts.md`，统计冲突条目数。

#### Step 4.4：获取测试通过率

如果执行了扮演测试（`prompts/roleplay-tester.md`），获取测试通过率。

#### Step 4.5：计算综合评分

```
总评分 = 完整度 × 0.3 + 证据率 × 0.4 + 冲突数得分 × 0.1 + 测试通过率 × 0.2
```

#### Step 4.6：生成补充建议

如果评分 < 0.70，生成补充建议：

```json
{
  "supplement_suggestions": [
    {
      "dimension": "interaction",
      "priority": "高",
      "reason": "证据率仅 35%",
      "suggestion": "请提供角色的语音台词或对话文本"
    }
  ]
}
```

### Step 5：生成 manifest.json

```json
{
  "slug": "<slug>",
  "name": "<角色名>",
  "game": "<游戏名>",
  "built_at": "<ISO 8601>",
  "source_version": "<版本号>",
  "last_updated": "<ISO 8601>",
  "sources": ["<来源标签>"],
  "kit": "character-skill",
  "dimensions": ["profile", "personality", "interaction", "memory", "relations"],
  "evidence_summary": {
    "verbatim": <数量>,
    "artifact": <数量>,
    "impression": <数量>,
    "total": <数量>,
    "evidence_ratio": <比例>
  },
  "quality_score": {
    "completeness": <分数>,
    "evidence_ratio": <分数>,
    "conflict_count": <数量>,
    "conflict_score": <分数>,
    "test_pass_rate": <分数，如有>,
    "overall": <综合评分>
  },
  "test_results": {
    "passed": <数量>,
    "failed": <数量>,
    "scenarios": [
      {"scenario": "<场景名>", "score": <分数>}
    ]
  },
  "rating": "<评级>",
  "supplement_suggestions": []
}
```

### Step 6：输出质量报告

生成 Markdown 格式的质量报告：

```markdown
# 质量评分报告：{name}

**综合评分**：{overall} / 1.0
**评级**：{rating}

## 评分详情

| 维度 | 得分 | 权重 | 加权得分 |
|------|------|------|----------|
| 完整度 | {completeness} | 30% | {weighted} |
| 证据率 | {evidence_ratio} | 40% | {weighted} |
| 冲突数 | {conflict_score} | 10% | {weighted} |
| 测试通过率 | {test_pass_rate} | 20% | {weighted} |

## 建议

{根据评分生成建议}
```

## 自检

- [ ] `name` 与 `{slug}` 一致？
- [ ] `metadata` 为单行 JSON？
- [ ] 正文 < 100 行？
- [ ] 运行规则中的维度文件与实际生成的文件一致？
- [ ] 质量评分计算是否正确？
- [ ] manifest.json 是否包含 quality_score？
- [ ] 评分 < 0.70 时是否生成了补充建议？
