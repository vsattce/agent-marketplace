"""Shared paths for repository-local test artifacts."""

from pathlib import Path
import tempfile


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TEST_TEMP_ROOT = REPOSITORY_ROOT / ".agent-tmp" / "tests"


def _prepare_test_temp_root() -> None:
    repository = REPOSITORY_ROOT.absolute()
    if repository.is_symlink() or repository.is_junction() or repository.resolve() != repository:
        raise RuntimeError("Repository test root is redirected")

    expected = repository / ".agent-tmp" / "tests"
    if TEST_TEMP_ROOT.absolute() != expected:
        raise RuntimeError("Test temporary directory is outside its repository location")

    for directory in (repository / ".agent-tmp", TEST_TEMP_ROOT):
        try:
            if directory.is_symlink() or directory.is_junction() or directory.resolve() != directory.absolute():
                raise RuntimeError(f"Test temporary directory is redirected: {directory.name}")
            if directory.exists() and not directory.is_dir():
                raise RuntimeError(f"Test temporary path is not a directory: {directory.name}")
            directory.mkdir(exist_ok=True)
            if directory.is_symlink() or directory.is_junction() or directory.resolve() != directory.absolute():
                raise RuntimeError(f"Test temporary directory is redirected: {directory.name}")
        except OSError as error:
            raise RuntimeError(f"Cannot prepare test temporary directory: {directory.name}") from error


def temporary_test_directory(scope: str) -> tempfile.TemporaryDirectory:
    _prepare_test_temp_root()
    return tempfile.TemporaryDirectory(prefix=f"{scope}-", dir=TEST_TEMP_ROOT)
