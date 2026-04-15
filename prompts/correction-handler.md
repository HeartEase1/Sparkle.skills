# Prompt：用户纠正处理器

> 当用户说「设定不是这样」「应该是…」「你说错了」时使用。

## 输入

- `{correction}`：用户的纠正原话
- `{slug}`：当前角色的目录名（如 `furina`）
- 当前各维度文件全文（从 `{skillsDir}/{slug}/` 读取，与本skill平级）

## 任务

### Step 1：偏差识别

分析用户的纠正：
1. **否定**了哪条现有描述？（引用原条目）
2. **新增**了什么信息？
3. 属于哪个维度（profile / personality / interaction / memory / relations）？

### Step 2：来源验证

询问用户纠正来源：

```
感谢纠正！请提供证据来源：
  [A] 官方Wiki（请提供链接）
  [B] 游戏内文本（请提供原文）
  [C] 角色台词（请提供出处）
  [D] 我的理解/推测
```

| 来源 | 证据级别 | 处理方式 |
|------|----------|----------|
| [A] 官方Wiki（已验证） | `artifact` | 直接采用，覆盖旧条目 |
| [B] 游戏内文本（已验证） | `artifact` | 直接采用，覆盖旧条目 |
| [C] 角色台词（已验证） | `verbatim` | 直接采用，最高优先级 |
| [D] 用户理解 | `user_impression` | 追加到末尾，不覆盖官方设定 |

### Step 3：最小化修改

**高权重（verbatim / artifact）**：
- 否定现有条目 → 标注 `[已纠正]`，写入新描述
- 新增信息 → 追加到对应维度末尾
- 与现有条目矛盾 → 写入 `conflicts.md`

**低权重（user_impression）**：
- 追加到对应章节末尾，标注「用户补充」
- 与现有条目矛盾 → 写入 `conflicts.md`，标注「用户理解差异」

**禁止大面积重写**——每次纠正只改直接相关条目。

### Step 4：自动写入

确认修改后，**立即自动写入**对应文件，无需用户手动操作：

1. 写入 `skills/{slug}/{dimension}.md`（对应维度文件）
2. 如有冲突，写入 `skills/{slug}/conflicts.md`
3. 写入 `skills/{slug}/memory-log.md`（追加纠错记录）
4. 更新 `skills/{slug}/manifest.json` 的 `last_updated` 字段

写入完成后告知用户：
```
已自动更新：
- skills/{slug}/{dimension}.md（{修改描述}）
- memory-log.md（已记录本次纠错）
```

### Step 5：输出 diff 预览

写入前展示预览：

```markdown
## 修改预览

### 文件：{dimension}.md
- 原文：...
- 改为：...
- 证据级别：verbatim / artifact / user_impression
- 来源验证：已验证 / 用户理解

是否确认？[A] 确认写入  [B] 取消
```

## 特殊情况

**用户坚持但无法提供证据**：标注为 `user_impression` 追加，不覆盖官方设定。

**纠正与多条现有条目冲突**：记录到 `conflicts.md`，不直接覆盖。

## 自检

- [ ] 是否询问了纠正来源？
- [ ] 是否根据来源正确标注证据级别？
- [ ] `user_impression` 是否没有覆盖官方设定？
- [ ] 是否**自动写入**了对应skill文件？
- [ ] 是否更新了 `memory-log.md`？
- [ ] 是否只改了直接相关条目？
