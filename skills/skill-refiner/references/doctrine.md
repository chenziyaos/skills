# Doctrine Checklist — Skill 101 + Harness 101

蒸馏自飞书《Skill 101》5 篇 + 《Harness 101》12 篇，作为 skill-refiner 修改 SKILL.md 时的判定依据。

> Skill 101 给 skill 层的设计原则；Harness 101 给包围 skill 层的 runtime 经济学（context 压缩、工具幂等性、调度模式）。两者合并构成 audit doctrine。

## 核心命题

| # | 命题 | 来源 |
|---|------|------|
| 1 | Skill = capability bundle，不是单纯 prompt | 前传 |
| 2 | discovery 靠 frontmatter metadata 扫描，不是 RAG | 前传 |
| 3 | Progressive Disclosure：主入口轻，子文件按需加载 | 前传 + 第 2 篇 |
| 4 | description 是唯一触发器；写不好 → 永远不被调用 | 第 2 篇 |
| 5 | SKILL.md 主入口控制在 ~100 行内 | 第 2 篇 |
| 6 | 脚本优先于 prompt — 确定性逻辑剥离到 scripts/ | 第 2 篇 |
| 7 | 用 `allowed-tools` frontmatter 收窄权限 | 第 2 篇 |
| 8 | 复杂 skill 用 `spawn` + `allowed-tools: Agent Task` 启用并行子任务 | 第 3 篇 |
| 9 | 更新/分发逻辑**不**进 SKILL.md，放 CLI / Hook / Harness 层 | 第 4 篇 |
| 10 | 测试驱动：先写 eval，再写 skill；持续 RL 式迭代 | 第 2 篇 |

## 可机检规则（已落地于 `skillctl audit`）

| 规则 | 严重度 | 修复模式 |
|---|---|---|
| `size-hard` (>200 行) | warn | 拆 references/、把示例移到 examples/、把数据/规则移到 scripts/ |
| `size-soft` (>100 行) | info | 同上但优先级低 |
| `frontmatter-missing` | fail | 在文件头加 `---\nname: ...\ndescription: ...\n---` |
| `missing-name` / `missing-description` | fail | 必填 |
| `missing-version` | warn | 加 `version: v0.1.0` |
| `missing-allowed-tools` | info | 加 `allowed-tools: Read, Write, Edit, Bash, ...`（按实际需求） |
| `allowed-tools-non-microcompact` | info | 工具落在 Microcompact 白名单外（Harness 101 #07）：`Bash / Read / Grep / Glob / WebFetch / WebSearch / FileEdit / FileWrite`。非白名单工具的 tool_result 不会被 auto-compact，会留在 context 跨轮累积。考虑是否真有必要，或拆成子 skill。|
| `references-is-copy-of-external` | info | references/ 里的大段内容像是从外部文档/代码库**复制粘贴**而来（无 attribution、无指针）。"Code is Doc" 原则：**指引优于内容**。考虑改成"看 `<path>` / 跑 `<cmd>`"指引；如确实在沉淀外部已消亡知识，应走 `ouro` 而非塞进 references。|
| `desc-too-short` (<60 字) | warn | 扩写 description，包含触发场景 |
| `desc-no-when` | info | description 加"when to use / 用于 / 当用户…时触发" |
| `desc-no-when-not` | info | description 加 boundary："Do NOT use for ..." / "不适合 ..." |
| `no-references` | info | 把领域知识、API 列表、术语表抽到 references/ |
| `scripts-without-tests` | info | 加 `scripts/test_*.py` 或 `eval/` |

## 不可机检但应人工判断

- **description 是否真的覆盖了 skill 内的全部触发场景**：需要对比 SKILL.md 正文与 description 是否对齐
- **references/ 是否被 SKILL.md 实际链接到**：未被链接的 reference 是死代码
- **scripts/ 里的脚本是否被 SKILL.md 引用作为确定性步骤**：未被引用 = 重复劳动
- **examples/ 是否覆盖了主流分支**：少于 2 个示例的 examples/ 通常不够用
- **是否存在"在 SKILL.md 里写更新逻辑"的反模式**：Skill 101 第 4 篇明令禁止

## 修改边界

- self/skills/* — skill-refiner 可直接 edit
- byted/*/skills/* — 只生成报告附录，引导走 managed-skill-orchestrator + MR
- 任何 frontmatter 编辑都应同时 +0.0.1 patch version
- 任何重大重构（拆 references / 改 description 框架）应先在报告里给 diff 让用户确认

## 优先级建议

按"高 ROI、低风险"排序：

1. 加 `allowed-tools`（纯加法，不破坏触发）
2. 补 `version` 字段（如缺失）
3. 给 description 加 `when NOT to use`（提升精度）
4. 拆 size-hard 文件到 references/（最复杂，留最后）
