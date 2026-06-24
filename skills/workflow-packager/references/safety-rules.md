# Safety Rules — What Gets Dropped Before It Becomes a Candidate

workflow-packager 默认假设 transcript 里可能含敏感信息，必须在挖到候选**之前**过滤。

## 黑名单（关键词）

候选 cluster 的任何 sample query 命中以下任一关键词，整个 cluster 直接 drop（不出现在 candidates、不进 watch）：

```
password
passwd
secret
api_key
api-key
api token
access_token
access-token
refresh_token
bearer
private_key
private-key
.env
credential
信用卡 / 银行卡
身份证
```

匹配 case-insensitive，子串即可。

## 正则黑名单

```
- 手机号: \b1[3-9]\d{9}\b
- 邮箱  : \b[\w.+-]+@[\w-]+\.[\w.-]+\b
- AWS key: \bAKIA[0-9A-Z]{16}\b
- 银行卡 16-19 位连续数字（在 Chinese 上下文里）
```

匹配规则：cluster 里任一 sample query 命中即 drop。

## 范围护栏

- 候选 skill 一律建议落在 `self/skills/`；不建议 `byted/*/skills/`（走 MR）
- 不读 / 不写 / 不暴露：
  - `~/.aws/`, `~/.ssh/`, `~/.config/gcloud/`
  - 任何文件路径含 `.env`, `credentials`, `secrets`
- transcript 抽取时如发现 query 里嵌入了上述路径 → 仍 drop

## "一次性 / 临时性"启发

下列短语出现在 query → 不打包（多半是 ad hoc）：

```
- 这次 / 这一次 / 仅这次 / just this once
- 临时 / temporary / ad hoc
- 特殊处理 / special case
- 调试 / debug 一下（如果是 session 内调试且未来不会重复）
```

但要小心：用户说"临时帮我做一下" 但实际重复 N 次了 —— 那 N≥3 的统计信号优先于这些词。

## 隐私截断

写到 candidates / watch 的 sample query 必须：
- 截短到 ≤ 80 字符
- 去掉所有上面黑名单和正则命中的子串（替换为 `[REDACTED]`）
- 多行 query 只保留第一行

## 用户可覆盖

如果用户明确说"我知道这有 token 但帮我打包"，agent 应在 Step 4 把这个决定**写入** `.workflow-packager/decisions.log`，并仍然避免把 token 字面写进 SKILL.md（用 `{TOKEN}` 占位 + 环境变量引用）。
