# Signal Patterns — How Repetition Gets Detected

## Source: Cursor / Claude / Codex transcripts

复用 skill-refiner 的 transcript 发现逻辑，但聚合层不一样：
- skill-refiner: 按"skill 名 mention"切片
- workflow-packager: 按"session 初始 user query"切片

### 抽取规则

对每个 transcript 文件：
1. 找 **role=user 且包含 `<user_query>` 包装** 的 turn，作为 "session 启动 query"
2. 同时收集 **session 中后续的独立 user query**（不在 `<user_query>` 包装里但属于 user 角色且 < 500 字符）
3. 单文件里 user query 数量上限 50（避免极长 session 占主导）

### 规范化

清洗 query 文本（让模糊匹配可行）：
- 去 `<user_query>` 包装、去 timestamp 标签
- 全部小写
- 去标点（保留中英文字符 + 数字）
- collapse whitespace

### Token 抽取

支持中英文混合：
- 英文：`[a-zA-Z]{2,}`（≥ 2 字符）
- 中文：`[\u4e00-\u9fff]{2,}`（连续中文字符 ≥ 2）
- 数字单独不算 token（避免日期/版本噪音）
- 停用词表：见 STOPWORDS in `scripts/mine_patterns.py`

每个 query 得到一组 token，再取**频率最高的 N=5** 作为 signature。

## Clustering

朴素 Jaccard 聚类：
- 两个 query 的 token set Jaccard ≥ 0.5 → 同一 cluster
- 用 union-find（不是 KMeans / DBSCAN，因为：cluster 数未知、距离非欧、规模 < 1000）

为什么不上 sklearn：依赖膨胀，体感无收益。50% Jaccard 在中文短 query 上经验值。

## Cluster 表征

每个 cluster 输出：
- `signature`: token 频率排序 top 5（跨整 cluster 聚合）
- `count`: 包含的 query 数
- `sessions`: 出现的不同 session 数（重要：跨 session 比 单 session 重复更有价值）
- `samples`: ≤ 3 个原始 query 抽样（截短 80 字符）
- `date_range`: 最早 / 最晚出现时间（用 transcript file mtime 近似）
- `tool_traces`: 在该 cluster 的 session 里出现频率最高的 tool name 5 个（用于 Skill/Subagent/Shell-Automation 判定）

## "推荐形式" 决策细节

代码层面的判定（packager-doctrine.md 是概念层）：

```
turns_median = median(turns per session in cluster)
deterministic_only = tool_traces ⊆ {Shell, Read, Write, Edit, Glob, Grep}
llm_required = any('分析','解读','review','评估','建议','总结','起草') ∈ query tokens
cross_tool = lark-* ∈ tool_traces OR git ∈ tool_traces OR (multiple lark + dev tools)

if turns_median <= 5 and deterministic_only and not llm_required:
    return 'Shell-Automation'
if turns_median > 30 or 'batch' or 'parallel' tokens:
    return 'Subagent'
return 'Skill'
```

## Watch 累计

`watch.md` 用简单的 markdown 表，每行：
```
| signature             | hits | last_seen   | sessions | sample |
|-----------------------|------|-------------|----------|--------|
| review pr github      | 2    | 2026-05-22  | 2        | "..." |
```

`build_candidates.py` 读旧 watch.md → 累加本次 hits → 写回。当某行 `hits ≥ min` 时自动升入下次 candidates 表（并从 watch.md 删除）。

## 扩展点（MVP 未启用）

| 信号源 | 集成方式 | 价值 |
|---|---|---|
| lark calendar 重复日程 | `lark-cli calendar +list-events --past 30 --recurring` → 提取标题 | 发现周期性会议 → 周报 / 待办 skill 候选 |
| lark IM 高频问询 | `lark-cli im +chat-history` + 关键词聚类 | 发现"反复回答同一类问题" → FAQ skill |
| git 操作日志 | `git reflog` + 命令模式聚类 | 发现"反复执行的 git workflow" → Shell-Automation |

加这些时记住 doctrine：脚本只产候选，不做创建。
