from __future__ import annotations

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

class CliRuntimeTest(OuroShadowRuntimeTestCase):
    def test_wrapper_help(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(WRAPPER), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertIn("Run the advisory-only Ouro shadow runtime", completed.stdout)

    def test_memory_read_bm25_degradation_is_visible(self) -> None:
        args = runtime.parse_args([
            "--prompt",
            "用 $ouro 处理一个长期流程改造建议，并说明当前 retrieval 模式的限制。",
            "--ledger-size-bucket",
            "21+",
        ])
        with patch.dict(
            "os.environ",
            {
                "OURO_HOST_LEDGER_RECORDS": json.dumps(
                    [
                        {
                            "id": "ledger-1",
                            "decision": "extend-skill",
                            "target": "deploy-guard",
                            "outcome": "success",
                            "input": {
                                "sha256_12": "abc123def456",
                                "summary": "release guard overlap",
                                "uri": "memory://ouro.ledger/ledger-1",
                            },
                        }
                    ]
                )
            },
            clear=False,
        ):
            result = runtime.build_run_result(args)
        self.assertEqual(result["retrievalMode"], "memory-read-bm25")
        self.assertEqual(result["host"]["memoryRead"], True)
        self.assertEqual(result["host"]["ledgerRecordCount"], 1)
        self.assertTrue(any("retrieval_mode=memory-read-bm25" in item for item in result["degradations"]))

    def test_memory_read_without_matching_priors_reports_no_match_degradation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bridge_path = Path(temp_dir) / "provider-host.json"
            bridge_path.write_text(
                json.dumps(
                    {
                        "capabilities": {
                            "memory.read": True,
                        }
                    }
                ),
                encoding="utf-8",
            )
            with patch.dict("os.environ", {"OURO_HOST_PROVIDER_FILE": str(bridge_path)}, clear=False):
                result = self.run_prompt(
                    "用 $ouro 处理这条长期行为约束：以后凡是回答涉及风险、变更或回滚的话题，agent 都必须先给出风险摘要，再给出建议。"
                )
        self.assertEqual(result["retrievalMode"], "memory-read-bm25")
        self.assertIn("ledger_prior=no-match; retrieval is available but returned no prior decisions.", result["degradations"])
        self.assertFalse(result["priorEvidence"]["ledgerPriorsPresent"])
        self.assertEqual(result["priorEvidence"]["ledgerPriorCount"], 0)

    def test_prior_evidence_surfaces_read_only_ledger_summary(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "OURO_HOST_LEDGER_RECORDS": json.dumps(
                    [
                        {
                            "id": "ledger-1",
                            "decision": "update-agent-md",
                            "target": "risk-first",
                            "outcome": "success",
                            "input": {
                                "sha256_12": "abc123def456",
                                "summary": "risk-first behavior",
                                "uri": "memory://ouro.ledger/ledger-1",
                            },
                        }
                    ]
                )
            },
            clear=False,
        ):
            result = self.run_prompt("用 $ouro 处理这条长期行为约束：以后回答高风险变更前先给风险摘要，再给建议。")
        self.assertEqual(result["retrievalMode"], "memory-read-bm25")
        self.assertTrue(result["priorEvidence"]["ledgerPriorsPresent"])
        self.assertEqual(result["priorEvidence"]["ledgerPriorCount"], 1)
        self.assertEqual(result["priorEvidence"]["decisionCounts"], {"update-agent-md": 1})
        self.assertEqual(result["priorEvidence"]["outcomeCounts"], {"success": 1})
        self.assertTrue(result["priorEvidence"]["readOnly"])

    def test_pending_prior_outcome_caps_confidence(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "OURO_HOST_LEDGER_RECORDS": json.dumps(
                    [
                        {
                            "id": "ledger-2",
                            "decision": "create-skill",
                            "target": "deploy-guard",
                            "outcome": "pending",
                            "input": {
                                "sha256_12": "fff111aaa222",
                                "summary": "deploy guard workflow",
                                "uri": "memory://ouro.ledger/ledger-2",
                            },
                        }
                    ]
                )
            },
            clear=False,
        ):
            result = self.run_prompt(
                "Use $ouro to turn this repo release workflow into a durable agent capability with steps, rollback, validation, and reuse scope."
            )
        self.assertIn(
            "ledger_prior=unresolved-history; prior outcomes remain pending or unresolved, so confidence stays capped.",
            result["degradations"],
        )
        self.assertNotEqual(result["confidence"], "H")
        self.assertEqual(result["priorEvidence"]["unresolvedCount"], 1)

    def test_probe_observability_is_report_only_without_host_exec(self) -> None:
        result = self.run_prompt(
            "用 $ouro 处理这份材料。它描述了一套稳定的 PDF 审批包生成流程：\n\n"
            "- 输入：合同 PDF、审批单模板、签章规则\n"
            "- 步骤：抽取字段 → 填模板 → 合并附件 → 生成目录页 → 校验页码 → 导出审批包\n"
            "- 失败处理：字段缺失时停止并提示补录；页码错乱时回滚到合并前",
            "--host-memory-search",
            "yes",
        )
        self.assertEqual(result["probe"]["mode"], "report-only")
        self.assertEqual(result["probe"]["dryRun"]["status"], "skipped")
        self.assertEqual(result["probe"]["adversarial"]["status"], "skipped")
        self.assertTrue(any(item.startswith("probe_mode=report-only") for item in result["degradations"]))

    def test_probe_observability_never_claims_execution_when_host_exec_exists(self) -> None:
        result = self.run_prompt(
            "用 $ouro 处理这份材料。它描述了一套稳定的 PDF 审批包生成流程：\n\n"
            "- 输入：合同 PDF、审批单模板、签章规则\n"
            "- 步骤：抽取字段 → 填模板 → 合并附件 → 生成目录页 → 校验页码 → 导出审批包\n"
            "- 失败处理：字段缺失时停止并提示补录；页码错乱时回滚到合并前",
            "--host-memory-search",
            "yes",
            "--host-exec",
            "yes",
        )
        self.assertEqual(result["probe"]["mode"], "available-but-not-executed")
        self.assertEqual(result["probe"]["dryRun"]["status"], "not-executed")
        self.assertEqual(result["probe"]["adversarial"]["status"], "not-executed")
        self.assertNotIn("executed", result["probe"]["notes"].lower())

    def test_non_triggered_runs_still_emit_evidence_and_shadow_boundary(self) -> None:
        result = self.run_prompt("帮我看看这个文档讲了什么：https://example.com/incident-postmortem")
        self.assertIn("evidence", result)
        self.assertIn("trigger", result["evidence"])
        self.assertTrue(result["shadowBoundary"]["advisoryOnly"])
        self.assertFalse(result["shadowBoundary"]["writesLedger"])
        self.assertIn("controlPlane", result)
        self.assertFalse(result["controlPlane"]["requested"])

    def test_show_scores_exposes_score_breakdown(self) -> None:
        result = self.run_prompt(
            "用 $ouro 吸收这条规则：如果用户请求修改生产配置而没有提供回滚方案，就先拒绝执行并要求补回滚步骤；这条规则只要一行就能表达，不需要额外流程。",
            "--show-scores",
        )
        self.assertTrue(result["observability"]["showScores"])
        self.assertIn("scoreBreakdown", result["observability"])
        scores = result["observability"]["scoreBreakdown"]
        self.assertEqual(result["decision"], "add-rule")
        self.assertGreater(scores["add-rule"], scores["update-agent-md"])
        self.assertGreater(scores["add-rule"], scores["create-skill"])

    def test_explain_decision_exposes_boundary_and_signal_buckets(self) -> None:
        result = self.run_prompt(
            "现有 `incident-review` skill 已支持：事故摘要、时间线、影响面、行动项。新材料新增：自动生成监管报送模板、法务复核清单、外部沟通草稿。用 $ouro 判断应该怎么沉淀。",
            "--host-memory-search",
            "yes",
            "--host-list-capabilities",
            "yes",
            "--host-exec",
            "yes",
            "--explain-decision",
        )
        explanation = result["observability"]["decisionExplanation"]
        self.assertEqual(explanation["topDecision"], "extend-skill")
        self.assertEqual(explanation["runnerUpDecision"], "create-skill")
        self.assertTrue(explanation["boundaryAmbiguity"])
        self.assertIn("signalBuckets", explanation)

    def test_main_returns_structured_error_for_invalid_host_bridge_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bridge_path = Path(temp_dir) / "host-bridge.json"
            bridge_path.write_text("{not-json}", encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(WRAPPER),
                    "--prompt",
                    "用 $ouro 处理一个长期行为约束。",
                    "--host-bridge-file",
                    str(bridge_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 1)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["mode"], "error")
            self.assertIn("failed to parse host bridge file", payload["error"])

    def test_main_persists_run_result_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            exit_code = runtime.main([
                "--prompt",
                "用 $ouro 吸收这条规则：如果用户请求修改生产配置而没有提供回滚方案，就先拒绝执行并要求补回滚步骤；这条规则只要一行就能表达，不需要额外流程。",
                "--output-dir",
                temp_dir,
            ])
            self.assertEqual(exit_code, 0)
            payload = json.loads((Path(temp_dir) / "run_result.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["decision"], "add-rule")
            self.assertEqual(payload["probe"]["mode"], "report-only")
            self.assertTrue(payload["shadowBoundary"]["advisoryOnly"])
            self.assertEqual(payload["outputPolicy"]["outputMode"], "explicit")
            self.assertEqual(payload["outputPolicy"]["expiredRunDirsRemovedCount"], 0)
            self.assertEqual(payload["outputPolicy"]["expiredRunDirsSample"], [])
            self.assertEqual(payload["outputPolicy"]["cleanupWarnings"], [])

    def test_main_emits_cache_retention_metadata_for_default_cache_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(runtime, "DEFAULT_OUTPUT_ROOT", Path(temp_dir) / "cache"):
                exit_code = runtime.main([
                    "--prompt",
                    "用 $ouro 吸收这条规则：如果用户请求修改生产配置而没有提供回滚方案，就先拒绝执行并要求补回滚步骤；这条规则只要一行就能表达，不需要额外流程。",
                    "--cache-ttl-hours",
                    "1",
                ])
                self.assertEqual(exit_code, 0)
                run_dirs = list((Path(temp_dir) / "cache").glob("shadow_run_*"))
                self.assertEqual(len(run_dirs), 1)
                payload = json.loads((run_dirs[0] / "run_result.json").read_text(encoding="utf-8"))
                self.assertEqual(payload["outputPolicy"]["outputMode"], "default-cache")
                self.assertEqual(payload["outputPolicy"]["cacheTtlHours"], 1)
                self.assertEqual(payload["outputPolicy"]["expiredRunDirsRemovedCount"], 0)
                self.assertEqual(payload["outputPolicy"]["expiredRunDirsSample"], [])
                self.assertEqual(payload["outputPolicy"]["cleanupWarnings"], [])
