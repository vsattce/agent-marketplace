"""Opt-in native discovery and injection, isolated from daily Codex state."""

import json
import unittest

import test_codex_loader as codex_loader


class PersonalDevLoaderTests(codex_loader.CodexLoaderTests):
    def setUp(self):
        super().setUp()
        codex_loader.run(["codex", "plugin", "add", "personal-dev@agent-marketplace", "--json"], self.env, self.project)

    def test_discovery_and_manual_only_context(self):
        inventory, _ = codex_loader.rpc_skills(self.project, self.env)
        skills = [item for item in inventory if item["name"].startswith("personal-dev:")]
        self.assertEqual(
            {item["name"] for item in skills},
            {
                "personal-dev:dev-prepare",
                "personal-dev:dev-delegate",
                "personal-dev:dev-auto",
                "personal-dev:dev-review",
                "personal-dev:dev-simplify",
                "personal-dev:dev-runtime-check",
            },
        )
        self.assertTrue(all(item.get("enabled", True) for item in skills))
        ordinary = self.capture("远端 Linux 服务最近负载升高，请讨论可能原因，但本轮不调用 Skill。")
        self.assertNotIn("# 需求与计划准备", ordinary)
        self.assertNotIn("# 自动准备与委派开发", ordinary)
        self.assertNotIn("# 委派开发与独立验收", ordinary)
        self.assertNotIn("# 增强代码审查", ordinary)
        self.assertNotIn("# 远端运行诊断", ordinary)
        for marker in ("# 精简当前改动",):
            self.assertNotIn(marker, ordinary)
        explicit = self.capture("$personal-dev:dev-delegate 仅验证加载，本轮不执行正文、不派发模型、不修改文件。")
        self.assertIn("# 委派开发与独立验收", explicit)
        injected = codex_loader.captured_skill_source(json.loads(explicit), "personal-dev:dev-delegate")
        self.assertIsNotNone(injected)
        self.assertIn(codex_loader.skill_body("personal-dev", "dev-delegate"), injected[1].replace("\r\n", "\n"))
        self.assertIn("编码模型：", explicit)
        self.assertIn("验收模型：", explicit)
        for name in ("dev-prepare", "dev-auto"):
            with self.subTest(invocation=name):
                loaded = self.capture(
                    f"$personal-dev:{name} 仅验证加载，不生成文件、不开发、不派发、不修改文件。"
                )
                source = codex_loader.captured_skill_source(json.loads(loaded), f"personal-dev:{name}")
                self.assertIsNotNone(source)
                self.assertIn(codex_loader.skill_body("personal-dev", name), source[1].replace("\r\n", "\n"))
        review = self.capture("$personal-dev:dev-review 仅验证加载，本轮不执行正文、不派发模型、不修改文件。")
        self.assertIn("# 增强代码审查", review)
        self.assertIn("审查模型：", review)
        self.assertIn("复核模型：", review)

        for name, marker in (("dev-simplify", "# 精简当前改动"),):
            with self.subTest(invocation=name):
                loaded = self.capture(
                    f"$personal-dev:{name} 仅验证加载，本轮不执行建议或修改任何文件。"
                )
                self.assertIn(marker, loaded)

        combined = self.capture(
            "$personal-dev:dev-simplify 和 $personal-dev:dev-runtime-check 仅验证组合加载，不执行建议或修改文件。"
        )
        self.assertIn("# 精简当前改动", combined)
        self.assertIn("# 远端运行诊断", combined)
        runtime_check = self.capture(
            "$personal-dev:dev-runtime-check 仅验证加载，不连接主机、不执行诊断。"
        )
        self.assertIn("# 远端运行诊断", runtime_check)


if __name__ == "__main__":
    unittest.main()
