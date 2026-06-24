# plan-driven-phased-delivery — 生命周期图

## 线性流程

```
Phase 1        Phase 2          Phase 3        Phase 4
Plan v0 ──→ 4-Perspective ──→ Plan v1 ──→ Impl Prompt
  │          Review              │              │
  │            │                 │              │
  │         synthesis            │              ▼
  │            │                 │         Phase 5
  │            ▼                 │         Batch Exec
  │         H/M/L 决议 ─────────┘              │
  │                                            │
  │                                            ▼
  │                                       Phase 6
  │                                       Close Review
  │                                            │
  │         ┌─── H 项? ──→ 回到 Phase 5 ──────┘
  │         │
  │         └─── 无 H ──→ Phase 7
  │                        Handoff
  │                           │
  └───────── 下一轮 ◀─────────┘
```

## 角色参与矩阵

| Phase | 主设计师 | Reviewer A/B | Reviewer C/D | Impl Agent |
|-------|----------|--------------|--------------|------------|
| 1. Plan v0 | ★ 执行 | | | |
| 2. Review | 协调 | ★ 执行 | ★ 执行 | |
| 3. Plan v1 | ★ 执行 | | | |
| 4. Impl Prompt | ★ 执行 | | | |
| 5. Batch Exec | 监控 | | | ★ 执行 |
| 6. Close Review | 协调 | ★ 执行 | ★ 执行 | |
| 7. Handoff | ★ 执行 | | | |

## 典型时间分布

| Phase | 典型耗时 | 瓶颈 |
|-------|----------|------|
| Plan v0 | 30min - 2h | 设计决策 |
| Review | 1-4h | 外部 agent 响应时间 |
| Plan v1 | 30min - 1h | 决议 trade-off |
| Impl Prompt | 15-30min | 清晰度 |
| Batch Exec | 1h - 2d | 实现复杂度 |
| Close Review | 1-4h | 外部 agent 响应时间 |
| Handoff | 15-30min | 文档完整度 |

## 跨轮演进

```
W0 (walking skeleton)
  └─→ W1 (MVP)
        └─→ W1-Batch-A (hardening)
              └─→ W2 (next major)
                    └─→ W2-Batch-A (impl)
                          └─→ W2-Batch-A-Patch (fix)
```

每轮的 handoff notes 是下一轮 Phase 1 的输入。
