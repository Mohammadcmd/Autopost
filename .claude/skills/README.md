# Vendored Claude Code skills

The skills in this directory are vendored from upstream sources so they're
available to Claude Code whenever it works in this repository.

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

To pick up upstream updates, re-copy the relevant skill directory from its
source repository.
