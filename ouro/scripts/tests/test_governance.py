from __future__ import annotations

try:
    from tests.support import (
        OuroShadowRuntimeTestCase,
        WRAPPER,
        datetime,
        host_bridge,
        json,
        make_analysis,
        patch,
        Path,
        runtime,
        subprocess,
        sys,
        tempfile,
        text_utils,
        timedelta,
        timezone,
    )
except ImportError:
    from support import (
        OuroShadowRuntimeTestCase,
        WRAPPER,
        datetime,
        host_bridge,
        json,
        make_analysis,
        patch,
        Path,
        runtime,
        subprocess,
        sys,
        tempfile,
        text_utils,
        timedelta,
        timezone,
    )

class GovernanceRuntimeTest(OuroShadowRuntimeTestCase):
    def test_l1_merge_candidate_is_recognized(self) -> None:
        result = self.run_prompt(
            "用 $ouro 评估下面这两个能力资产是否存在明显重叠，并判断本次材料沉淀时是否应该附带 merge / freeze 建议，而不是继续无限扩张。\n\n"
            "资产 A：`release-review-skill`，负责发布前检查、风险摘要、回滚命令生成。\n\n"
            "资产 B：`deploy-guard-skill`，负责发布前检查、dry-run、回滚命令生成、风险提示。\n\n"
            "新材料：新增一套“发布前检查项模板”，内容与 A/B 高度重叠。",
            "--host-memory-search",
            "yes",
            "--host-list-capabilities",
            "yes",
            "--host-exec",
            "yes",
        )
        self.assertEqual(result["decision"], "extend-skill")
        self.assertEqual(result["governanceReview"]["signal"], "merge-candidate")
        self.assertEqual(result["governanceReview"]["evidenceMaturity"], "prompt-only")
        self.assertIn("does not mean a merge already happened", result["governanceReview"]["notes"])

    def test_l2_stale_asset_prefers_freeze_not_retire(self) -> None:
        result = self.run_prompt(
            "用 $ouro 评估下面这个历史能力资产是否应该 retire。\n\n"
            "资产：`incident-summary-skill`，最近 60 天几乎没被调用，但一旦有重大事故仍会被使用；其输出质量稳定，没有明确替代者。\n\n"
            "请判断：它应该保持 active/stale、冻结、还是 retire。",
            "--host-memory-search",
            "yes",
            "--host-list-capabilities",
            "yes",
            "--host-exec",
            "yes",
        )
        self.assertEqual(result["decision"], "skip")
        self.assertEqual(result["governanceReview"]["signal"], "freeze-candidate")
        self.assertIn("advisory governance pressure", result["governanceReview"]["notes"])

    def test_l3_successor_relationship_prefers_deprecate_candidate(self) -> None:
        result = self.run_prompt(
            "用 $ouro 判断下面这组能力资产是否已经形成“旧资产 + 新替代资产”的关系。\n\n"
            "旧资产：`report-writer-v1`，只能输出长文报告。\n"
            "新资产：`report-writer-v2`，支持 TL;DR、结构化风险段、验证与回滚段，且已覆盖 v1 的主要职责。\n\n"
            "请判断这次后续治理应该如何建议。",
            "--host-memory-search",
            "yes",
            "--host-list-capabilities",
            "yes",
            "--host-exec",
            "yes",
        )
        self.assertEqual(result["governanceReview"]["signal"], "deprecate-candidate")
        self.assertIn("successor-evidence", result["governanceReview"]["evidenceBasis"])
        self.assertIn("does not mean deprecation already happened", result["governanceReview"]["notes"])

    def test_l4_retirement_blocked_stays_governance_signal(self) -> None:
        result = self.run_prompt(
            "用 $ouro 评估是否应该 retire 下面这条规则：`critical-rollback-rule`。背景：涉及高风险改动时必须先给回滚方案。最近有人觉得这条规则有点啰嗦，想删掉，但还没有替代规则，也没有证明移除后更安全。"
        )
        self.assertEqual(result["decision"], "skip")
        self.assertEqual(result["governanceReview"]["signal"], "retirement-blocked")
        self.assertEqual(result["governanceReview"]["evidenceMaturity"], "prompt-only")
        self.assertIn("advisory observation only", result["governanceReview"]["notes"])

    def test_shadow_runtime_never_emits_lifecycle_state_machine_field(self) -> None:
        result = self.run_prompt(
            "用 $ouro 评估下面这个历史能力资产是否应该 retire。\n\n"
            "资产：`incident-summary-skill`，最近 60 天几乎没被调用，但一旦有重大事故仍会被使用；其输出质量稳定，没有明确替代者。"
        )
        self.assertNotIn("lifecycleState", result["governanceReview"])
        notes = result["governanceReview"]["notes"] or ""
        self.assertNotIn("merge actually happened", notes)
        self.assertNotIn("deprecation actually happened", notes)
        self.assertNotIn("retirement is approved", notes)

    def test_governance_artifact_emits_only_with_complete_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            inventory_path = Path(temp_dir) / "inventory.yaml"
            inventory_path.write_text(
                "assets:\n"
                "  - asset_id: response-caution-rule\n"
                "    asset_type: rule\n"
                "    scope: global\n"
                "    merged_into: risk-first-agent-md\n"
                "    depends_on: [risk-first-agent-md]\n",
                encoding="utf-8",
            )
            output_dir = Path(temp_dir) / "run"
            args = runtime.parse_args([
                "--prompt",
                "用 $ouro 评估 `response-caution-rule` 是否该继续并行增长，还是更适合 merge 到 `risk-first-agent-md`。这属于长期行为约束而不是单独 skill。",
                "--asset-inventory-file",
                str(inventory_path),
                "--output-dir",
                str(output_dir),
                "--host-memory-search",
                "yes",
            ])
            result = runtime.persist_result(output_dir, runtime.build_run_result(args))
            artifact_path = Path(result["artifacts"]["governanceReviewYaml"])
            self.assertTrue(artifact_path.exists())
            artifact_text = artifact_path.read_text(encoding="utf-8")
            self.assertIn("signal: deprecate-candidate", artifact_text)
            self.assertIn("inventory_evidence_present: true", artifact_text)
            self.assertNotIn("durable governance state", artifact_text)
            payload = json.loads((output_dir / "run_result.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["decision"], "update-agent-md")
            self.assertEqual(payload["governanceReview"]["signal"], "deprecate-candidate")
            self.assertEqual(payload["governanceReview"]["evidenceMaturity"], "well-evidenced")
            self.assertNotIn("lifecycleState", payload["governanceReview"])
            self.assertEqual(payload["mode"], "shadow")
            self.assertIn("runResultJson", payload["artifacts"])

    def test_prior_evidence_wording_stays_advisory_and_read_only(self) -> None:
        result = self.run_prompt(
            "用 $ouro 处理这条长期行为约束：以后凡是回答涉及风险、变更或回滚的话题，agent 都必须先给出风险摘要，再给出建议。",
            "--host-memory-search",
            "yes",
        )
        notes = result["priorEvidence"]["notes"]
        self.assertIn("Read-only ledger priors inform advisory confidence only", notes)
        self.assertNotIn("merged", notes)
        self.assertNotIn("deprecated", notes)
        self.assertNotIn("executed", notes)

    def test_governance_review_truth_table_prefers_retirement_blocked_over_stale(self) -> None:
        analysis = make_analysis(
            explicit_trigger=True,
            retirement_pressure=True,
            retirement_risk=True,
            stale_signal=True,
            asset_ids=("critical-rollback-rule",),
        )
        evidence = runtime.build_evidence_envelope(analysis)
        decision = runtime.classify_decision(evidence)
        review = runtime.infer_governance_review(evidence, decision, [])
        self.assertEqual(review["signal"], "retirement-blocked")
        self.assertEqual(review["impactPosture"], "worth-keeping")

    def test_governance_review_truth_table_prefers_inventory_successor_over_stale(self) -> None:
        analysis = make_analysis(
            explicit_trigger=True,
            stale_signal=True,
            asset_ids=("report-writer-v1",),
            inventory_evidence_present=True,
        )
        evidence = runtime.build_evidence_envelope(analysis)
        decision = runtime.classify_decision(evidence)
        review = runtime.infer_governance_review(
            evidence,
            decision,
            [{"asset_id": "report-writer-v1", "merged_into": "report-writer-v2", "depends_on": []}],
        )
        self.assertEqual(review["signal"], "deprecate-candidate")
        self.assertEqual(review["evidenceMaturity"], "well-evidenced")
        self.assertIn("successor-evidence", review["evidenceBasis"])

    def test_governance_review_marks_supported_signal_without_inventory_uncertainty(self) -> None:
        analysis = make_analysis(
            explicit_trigger=True,
            merge_signal=True,
            overlap_tokens=("重叠", "不要重复造轮子"),
            asset_ids=("deploy-guard",),
        )
        evidence = runtime.build_evidence_envelope(analysis)
        decision = runtime.classify_decision(evidence)
        review = runtime.infer_governance_review(
            evidence,
            decision,
            [{"asset_id": "deploy-guard", "depends_on": []}],
        )
        self.assertEqual(review["signal"], "merge-candidate")
        self.assertEqual(review["evidenceMaturity"], "supported-signal")
        self.assertNotIn("attribution-uncertainty", review["evidenceBasis"])

    def test_governance_notes_builder_preserves_advisory_wording(self) -> None:
        notes = runtime.build_governance_notes("merge-candidate", boundary_ambiguity=True)
        self.assertIn("does not mean a merge already happened", notes)
        self.assertIn("Primary routing remains close to a neighboring decision", notes)
        self.assertNotIn("merge already happened.", notes.replace("does not mean a merge already happened", ""))
