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

class RuntimeIoTest(OuroShadowRuntimeTestCase):
    def test_input_file_path_is_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "prompt.txt"
            input_path.write_text(
                "用 $ouro 处理这条长期行为约束：以后凡是回答涉及风险、变更或回滚的话题，agent 都必须先给出风险摘要，再给出建议，不允许直接给最终操作步骤。",
                encoding="utf-8",
            )
            result = self.run_file_input(input_path, "--host-memory-search", "yes")
            self.assertEqual(result["input"]["source"], "input-file")
            self.assertEqual(result["input"]["inputFile"], str(input_path))
            self.assertEqual(result["decision"], "update-agent-md")

    def test_missing_input_file_raises_runtime_error(self) -> None:
        missing = Path(tempfile.gettempdir()) / "missing-ouropath-input.txt"
        args = runtime.parse_args(["--input-file", str(missing)])
        with self.assertRaises(runtime.OuroRuntimeError):
            runtime.read_input_text(args)

    def test_json_inventory_is_normalized(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            inventory_path = Path(temp_dir) / "inventory.json"
            inventory_path.write_text(
                json.dumps(
                    {
                        "assets": [
                            {
                                "assetId": "report-writer-v2",
                                "assetType": "skill",
                                "scope": "repo",
                                "successorOf": "report-writer-v1",
                                "dependsOn": ["risk-formatter"],
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            assets, metadata = runtime.read_inventory(str(inventory_path))
            self.assertEqual(metadata["assetCount"], 1)
            self.assertEqual(assets[0]["asset_id"], "report-writer-v2")
            self.assertEqual(assets[0]["successor_of"], "report-writer-v1")
            self.assertEqual(assets[0]["depends_on"], ["risk-formatter"])

    def test_malformed_inventory_raises_runtime_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            inventory_path = Path(temp_dir) / "inventory.yaml"
            inventory_path.write_text("assets:\n  broken-line-without-colon\n", encoding="utf-8")
            with self.assertRaises(runtime.OuroRuntimeError):
                runtime.read_inventory(str(inventory_path))

    def test_build_run_context_is_deterministic_for_same_time_and_input(self) -> None:
        now = datetime(2026, 5, 23, 15, 30, 45, 123456, tzinfo=timezone.utc)
        left = runtime.build_run_context("use $ouro for rollback policy", now)
        right = runtime.build_run_context("use $ouro for rollback policy", now)
        self.assertEqual(left, right)
        self.assertEqual(left.timestamp, "2026-05-23T15:30:45+00:00")
        self.assertIn("20260523T153045.123456Z", left.run_id)

    def test_build_run_result_honors_injected_run_context(self) -> None:
        run_context = runtime.build_run_context(
            "用 $ouro 吸收一条回滚规则。",
            datetime(2026, 5, 23, 16, 0, 1, 654321, tzinfo=timezone.utc),
        )
        args = runtime.parse_args(["--prompt", "用 $ouro 吸收一条回滚规则。"])
        result = runtime.build_run_result(args, run_context)
        self.assertEqual(result["runId"], run_context.run_id)
        self.assertEqual(result["ts"], run_context.timestamp)

    def test_wrapper_default_output_dir_falls_back_to_tmp_when_home_cache_is_unavailable(self) -> None:
        run_context = runtime.build_run_context("use $ouro for rollback policy", datetime(2026, 5, 23, 15, 30, 45, 123456, tzinfo=timezone.utc))
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(runtime, "default_output_dir", return_value=Path("/dev/null") / "shadow_run_blocked"):
                with patch.object(runtime, "fallback_output_dir", return_value=Path(temp_dir) / "shadow_run_fallback"):
                    output_dir, output_mode = runtime.ensure_output_dir(None, run_context.run_id)
        self.assertTrue(str(output_dir).startswith(temp_dir))
        self.assertEqual(output_mode, "fallback-tmp")

    def test_cleanup_expired_output_dirs_removes_only_expired_shadow_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            expired = root / "shadow_run_expired"
            fresh = root / "shadow_run_fresh"
            other = root / "notes"
            expired.mkdir()
            fresh.mkdir()
            other.mkdir()
            now = datetime(2026, 5, 23, 15, 30, 45, tzinfo=timezone.utc)
            expired_ts = (now - timedelta(hours=10)).timestamp()
            fresh_ts = (now - timedelta(hours=1)).timestamp()
            other_ts = (now - timedelta(hours=10)).timestamp()
            expired.touch()
            fresh.touch()
            other.touch()
            import os
            os.utime(expired, (expired_ts, expired_ts))
            os.utime(fresh, (fresh_ts, fresh_ts))
            os.utime(other, (other_ts, other_ts))
            summary = runtime.cleanup_expired_output_dirs(root, now, 2)
            self.assertEqual(summary.removed_count, 1)
            self.assertEqual(list(summary.removed_sample), ["shadow_run_expired"])
            self.assertEqual(list(summary.warnings), [])
            self.assertFalse(expired.exists())
            self.assertTrue(fresh.exists())
            self.assertTrue(other.exists())

    def test_cleanup_expired_output_dirs_keeps_excluded_current_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            current = root / "shadow_run_current"
            current.mkdir()
            now = datetime(2026, 5, 23, 15, 30, 45, tzinfo=timezone.utc)
            old_ts = (now - timedelta(hours=10)).timestamp()
            import os
            os.utime(current, (old_ts, old_ts))
            summary = runtime.cleanup_expired_output_dirs(root, now, 2, {"shadow_run_current"})
            self.assertEqual(summary.removed_count, 0)
            self.assertEqual(list(summary.removed_sample), [])
            self.assertTrue(current.exists())

    def test_cleanup_expired_output_dirs_negative_ttl_disables_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            expired = root / "shadow_run_expired"
            expired.mkdir()
            now = datetime(2026, 5, 23, 15, 30, 45, tzinfo=timezone.utc)
            summary = runtime.cleanup_expired_output_dirs(root, now, -1)
            self.assertEqual(summary.removed_count, 0)
            self.assertTrue(expired.exists())

    def test_cleanup_expired_output_dirs_zero_ttl_removes_existing_shadow_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            expired = root / "shadow_run_expired"
            expired.mkdir()
            summary = runtime.cleanup_expired_output_dirs(root, datetime.now(timezone.utc), 0)
            self.assertEqual(summary.removed_count, 1)
            self.assertFalse(expired.exists())

    def test_cleanup_expired_output_dirs_is_best_effort_when_remove_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            expired = root / "shadow_run_expired"
            expired.mkdir()
            now = datetime(2026, 5, 23, 15, 30, 45, tzinfo=timezone.utc)
            old_ts = (now - timedelta(hours=1)).timestamp()
            import os
            os.utime(expired, (old_ts, old_ts))
            with patch.object(runtime.shutil, "rmtree", side_effect=OSError("busy")):
                summary = runtime.cleanup_expired_output_dirs(root, now, 0)
            self.assertEqual(summary.removed_count, 0)
            self.assertEqual(list(summary.removed_sample), [])
            self.assertTrue(summary.warnings)
            self.assertTrue(expired.exists())

    def test_ensure_output_dir_rejects_default_collision(self) -> None:
        run_id = "run-20260523T153045.123456Z-b58842"
        with tempfile.TemporaryDirectory() as temp_dir:
            colliding = Path(temp_dir) / f"shadow_run_{run_id}"
            colliding.mkdir()
            with patch.object(runtime, "DEFAULT_OUTPUT_ROOT", Path(temp_dir)):
                with self.assertRaises(runtime.OuroRuntimeError):
                    runtime.ensure_output_dir(None, run_id)

    def test_ensure_output_dir_rejects_explicit_directory_with_existing_run_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            (output_dir / "run_result.json").write_text("{}", encoding="utf-8")
            with self.assertRaises(runtime.OuroRuntimeError):
                runtime.ensure_output_dir(str(output_dir), "run-20260523T153045.123456Z-b58842")
