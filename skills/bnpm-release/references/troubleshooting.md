# bnpm-release — 故障排查

## 常见错误

| 错误 | 原因 | 解法 |
|------|------|------|
| `E403 Forbidden` | 未登录或 token 过期 | `npx @bytedance-dev/bnpm@latest login --auth-type=sso` |
| `E404 scope not found` | scope 未在 bnpm 注册 | 通过 bnpm 管理后台申请 scope 归属 |
| `EPUBLISHCONFLICT` | 版本号已在 registry 中存在 | 重新 bump 版本号（不能 unpublish 后重发同版本） |
| changeset version 改了 ignored 包 | cosmetic reformat (如 `"files"` 排版变化) | `git checkout -- <path>` 还原无关改动 |
| `--dry-run` 显示错误 registry | 缺少 publishConfig | 在 package.json 添加 `"publishConfig": {"registry": "https://bnpm.byted.org"}` |
| `ERR_PNPM_GIT_UNCLEAN` | MR merge commit 导致 working tree dirty | 加 `--no-git-checks` 参数 |
| `ENEEDAUTH` | .npmrc 中没有 token | 重新运行 `bnpm login`，确认 `~/.npmrc` 有 `//bnpm.byted.org/:_authToken=...` |

## 回滚流程

### 场景 A: publish 了错误版本

bnpm **不支持 unpublish 后重发同版本号**。解法：
1. 修复代码
2. bump 到下一个 patch（如 0.2.1 → 0.2.2）
3. 重新走 Phase 2–7

### 场景 B: tag 打错了

```bash
git tag -d v<WRONG_VERSION>
git push origin :refs/tags/v<WRONG_VERSION>
git tag v<CORRECT_VERSION>
git push origin v<CORRECT_VERSION>
```

### 场景 C: changeset version 后发现 bump 范围不对

```bash
git checkout -- .
# 重新创建 changeset，调整受影响包范围
pnpm changeset
pnpm changeset version
```

## 部分发布（选择性 publish）

如果只想发布部分包而非全部：

```bash
pnpm publish -r \
  --filter '@scope/pkg-a' \
  --filter '@scope/pkg-b' \
  --registry https://bnpm.byted.org \
  --no-git-checks
```
