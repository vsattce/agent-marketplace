# Personal Dev Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development. The primary writes the spec/plan and performs final acceptance; `gpt-6-luna` / `xhigh` implements, and a separate `gpt-6-luna` / `max` reviews. User-agreed routing and the two-round stop policy override upstream defaults.

**Goal:** Deliver a Codex-only, manual development workflow with explicit model selection and visible startup routing.

**Architecture:** Keep the workflow in one Skill with compact role instructions. A standard-library Python resolver validates a supplied current-tool inventory; it never discovers models or changes Codex configuration.

**Tech Stack:** Markdown, JSON, YAML metadata, Python 3.12+, unittest, existing uv/mise validation.

**Spec:** `docs/superpowers/specs/2026-10-10-personal-dev-design.md`

## Global Constraints

- Codex only; register only in `.agents/plugins/marketplace.json`.
- Explicit invocation; `allow_implicit_invocation: false` and `disable-model-invocation: true`.
- Coding defaults to `xhigh`; independent same-model review defaults to `max`.
- Unknown or ambiguous model decisions block; no silent model/effort fallback.
- Two repair rounds per task, no automatic escalation or controller coding.
- Preserve user changes; no global configuration/install mutation; sources/lock remain unchanged.
- Commit and push the completed task once under the repository's existing delivery rule.

## Review Focus

- Current tool inventory must remain authoritative over public catalog names.
- Missing current primary identity must not be filled from default config.
- Numeric versions and aliases must not produce accidental old-generation selection.
- Uncommitted and newly created files must be included in review evidence.
- Final-review repairs and context recovery must not reset repair counts.

## Task 1: Deterministic model selection

**Files:** `plugins/personal-dev/skills/delegated-development/scripts/select_models.py`, `tests/test_personal_dev.py`.

**Interface:** `select_models(payload: dict) -> dict`, plus JSON stdin CLI. Input: `primary_model`, `primary_model_source` (`current-turn` or `user`), `inventory_source` (`current-spawn-tool`), `models` list with `id` and `efforts`; optional `model_override` and boolean `override_confirmed`; optional `coding_effort` / `review_effort`. Output: `READY` with coding/review model and effort plus display lines, or `BLOCKED` with reasons. CLI exits 0 for READY and 2 for BLOCKED. Invalid JSON returns BLOCKED without echoing input. No external dependencies or side effects.

- [x] Write behavioral tests before production code; verify expected RED.
- [x] Implement numeric selection within the primary major version, approved Luna series, explicit confirmed override, supported-effort checks and ambiguity rejection.
- [x] Verify READY defaults/overrides and BLOCKED missing/unknown/ambiguous cases, JSON CLI and read-only behavior.

## Task 2: Skill, Codex packaging and documentation

**Files:** Plugin manifest, `agents/openai.yaml`, `SKILL.md`, `references/roles.md`, Codex catalog, README, usage/maintenance docs, existing cross-client packaging tests.

**Interfaces:** Consume Task 1's exact JSON input/output contract and CLI exit codes. Expose `$personal-dev:delegated-development` through the Codex catalog only. Reuse the existing isolated loader harness; never install into the user's daily Codex configuration.

- [x] Run no-guidance behavioral baseline before authoring the Skill.
- [x] Write compact instructions and required visible startup/stop output; document the helper's provenance and enforcement limits.
- [x] Register only in Codex, retain five existing Claude/Kimi plugins and 16 skills, add packaging tests for this explicit difference.
- [x] Validate guided behavior and isolated native discovery / explicit loading.

## Task 3: Acceptance and delivery

- [x] Independent `gpt-6-luna` / `max` review of actual edits and test evidence; address concrete blockers within the agreed repair cap.
- [x] Primary overall acceptance, targeted/full relevant Python tests and `git diff --check`.
- [x] Confirm README consistency and prepare the verified changes for Git delivery.

Delivery: create a Conventional Commit, push the current branch, and verify the remote hash and clean synchronized worktree. Record the actual delivery result in the final conversation response, rather than embedding a commit's own hash in its contents.

## Execution record

- Authorization: user explicitly requested spec, plan, implementation and independent acceptance on 2026-10-10. Continue without another plan approval pause. Keep the existing checkout/current branch under the project rule; do not duplicate the existing uncommitted work into another checkout.
- Baseline: `a334ad4bbe375d6ee2b9409a555a4d323d00ca40`; the checkout was clean before this task. Existing local changes belong to this task; no commit or push had occurred at resume.
- Preflight: Task 1 produces the resolver contract consumed by Task 2; both agree on IDs, efforts, exit codes and stop behavior. Task 3 reviews both and performs delivery without introducing another implementation interface.
- Task 1: complete. Implementer `/root/model_selector`; independent reviewer `/root/resolver_review` (`gpt-6-luna` / `max`) approved actual source/tests with no blockers, independently ran 21 passing targeted tests. Repair rounds: 0/2.
- Task 2: complete. Implementer `/root/plugin_author` (`gpt-6-luna` / `xhigh`); independent reviewer `/root/plugin_review` (`gpt-6-luna` / `max`) approved the actual files and evidence with no blockers. Packaging tests 2/2 passed; isolated native loader 1/1 passed. The author's report omitted the existing packaging-test adjustment from its file list; the reviewer and primary inspected that diff directly. Repair rounds: 0/2.
- Guided behavior: `/root/skill_guided_probe` (`gpt-6-luna` / `xhigh`, clean context) read the actual Skill/role contract and passed eight simulated scenarios: defaults, cross-generation/renamed uncertainty, two-round stop, no implicit invocation, future same-major selection, final-review counter persistence, confirmed exact replacement, and highest-version missing max. This is a decision simulation, not actual future-model dispatch or execution of the Skill body.
- Validation baseline: the previous full run executed 111 tests with 7 errors and 7 skips. The errors report managed-plugin path resolution in existing sync tests; diagnose against unchanged code before assigning them to this feature. Native loader tests were skipped because opt-in was unset.
- Baseline diagnosis: unchanged `scripts/sync.py` and `tests/test_sync.py` reject the Windows `C:\Users\ADMINI~1` temporary path because `resolve()` expands it to `C:\Users\Administrator`. All 13 sync tests pass when only the test process uses the canonical temporary directory (`tempfile.tempdir = str(Path(tempfile.gettempdir()).resolve())`). Preserve the existing synchronization/security logic; use that process-local test setup for full validation.
- Final normal suite: 111 tests executed, 104 passed and 7 opt-in client tests skipped, no failures/errors. The new personal-dev native loading test was separately enabled and passed on Codex CLI 0.160.1. Root reused the canonical-temp test setup without changing the environment permanently or editing synchronization code.
- Primary final acceptance: complete; reviewed cumulative tracked/untracked source, cross-client boundaries, resolver/Skill contract, repair counters, validation evidence and README consistency. No blockers. Git delivery follows under the repository's current-branch rule.
