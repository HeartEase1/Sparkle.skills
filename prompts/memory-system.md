# Prompt：可选记忆辅助协议

> 注意：Skills 本身通常不保证全自动长期记忆写入。本文件只描述一个可选的文件协议与辅助 CLI，供支持文件写入或脚本调用的运行时接入。

## 定位

生成的角色 Skill 可以附带 `memory/` 目录和 `scripts/memory_runtime.py`，用于保存对话事件、偏好、纠错和摘要。

但如果运行时没有主动读写这些文件，长期记忆不会自动生效。

## 可选文件结构

```text
memory/
├── events.jsonl
├── facts.json
├── relationship.json
├── corrections.jsonl
├── summaries.md
└── index.json
```

`memory-log.md` 可作为人类可读记录保留，但不是必须依赖项。

## 适用条件

至少满足其一：

- 运行时允许读写 Skill 目录；
- 运行时允许指定外部可写状态目录；
- 运行时允许调用 Python 脚本；
- 平台开发者按该文件结构自行实现持久化。

如果程序只加载 `SKILL.md`，不支持任何持久化，则本协议不会自动工作。

## 最小接入示例

记录用户消息：

```bash
python3 scripts/memory_runtime.py record --skill-dir "../xiadie-skill" --role user --content "以后叫我小灰毛" --extract
```

获取可注入上下文：

```bash
python3 scripts/memory_runtime.py context --skill-dir "../xiadie-skill" --query "你应该叫我什么" --recent 12
```

记录助手回复：

```bash
python3 scripts/memory_runtime.py record --skill-dir "../xiadie-skill" --role assistant --content "我记住了。"
```

## 沙箱 / 只读目录

如果 Skill 目录不可写，使用 `--memory-dir` 指向运行时提供的可写目录：

```bash
python3 scripts/memory_runtime.py record \
  --skill-dir "/app/skills/xiadie-skill" \
  --memory-dir "/app/state/xiadie-skill-memory" \
  --role user \
  --content "以后叫我小灰毛" \
  --extract
```

也可以设置环境变量：

```bash
export SKILL_MEMORY_DIR="/app/state/xiadie-skill-memory"
```

## 自动提取范围

`--extract` 只提供基础规则提取，可识别：

- 用户希望被如何称呼；
- 用户如何称呼角色；
- “记住 / 别忘了”类显式记忆；
- 喜好、边界、互动风格；
- 纠错或 OOC 反馈。

## 重要限制

- 这不是 Skills 标准内置能力；
- 不能保证所有程序自动写入；
- 沙箱环境可能禁止写文件或执行脚本；
- 若运行时没有接入，`memory/` 会保持初始化状态。
