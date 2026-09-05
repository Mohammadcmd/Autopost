# Vendored Claude Code skills

The skills in this directory are vendored from upstream sources so they're
available to Claude Code whenever it works in this repository.

## `ui-ux-pro-max-skill`

Source: [nextlevelbuilder/ui-ux-pro-max-skill](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill),
MIT licensed — see `LICENSE-ui-ux-pro-max-skill`.

- `banner-design`, `brand`, `design`, `design-system`, `slides`, `ui-styling`, `ui-ux-pro-max`

## `superpowers`

Source: [obra/superpowers](https://github.com/obra/superpowers), MIT
licensed — see `LICENSE-superpowers`. A software development methodology
(brainstorming, TDD, systematic debugging, code review, plan writing, etc.).

- `brainstorming`, `dispatching-parallel-agents`, `executing-plans`,
  `finishing-a-development-branch`, `receiving-code-review`,
  `requesting-code-review`, `subagent-driven-development`,
  `systematic-debugging`, `test-driven-development`, `using-git-worktrees`,
  `using-superpowers`, `verification-before-completion`, `writing-plans`,
  `writing-skills`

## `frontend-design`

Source: [anthropics/claude-code](https://github.com/anthropics/claude-code)
(`plugins/frontend-design/skills/frontend-design/SKILL.md`), an official
Claude Code example plugin. Guidance for distinctive, intentional visual
design when building or reshaping UI.

Note: unlike the other skills vendored in this directory, this file is not
MIT licensed. The `claude-code` repository is © Anthropic PBC, all rights
reserved, and use is subject to Anthropic's
[Commercial Terms of Service](https://www.anthropic.com/legal/commercial-terms).
It's included here per the repo's own documented intent (its `plugins/README.md`
describes these plugins as meant to be shared and used across projects and
teams).

## `code-review`

Source: [mattpocock/skills](https://github.com/mattpocock/skills)
(`skills/engineering/code-review`), MIT licensed — see
`LICENSE-mattpocock-skills`. Two-axis review of a diff (coding standards +
spec conformance) using parallel sub-agents.

## `claude-mem`

Source: [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem)
(`plugin/skills/`), Apache-2.0 licensed — see `LICENSE-claude-mem` and
`NOTICE-claude-mem`.

- `babysit`, `cloud-sync`, `design-is`, `do`, `how-it-works`,
  `knowledge-agent`, `learn-codebase`, `make-plan`, `mem-search`,
  `mode-creator`, `oh-my-issues`, `pathfinder`, `smart-explore`, `standup`,
  `timeline-report`, `version-bump`, `weekly-digests`, `what-the`,
  `wowerpoint`

**Important caveat:** claude-mem is not just a skill bundle — it's a full
memory system with a background worker, SQLite storage, an MCP server, and
(for cloud sync) an account sign-in flow. Several of these skills
(`mem-search`, `cloud-sync`, `knowledge-agent`, etc.) assume that worker/MCP
infrastructure is actually running and will not do anything useful without
it. Only the skill *documents* are vendored here — the runtime itself is not
installed. To get the full working system, install it separately:

```bash
npx claude-mem install
```

or, inside Claude Code:

```
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem
```

To pick up upstream updates, re-copy the relevant skill directories from
their source repositories.
