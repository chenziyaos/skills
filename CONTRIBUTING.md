# Contributing

本仓库是一个本地 skills 工作区，不同目录代表不同层级的职责。提交前先判断改动属于哪个目录，尽量不要把多类事项混在同一个 commit 里。

## Scope

### Root

根目录只处理跨目录的仓库级事项，例如：

- workspace README / CONTRIBUTING / `.gitignore`
- 通用安装、校验、清理脚本
- 多个 skill 共享的约定

如果改动只影响某一个 skill，不要顺手把它抬到根目录处理。

### `ouro/`

`ouro/` 是一个 quasi-library skill，不按 PyPI-style library 默认治理。

保留这类改动：

- `SKILL.md` / `README.md` / `CHANGELOG.md` 维护
- shadow runtime bug fix
- 回归测试补齐
- 仅在有实际收益时补最小 packaging metadata

默认不要引入这类事项，除非仓库目标发生变化：

- CI-first 改造
- PyPI 发布流
- 额外 console entry points
- 严格 lint/type gate 作为默认门槛

### `scripts/`

`scripts/` 放工作区级辅助脚本。这里的改动应该服务于整个 workspace，而不是只为单个 skill 定制。

### `skill-guide-writer/`

该目录下的改动应限定在文档生成相关能力本身，不要和 `ouro/` 的运行时修复混在一起提交。

## Commit Boundaries

优先按目录和关注点拆 commit：

- `ouro/` 行为修复单独提交
- 根目录文档或工作区脚本单独提交
- `skill-guide-writer/` 单独提交

只有在一个需求天然跨目录时，才允许放进同一个 commit。例如：

- `ouro/` 入口路径变更，同时需要同步根目录 README
- 仓库级安装脚本变化，同时要更新对应使用说明

避免这些混搭：

- 在一个 commit 里同时做 `ouro/` runtime 修复和 root 文档整理
- 把工程化清洁项和行为 correctness 修复混在一起
- 为了“顺手”改多个无关目录

## Commit Message

使用 conventional commits：

```text
<type>(<scope>): <summary>
```

常见 scope 建议：

- `ouro`
- `scripts`
- `skill-guide-writer`
- `repo`

示例：

```text
fix(ouro): tighten control-plane direct-text detection

docs(repo): add workspace contribution guide

chore(scripts): improve local skill verification flow
```

## Validation

按改动范围做最小必要验证，不要求一上来就做整仓库工程化升级。

### 改动 `ouro/`

至少运行相关回归；如不确定，先跑：

```bash
python3 -m unittest discover -s ouro/scripts -p 'test_ouro.py'
```

如果只是局部修复，也可以优先跑 `ouro/scripts/tests/` 下的定向测试。

### 改动根目录 `scripts/`

至少执行受影响脚本一次，并确认 README 中对应命令仍然成立。

### 纯文档改动

不强制跑测试，但要确保命令、路径、目录名与仓库当前状态一致。

## Practical Rules

- 先改现有文件，只有职责明显新增时再新建文件。
- 不保留注释掉的旧代码。
- 不把一次修复扩展成无关重构。
- 如果一个改动会影响用户如何运行 skill，同步更新对应 README / `SKILL.md` / `CHANGELOG.md`。
- 提交前再看一遍 diff，确认它只表达一个清晰意图。
