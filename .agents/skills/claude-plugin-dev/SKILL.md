---
name: claude-plugin-dev
description: Use when developing, repairing, or checking this repository's Claude Code plugin manifests and discovery, commands, agents, hooks, MCP servers, settings, or Skills. Applies only to Claude Code plugin behavior in this repository.
---

# Claude Code Plugin Development

Use the relevant official reference bundled at `.agents/plugin-dev/upstream/`. Start with that topic's `SKILL.md` or guide, then read only the linked references, examples, and scripts needed for the task. The bundle's entry point is `.agents/plugin-dev/upstream/README.md`.

| Topic | Start here | Related upstream material |
| --- | --- | --- |
| Plugin manifests and discovery | `skills/plugin-structure/SKILL.md` | `skills/plugin-structure/references/manifest-reference.md`, `skills/plugin-structure/README.md`, `.claude-plugin/plugin.json` |
| Commands | `skills/command-development/SKILL.md` | `commands/create-plugin.md`, `skills/command-development/references/`, `skills/command-development/examples/` |
| Agents | `skills/agent-development/SKILL.md` | `agents/agent-creator.md`, `agents/plugin-validator.md`, `agents/skill-reviewer.md`, `skills/agent-development/references/`, `skills/agent-development/examples/` |
| Hooks | `skills/hook-development/SKILL.md` | `skills/hook-development/references/`, `skills/hook-development/examples/`, `skills/hook-development/scripts/` |
| MCP servers | `skills/mcp-integration/SKILL.md` | `skills/mcp-integration/references/`, `skills/mcp-integration/examples/` |
| Plugin settings | `skills/plugin-settings/SKILL.md` | `skills/plugin-settings/references/`, `skills/plugin-settings/examples/`, `skills/plugin-settings/scripts/` |
| Skills | `skills/skill-development/SKILL.md` | `skills/skill-development/references/` |

Keep the change within the user's requested Claude Code plugin scope and this repository's existing contracts. Do not apply generic development workflow Skills automatically. Treat Claude-only commands such as `/plugin-dev:create-plugin`, Claude subagent fields, `allowed-tools`, model names, and `CLAUDE_PLUGIN_ROOT` as Claude Code behavior; do not present them as Codex capabilities. Read bundled resources by their actual repository paths. Do not run every upstream script as a blanket check; select a relevant validator only when it fits the task.

The bundled upstream snapshot is fixed by `.agents/plugin-dev/source.json`. For version-sensitive behavior, check the current Claude Code documentation as well as the bundled reference and report any version boundary that affects the change.
