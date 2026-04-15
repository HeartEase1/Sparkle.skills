# Prompt：长期记忆系统

> 每个角色skill携带独立的 `memory-log.md`，对话中自动积累，角色越聊越还原。

## 文件位置

```
skills/{slug}/memory-log.md
```

## memory-log.md 结构

```markdown
# {角色名} 长期记忆日志

## 元数据
- 角色：{name}
- 游戏：{game}
- 创建时间：{ISO 8601}
- 最后更新：{ISO 8601}
- 记录条数：{n}

## 记忆条目

### [{序号}] {标题}
- 时间：{ISO 8601}
- 类型：correction / discovery / feedback / impression
- 维度：profile / personality / interaction / memory / relations
- 内容：{具体内容}
- 证据级别：verbatim / artifact / user_impression
- 是否已写入skill：是 / 否
```

## 触发时机

以下情况**自动**追加到 `memory-log.md`：

| 触发 | 类型 | 说明 |
|------|------|------|
| 用户纠错并确认 | `correction` | 记录纠错内容和证据级别 |
| 对话中发现新角色细节 | `discovery` | 用户提到的官方设定细节 |
| 扮演测试反馈 | `feedback` | 测试中发现的OOC问题 |
| 用户补充印象 | `impression` | 用户的主观理解（不覆盖官方） |

## 写入规则

1. **每次对话结束前**，扫描本次对话，提取新增的角色信息
2. **去重**：与已有条目重复的不写入
3. **分级**：`verbatim` / `artifact` 优先级高于 `user_impression`
4. **已写入skill的条目**标注 `是否已写入skill: 是`

## 记忆应用

加载角色skill时：
1. 读取 `memory-log.md` 中**已写入skill**的条目，已反映在维度文件中
2. 读取**未写入skill**的条目，作为补充上下文
3. 对话中如发现新细节，追加到 `memory-log.md`

## 定期合并

当 `memory-log.md` 条目数 ≥ 20 时，提示用户：

```
记忆日志已积累 {n} 条新信息，建议合并到skill文件以提升角色还原度。

是否现在合并？
  [A] 合并（将未写入的条目批量写入对应维度文件）
  [B] 稍后
```

合并后将所有条目标注 `是否已写入skill: 是`。

## 自检

- [ ] 每次对话是否扫描并追加新发现？
- [ ] 是否正确标注了证据级别？
- [ ] 是否避免了重复条目？
- [ ] 条目数 ≥ 20 时是否提示合并？
