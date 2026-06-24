---
name: workflow-packager
description: "Meta-skill that mines local conversation history for repeated workflows and proposes them as new Skills / Subagents / Shell-Automations. Use when the user asks to 回顾 / 总结 / 打包 recent work, when looking for what to automate next, when running periodic 'what should we turn into a skill' reviews. Do NOT use to improve an existing skill (use skill-refiner) or to create a skill the user has already designed (use skill-creator)."
version: v0.2.0
allowed-tools: Bash, Read, Grep, Glob, Edit, Write
metadata:
  reads:
    - "~/.cursor/projects/*/agent-transcripts/*/*.jsonl"
    - "~/.claude/projects/*/  (best-effort)"
    - "~/.codex/log/*  (best-effort)"
    - "skillctl list output (to dedupe against existing skills)"
  writes:
    - ".workflow-packager/candidates/<date>.md (in this skill directory)"
    - ".workflow-packager/watch.md (in this skill directory)"
---

# workflow-packager — Discover the Next Skill

> **生命周期里它的位置**：workflow-packager 负责"发现"，skill-creator 负责"出生"，skillctl 负责"分发"，skill-refiner 负责"成长"。四者解耦，各管一段。

## When to use

- "回顾我最近的工作 / 看看有没有可以打包的流程"
- "我好像每周都在做 X，能不能自动化"
- 周期性回顾（手动或 cron 触发 `scripts/weekly_scan.sh`）
- 看到 `.workflow-packager/watch.md` 里某个候选累积到 3 次以上

## When NOT to use

- 用户已经想清楚要建什么 skill → `skill-creator`
- 想改进一个已存在的 skill → `skill-refiner`
- 只想看 skill 的合规分 → `skillctl audit`
- 想把一个**外部** URL / 仓库 / 文档吸收成 skill → `ouro`（CogniVore）；本 skill 只看你自己的会话历史

## 不变量

- **不会替用户做创建动作**：脚本只产候选表 + watch 累计；起草 `SKILL.md` scaffold 由 LLM 在 Step 4 经用户确认后执行
- **报告/watch 都写在本 skill 自己目录**（`.workflow-packager/`），不污染其他 skill
- **单次至多产出 3 个候选**：硬上限，超出部分入 watch
- **离线**：不调用任何远程服务

## 标准工作流

### Phase 1 — 数据采集

```bash
# 挖最近 N 天 transcript 里的重复模式
python3 scripts/mine_patterns.py --days 30
```

`mine_patterns.py` 的逻辑见 [references/signal-patterns.md](references/signal-patterns.md)：抽取每个 session 的初始 user query → 规范化 → 提取 salient token 作 signature → 按 Jaccard 聚类。

如需补充信号源（lark calendar、IM repeating 任务），见 [references/signal-patterns.md](references/signal-patterns.md) 的扩展点（MVP 未启用）。

### Phase 2 — 交叉去重 + 安全过滤

```bash
python3 scripts/build_candidates.py --days 30 --min 3
```

会做这些事：
1. 跑 `skillctl list --json`（如不支持就降级为表格解析）拿现有 skill 描述
2. 对每个候选 cluster，与所有现有 skill 的 description 算 Jaccard token overlap
   - overlap ≥ 0.7 → 标为 `covered`，从表里剔除（理由记录在报告）
3. 黑名单过滤（见 [references/safety-rules.md](references/safety-rules.md)）：
   - 含 `password|secret|token|key|.env|credential` → drop
   - 含手机号 / 邮箱地址 / 卡号正则 → drop
4. 计算"推荐形式" Skill / Subagent / Shell-Automation（启发式见 doctrine）
5. 写出 `candidates/<date>.md`；同时把 `1 ≤ N < min` 的合并进 `watch.md`

### Phase 3 — 输出候选清单

固定表格格式：

```
| # | 工作流 signature        | 证据 (N 次)        | 频率/周 | 推荐形式         | 理由                  |
|---|-------------------------|--------------------|---------|------------------|-----------------------|
| 1 | git review + commit msg | 8 次 / 30d         | 1.9     | Shell-Automation | 全 deterministic 步骤 |
| 2 | tiktok 容灾盘点          | 5 次 / 30d         | 1.2     | Skill            | 自然语言触发；多步骤   |
| 3 | 周报整理 + 飞书发送      | 4 次 / 30d         | 0.9     | Skill            | 跨工具编排           |
```

低于阈值但出现 ≥ 2 次的进 `watch.md`，下次再跑时累计计数。

### Phase 4 — 执行（需用户确认）

调用 skill 的 LLM 在这一步：

1. 把候选表打印给用户
2. 用 `AskUserQuestion` 让用户挑 **≤ 3** 个；其余自动入 watch
3. 对每个选中项：
   - **Skill** 推荐：起草 `self/skills/<name>/SKILL.md` scaffold（参考 [references/packager-doctrine.md](references/packager-doctrine.md) 的最小模板），写完跑 `skillctl install`，并把生成的 skill name 反写进 candidates 报告
   - **Subagent** 推荐：起草 `~/.claude/agents/<name>.md`（仅 Claude Code 支持）；其他 agent 退化为 Skill
   - **Shell-Automation** 推荐：起草 `scripts/<name>.sh` + 一段 launchd plist / cron 行；不创建 skill 目录
4. 最终摘要：**已创建** / **已跳过** / **入 watch** 三段，写到本次 `candidates/<date>.md` 末尾

### Phase 5 — 周期触发（opt-in）

`scripts/weekly_scan.sh` 是 cron-friendly 入口，**不创建任何东西**，只追加到 `watch.md` 并打印 candidates。接 cron 示例：

```cron
0 10 * * 1  /Users/bytedance/aiops/skills/self/skills/workflow-packager/scripts/weekly_scan.sh >>/tmp/workflow-packager.log 2>&1
```

## 与同仓元 skill 的边界

| | 输入 | 输出 |
|---|---|---|
| `workflow-packager` (本 skill) | transcript 重复模式 | 候选 + watch（自下而上：你重复做了什么） |
| `ouro` (CogniVore) | 外部 URL / 仓库 / 文档 | skill / rule / config artifact（自上而下：你想吸收什么） |
| `skill-creator` (外置) | 用户已确认的需求 | 新 skill 的 SKILL.md |
| `skill-refiner` | 现有 skill + transcript 摩擦 | 改进报告（已有的怎么改） |
| `skillctl audit/install` | source 目录 | 合规分 / 三个 agent 的 symlink |

调用关系：

- **bottom-up 路径**：workflow-packager 产候选 → skill-creator 起草 → skillctl install → skill-refiner 巡检
- **top-down 路径**：ouro 吞噬外部源 → skill-creator 起草（或 ouro 直接产）→ skillctl install → skill-refiner 巡检

两条路径在 skill-creator 这步汇合。本 skill 在 Phase 4 遇到"用户其实是要吸收一个 URL/repo"的信号时（候选的 sample 含 http:// 或外部 repo 路径主导），应当**推荐改用 ouro**而非自己起草。

## 安全护栏

- **不自动写任何 skill 文件**：所有 `SKILL.md` 起草都经过 user-confirmed step
- **黑名单 + 正则**：transcript 里的 secrets / PII 不进候选
- **byted/ 不被建议**：候选只建议落在 `self/skills/`；如用户想推到 byted/* 需手动走 `managed-skill-orchestrator` MR 流程
- **不调用 LLM API**：所有 mining 都是确定性脚本；起草动作由触发本 skill 的 agent 完成

详见 [references/safety-rules.md](references/safety-rules.md)。
