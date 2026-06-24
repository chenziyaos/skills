---
name: bnpm-release
description: "ByteDance 内部 npm (bnpm) 发布流程：changeset 管理、版本 bump、构建验证、MR 合并、tag 打版、bnpm publish、端到端验收。适用于 pnpm monorepo 发布到 bnpm.byted.org。当用户提到 bnpm 发布、npm 发包到内部、changeset version、打 tag 触发 release、publish to bnpm、发布新版本到字节内部 registry 时触发。Do NOT use for: 公网 npmjs.org 发布、PyPI 发布、仅查询 bnpm 包信息（用 bytedcli luban npm-search）。"
version: v0.2.0
allowed-tools: Shell, Read
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

# bnpm-release — ByteDance 内部 npm 发布

> 将 pnpm monorepo 中的包发布到 `https://bnpm.byted.org`，覆盖从 changeset 创建到端到端验收的完整生命周期。

## When to use

- 用户说 "发布到 bnpm" / "bnpm publish" / "发个新版本"
- 项目使用 `@changesets/cli` 管理版本
- 目标 registry 是 `bnpm.byted.org`（字节内部 npm）
- monorepo 中需要选择性发布部分包

## When NOT to use

- 发布到公网 npmjs.org → 标准 `npm publish`
- PyPI 包发布 → `bytedcli luban` 或标准 twine
- 只查 bnpm 包信息 → `bytedcli luban npm-search`
- git commit + MR 自动化（非 release 场景）→ `managed-skill-submit`

## 协作边界

- **Phase 4 (Commit+MR)** 可委托 `managed-skill-submit` 执行 git+MR 部分
- **scope 注册**详见 [references/scope-guide.md](references/scope-guide.md)
- **故障排查 + 回滚**详见 [references/troubleshooting.md](references/troubleshooting.md)

## 标准工作流

### Phase 0 — Preflight ✅ 可全自动

```bash
bash scripts/preflight.sh @<scope>
```

检查：bnpm login 状态、changeset 配置、publishConfig 完整性。
**Gate**: 必须全绿才能进入 Phase 1。失败时按脚本提示修复。

### Phase 1 — Changeset 创建 🧑 需人工介入

```bash
pnpm changeset
```

交互式选择受影响的包 + 填写变更描述。**Agent 不可自动执行**（需 TTY 交互），应提示用户手动运行或用 `--empty` 创建空 changeset 后手动编辑。

**版本类型判断**：
- `patch`: bug fix, 内部重构, 依赖更新
- `minor`: 新功能, 新 API, 新导出
- `major`: breaking change, 删除 API, 行为不兼容

**Gate**: `.changeset/` 下存在 ≥1 个非 README.md 文件。

### Phase 2 — Version Bump ✅ 可全自动

```bash
pnpm changeset version
```

效果：消费 changeset → bump version → 生成 CHANGELOG → 级联依赖更新。

**注意**: `.changeset/config.json` 中 `"ignore"` 的包不会被 bump。若出现无关包被 cosmetic 修改，用 `git checkout -- <path>` 还原。

**Gate**: `git diff --stat` 确认只有预期包的 package.json + CHANGELOG 变动。

### Phase 3 — 构建 + 测试 ✅ 可全自动

```bash
pnpm build && pnpm test && pnpm lint
```

**Gate**: 全绿 (exit 0)。
**失败决策树**:
- build 失败 → 修复代码，回到 Phase 2（可能需要新 changeset）
- test 失败 → 修复代码，`git add && git commit --amend`
- lint 失败 → `pnpm lint --fix`，重新验证

### Phase 4 — Commit + MR ✅ 可全自动 (可委托 managed-skill-submit)

```bash
git checkout -b release/v<VERSION>
git add -A
git commit -m "chore(release): bump versions for v<VERSION>"
git push -u origin HEAD
```

VERSION 推导：从主包的 `package.json` 读取 `version` 字段。

开 MR 后等待 CI：
```bash
# 查看 MR check runs 状态
bytedcli codebase mr checks --mr-number <MR_NUMBER>

# CI 全绿后自动合并（通过 merge queue）
bytedcli codebase mr queue --mr-number <MR_NUMBER>
```

**Gate**: MR CI checks 全绿 + 合并完成（`bytedcli codebase mr checks` 全 passed）。

### Phase 5 — Dry-run 验证 ✅ 可全自动（安全门）

```bash
pnpm publish -r \
  --filter '@<scope>/*' \
  --registry https://bnpm.byted.org \
  --dry-run
```

确认输出显示 `Publishing to https://bnpm.byted.org`，包列表和版本号正确。

**Gate**: dry-run 输出无 error，registry 地址正确。**此步骤幂等，可安全重试。**

### Phase 6 — Tag ✅ 可全自动

```bash
git checkout main && git pull
git tag v<VERSION>
git push origin v<VERSION>
```

**⚠ 不可逆操作**：tag push 后若需修正，见 [references/troubleshooting.md](references/troubleshooting.md) 回滚流程。

### Phase 7 — Publish ⚠ 不可逆

```bash
pnpm publish -r \
  --filter '@<scope>/*' \
  --registry https://bnpm.byted.org \
  --no-git-checks
```

**⚠ 此步骤不可撤销**：版本号一旦发布，不能重用。发布前务必确认 Phase 5 dry-run 通过。

`--no-git-checks` 原因：Codebase MR merge 可能产生 merge commit 导致 git 状态不 clean。

逐包验证：
```bash
npm view @<scope>/<pkg> --registry https://bnpm.byted.org
```

### Phase 8 — 端到端验收 ✅ 可全自动

```bash
tmpdir=$(mktemp -d)
cd "$tmpdir"
npm install --registry=https://bnpm.byted.org @<scope>/<main-pkg>
# 执行 smoke test (项目自定义)
```

**Gate**: 安装成功 + smoke test 通过。

## 关键约束

1. **scope 必须预先注册** — 详见 [references/scope-guide.md](references/scope-guide.md)
2. **`private: true` 的包不会被 publish** — 确保发布包无此标记
3. **Codebase 不支持 GitHub Actions** — publish 必须本地触发
4. **registry 优先级**: `publishConfig.registry` > `.npmrc` > CLI `--registry`
5. **pnpm workspace protocol**: `workspace:*` 在 publish 时自动替换为实际版本号

## 决策速查

```
用户说 "发布" →
  ├─ 有未消费 changeset? → Phase 2 开始
  ├─ 无 changeset 且有新 commit? → Phase 1 开始
  ├─ 已 version bump 但未 publish? → Phase 3 开始
  └─ 不确定状态? → 跑 preflight (Phase 0)
```
