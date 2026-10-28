"""Shared registration and manual invocation of the owned development plugin."""

import json
import re
import subprocess
from pathlib import Path
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/personal-dev"
SKILL = PLUGIN / "skills/dev-delegate"
REVIEW = PLUGIN / "skills/dev-review"
RUNTIME_CHECK = PLUGIN / "skills/dev-runtime-check"
DEVELOPMENT_SKILLS = ("dev-prepare", "dev-delegate", "dev-auto")


class PersonalDevPackagingTests(unittest.TestCase):
    def test_every_entry_reaches_the_shared_model_contract(self):
        contract = PLUGIN / "references/subagent-models.md"
        self.assertTrue(contract.is_file())
        for directory in (PLUGIN / "skills").iterdir():
            source = directory / "SKILL.md"
            if not source.is_file():
                continue
            references = re.findall(r"\[[^\]]+\]\(([^)]+subagent-models\.md)\)",
                                    source.read_text(encoding="utf-8"))
            self.assertEqual(len(references), 1, directory.name)
            self.assertEqual((directory / references[0]).resolve(), contract.resolve())

    def test_model_preflight_precedes_preparation_and_review_outputs(self):
        for name, downstream in (("dev-auto", "2. 读取[准备与消费契约]"),
                                 ("dev-delegate", "先读取[准备与消费契约的执行入口]"),
                                 ("dev-review", "报告默认在聊天中输出")):
            source = (PLUGIN / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            with self.subTest(skill=name):
                arguments = ("reviewer=<model>:<effort>" if name == "dev-review" else
                             "worker=<model>:<effort> reviewer=<model>:<effort>")
                self.assertLess(source.index(arguments),
                                source.index(downstream))
                self.assertIn("缺 reviewer 立即中断" if name == "dev-review" else
                              "缺任一参数立即中断", source)
        auto = (PLUGIN / "skills/dev-auto/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("同一对已验证 worker / reviewer 配置传入", auto)

    def test_harness_contracts_require_explicit_fields_and_shared_roles(self):
        for harness, native in (("codex", "reasoning_effort"), ("claude", "Agent"),
                                ("agy", "invoke_subagent"), ("dsh", "subagent")):
            source = (PLUGIN / "references" / f"{harness}.md").read_text(encoding="utf-8")
            with self.subTest(harness=harness):
                self.assertIn("[子代理模型契约](subagent-models.md)", source)
                self.assertIn(native, source)
                for requirement in ("worker", "reviewer", "effort", "显式传", "BLOCKED",
                                    "Final Reviewer", "fresh coder"):
                    self.assertIn(requirement, source)
                for legacy in ("coding_effort", "review_effort", "audit_effort",
                               "verification_effort", "final_review_escalated", "同代最高"):
                    self.assertNotIn(legacy, source)
        codex = (PLUGIN / "references/codex.md").read_text(encoding="utf-8")
        self.assertIn('model = result[role]["model"]', codex)
        self.assertIn('reasoning_effort = result[role]["effort"]', codex)
        self.assertIn('fork_turns = "none"', codex)
        for name in ("dev-auto", "dev-delegate", "dev-review"):
            metadata = yaml.safe_load((PLUGIN / "skills" / name / "agents/openai.yaml")
                                      .read_text(encoding="utf-8"))
            self.assertIn("reviewer=<model>:<effort>" if name == "dev-review" else
                          "worker=<model>:<effort> reviewer=<model>:<effort>",
                          metadata["interface"]["default_prompt"])

    def test_delegate_defaults_to_short_path_and_preserves_risk_escalation(self):
        source = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("worker → reviewer → 必要修复 → 最终 fresh verification → DONE", source)
        self.assertIn("默认一个 worker 顺序执行", source)
        self.assertIn("通常有 blocker 时由原 Coder 修一次并独立复验", source)
        self.assertIn("上限不是默认流程", source)
        self.assertIn("只有真实 blocker 持续存在才进入下一轮", source)
        self.assertIn("不按轮次机械换人", source)
        self.assertIn("始终做一次整体检查与最终 fresh verification", source)
        for trigger in ("用户明确要求", "安全 / 权限", "并发 / 事务一致性",
                        "破坏性数据迁移", "公共 API 不兼容风险"):
            self.assertIn(trigger, source)
        orchestration = (SKILL / "references/orchestration.md").read_text(encoding="utf-8")
        self.assertIn("默认 `max_coders: 1`", orchestration)
        self.assertIn("不按任务数量强制创建 ledger", orchestration)
        self.assertIn("仅发生真实失败、未决共享契约或具体风险传播时启用依赖冻结", orchestration)
        for path in (SKILL / "SKILL.md", SKILL / "references/roles.md",
                     SKILL / "references/orchestration.md"):
            content = path.read_text(encoding="utf-8")
            self.assertNotIn("默认两个写代理并行", content)
            self.assertNotIn("第三轮按角色契约换 fresh coder", content)

    def test_review_defaults_to_one_reviewer_and_only_escalates_for_evidence(self):
        source = (REVIEW / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("reviewer → 主模型核验证据 → 输出报告", source)
        self.assertIn("不要求 worker", source)
        self.assertIn("小范围或普通审查默认一个 reviewer", source)
        self.assertIn("只有发现有依据的 P0/P1 候选或实质争议时，再派第二个独立 reviewer", source)
        self.assertIn("普通审查不建 progress", source)
        self.assertIn("更重的专项验证仅在具体证据缺口影响结论或用户明确要求时启用", source)
        for value in ("P0–P3", "COMPLETE", "PARTIAL", "BLOCKED", "只读"):
            self.assertIn(value, source)
        for harness in ("codex", "claude", "agy", "dsh"):
            adapter = (PLUGIN / "references" / f"{harness}.md").read_text(encoding="utf-8")
            self.assertIn("dev-review 只要求 reviewer", adapter)
            self.assertIn("默认单 worker 顺序执行", adapter)

    def test_plugin_display_describes_explicit_models_and_short_defaults(self):
        catalog = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text("utf-8"))
        entry = next(item for item in catalog["plugins"] if item["name"] == "personal-dev")
        manifest = json.loads((PLUGIN / "plugin.json").read_text("utf-8"))
        self.assertEqual(entry["interface"], manifest["extensions"]["com.openai"]["interface"])
        description = entry["interface"]["longDescription"]
        for expected in ("只需显式 reviewer=<model>:<effort>", "默认单 reviewer",
                         "最终 fresh verification", "最多三轮", "按实际需要启用",
                         "不自动选型", "不 fallback"):
            self.assertIn(expected, description)
        for obsolete in ("模型与 effort 自动选择", "同代 Luna", "默认两个编码代理并行"):
            self.assertNotIn(obsolete, description)

    def test_all_subagent_work_categories_use_only_two_model_roles(self):
        source = (PLUGIN / "references/subagent-models.md").read_text(encoding="utf-8")
        execution, judgment = [line for line in source.splitlines()
                               if line.startswith("| ") and ("`worker`" in line or "`reviewer`" in line)]
        for task in ("写代码", "搜索/读取文件", "查引用", "执行命令", "修改配置", "补测试",
                     "修复", "fresh coder"):
            self.assertIn(task, execution)
        self.assertTrue(execution.endswith("`worker` |"))
        for task in ("代码审查", "SPEC / PLAN", "验证结果", "回归风险", "独立检查", "复验",
                     "Final Reviewer"):
            self.assertIn(task, judgment)
        self.assertTrue(judgment.endswith("`reviewer` |"))
        for alias_group in ("worker / work / w / code", "reviewer / review / r / check"):
            self.assertIn(alias_group, source)
        ledger = (SKILL / "references/orchestration.md").read_text(encoding="utf-8")
        self.assertIn("所有并行 Worker 使用同一 worker", ledger)
        self.assertIn("多个 Reviewer 使用同一 reviewer", ledger)
        for legacy in ("coding_model:", "coding_effort:", "review_model:", "review_effort:",
                       "final_review_escalated"):
            self.assertNotIn(legacy, ledger)

    def test_delegate_orchestration_resources_resolve_inside_plugin(self):
        orchestration = SKILL / "references/orchestration.md"
        self.assertTrue(orchestration.is_file())
        sources = [PLUGIN / "skills" / name / "SKILL.md" for name in DEVELOPMENT_SKILLS]
        sources += [orchestration, SKILL / "references/roles.md",
                    PLUGIN / "references/preparation.md", PLUGIN / "references/artifacts.md",
                    PLUGIN / "references/subagent-models.md"]
        for source in sources:
            references = re.findall(r"\[[^\]]+\]\(([^)]+\.md)(?:#[^)]*)?\)", source.read_text(encoding="utf-8"))
            self.assertTrue(references, source)
            for reference in references:
                with self.subTest(source=source.name, reference=reference):
                    target = (source.parent / reference).resolve()
                    self.assertTrue(target.is_relative_to(PLUGIN.resolve()), reference)
                    self.assertTrue(target.is_file(), reference)

    def test_plugin_execution_artifacts_are_ignored_by_git(self):
        paths = [
            ".personal-dev/sdd/fixture/progress.md",
            ".personal-dev/sdd/fixture/logs/test.log",
            ".personal-dev/tests/fixture/config.json",
            ".agent-manager/tests/fixture/config.json",
        ]
        result = subprocess.run(
            ["git", "check-ignore", "--", *paths],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), paths)

    def test_spec_and_plan_remain_available_for_version_control(self):
        for path in ("docs/personal-dev/specs/fixture-design.md", "docs/personal-dev/plans/fixture.md"):
            with self.subTest(path=path):
                result = subprocess.run(
                    ["git", "check-ignore", "--no-index", "--", path],
                    cwd=ROOT, capture_output=True, text=True, check=False,
                )
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertEqual(result.stdout, "")

    def test_owned_plugins_do_not_direct_outputs_to_shared_agent_tmp(self):
        for plugin in (PLUGIN, ROOT / "plugins/agent-manager"):
            for source in plugin.rglob("*.md"):
                with self.subTest(source=source.relative_to(ROOT)):
                    self.assertNotIn(".agent-tmp", source.read_text(encoding="utf-8"))

    def test_development_entries_are_manual_only_and_fit_native_loading_budget(self):
        for name in (*DEVELOPMENT_SKILLS, "dev-review"):
            with self.subTest(skill=name):
                directory = PLUGIN / "skills" / name
                source = directory / "SKILL.md"
                frontmatter = yaml.safe_load(source.read_text(encoding="utf-8").split("---", 2)[1])
                metadata = yaml.safe_load((directory / "agents/openai.yaml").read_text(encoding="utf-8"))
                self.assertEqual(frontmatter["name"], name)
                self.assertIs(frontmatter["disable-model-invocation"], True)
                self.assertIs(metadata["policy"]["allow_implicit_invocation"], False)
                self.assertIn(f"$personal-dev:{name}", metadata["interface"]["default_prompt"])
                for value in (frontmatter["description"], metadata["interface"]["display_name"],
                              metadata["interface"]["short_description"]):
                    self.assertRegex(value, r"[\u4e00-\u9fff]")
                # Reserve headroom for the delegate entry below the observed
                # native Codex 8000-byte prefix boundary, including CRLF checkouts.
                byte_limit = 6000 if name == "dev-delegate" else 8000
                self.assertLessEqual(len(source.read_bytes()), byte_limit)
                self.assertLessEqual(len(source.read_text(encoding="utf-8")
                                         .replace("\n", "\r\n").encode("utf-8")), byte_limit)

    def test_codex_helper_protocol_example_uses_the_shared_validator(self):
        from test_personal_dev import SELECTOR

        adapter = (PLUGIN / "references/codex.md").read_text(encoding="utf-8")
        example = re.search(r"```json\n(.*?)\n```", adapter, re.DOTALL)
        self.assertIsNotNone(example)
        payload = json.loads(example[1])
        for required_roles in (("worker", "reviewer"), ("reviewer",)):
            with self.subTest(required_roles=required_roles):
                request = {key: value for key, value in payload.items()
                           if key != "worker" or "worker" in required_roles}
                result = SELECTOR.select_models(request, required_roles=required_roles)
                self.assertEqual(result["status"], "READY")
                self.assertEqual(set(result), {"status", "display", *required_roles})
                for role in required_roles:
                    self.assertEqual(result[role], {
                        "model": "gpt-6-luna" if role == "worker" else "gpt-6.1-terra",
                        "effort": "high",
                    })

    def test_auto_routes_to_shared_preparation_and_the_existing_executor(self):
        auto = PLUGIN / "skills/dev-auto"
        links = re.findall(r"\[[^\]]+\]\(([^)]+\.md)\)", (auto / "SKILL.md").read_text(encoding="utf-8"))
        self.assertEqual(
            {(auto / target).resolve() for target in links},
            {(PLUGIN / "references/preparation.md").resolve(), (SKILL / "SKILL.md").resolve(),
             (PLUGIN / "references/subagent-models.md").resolve()},
        )
        # The composition entry must not acquire a second selector, role contract or scheduler.
        self.assertEqual(
            {path.relative_to(auto).as_posix() for path in auto.rglob("*") if path.is_file()},
            {"SKILL.md", "agents/openai.yaml"},
        )

    def test_registered_in_codex_and_claude_with_bundled_resources(self):
        codex = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
        entries = [entry for entry in codex["plugins"] if entry["name"] == "personal-dev"]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["source"], {"source": "local", "path": "./plugins/personal-dev"})
        self.assertEqual(entries[0]["skills"], "./skills/")
        manifest = json.loads((PLUGIN / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(
            {path.parent.name for path in (PLUGIN / "skills").glob("*/SKILL.md")},
            {"dev-prepare", "dev-delegate", "dev-auto", "dev-review", "dev-simplify", "dev-runtime-check"},
        )
        self.assertEqual(manifest["name"], entries[0]["name"])
        self.assertEqual(manifest["version"], "0.9.3")
        self.assertEqual(manifest["extensions"]["com.openai"]["interface"], entries[0]["interface"])
        self.assertTrue((SKILL / "scripts/select_models.py").is_file())
        self.assertTrue((SKILL / "references/roles.md").is_file())
        self.assertTrue((PLUGIN / "references/artifacts.md").is_file())
        self.assertTrue((REVIEW / "scripts/select_models.py").is_file())
        self.assertTrue((REVIEW / "references/review-contract.md").is_file())
        self.assertTrue((REVIEW / "references/report-template.md").is_file())

        review_frontmatter = yaml.safe_load((REVIEW / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[1])
        review_metadata = yaml.safe_load((REVIEW / "agents/openai.yaml").read_text(encoding="utf-8"))
        self.assertEqual(review_frontmatter["name"], "dev-review")
        self.assertIs(review_frontmatter["disable-model-invocation"], True)
        self.assertIs(review_metadata["policy"]["allow_implicit_invocation"], False)
        self.assertIn("$personal-dev:dev-review", review_metadata["interface"]["default_prompt"])

        for skill_name in ("dev-simplify",):
            skill_dir = PLUGIN / "skills" / skill_name
            frontmatter = yaml.safe_load((skill_dir / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[1])
            metadata = yaml.safe_load((skill_dir / "agents/openai.yaml").read_text(encoding="utf-8"))
            self.assertEqual(frontmatter["name"], skill_name)
            self.assertIs(frontmatter["disable-model-invocation"], True)
            self.assertIs(metadata["policy"]["allow_implicit_invocation"], False)
            self.assertIn(f"$personal-dev:{skill_name}", metadata["interface"]["default_prompt"])
            self.assertEqual(
                {path.relative_to(skill_dir).as_posix() for path in skill_dir.rglob("*") if path.is_file()},
                {"SKILL.md", "agents/openai.yaml"},
            )

        claude = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        claude_entry = next(entry for entry in claude["plugins"] if entry["name"] == "personal-dev")
        self.assertEqual(claude_entry["source"], "./plugins/personal-dev")
        claude_manifest = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(claude_manifest["name"], "personal-dev")
        self.assertNotIn("version", claude_manifest)
        self.assertTrue((PLUGIN / "references/codex.md").is_file())
        self.assertTrue((PLUGIN / "references/claude.md").is_file())

        sources = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))["groups"]
        lock = json.loads((ROOT / "sources.lock.json").read_text(encoding="utf-8"))["skills"]
        self.assertEqual(set(sources), {"common-workflow", "software-dev", "engineering-tools"})
        self.assertEqual(sum(len(group["skills"]) for group in sources.values()), 20)
        self.assertEqual(len(lock), 20)
        self.assertIn("vue", lock)
        self.assertEqual(
            {item["name"] for item in sources["software-dev"]["skills"]},
            {"frontend-design", "web-design-guidelines", "vue", "fastapi", "java-springboot"},
        )
        self.assertEqual(
            {item["name"] for item in sources["engineering-tools"]["skills"]},
            {"docker-build-strategies", "docker-compose-patterns", "playwright-cli"},
        )
        self.assertNotIn("vue-best-practices", lock)
        self.assertNotIn("playwright-best-practices", lock)
        self.assertNotIn("webapp-testing", lock)
        self.assertEqual(lock["fastapi"]["group"], "software-dev")
        self.assertEqual(lock["docker-build-strategies"]["group"], "engineering-tools")

    def test_runtime_diagnostics_skill_has_chinese_manual_only_metadata(self):
        entry = (RUNTIME_CHECK / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = yaml.safe_load(entry.split("---", 2)[1])
        metadata = yaml.safe_load((RUNTIME_CHECK / "agents/openai.yaml").read_text(encoding="utf-8"))
        self.assertEqual(frontmatter["name"], "dev-runtime-check")
        self.assertTrue(any("\u4e00" <= character <= "\u9fff" for character in frontmatter["description"]))
        self.assertIs(frontmatter["disable-model-invocation"], True)
        self.assertEqual(metadata["interface"]["display_name"], "远端运行诊断")
        self.assertTrue(any("\u4e00" <= character <= "\u9fff" for character in metadata["interface"]["short_description"]))
        self.assertIs(metadata["policy"]["allow_implicit_invocation"], False)
        prompt = metadata["interface"]["default_prompt"]
        self.assertIn("$personal-dev:dev-runtime-check", prompt)
        self.assertIn("/personal-dev:dev-runtime-check", entry)

    def test_manual_only_policy_and_owned_source_boundary(self):
        frontmatter = yaml.safe_load((SKILL / "SKILL.md").read_text(encoding="utf-8").split("---", 2)[1])
        metadata = yaml.safe_load((SKILL / "agents/openai.yaml").read_text(encoding="utf-8"))
        self.assertEqual(frontmatter["name"], "dev-delegate")
        self.assertIs(frontmatter["disable-model-invocation"], True)
        self.assertIs(metadata["policy"]["allow_implicit_invocation"], False)
        self.assertIn("$personal-dev:dev-delegate", metadata["interface"]["default_prompt"])
        sources = yaml.safe_load((ROOT / "sources.yaml").read_text(encoding="utf-8"))
        lock = json.loads((ROOT / "sources.lock.json").read_text(encoding="utf-8"))
        self.assertNotIn("personal-dev", sources["groups"])
        self.assertNotIn("personal-dev", {entry["group"] for entry in lock["skills"].values()})


if __name__ == "__main__":
    unittest.main()
