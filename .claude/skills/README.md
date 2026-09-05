# Vendored Claude Code skills

The skills in this directory are vendored from
[thedotmack/claude-mem](https://github.com/thedotmack/claude-mem)
(`plugin/skills/`), Apache-2.0 licensed — see `LICENSE-claude-mem` and
`NOTICE-claude-mem`.

- `babysit`, `cloud-sync`, `design-is`, `do`, `how-it-works`,
  `knowledge-agent`, `learn-codebase`, `make-plan`, `mem-search`,
  `mode-creator`, `oh-my-issues`, `pathfinder`, `smart-explore`, `standup`,
  `timeline-report`, `version-bump`, `weekly-digests`, `what-the`,
  `wowerpoint`

## Important caveat

claude-mem is not just a skill bundle — it's a full memory system with a
background worker, SQLite storage, an MCP server, and (for cloud sync) an
account sign-in flow. Several of these skills (`mem-search`, `cloud-sync`,
`knowledge-agent`, etc.) assume that worker/MCP infrastructure is actually
running and will not do anything useful without it.

Only the skill *documents* are vendored here — the runtime itself is not
installed. To get the full working system, install it separately per the
upstream project's instructions:

```bash
npx claude-mem install
```

or, inside Claude Code:

```
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem
```

To pick up upstream updates, re-copy the relevant skill directories from the
source repository.
