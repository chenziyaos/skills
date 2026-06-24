---
name: skill-refiner
description: "Meta-skill that refines other skills using deterministic doctrine audit plus real conversation transcripts. Use when the user asks to review/refine/improve/炼化 their skills, when running periodic skill quality reviews, when asking how to make a specific skill trigger more reliably, or when investigating why a skill underperformed in a past session. Do NOT use for inventing new skills (use skill-creator instead) or for editing skills under byted/* (those go through managed-skill-* MR flow)."
version: v0.2.0
allowed-tools: Bash, Read, Grep, Glob, Edit, Write
metadata:
  requires:
    bins: ["python3 >= 3.10"]
  reads:
    - "skillctl audit --json output"
    - "~/.cursor/projects/*/agent-transcripts/*.jsonl"
    - "~/.claude/projects/* (best-effort)"
  writes:
    - ".skill-refiner/reports/<skill>.md (in this skill directory)"
    - ".skill-refiner/snapshots/<date>.json (in this skill directory)"
---

# skill-refiner — Skill Quality Refiner

> Skill 101 第 2 篇把 skill-creator 的迭代闭环描述为"生成 → 用 → 反馈 → 改"，称之为人工 RLHF。
> 这个 skill 把"反馈"这一步从手动升级到自动：用 doctrine audit 抓静态问题，用 transcript 挖掘抓真实摩擦，让 LLM 在两份证据上做编辑判断。

## When to use

触发场景：
- "review my skills" / "炼化一下 skills" / "看看哪个 skill 该改"
- "为什么 \<skill\> 总是不被触发？" / "\<skill\> 在上次会话没起作用"
- "做一次周度 skill 质量回顾"
- 用户提到 `.skill-refiner/queue.md` 或 `.skill-refiner/reports/`

## When NOT to use

- 想知道**该建什么新 skill** → `workflow-packager`（挖 transcript 找重复模式，自下而上）
- 想把**外部** URL / 仓库 / 文档吸收成 skill / rule → `ouro`（CogniVore，自上而下）
- 用户已确认要建一个 skill → `skill-creator`
- 想改 `byted/*/skills/` 下的 skill → 走 `managed-skill-orchestrator` 的 MR 流程，本 skill 默认只对 `self/skills/` 写盘
- 想跑 install / verify / pull → `skillctl` 直接做

## 不变量

- **report-only**：本 skill 自己不修改任何 SKILL.md；产物只有报告文件（`.skill-refiner/reports/<skill>.md`）
- **只对 self/ 写报告**：byted/* 的报告允许生成（用于审视），但 SKILL.md 一律不动
- **离线优先**：不调用任何远程服务；仅读取本地 audit 输出 + 本机 transcript

## 标准工作流

### Step 1 — 选目标

如果用户没指明 skill 名，先 `python3 scripts/build_report.py --list-targets`，列出所有可审视的 skill 与最近一次得分，让用户挑。

### Step 2 — 拉两份证据

```bash
# 确定性合规（静态）
skillctl audit <skill-name> --json --verbose

# 真实摩擦（动态）—— 默认扫 Cursor，可选扫 Claude/Codex
python3 scripts/scan_transcripts.py --skill <skill-name> --days 30
```

`scan_transcripts.py` 抓的摩擦信号在 [references/friction-signals.md](references/friction-signals.md) 列了一份穷举表（用户说"不对"/重试 N 次/明确说"为什么没触发"/agent 误用工具 等）。

### Step 3 — 生成报告

```bash
python3 scripts/build_report.py --skill <skill-name>
```

会把 audit + transcript 信号合成成 `.skill-refiner/reports/<skill-name>.md`，结构见 [references/report-template.md](references/report-template.md)。

### Step 4 — Agent 上手改

读 [references/doctrine.md](references/doctrine.md)（蒸馏自 Skill 101 五篇的可执行 checklist），结合报告里的具体 finding：

1. 找出**最高 ROI 的 1–3 个 finding**（不要一次改 10 处，会失控）
2. 对每个 finding，给出**最小补丁**：preferable diff > preferable rewrite
3. 对 `self/` 下的 skill：用 Edit 工具直接改 `SKILL.md` / 拆 `references/` / 加 `allowed-tools` 等
4. 对 `byted/` 下的 skill：把补丁建议写成报告附录，引导用户用 `managed-skill-orchestrator` 走 MR

### Step 5 — 让 Human 拍板

按 Skill 101 第 2 篇的强调，每一轮都是 RLHF。改完后：
- diff 出来给用户看
- 用 AskUserQuestion 收一次反馈
- 通过则保存，不通过则回滚

## 周期触发（opt-in）

`scripts/refine_weekly.sh` 是个 cron-friendly 入口：
- 跑一次 `skillctl audit --json` 把当周快照存到 `.skill-refiner/snapshots/YYYY-MM-DD.json`
- 对比上次快照，把得分下滑 ≥ 10 分或新增 fail/warn 的 skill 写入 `.skill-refiner/queue.md`
- **不触发任何修改**，只生成观察数据

接入 launchd / cron 示例见脚本注释。

## 注意

- 报告写在**本 skill 自己的目录**（`self/skills/skill-refiner/.skill-refiner/`），不污染被审视的 skill 自身
- transcript 扫描只读不写，不外发任何内容
- audit 是确定性的，可以反复跑；transcript 扫描有 `--days N` 上限避免扫全历史
