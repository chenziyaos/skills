---
name: bnpm-release
description: "ByteDance 内部 npm (bnpm) 发布流程。Use when a pnpm monorepo package needs a changeset-driven release to bnpm.byted.org, including version bump, validation, MR, tag, publish, and acceptance. Do NOT use for npmjs.org, PyPI, or generic git/MR automation outside release flow."
version: v0.2.1
allowed-tools: Bash, Read
triggers:
  - "bnpm 发布"
  - "发布到 bnpm"
  - "npm publish 到内部"
  - "changeset version"
  - "打 tag 发 release"
  - "publish new version"
  - "发布新版本"
  - "版本 bump + 发包"
---

# bnpm-release

> 面向 `bnpm.byted.org` 的 changeset 发布流程，覆盖 preflight、version bump、验证、MR、tag、publish、验收。

## When to use

- 发布到 `bnpm.byted.org`
- 项目使用 `pnpm` + `changesets`
- 需要从 version bump 一直走到 publish / 验收
- monorepo 中需要选择性发布一组包

## When NOT to use

- 公网 `npmjs.org` 发布
- PyPI 发布
- 只查 bnpm 包信息
- 非 release 场景的 git / MR 自动化

## 协作边界

- Phase 4 的 git / MR 动作可委托 `managed-skill-submit`
- scope 注册看 [references/scope-guide.md](references/scope-guide.md)
- 排障与回滚看 [references/troubleshooting.md](references/troubleshooting.md)

## 标准工作流

1. **Preflight**：`bash scripts/preflight.sh @<scope>`
2. **Changeset**：人工执行 `pnpm changeset`
3. **Version bump**：`pnpm changeset version`
4. **Build + test + lint**：全绿后继续
5. **Commit + MR**：创建 release 分支并等待 CI
6. **Dry-run publish**：确认 registry / 包列表 / 版本正确
7. **Tag**：推送 `v<VERSION>` tag
8. **Publish**：执行 `pnpm publish -r --registry https://bnpm.byted.org --no-git-checks`
9. **Acceptance**：新装包做 smoke test

## Phase gates

- Preflight 全绿
- `.changeset/` 下存在待消费文件
- version bump 后 diff 只含预期包
- build / test / lint 全绿
- MR checks 全绿并合并
- dry-run 输出正确
- publish 后安装与 smoke test 成功

## 关键约束

- scope 必须已注册
- `private: true` 的包不会发布
- publish 必须本地触发
- registry 优先级：`publishConfig.registry` > `.npmrc` > CLI `--registry`
- `workspace:*` 会在 publish 时替换为实际版本

## 决策速查

- 有未消费 changeset → 从 Version bump 开始
- 无 changeset 但有新改动 → 从 Changeset 开始
- 已 version bump 未 publish → 从验证阶段开始
- 状态不明确 → 先跑 preflight
