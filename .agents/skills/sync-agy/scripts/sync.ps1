#requires -Version 7.0
[CmdletBinding()]
param(
    [string] $AgyPath,
    [switch] $CheckOnly
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repositoryRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../../..'))
$gitRoot = & git -C $repositoryRoot rev-parse --show-toplevel
if ($LASTEXITCODE -ne 0 -or [IO.Path]::GetFullPath($gitRoot) -ne $repositoryRoot) {
    throw 'sync-agy must run from its agent-marketplace Git checkout.'
}
$catalog = Get-Content -LiteralPath (Join-Path $repositoryRoot '.agents/plugins/marketplace.json') -Raw | ConvertFrom-Json
if ($catalog.name -ne 'agent-marketplace') { throw 'Unexpected Marketplace identity.' }
if (-not $AgyPath) {
    $agyCommand = Get-Command agy -ErrorAction SilentlyContinue
    if ($agyCommand) { $AgyPath = $agyCommand.Source }
    elseif ($env:LOCALAPPDATA) { $AgyPath = Join-Path $env:LOCALAPPDATA 'agy/bin/agy.exe' }
}
if (-not $AgyPath -or -not (Get-Command $AgyPath -ErrorAction SilentlyContinue)) {
    throw 'agy was not found. Provide -AgyPath; no PATH or installation changes were made.'
}

function Invoke-Agy([string[]] $Arguments) {
    $global:LASTEXITCODE = 0
    $output = @(& $AgyPath @Arguments)
    if ($LASTEXITCODE -ne 0) {
        $operation = ($Arguments | Select-Object -First 2) -join ' '
        throw "agy $operation failed (exit $LASTEXITCODE)."
    }
    $output
}

Write-Host "agy version: $(Invoke-Agy @('--version'))"
$before = @(Invoke-Agy @('plugin', 'list', '--json') | ConvertFrom-Json)
$targets = @()
$names = @()
foreach ($plugin in $catalog.plugins) {
    if ($plugin.name -notmatch '^[a-zA-Z0-9_-]+$' -or $plugin.name -in $names -or
        $plugin.source.source -ne 'local' -or $plugin.source.path -ne "./plugins/$($plugin.name)") {
        throw "Unexpected or duplicate product source: $($plugin.name)"
    }
    $names += $plugin.name
    $sourcePath = Join-Path $repositoryRoot "plugins/$($plugin.name)"
    $sourceItem = Get-Item -LiteralPath $sourcePath
    $links = @(Get-ChildItem -LiteralPath $sourcePath -Recurse -Attributes ReparsePoint)
    if ($sourceItem.Attributes -band [IO.FileAttributes]::ReparsePoint -or $links.Count) {
        throw "Linked plugin resources are not supported: $($plugin.name)"
    }
    $validation = Invoke-Agy @('plugin', 'validate', $sourcePath, '--json') | ConvertFrom-Json
    if ($validation.name -ne $plugin.name -or $validation.components.skills -lt 1 -or
        @($validation.findings | Where-Object severity -eq 'error').Count) {
        throw "Plugin validation failed: $($plugin.name)"
    }
    $existing = @($before | Where-Object name -eq $plugin.name)
    if ($existing.Count -gt 1) { throw "Ambiguous installed plugin: $($plugin.name)" }
    $targets += [pscustomobject]@{
        Name = $plugin.name
        Source = $sourcePath
        Skills = $validation.components.skills
        Installed = $existing.Count -eq 1
        Enabled = if ($existing.Count) { $existing[0].enabled } else { $true }
    }
}
if (-not $targets.Count) { throw 'No product plugins found.' }
if ($CheckOnly) {
    $targets | Select-Object Name, Skills, Installed, Enabled
    return
}

foreach ($target in $targets) {
    Write-Host "Syncing $($target.Name)..."
    Invoke-Agy @('plugin', 'install', $target.Source) | ForEach-Object { Write-Host $_ }
    if (-not $target.Enabled) { Invoke-Agy @('plugin', 'disable', $target.Name) | Out-Null }
    $installed = @(Invoke-Agy @('plugin', 'list', '--json') | ConvertFrom-Json |
        Where-Object name -eq $target.Name)
    if ($installed.Count -ne 1 -or $installed[0].enabled -ne $target.Enabled) {
        throw "Installation or enablement verification failed: $($target.Name)"
    }
    $expectedSkills = @(Get-ChildItem -LiteralPath (Join-Path $target.Source 'skills') -Directory |
        Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'SKILL.md') } |
        Select-Object -ExpandProperty Name)
    if (Compare-Object $expectedSkills @($installed[0].skills)) {
        throw "Installed skill inventory differs: $($target.Name)"
    }
    foreach ($folder in @('skills', 'references', 'licenses', 'assets')) {
        $resourceRoot = Join-Path $target.Source $folder
        if (-not (Test-Path -LiteralPath $resourceRoot)) { continue }
        foreach ($file in Get-ChildItem -LiteralPath $resourceRoot -Recurse -File) {
            $relative = [IO.Path]::GetRelativePath($target.Source, $file.FullName)
            $copy = Join-Path $installed[0].path $relative
            if (-not (Test-Path -LiteralPath $copy -PathType Leaf) -or
                (Get-FileHash -LiteralPath $file.FullName).Hash -ne (Get-FileHash -LiteralPath $copy).Hash) {
                throw "Installed resource differs: $($target.Name)/$relative"
            }
        }
    }
    Write-Host "Verified $($target.Name): $($target.Skills) skills at $($installed[0].path)"
}
$after = @(Invoke-Agy @('plugin', 'list', '--json') | ConvertFrom-Json)
foreach ($unrelated in $before | Where-Object { $_.name -notin $names }) {
    $retained = @($after | Where-Object name -eq $unrelated.name)
    if ($retained.Count -ne 1 -or $retained[0].enabled -ne $unrelated.enabled -or
        $retained[0].path -ne $unrelated.path -or $retained[0].version -ne $unrelated.version) {
        throw "Unrelated plugin state changed: $($unrelated.name)"
    }
}
Write-Host "Verified all $($targets.Count) product plugins. Open a new agy session to check loaded commands."
