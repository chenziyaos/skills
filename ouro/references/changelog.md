# Ouro — Digestion History & Changelog

> This file stores historical ouro-digested annotations and expanded Skill Log entries that were previously inline in SKILL.md. Moved here in v1.1.0 to reduce main body weight.

## Digestion Annotations (moved from SKILL.md header)

### lg-20260521-004 (self, v1.0.2)

- **scope**: P2-7(未验证参数标注) / P2-9(D4/D5 待验证标注 + N=20 标注) / P2-10(§3 M1-M5 增加验证方法列 + 可证伪性声明)
- **decision**: extend-skill
- **confidence**: L
- **reviewer**: chenziyao.never

### lg-20260521-003 (self, v1.0.1)

- **scope**: A1(八步计数统一) / A2(白名单纳入§15-17) / A3(references同步14项) / A4(outcome_window=7d) / B1(pulse_schema_version) / B2(probe.budget_used) / B3(D5 archive→ouro.archive) / B4(§11.12 机械判定信号集)
- **decision**: extend-skill
- **confidence**: L
- **reviewer**: chenziyao.never

### lg-20260521-002 (self, v1.0.0 repo split)

- **scope**: R6.0 清理 v4.x 内联标注 / R6.1 description ≤150 字符 + 触发词移入 §17 / R6.2 §15 Skill Log / R6.3 §16 失败契约 / R6.4 §12 版本差异迁移 / R6.6 §3 与 §11.10 让位原则去重 / R6.9 §5/§10 Source-of-Truth 声明 / R6.10 references/ledger-schema.md inspiration_lineage + 容量数 / R6.11 删除空 references 文件
- **decision**: extend-skill
- **confidence**: L
- **reviewer**: chenziyao.never

### lg-20260521-001 (external input)

- **source**: "Agent 的超级进化" (https://bytedance.larkoffice.com/wiki/XnxKwh7VniWTD1kQsizckCPin1n)
- **sha256**: 14f0ad531e45
- **scope**: R1(§11.12 主见原则) + R2(§8 N12 一次性外链) + R3(§9 N=10 候选注释) + R4(§6 inspiration_lineage 字段)
- **inspiration_lineage**: "无脸男 (千与千寻) → 衔尾蛇 (Ouroboros)"
- **decision**: extend-skill
- **confidence**: L
- **reviewer**: chenziyao.never

### self-digest-0002 (v4.2 → v1.0.0 transition)

- **scope**: 21 处修订（A1-A5 / B1-B3 / C1-C3 / D1-D6 / E1 + 写入原子性 + 去重）
- **decision**: extend-skill
- **confidence**: L
- **reviewer**: chenziyao.never

## Expanded Skill Log (historical versions)

### v1.0.3 — 2026-05-21

- §5 / §10 增加"快捷导读"段落，引导集成方直接读 references/，设计者读主节。

### v1.0.2 — 2026-05-21

- P2-7: §3 overlap 公式、§4.5 Probe Budget、§5 容量阈值、§9 N=20 统一标注"⚠️ 初始值，未经 runtime 验证"。
- P2-9: §9 D4/D5 标注"待 Ledger n≥30 / 待 unattended 宿主接入后验证"。
- P2-10: §3 复利表增加"验证方法"列 + "可证伪性声明"段落。
- Ledger 入账：`lg-20260521-004`（self），outcome=pending。

### v1.0.1 — 2026-05-21

- A1: 工作流计数统一为八步。
- A2: §0.1 / §9 白名单显式纳入 §15 / §16 / §17。
- A3: references/host-adapter.md 同步 14 项。
- A4: 引入 outcome_window_days: 7。
- B1: Health Pulse 增加 pulse_schema_version: 1。
- B2: §5 probe 增加 budget_used 字段。
- B3: §9 D5 archive 目的地明确为 ouro.archive namespace。
- B4: §11.12 主见原则增加机械判定信号集。
- Ledger 入账：`lg-20260521-003`（self），outcome=pending。

### v1.0.0 — 2026-05-21

- 仓库化首发。引入 version / metadata.requires.bins frontmatter；新增 §14 / §15 / §16 / §17；description ≤150 字符；§5 / §10 标注 source of truth；清理 v4.x 标注。
- Ledger 入账：`lg-20260521-002`（self），outcome=pending。

### Pre-1.0 (compact)

- **v4.2**: 21 处修订；Step 5 两阶段提交；Step 5.5 状态机；§0.1 安全护栏；D4/D5 降级；让位纪律；触发词消歧；元元学习边界冻结。
- **v4.1**: Ledger 强制绑定本地 agent 记忆；D1/D2/D3 降级触发器。
- **v4**: M1–M5 复利结构；Decision Ledger schema v1.0；自我吞噬。
- **v3**: 平台无关性立项；§10 抽象 capability 雏形。
- **v2**: Ouroboros 隐喻 pivot；术语通用化。
- **v1**: 原型，基于"无脸男"的 5 步消化器。
