# skills

本仓库是一个 **public-only** 的本地 skills 工作区，只存放允许上传到 GitHub 的通用 skill、工作区脚本和公共文档。

公司内部 skill 必须放在当前仓库之外的独立 private workspace，例如 `/Users/bytedance/my_skills_internal`。不要把 internal skill 放进本仓库再依赖 `.gitignore`；这不是可靠的发布边界。

## 目录结构

### `skills/`
public skill 的唯一来源目录。

当前包含：
- `skills/ouro/`
- `skills/skill-guide-writer/`

新增 public skill 时，统一使用：

```text
skills/<skill-name>/SKILL.md
```

### `skills/ouro/`
一个 quasi-library skill。

包含：
- `SKILL.md` 主契约
- `references/` 协议与运行时参考文档
- `scripts/run_ouro.py` shadow runtime 稳定入口
- `scripts/ouro/` Python 实现
- `scripts/tests/` 回归测试

适合做：
- capability routing / governance semirun
- shadow runtime contract validation
- 多 host 适配前的本地验证

### `skills/skill-guide-writer/`
面向 skill 文档生成的独立 skill。

适合做：
- 为某个 skill 自动生成 Quick Start / Full Guide
- 基于 skill 元信息补使用说明
- 做文档覆盖度与一致性自检

### `scripts/`
工作区级辅助脚本。

当前包含：
- `install-skills.sh` 安装 configured skill sources
- `verify-skills.sh` 校验安装结果
- `list-skills.sh` 列出当前 skills
- `cleanup-skills.sh` 清理残留
- `uninstall-skills.sh` 卸载 skills

默认行为：
- 只扫描 `skills/` 下的 public skill
- 只有显式设置 `EXTRA_SKILL_SOURCES` 时，才额外扫描 repo 外的 private skill root

适合做：
- 本地 skill 安装与清理
- public/private workspace 联合管理
- 工作区巡检

## 快速开始

> **推荐**：本仓库已切到顶层 [`../skillctl`](../README.md)（覆盖 Claude + Codex + Cursor 三个 agent，并同时管理 `byted/*/skills/`）。
> 本目录下的 `scripts/*.sh` 仅扫描 `self/skills/`、仅同步 Claude + Codex，保留为 legacy。

查看 public skills（legacy 路径）：

```bash
bash scripts/list-skills.sh
```

安装 public skills：

```bash
bash scripts/install-skills.sh
```

校验安装结果：

```bash
bash scripts/verify-skills.sh
```

如果你本机还维护了 private workspace，可以显式追加额外来源：

```bash
EXTRA_SKILL_SOURCES="/Users/bytedance/my_skills_internal/skills" bash scripts/list-skills.sh
```

运行 Ouro shadow runtime：

```bash
python3 skills/ouro/scripts/run_ouro.py --help
```

运行 Ouro 测试：

```bash
python3 -m unittest discover -s skills/ouro/scripts -p 'test_ouro.py'
```

## 发布边界

- 本仓库只允许 public/general skill
- internal/company skill 必须在 repo 外独立存放
- `skills/` 是唯一默认扫描的 allowlisted source root
- `EXTRA_SKILL_SOURCES` 是显式 opt-in，不配置就不会扫描 private workspace
- 多 source 出现同名 skill 时，脚本会直接报错，避免静默覆盖

## 贡献约定

提交边界、目录职责和最小验证约定见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 维护原则

- skill 仓库默认按 skill-tier / quasi-library tier / PyPI-library tier 分级治理
- 当前 `skills/ouro/` 属于 quasi-library skill，而不是 PyPI-style library
- 只有跨目录的仓库级事项，才应该在根目录统一处理
- 任何扩大 skill 扫描范围的改动，都应被视为发布边界变更并谨慎 review
