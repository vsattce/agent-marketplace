"""Opt-in native discovery and injection, isolated from daily Codex state."""

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
                "personal-dev:dev-delegate",
                "personal-dev:dev-review",
                "personal-dev:dev-yagni",
                "personal-dev:dev-simplify",
            },
        )
        self.assertTrue(all(item.get("enabled", True) for item in skills))
        ordinary = self.capture("讨论使用便宜模型编码和独立验收的方案，本轮不调用 Skill。")
        self.assertNotIn("# 委派开发与独立验收", ordinary)
        self.assertNotIn("# 增强代码审查", ordinary)
        for marker in ("# 按需实现", "# 精简当前改动"):
            self.assertNotIn(marker, ordinary)
        explicit = self.capture("$personal-dev:dev-delegate 仅验证加载，本轮不执行正文、不派发模型、不修改文件。")
        self.assertIn("# 委派开发与独立验收", explicit)
        self.assertIn("编码模型：", explicit)
        self.assertIn("验收模型：", explicit)
        review = self.capture("$personal-dev:dev-review 仅验证加载，本轮不执行正文、不派发模型、不修改文件。")
        self.assertIn("# 增强代码审查", review)
        self.assertIn("审查模型：", review)
        self.assertIn("复核模型：", review)

        for name, marker in (("dev-yagni", "# 按需实现"), ("dev-simplify", "# 精简当前改动")):
            with self.subTest(invocation=name):
                loaded = self.capture(
                    f"$personal-dev:{name} 仅验证加载，本轮不执行建议或修改任何文件。"
                )
                self.assertIn(marker, loaded)

        combined = self.capture(
            "$personal-dev:dev-yagni 和 $personal-dev:dev-simplify 仅验证组合加载，不执行建议或修改文件。"
        )
        self.assertIn("# 按需实现", combined)
        self.assertIn("# 精简当前改动", combined)


if __name__ == "__main__":
    unittest.main()
