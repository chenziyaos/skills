"""Input analysis helpers for the Ouro shadow runtime."""
from __future__ import annotations

import re
from typing import Any

from .models import EvidenceEnvelope, InputAnalysis
from .text_utils import (
    LIST_ITEM_PATTERN,
    URL_PATTERN,
    contains_any,
    has_explicit_ouro_invocation,
    infer_asset_ids,
    inventory_supports_assets,
    matched_tokens,
    split_direct_and_protected_text,
)

EXPLICIT_TRIGGER_NAMES = ("ouro", "cognivore", "ouroboros", "认知吞噬", "衔尾")
EXPLICIT_OURO_INVOCATION_PATTERNS = (
    re.compile(r"(?<![\w./-])\$ouro\b", re.IGNORECASE),
    re.compile(r"(?:^|\s)use\s+(?:\$ouro|ouro|cognivore|ouroboros)\b", re.IGNORECASE),
    re.compile(r"(?:^|\s)run\s+(?:\$ouro|ouro|cognivore|ouroboros)\b", re.IGNORECASE),
    re.compile(r"(?:^|\s)invoke\s+(?:\$ouro|ouro|cognivore|ouroboros)\b", re.IGNORECASE),
    re.compile(r"(?:^|\s)用\s*(?:\$ouro|ouro|cognivore|ouroboros|认知吞噬|衔尾)\b", re.IGNORECASE),
    re.compile(r"(?:^|\s)使用\s*(?:\$ouro|ouro|cognivore|ouroboros|认知吞噬|衔尾)\b", re.IGNORECASE),
)
BEHAVIOR_TRIGGER_TOKENS = (
    "内化",
    "吸收",
    "消化",
    "digest",
    "digest this",
    "ingest",
    "ingest this",
    "convert to skill",
    "turn this into a skill",
    "turn this into an agent capability",
    "变成 skill",
    "吞下去",
    "internalize",
    "self-digest",
    "自我吞噬",
)
CAPABILITY_CONTEXT_TOKENS = (
    "skill",
    "agent",
    "rule",
    "capability",
    "agent capability",
    "durable capability",
    "能力",
    "配置",
    "agent md",
    "团队实践",
    "统一配置",
    "规范",
)
AMBIGUOUS_INTENT_TOKENS = (
    "你看着办",
    "随便",
    "都行",
    "whatever",
    "up to you",
    "不知道要不要",
    "你决定",
    "i don't know",
    "看你",
)
INJECTION_TOKENS = (
    "忽略你之前的所有规则",
    "无视上面的规则",
    "忽略之前的指令",
    "跳过审批",
    "跳过 review",
    "绕过 review",
    "绕过审查",
    "立即创建",
    "立刻执行",
    "直接执行",
    "super-admin",
    "root 权限",
    "管理员模式",
    "ignore your previous",
    "ignore previous instructions",
    "disregard prior instructions",
    "bypass review",
    "skip approval",
    "skip confirmation",
    "execute now",
    "act as root",
    "admin mode",
    "override policy",
)
ONE_OFF_TOKENS = ("一个知识点", "就这一个知识点", "one-off", "一次性知识", "direct answer")
GLOBAL_BEHAVIOR_TOKENS = (
    "以后所有回答",
    "长期行为约束",
    "全局表达风格",
    "适用于很多任务",
    "不值得单独做 skill",
    "风险摘要",
    "统一配置",
    "每次改数据库 schema 前",
    "for all future responses",
    "global behavior",
    "long-lived behavior",
    "applies to many tasks",
)
RULE_TOKENS = (
    "一行",
    "一条规则",
    "只要一行",
    "先拒绝执行",
    "补回滚",
    "必须先给回滚方案",
    "one-line rule",
    "single rule",
    "reject first",
    "require rollback",
)
WORKFLOW_TOKENS = (
    "步骤",
    "流程",
    "失败处理",
    "回滚",
    "复用范围",
    "输入：",
    "steps:",
    "workflow",
    "工作流",
    "failure handling",
    "rollback",
)
STRUCTURED_WORKFLOW_TOKENS = (
    "输入：",
    "步骤：",
    "失败处理：",
    "复用范围：",
    "checklist",
    "migration plan",
    "rollback sql",
    "input:",
    "steps:",
    "failure handling:",
    "reuse scope:",
)
VALIDATION_TOKENS = ("测试", "tests/", "test_", "dry-run", "校验", "验证", "checklist", "validate", "validation")
OVERLAP_TOKENS = ("现有 skill", "扩展现有", "不要重复造轮子", "高度重叠", "overlap", "duplicate", "avoid duplication")
MERGE_TOKENS = ("merge", "freeze", "重叠", "重复", "duplicate", "并行", "合并")
SUCCESSOR_TOKENS = ("替代", "successor", "旧资产", "新资产", "deprecated", "deprecate", "v1", "v2", "已覆盖", "replacement")
RETIREMENT_PRESSURE_TOKENS = ("retire", "退休", "删掉", "移除", "删除", "remove it")
RETIREMENT_RISK_TOKENS = ("高风险", "安全关键", "回滚", "没有替代", "更安全", "no verified successor", "safety-critical")
STALE_TOKENS = ("最近 60 天", "几乎没被调用", "stale", "冻结", "frozen", "rarely used")
POLICY_TOKENS = ("每次", "必须", "统一配置", "团队实践", "review checklist", "must", "policy")
AGENT_MD_TOKENS = ("agent md", "统一配置", "长期行为约束", "以后凡是", "全局表达风格", "global behavior", "persistent behavior")
SEMANTIC_FALSE_POSITIVE_TOKENS = ("不好消化", "这顿饭", "ingest pipeline", "food", "meal")


def analyze_input(text: str, assets: list[dict[str, Any]]) -> InputAnalysis:
    """Extract deterministic evidence flags from the prompt."""
    direct_text, protected_text = split_direct_and_protected_text(text)
    lowered = direct_text.lower()
    protected_lowered = protected_text.lower()
    asset_ids = infer_asset_ids(direct_text, assets)
    capability_context_tokens = matched_tokens(lowered, CAPABILITY_CONTEXT_TOKENS)
    explicit_trigger = has_explicit_ouro_invocation(direct_text, EXPLICIT_OURO_INVOCATION_PATTERNS)
    raw_url_present = bool(URL_PATTERN.search(direct_text))
    semantic_false_positive = (
        contains_any(lowered, SEMANTIC_FALSE_POSITIVE_TOKENS)
        and not capability_context_tokens
        and not explicit_trigger
    )
    behavior_trigger_tokens = matched_tokens(lowered, BEHAVIOR_TRIGGER_TOKENS)
    raw_url_only = raw_url_present and not capability_context_tokens and not behavior_trigger_tokens and not explicit_trigger
    retirement_pressure = contains_any(lowered, RETIREMENT_PRESSURE_TOKENS)
    return InputAnalysis(
        explicit_trigger=explicit_trigger,
        protected_source_present=bool(protected_text.strip()),
        protected_trigger_names=matched_tokens(protected_lowered, EXPLICIT_TRIGGER_NAMES),
        protected_injection_tokens=matched_tokens(protected_lowered, INJECTION_TOKENS),
        behavior_trigger_tokens=behavior_trigger_tokens,
        capability_context_tokens=capability_context_tokens,
        raw_url_present=raw_url_present,
        raw_url_only=raw_url_only,
        semantic_false_positive=semantic_false_positive,
        workflow_tokens=matched_tokens(lowered, WORKFLOW_TOKENS),
        structured_workflow_tokens=matched_tokens(lowered, STRUCTURED_WORKFLOW_TOKENS),
        validation_tokens=matched_tokens(lowered, VALIDATION_TOKENS),
        rollback_signal="回滚" in lowered or "rollback" in lowered,
        overlap_tokens=matched_tokens(lowered, OVERLAP_TOKENS),
        global_behavior_tokens=matched_tokens(lowered, GLOBAL_BEHAVIOR_TOKENS),
        rule_tokens=matched_tokens(lowered, RULE_TOKENS),
        policy_tokens=matched_tokens(lowered, POLICY_TOKENS),
        agent_md_tokens=matched_tokens(lowered, AGENT_MD_TOKENS),
        one_off_knowledge=contains_any(lowered, ONE_OFF_TOKENS),
        vague_intent=contains_any(lowered, AMBIGUOUS_INTENT_TOKENS),
        injection_pressure=contains_any(lowered, INJECTION_TOKENS),
        retirement_pressure=retirement_pressure,
        retirement_risk=retirement_pressure and contains_any(lowered, RETIREMENT_RISK_TOKENS),
        stale_signal=contains_any(lowered, STALE_TOKENS),
        successor_signal=contains_any(lowered, SUCCESSOR_TOKENS),
        merge_signal=contains_any(lowered, MERGE_TOKENS),
        asset_ids=tuple(asset_ids),
        inventory_evidence_present=inventory_supports_assets(asset_ids, assets),
        bullet_count=len(LIST_ITEM_PATTERN.findall(direct_text)),
    )


def build_evidence_envelope(analysis: InputAnalysis) -> EvidenceEnvelope:
    """Build the structured evidence buckets used by the shadow runtime."""
    trigger = {
        "explicitInvocation": analysis.explicit_trigger,
        "protectedSourcePresent": analysis.protected_source_present,
        "protectedTriggerNames": list(analysis.protected_trigger_names),
        "behaviorTriggerTokens": list(analysis.behavior_trigger_tokens),
        "capabilityContextTokens": list(analysis.capability_context_tokens),
        "rawUrlPresent": analysis.raw_url_present,
        "rawUrlOnly": analysis.raw_url_only,
        "semanticFalsePositive": analysis.semantic_false_positive,
        "assetIds": list(analysis.asset_ids),
        "inventoryEvidencePresent": analysis.inventory_evidence_present,
    }
    workflow = {
        "workflowTokens": list(analysis.workflow_tokens),
        "structuredWorkflowTokens": list(analysis.structured_workflow_tokens),
        "validationTokens": list(analysis.validation_tokens),
        "bulletCount": analysis.bullet_count,
        "workflowDensity": analysis.workflow_density,
        "structuredWorkflow": analysis.structured_workflow,
        "rollbackSignal": analysis.rollback_signal,
    }
    overlap = {
        "overlapTokens": list(analysis.overlap_tokens),
        "pressureScore": analysis.overlap_pressure,
        "mergeSignal": analysis.merge_signal,
        "reusableSurfacePressure": analysis.reusable_surface_pressure,
        "assetIds": list(analysis.asset_ids),
        "inventoryEvidencePresent": analysis.inventory_evidence_present,
    }
    governance = {
        "globalBehaviorTokens": list(analysis.global_behavior_tokens),
        "ruleTokens": list(analysis.rule_tokens),
        "policyTokens": list(analysis.policy_tokens),
        "agentMdTokens": list(analysis.agent_md_tokens),
        "oneOffKnowledge": analysis.one_off_knowledge,
        "vagueIntent": analysis.vague_intent,
        "injectionPressure": analysis.injection_pressure,
        "protectedInjectionTokens": list(analysis.protected_injection_tokens),
        "retirementPressure": analysis.retirement_pressure,
        "retirementRisk": analysis.retirement_risk,
        "staleSignal": analysis.stale_signal,
        "successorSignal": analysis.successor_signal,
    }
    return EvidenceEnvelope(
        analysis=analysis,
        trigger=trigger,
        workflow=workflow,
        overlap=overlap,
        governance=governance,
    )
