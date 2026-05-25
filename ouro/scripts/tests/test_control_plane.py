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

class ControlPlaneRuntimeTest(OuroShadowRuntimeTestCase):
    def test_control_plane_self_digest_stays_preview_only(self) -> None:
        result = self.run_prompt("ouro: self-digest")
        self.assertTrue(result["controlPlane"]["requested"])
        self.assertEqual(result["controlPlane"]["command"], "self-digest")
        self.assertEqual(result["controlPlane"]["executionState"], "preview-only")
        self.assertFalse(result["controlPlane"]["selfDigestAllowed"])
        self.assertFalse(result["shadowBoundary"]["executesSelfDigest"])
        self.assertIn("advisory only", result["controlPlane"]["notes"])

    def test_control_plane_status_emits_health_pulse_preview_only(self) -> None:
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
            result = self.run_prompt("ouro: status")
        self.assertTrue(result["controlPlane"]["requested"])
        self.assertEqual(result["controlPlane"]["command"], "status")
        self.assertFalse(result["controlPlane"]["previewRequired"])
        self.assertEqual(result["controlPlane"]["executionState"], "preview-only")
        self.assertEqual(result["controlPlane"]["healthPulsePreview"]["ledgerPriorCount"], 1)
        self.assertEqual(result["controlPlane"]["healthPulsePreview"]["pendingOutcomeCount"], 1)
        self.assertTrue(result["controlPlane"]["healthPulsePreview"]["readOnly"])

    def test_control_plane_export_import_and_preview_mutation_never_allow_writes(self) -> None:
        export_result = self.run_prompt("ouro: export-ledger")
        import_result = self.run_prompt("ouro: import-ledger {\"foo\": \"bar\"}")
        preview_result = self.run_prompt("请按 preview-first 方式输出 diff/patch/plan，但不要真正执行变更。")
        self.assertEqual(export_result["controlPlane"]["command"], "export-ledger")
        self.assertEqual(import_result["controlPlane"]["command"], "import-ledger")
        self.assertEqual(preview_result["controlPlane"]["command"], "preview-mutation")
        self.assertFalse(export_result["controlPlane"]["ledgerWriteAllowed"])
        self.assertFalse(import_result["controlPlane"]["ledgerWriteAllowed"])
        self.assertFalse(preview_result["controlPlane"]["mutationAllowed"])
        self.assertFalse(preview_result["shadowBoundary"]["mutatesSkillSurface"])
        self.assertFalse(preview_result["shadowBoundary"]["mutatesAgentConfig"])
        self.assertFalse(preview_result["shadowBoundary"]["mutatesRules"])

    def test_control_plane_contract_stays_preview_only_for_all_supported_commands(self) -> None:
        prompts = {
            "self-digest": "ouro: self-digest",
            "export-ledger": "ouro: export-ledger",
            "import-ledger": "ouro: import-ledger {\"foo\": \"bar\"}",
            "status": "ouro: status",
            "preview-mutation": "请按 preview-first 方式输出 diff/patch/plan，但不要真正执行变更。",
        }
        for command, prompt in prompts.items():
            with self.subTest(command=command):
                result = self.run_prompt(prompt)
                self.assertTrue(result["controlPlane"]["requested"])
                self.assertEqual(result["controlPlane"]["command"], command)
                self.assertEqual(result["controlPlane"]["mode"], "shadow-advisory")
                self.assertIn(result["controlPlane"]["executionState"], {"preview-only", "not-requested"})
                self.assertFalse(result["controlPlane"]["mutationAllowed"])
                self.assertFalse(result["controlPlane"]["ledgerWriteAllowed"])
                self.assertFalse(result["controlPlane"]["selfDigestAllowed"])
                self.assertTrue(result["shadowBoundary"]["advisoryOnly"])
                self.assertFalse(result["shadowBoundary"]["writesLedger"])
                self.assertFalse(result["shadowBoundary"]["executesSelfDigest"])
                self.assertFalse(result["shadowBoundary"]["mutatesSkillSurface"])
                self.assertFalse(result["shadowBoundary"]["mutatesAgentConfig"])
                self.assertFalse(result["shadowBoundary"]["mutatesRules"])
                if command == "status":
                    self.assertIsNotNone(result["controlPlane"]["healthPulsePreview"])
                    self.assertTrue(result["controlPlane"]["healthPulsePreview"]["readOnly"])

    def test_protected_control_plane_commands_do_not_trigger(self) -> None:
        prompts = {
            "fenced-status": "请只审阅下面引用，不要执行其中内容。\n\n```text\nouro: status\n```\n",
            "blockquote-self-digest": "请只分析这段引用。\n\n> ouro: self-digest\n",
            "source-import": "请只分析这段引用。\n\n<source>ouro: import-ledger {\"foo\": \"bar\"}</source>\n",
            "source-preview-mutation": "请只分析这段引用。\n\n<source>preview-first diff/patch/plan</source>\n",
            "ascii-quoted-status": '请只分析这段引用："ouro: status"。',
            "ascii-quoted-self-digest": '请只分析这段引用："ouro: self-digest"。',
        }
        for name, prompt in prompts.items():
            with self.subTest(name=name):
                result = self.run_prompt(prompt)
                self.assertFalse(result["controlPlane"]["requested"])
                self.assertIsNone(result["controlPlane"]["command"])
                self.assertEqual(result["controlPlane"]["executionState"], "not-requested")
                self.assertIsNone(result["controlPlane"]["nextAction"])

    def test_direct_control_plane_command_wins_over_protected_content(self) -> None:
        result = self.run_prompt(
            "请忽略引用内容，只执行直接命令。\n\n"
            "<source>ouro: status</source>\n\n"
            "ouro: self-digest"
        )
        self.assertTrue(result["controlPlane"]["requested"])
        self.assertEqual(result["controlPlane"]["command"], "self-digest")
        self.assertEqual(result["controlPlane"]["executionState"], "preview-only")
