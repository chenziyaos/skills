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

class HostBridgeRuntimeTest(OuroShadowRuntimeTestCase):
    def test_host_bridge_snapshot_from_cli_flags(self) -> None:
        args = runtime.parse_args([
            "--prompt",
            "用 $ouro 处理一个长期行为约束。",
            "--host-memory-search",
            "yes",
            "--host-list-capabilities",
            "yes",
            "--host-exec",
            "no",
            "--ledger-size-bucket",
            "21+",
        ])
        snapshot = host_bridge.build_host_bridge(args)
        self.assertTrue(snapshot.capability_available("host.memory.search"))
        self.assertTrue(snapshot.capability_available("host.list_capabilities"))
        self.assertFalse(snapshot.capability_available("host.exec"))
        self.assertEqual(snapshot.retrieval_mode, "memory-search")
        self.assertEqual(snapshot.discovery_mode, "active")
        self.assertEqual(snapshot.ledger_size_bucket, "21+")
        self.assertTrue(snapshot.read_only)

    def test_host_bridge_file_normalizes_aliases_and_observed_assets(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bridge_path = Path(temp_dir) / "host-bridge.json"
            bridge_path.write_text(
                json.dumps(
                    {
                        "capabilities": {
                            "memory.search": True,
                            "list_capabilities": True,
                            "exec": False,
                            "skill.list": True,
                        },
                        "mode": "unattended",
                        "tenant_id": "team-alpha",
                        "ledger_size_bucket": "1-20",
                        "time_now": "2026-05-22T16:00:00Z",
                        "skills": [
                            {
                                "assetId": "deploy-guard",
                                "assetType": "skill",
                                "scope": "repo",
                            }
                        ],
                        "memory_hits": [
                            {
                                "asset_id": "incident-review",
                                "asset_type": "skill",
                                "scope": "global",
                                "depends_on": ["risk-formatter"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            args = runtime.parse_args([
                "--prompt",
                "用 $ouro 评估 `deploy-guard` 是否应该扩展。",
                "--host-bridge-file",
                str(bridge_path),
            ])
            snapshot = host_bridge.build_host_bridge(args)
            self.assertEqual(snapshot.source, "host-bridge-file")
            self.assertEqual(snapshot.mode, "unattended")
            self.assertEqual(snapshot.tenant_id, "team-alpha")
            self.assertEqual(snapshot.ledger_size_bucket, "1-20")
            self.assertEqual(snapshot.time_now, "2026-05-22T16:00:00Z")
            self.assertTrue(snapshot.capability_available("host.memory.search"))
            self.assertTrue(snapshot.capability_available("host.list_capabilities"))
            self.assertTrue(snapshot.capability_available("host.skill.list"))
            self.assertEqual(len(snapshot.skill_registry), 1)
            self.assertEqual(len(snapshot.memory_hits), 1)
            self.assertEqual(len(snapshot.observed_assets), 2)
            self.assertEqual(snapshot.observed_assets[0]["evidence_sources"], ["host-skill-registry"])
            self.assertEqual(snapshot.observed_assets[1]["evidence_sources"], ["host-memory-search"])

    def test_host_bridge_result_payload_contains_capability_snapshot(self) -> None:
        result = self.run_prompt(
            "用 $ouro 处理这条长期行为约束：以后凡是回答涉及风险、变更或回滚的话题，agent 都必须先给出风险摘要，再给出建议。",
            "--host-memory-search",
            "yes",
            "--host-list-capabilities",
            "yes",
        )
        self.assertEqual(result["host"]["retrievalMode"], "memory-search")
        self.assertEqual(result["host"]["discoveryMode"], "active")
        self.assertTrue(result["host"]["readOnly"])
        self.assertEqual(result["host"]["bridgeSource"], "cli-flags")
        self.assertIn("host.exec", result["host"]["capabilities"])
        self.assertIn("conceptualCapabilities", result["host"])
        self.assertTrue(result["host"]["conceptualCapabilities"]["host.memory"])
        self.assertFalse(result["host"]["conceptualCapabilities"]["host.exec"])

    def test_env_backed_host_provider_file_is_normalized_as_read_only_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bridge_path = Path(temp_dir) / "provider-host.json"
            bridge_path.write_text(
                json.dumps(
                    {
                        "capabilities": {
                            "memory.search": True,
                            "list_capabilities": True,
                            "skill.list": True,
                        },
                        "tenantId": "team-provider",
                        "timeNow": "2026-05-24T06:15:00Z",
                        "skillRegistry": [
                            {
                                "assetId": "deploy-guard",
                                "assetType": "skill",
                                "scope": "repo",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            args = runtime.parse_args([
                "--prompt",
                "用 $ouro 评估 `deploy-guard` 是否应该扩展。",
            ])
            with patch.dict("os.environ", {"OURO_HOST_PROVIDER_FILE": str(bridge_path)}, clear=False):
                snapshot = host_bridge.build_host_bridge(args)
            self.assertEqual(snapshot.source, "host-provider-file")
            self.assertEqual(snapshot.tenant_id, "team-provider")
            self.assertEqual(snapshot.time_now, "2026-05-24T06:15:00Z")
            self.assertTrue(snapshot.capability_available("host.memory.search"))
            self.assertTrue(snapshot.capability_available("host.list_capabilities"))
            self.assertEqual(len(snapshot.skill_registry), 1)

    def test_env_backed_host_metadata_updates_snapshot_defaults(self) -> None:
        args = runtime.parse_args([
            "--prompt",
            "用 $ouro 处理一个长期行为约束。",
        ])
        with patch.dict(
            "os.environ",
            {
                "OURO_HOST_MODE": "unattended",
                "OURO_HOST_TENANT_ID": "team-env",
                "OURO_HOST_TIME_NOW": "2026-05-24T06:20:00Z",
            },
            clear=False,
        ):
            snapshot = host_bridge.build_host_bridge(args)
        self.assertEqual(snapshot.source, "cli-flags")
        self.assertEqual(snapshot.mode, "unattended")
        self.assertEqual(snapshot.tenant_id, "team-env")
        self.assertEqual(snapshot.time_now, "2026-05-24T06:20:00Z")
        self.assertTrue(snapshot.capability_available("host.time.now"))

    def test_env_backed_ledger_records_enable_memory_read_bm25_mode(self) -> None:
        args = runtime.parse_args([
            "--prompt",
            "用 $ouro 处理一个长期行为约束。",
        ])
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
            snapshot = host_bridge.build_host_bridge(args)
        self.assertEqual(snapshot.retrieval_mode, "memory-read-bm25")
        self.assertTrue(snapshot.capability_available("host.memory.read"))
        self.assertEqual(len(snapshot.ledger_records), 1)

    def test_conceptual_capability_presence_does_not_imply_full_skill_surface(self) -> None:
        snapshot = host_bridge.build_host_bridge_from_payload(
            {
                "capabilities": {
                    "skill.list": True,
                    "skill.create": False,
                    "skill.update": False,
                }
            },
            source="host-bridge-file",
            fallback_ledger_size_bucket="0",
        )
        payload = snapshot.to_result_dict()
        self.assertTrue(payload["conceptualCapabilities"]["host.skill"])
        self.assertTrue(payload["capabilities"]["host.skill.list"])
        self.assertFalse(payload["capabilities"]["host.skill.create"])
        self.assertFalse(payload["capabilities"]["host.skill.update"])

    def test_host_bridge_file_enriches_result_payload_and_asset_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bridge_path = Path(temp_dir) / "host-bridge.json"
            bridge_path.write_text(
                json.dumps(
                    {
                        "capabilities": {
                            "memory.search": True,
                            "list_capabilities": True,
                            "skill.list": True,
                        },
                        "mode": "interactive",
                        "tenantId": "team-alpha",
                        "ledgerSizeBucket": "21+",
                        "skillRegistry": [
                            {
                                "assetId": "deploy-guard",
                                "assetType": "skill",
                                "scope": "repo",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            result = self.run_prompt(
                "用 $ouro review 这段新增能力。现有 skill `deploy-guard` 已负责发布前检查、dry-run、回滚命令生成。新材料新增灰度比例建议、金丝雀阈值和异常停止发布。要求不要重复造轮子。",
                "--host-bridge-file",
                str(bridge_path),
            )
            self.assertEqual(result["host"]["bridgeSource"], "host-bridge-file")
            self.assertEqual(result["host"]["retrievalMode"], "memory-search")
            self.assertEqual(result["host"]["discoveryMode"], "active")
            self.assertEqual(result["host"]["skillRegistryCount"], 1)
            self.assertEqual(result["host"]["observedAssetCount"], 1)
            self.assertTrue(result["evidence"]["trigger"]["inventoryEvidencePresent"])
            self.assertEqual(result["decision"], "extend-skill")

    def test_invalid_host_bridge_file_raises_host_bridge_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bridge_path = Path(temp_dir) / "host-bridge.json"
            bridge_path.write_text("{not-json}", encoding="utf-8")
            args = runtime.parse_args([
                "--prompt",
                "用 $ouro 处理一个长期行为约束。",
                "--host-bridge-file",
                str(bridge_path),
            ])
            with self.assertRaises(host_bridge.HostBridgeError):
                host_bridge.build_host_bridge(args)
