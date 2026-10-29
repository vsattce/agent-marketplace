"""Exercise sync orchestration without touching the real agy profile."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".agents/skills/sync-agy/scripts/sync.ps1"
CATALOG = json.loads((ROOT / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
NAMES = {entry["name"] for entry in CATALOG["plugins"]}
PWSH = shutil.which("pwsh")
HARNESS = r"""
$global:mockCalls = @()
$global:mockInstalled = @(
    @{name='unrelated'; enabled=$true; version='1'; path='unrelated'; skills=@()},
    @{name='software-dev'; enabled=$false; version='old'; path='old'; skills=@()}
)
if ($env:AGY_TEST_MODE -eq 'legacy') {
    $global:mockInstalled += @{name='testing-automation'; enabled=$true; version='old'; path='legacy'; skills=@('playwright-cli')}
}
function global:agy {
    $global:LASTEXITCODE = 0
    $global:mockCalls += ($args -join '|')
    if ($args[0] -eq '--version') { 'fixture'; return }
    switch ($args[1]) {
        'list' { ConvertTo-Json -InputObject @($global:mockInstalled) -Depth 5 -Compress }
        'validate' {
            $name = Split-Path $args[2] -Leaf
            if ($env:AGY_TEST_MODE -eq 'invalid' -and $name -eq 'personal-dev') {
                $global:LASTEXITCODE = 2
                return
            }
            $count = @(Get-ChildItem (Join-Path $args[2] 'skills') -Directory |
                Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') }).Count
            @{name=$name; components=@{skills=$count}; findings=@()} | ConvertTo-Json -Depth 4 -Compress
        }
        'install' {
            $name = Split-Path $args[2] -Leaf
            if ($env:AGY_TEST_MODE -eq 'fail' -and $name -eq 'software-dev') {
                $global:LASTEXITCODE = 3
                return
            }
            $skills = @(Get-ChildItem (Join-Path $args[2] 'skills') -Directory |
                Where-Object { Test-Path (Join-Path $_.FullName 'SKILL.md') } | Select-Object -ExpandProperty Name)
            if ($env:AGY_TEST_MODE -eq 'missing') { $skills = @('missing') }
            $global:mockInstalled = @($global:mockInstalled | Where-Object name -ne $name) + @(
                @{name=$name; enabled=$true; version='new'; path=$args[2]; skills=$skills}
            )
        }
        'disable' { ($global:mockInstalled | Where-Object name -eq $args[2]).enabled = $false }
        default { throw 'Unexpected agy operation' }
    }
}
$failure = $null
try {
    & $env:AGY_SYNC_SCRIPT -AgyPath agy -CheckOnly:($env:AGY_TEST_MODE -eq 'check') | Out-Null
} catch { $failure = $_.Exception.Message }
$result = @{failure=$failure; calls=@($global:mockCalls); installed=@($global:mockInstalled)}
'AGY_TEST:' + (ConvertTo-Json -InputObject $result -Depth 6 -Compress)
"""


@unittest.skipUnless(PWSH, "PowerShell 7 is required")
class AgySyncTests(unittest.TestCase):
    def run_sync(self, mode):
        environment = dict(os.environ, AGY_SYNC_SCRIPT=str(SCRIPT), AGY_TEST_MODE=mode)
        result = subprocess.run(
            [PWSH, "-NoProfile", "-NonInteractive", "-Command", HARNESS],
            cwd=ROOT, env=environment, capture_output=True, text=True, encoding="utf-8",
            timeout=45, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = [line for line in result.stdout.splitlines() if line.startswith("AGY_TEST:")]
        self.assertEqual(len(payload), 1, result.stdout + result.stderr)
        return json.loads(payload[0].removeprefix("AGY_TEST:"))

    def test_check_only_validates_every_product_without_mutation(self):
        result = self.run_sync("check")
        self.assertIsNone(result["failure"])
        self.assertEqual(sum(call.startswith("plugin|validate|") for call in result["calls"]), len(NAMES))
        self.assertFalse(any(call.startswith(("plugin|install|", "plugin|disable|")) for call in result["calls"]))
        self.assertEqual({item["name"] for item in result["installed"]}, {"unrelated", "software-dev"})

    def test_sync_preserves_disabled_and_unrelated_plugins(self):
        result = self.run_sync("sync")
        self.assertIsNone(result["failure"])
        installed = {item["name"]: item for item in result["installed"]}
        self.assertEqual(set(installed), NAMES | {"unrelated"})
        self.assertFalse(installed["software-dev"]["enabled"])
        self.assertEqual(installed["unrelated"]["path"], "unrelated")
        self.assertEqual(installed["unrelated"]["version"], "1")
        calls = result["calls"]
        last_validation = max(index for index, call in enumerate(calls) if call.startswith("plugin|validate|"))
        first_install = min(index for index, call in enumerate(calls) if call.startswith("plugin|install|"))
        self.assertLess(last_validation, first_install)
        self.assertNotIn("am-context", installed["agent-manager"]["skills"])
        self.assertEqual(set(installed["engineering-tools"]["skills"]), {
            "docker-build-strategies", "docker-compose-patterns", "playwright-cli",
        })

    def test_old_testing_plugin_blocks_sync_before_mutation(self):
        result = self.run_sync("legacy")
        self.assertIn("Uninstall the old plugin", result["failure"])
        self.assertFalse(any(call.startswith(("plugin|install|", "plugin|disable|")) for call in result["calls"]))
        self.assertEqual({item["name"] for item in result["installed"]}, {
            "unrelated", "software-dev", "testing-automation",
        })

    def test_invalid_product_prevents_all_installs(self):
        result = self.run_sync("invalid")
        self.assertIn("failed", result["failure"])
        self.assertFalse(any(call.startswith("plugin|install|") for call in result["calls"]))

    def test_install_failure_stops_without_retry_or_uninstall(self):
        result = self.run_sync("fail")
        self.assertIn("exit 3", result["failure"])
        installs = [call for call in result["calls"] if call.startswith("plugin|install|")]
        self.assertEqual(len(installs), 3)
        self.assertFalse(any("uninstall" in call for call in result["calls"]))

    def test_missing_installed_skill_stops_verification(self):
        result = self.run_sync("missing")
        self.assertIn("skill inventory differs", result["failure"])
        self.assertEqual(sum(call.startswith("plugin|install|") for call in result["calls"]), 1)


if __name__ == "__main__":
    unittest.main()
