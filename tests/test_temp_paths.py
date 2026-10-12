"""Safety checks for repository-local test artifact paths."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import temp_paths


class TemporaryTestDirectoryTests(unittest.TestCase):
    def setUp(self):
        self.sandbox = tempfile.TemporaryDirectory()
        self.addCleanup(self.sandbox.cleanup)
        self.repository = Path(self.sandbox.name) / "repository"
        self.repository.mkdir()
        self.temporary_root = self.repository / ".agent-tmp" / "tests"

    def test_creates_unique_run_directories_inside_repository(self):
        with patch.object(temp_paths, "REPOSITORY_ROOT", self.repository), patch.object(
            temp_paths, "TEST_TEMP_ROOT", self.temporary_root
        ):
            first = temp_paths.temporary_test_directory("fixture")
            second = temp_paths.temporary_test_directory("fixture")
            self.addCleanup(first.cleanup)
            self.addCleanup(second.cleanup)

        self.assertNotEqual(first.name, second.name)
        self.assertEqual(Path(first.name).parent, self.temporary_root)
        self.assertEqual(Path(second.name).parent, self.temporary_root)
        first.cleanup()
        second.cleanup()
        self.assertFalse(Path(first.name).exists())
        self.assertFalse(Path(second.name).exists())

    def test_rejects_redirected_test_directory_without_writing_outside(self):
        temporary_parent = self.repository / ".agent-tmp"
        temporary_parent.mkdir()
        outside = Path(self.sandbox.name) / "outside"
        outside.mkdir()
        test_root = temporary_parent / "tests"
        try:
            test_root.symlink_to(outside, target_is_directory=True)
        except OSError:
            self.skipTest("Host does not permit symlink creation")

        with patch.object(temp_paths, "REPOSITORY_ROOT", self.repository), patch.object(
            temp_paths, "TEST_TEMP_ROOT", test_root
        ):
            with self.assertRaises(RuntimeError):
                temp_paths.temporary_test_directory("fixture")

        self.assertEqual(list(outside.iterdir()), [])

    def test_rejects_non_directory_test_parent(self):
        (self.repository / ".agent-tmp").write_text("occupied", encoding="utf-8")

        with patch.object(temp_paths, "REPOSITORY_ROOT", self.repository), patch.object(
            temp_paths, "TEST_TEMP_ROOT", self.temporary_root
        ):
            with self.assertRaises(RuntimeError):
                temp_paths.temporary_test_directory("fixture")

    def test_rejects_test_directory_outside_repository(self):
        outside = Path(self.sandbox.name) / "outside-tests"

        with patch.object(temp_paths, "REPOSITORY_ROOT", self.repository), patch.object(
            temp_paths, "TEST_TEMP_ROOT", outside
        ):
            with self.assertRaises(RuntimeError):
                temp_paths.temporary_test_directory("fixture")

        self.assertFalse(outside.exists())


if __name__ == "__main__":
    unittest.main()
