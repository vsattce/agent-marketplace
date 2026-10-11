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
            [item["name"] for item in skills],
            ["personal-dev:dev-delegate", "personal-dev:dev-review"],
        )
        self.assertTrue(all(item.get("enabled", True) for item in skills))
        ordinary = self.capture("讨论使用便宜模型编码和独立验收的方案，本轮不调用 Skill。")
        self.assertNotIn("# 委派开发与独立验收", ordinary)
        self.assertNotIn("# 增强代码审查", ordinary)
        explicit = self.capture("$personal-dev:dev-delegate 仅验证加载，本轮不执行正文、不派发模型、不修改文件。")
        self.assertIn("# 委派开发与独立验收", explicit)
        self.assertIn("编码模型：", explicit)
        self.assertIn("验收模型：", explicit)
        review = self.capture("$personal-dev:dev-review 仅验证加载，本轮不执行正文、不派发模型、不修改文件。")
        self.assertIn("# 增强代码审查", review)
        self.assertIn("审查模型：", review)
        self.assertIn("复核模型：", review)


if __name__ == "__main__":
    unittest.main()
