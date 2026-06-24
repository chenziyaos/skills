# bnpm-release — Scope 选择与注册指南

## 可用 Scope

| scope | 适用场景 | 注册方式 |
|-------|----------|----------|
| `@byted` | 字节内部通用工具/SDK | 已存在，直接使用 |
| `@bytedance-dev` | 开发工具链、CLI 工具 | 已存在，直接使用 |
| `@byted-tiktok` | TikTok 业务线专用 | 已存在，直接使用 |
| 自定义 scope | 团队/项目专属 | 需通过 bnpm 管理后台申请 |

## Scope 注册检查

```bash
# 检查 scope 是否可用（能 view 到任一包说明 scope 存在）
npm view @<scope>/any-known-pkg --registry https://bnpm.byted.org

# 如果返回 404 且确认 scope 不存在，需申请
```

## 申请新 Scope

1. 访问 bnpm 管理后台（内网）
2. "组织管理" → "创建组织"
3. 填写 scope 名（不带 `@`）、管理员列表
4. 等待审批（通常 < 1 工作日）

## Package 命名建议

```
@<scope>/<project>-<module>
```

示例：
- `@byted/mira-cli` — Mira 的 CLI 入口
- `@byted/mira-shared` — Mira 的共享库
- `@byted/mira-sdk-sandbox` — Mira SDK 的沙箱子模块

## publishConfig 配置

每个需要发布的包的 `package.json` 必须包含：

```json
{
  "publishConfig": {
    "registry": "https://bnpm.byted.org",
    "access": "restricted"
  }
}
```

`"access": "restricted"` 表示只在字节内网可见（默认行为，但显式声明更安全）。
