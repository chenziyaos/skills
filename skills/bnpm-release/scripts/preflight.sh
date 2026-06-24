#!/usr/bin/env bash
set -euo pipefail

# bnpm-release preflight — 发布前自动检查
# Usage: bash scripts/preflight.sh [@scope]
# Exit 0 = all checks pass; non-zero = blocked

SCOPE="${1:-}"
REGISTRY="https://bnpm.byted.org"
FAIL=0

check() {
  local label="$1" cmd="$2"
  if eval "$cmd" >/dev/null 2>&1; then
    printf "  ✓ %s\n" "$label"
  else
    printf "  ✗ %s\n" "$label"
    FAIL=1
  fi
}

echo "=== bnpm-release preflight ==="
echo ""

echo "[1/5] bnpm CLI"
check "bnpm 可用" "command -v bnpm || npx @bytedance-dev/bnpm --version"

echo "[2/5] 登录状态"
check "已登录 bnpm" "npm whoami --registry $REGISTRY"

echo "[3/5] changesets 配置"
check ".changeset/config.json 存在" "test -f .changeset/config.json"

echo "[4/5] 待消费的 changeset"
PENDING=$(find .changeset -name "*.md" ! -name "README.md" 2>/dev/null | wc -l | tr -d ' ')
if [ "$PENDING" -gt 0 ]; then
  printf "  ✓ %s 个待消费 changeset\n" "$PENDING"
else
  printf "  ⚠ 无待消费 changeset（可能已 version bump 过）\n"
fi

echo "[5/5] publishConfig 检查"
if [ -n "$SCOPE" ]; then
  MISSING=$(find packages -name "package.json" -not -path "*/node_modules/*" -exec grep -L "publishConfig" {} \; 2>/dev/null | head -5)
  if [ -z "$MISSING" ]; then
    printf "  ✓ 所有 packages 含 publishConfig\n"
  else
    printf "  ⚠ 以下包缺少 publishConfig:\n"
    echo "$MISSING" | while read -r p; do printf "    - %s\n" "$p"; done
  fi
else
  printf "  ⊘ 未指定 scope，跳过 publishConfig 检查\n"
fi

echo ""
if [ "$FAIL" -eq 0 ]; then
  echo "✅ All preflight checks passed. Ready to publish."
else
  echo "❌ Preflight failed. Fix above issues before continuing."
  exit 1
fi
