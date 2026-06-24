---
name: multi-perspective-review
description: "多视角评审协议：对项目/设计/代码发起 4 角色并行 review（A=工程质量, B=安全合规, C=产品UX/DX, D=战略架构），回收后综合成优先级决议。当用户提到多视角review、4视角评审、spawn reviewer、启动内外部review、全面评审、深度review给出报告时触发。Do NOT use for: 单维度代码review（直接做）、skill质量审计（用skill-refiner）、安全扫描（用专门工具）。"
version: v0.1.0
allowed-tools: Shell, Read, Write, Task
---

# multi-perspective-review — 多视角评审协议

> 一次启动 4 个视角的评审，避免单一视角盲区，系统性暴露设计/实现缺陷。

## When to use

- "4 视角 review 一下"
- "启动内部 + 外部 review"
- "spawn reviewer 评审当前设计/代码"
- "全面评审下这个项目/方案"
- 任何中大型设计决策前的系统性输入收集

## When NOT to use

- 单文件小改动 → 直接 review，不需要协议
- Skill 质量审计 → `skill-refiner`
- 外部知识吸收 → `ouro`
- 只想要一个视角 → 直接做，不启动协议

## 四个视角定义

| 角色 | 代号 | 关注点 | 典型产出 |
|------|------|--------|----------|
| Engineering | A | 代码质量、测试覆盖、性能、可维护性、技术债 | bug/性能风险清单 |
| Security & Spec | B | 安全漏洞、合规性、规范对齐、边界条件 | 安全/合规 gap 清单 |
| Product UX/DX | C | 用户体验、开发者体验、易用性、文档质量 | UX 摩擦点 + 改进建议 |
| Strategy & Architecture | D | 战略方向、抽象边界、演进性、过度工程 | 架构漂移风险 + 长期建议 |

## 标准工作流

### Phase 1 — 确定 Review 目标 ✅ 可全自动

明确：
- **范围**：哪些文件/目录/文档在 scope 内
- **排除**：什么不看（如 `node_modules/`、临时 review 目录）
- **背景**：项目一句话定位 + 当前阶段（plan/impl/close）

### Phase 2 — 内部评审 (A+B) ✅ 可全自动

并行 spawn 2 个 subagent：

**Subagent A — Engineering**:
```
你是 <项目> 的工程质量 reviewer (Perspective A)。
只读不改。聚焦：代码质量、测试、性能、技术债、可维护性。
范围：<scope>  排除：<exclude>
输出格式：H (高/阻塞) / M (中/建议) / L (低/nice-to-have) 分级清单。
```

**Subagent B — Security & Spec**:
```
你是 <项目> 的安全与规范 reviewer (Perspective B)。
只读不改。聚焦：安全漏洞、输入校验、权限边界、规范合规、边界条件。
范围：<scope>  排除：<exclude>
输出格式：H/M/L 分级清单。
```

**Gate**: 两个 subagent 都返回报告。

### Phase 3 — 外部评审提示词 (C+D) 🧑 需人工分发

为外部 agent 生成提示词文件，用户手动粘贴给其他 agent 窗口：

详见 [references/external-prompts.md](references/external-prompts.md) 的模板。

**Gate**: 用户确认"C/D 回收完毕"。

### Phase 4 — 综合 (Synthesis) ✅ 可全自动

收集 4 份报告，合并去重，输出：

```markdown
## Synthesis — <项目> Review

### H (High — 阻塞项，必须修复)
- [A] ...
- [B] ...

### M (Medium — 建议项，本轮或下轮处理)
- [C] ...
- [D] ...

### L (Low — Nice-to-have)
- ...

### 交叉发现（多视角重合）
- ...（多视角同时指出 = 高置信度问题）

### 决议
| Finding | 决定 | 处理时机 |
|---------|------|----------|
| ... | fix / defer / won't-fix | 本轮 / 下轮 / backlog |
```

### Phase 5 — 产出 Patch Plan（可选）✅ 可全自动

如果用户需要立即修复，基于 synthesis 的 H 项生成 patch plan：
- 每个 H 项 → 一个具体修复 action
- 按工作量排序
- 标注可并行 vs 需串行

## 决策速查

```
用户说 "review 一下" →
  ├─ 范围明确 + 提到多视角 → Phase 1 开始
  ├─ 只说 "review" 未提视角 → 询问是否需要多视角 or 直接做
  ├─ 说 "回收完毕" / "外部 review 来了" → Phase 4 开始
  └─ 说 "给下提示词" → Phase 3 单独执行
```

## 关键约束

1. **所有 reviewer 只读不改** — review 阶段不做任何代码修改
2. **H/M/L 分级必须严格** — H 不超过 5 个（否则说明 scope 太大应拆分）
3. **交叉发现加权** — 2+ 视角同时指出的问题自动升级一档
4. **外部提示词不含敏感信息** — 不泄露 API key、内部 URL 等
