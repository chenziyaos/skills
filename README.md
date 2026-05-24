# skills

本仓库是一个本地 skills 工作区，用来集中维护可被 Claude Code / 其他 agent 运行环境消费的 skill 资产、辅助脚本和实验性能力容器。

## 目录结构

### `ouro/`
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

### `scripts/`
工作区级辅助脚本。

当前包含：
- `install-skills.sh` 安装 skills
- `verify-skills.sh` 校验安装结果
- `list-skills.sh` 列出当前 skills
- `cleanup-skills.sh` 清理残留
- `uninstall-skills.sh` 卸载 skills

适合做：
- 本地 skill 安装与清理
- 工作区巡检
- 多 skill 管理

### `skill-guide-writer/`
面向 skill 文档生成的独立 skill。

适合做：
- 为某个 skill 自动生成 Quick Start / Full Guide
- 基于 skill 元信息补使用说明
- 做文档覆盖度与一致性自检

## 快速开始

查看工作区内容：

```bash
ls
```

安装本地 skills：

```bash
bash scripts/install-skills.sh
```

校验安装结果：

```bash
bash scripts/verify-skills.sh
```

运行 Ouro shadow runtime：

```bash
python3 ouro/scripts/run_ouro.py --help
```

运行 Ouro 测试：

```bash
python3 -m unittest discover -s ouro/scripts -p 'test_ouro.py'
```

## 贡献约定

提交边界、目录职责和最小验证约定见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 维护原则

- skill 仓库默认按 skill-tier / quasi-library tier / PyPI-library tier 分级治理
- 当前 `ouro/` 属于 quasi-library skill，而不是 PyPI-style library
- 只有跨目录的仓库级事项，才应该在根目录统一处理
