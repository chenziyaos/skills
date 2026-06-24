# Friction Signals — Mining Conversation Transcripts

scan_transcripts.py 在 chat 历史里寻找的"信号词 + 上下文"清单。每命中一条记为一个 friction event，关联到最近一次提及的 skill 名。

## 信号分类

### Tier 1 — 强信号（基本可确认为该 skill 的真实问题）

| 信号 | 模式 | 解读 |
|---|---|---|
| 用户否定 | `不对` / `不是这样` / `wrong` / `that's not right` 出现在 skill 触发后 5 条消息内 | skill 的执行结果被用户当场否决 |
| 显式抱怨触发 | `为什么(没有)?触发` / `should have used` / `forgot to use` | description 太弱，没被 agent 选中 |
| 显式抱怨遗漏 | `(怎么|why) 没? (.+)? (用|use)? <skill>` | 同上 |
| 中断/取消 | `算了` / `停` / `cancel` / `nevermind` | skill 跑歪 |
| 直接撤回 | `回滚` / `撤回` / `revert` / `undo` | 修改后被回退 |

### Tier 2 — 中等信号（值得人工 review）

| 信号 | 模式 | 解读 |
|---|---|---|
| 重试 | 用户连续 3+ 次让 agent 重做 | skill 不稳定 |
| 详细补充 | 用户在 skill 触发后立刻补一大段"你应该 X 然后 Y" | description 没说清楚行为 |
| 拒绝交互 | 用户多次 reject 同一类 AskUserQuestion | UX 不顺 |
| 用错工具 | agent 用了 Bash + tail 或 cat 读文件（应用 Read） | tool selection guidance 缺失 |

### Tier 3 — 弱信号（统计参考）

| 信号 | 模式 | 解读 |
|---|---|---|
| 长 turn | 单个 turn 超过 N tokens | skill 主入口过重 |
| skill 名首次出现到结案 turn 数 | > 10 | 工作流冗长 |
| 用户主动总结 | 用户最后说"以后这样做：..." | 隐含 PRD 反馈 |

## 提取规范

### 输入

Cursor `agent-transcripts/<uuid>.jsonl`，每行一个 JSON 对象。常见字段：
- `role`: "user" / "assistant" / "tool"
- `content`: 字符串或 block 数组
- `timestamp`: ISO 8601

Claude Code `~/.claude/projects/*/conversation.jsonl`（best-effort，结构可能演化）。

Codex `~/.codex/log/*.json`（best-effort，结构尚未稳定）。

### 命中逻辑

1. 找到所有提及 `<skill-name>` 的 turn（关键词匹配，case-insensitive；skill 名规范化为 `name` 和 `name-replace-dash-with-space`）
2. 围绕命中 turn 取 `± window` 范围（默认 ± 10 turns）
3. 在 window 内匹配上面的 Tier 1/2/3 信号模式
4. 输出 JSON：`{skill, file, hit_turn_idx, signals: [{tier, kind, snippet, turn_idx}]}`

### 隐私

- 输出**默认截断 snippet 到 200 字符**
- 不外发任何 chat 内容
- 报告里只引用 snippet 关键句，不复制整段对话

## 不抓的信号

避免误报：
- 用户在工程上下文说"不对"但与 skill 无关 → 通过 ± window 约束减弱
- 用户用 skill 完成任务后说"算了我自己来" → 这不是 skill 失败而是用户结束
- 工具错误（如 lark-cli 报错）→ 不归 skill，归依赖

skill-refiner 拿到 signals 后，仍应让 LLM/人工做最终判断，friction-signals 只负责"圈出值得看的会话"。

## 分流：friction 应该走 Rule、改 description、还是新 Skill？

蒸馏自《Agent 的超级进化》一文。同一个 friction event，根据**根因**应该走不同的修正通道：

| friction 形态 | 根因 | 修正通道 |
|---|---|---|
| 模型每次都漏掉同一个步骤（例："提交前没跑 audit"） | 缺乏 always-on 约束 | **写 Rule**（`~/.claude/rules/*.md` 或 `.cursor/rules/*.mdc`）— 不要改 Skill |
| 模型理解错触发条件（例：该用 ouro 时用了 workflow-packager） | description 不够精准 | **改 SKILL.md 的 `description`** — 不要写 Rule 也不要新 Skill |
| 模型一犯再犯同一类风格错误（例：中文回复用半角逗号） | 缺乏 always-on 风格约束 | **写 Rule** |
| 模型在一个新的多步骤工作流上反复用相似 prompt | 缺乏可复用的工作流 | **新 Skill 候选**（让 `workflow-packager` 捕到，或人工起草）|
| 模型用错工具（应 Read 却 Bash + cat） | 缺乏 tool-selection guidance | 在最相关的 Skill 里加一行 "use Read not Bash + cat" 或写 Rule |
| 单次 skill 运行的报告/产物超 context 阈值 | 工作流过重 | 改 Skill：拆子 skill 或加 offloading（写文件） |

**误用警告**：

- 不要把"每次都犯的小错"写成 Skill（Skill 是按需加载的，不会每次自动看到；犯错本身的根因就是"没有持续约束"）
- 不要把"description 不准"问题写成 Rule（让 Rule 永远去 override skill 的触发判断，会污染所有其他 skill 的决策）
- 也不要任何一次 friction 都升级为 Skill / Rule（建议 `min_occurrences >= 3` 跨 sessions）
