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

To pick up upstream updates, re-copy the relevant skill directories from
their source repositories.
