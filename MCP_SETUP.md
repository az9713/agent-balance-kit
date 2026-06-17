# MCP Setup for the Zack-Style External Loop

This kit does not ship your Slack, Linear, GitHub, browser, or Oura credentials. Configure MCP servers in Claude Code and keep secrets outside Git.

Claude Code supports adding MCP servers from JSON with `claude mcp add-json <name> '<json>'`, and the JSON can describe HTTP or stdio servers. Use `--scope user` for personal servers and project scope only for shareable, non-secret configuration.

## Recommended MCP names

Use these stable server names so the included skills can refer to them:

- `slack`
- `linear`
- `github`
- `playwright`
- `oura` or `health`

## Generic examples

HTTP server with token header:

```powershell
claude mcp add-json slack '{"type":"http","url":"https://YOUR-SLACK-MCP/mcp","headers":{"Authorization":"Bearer YOUR_TOKEN"}}' --scope user
```

Local stdio server:

```powershell
claude mcp add-json playwright '{"type":"stdio","command":"npx","args":["-y","YOUR_PLAYWRIGHT_MCP_PACKAGE"]}' --scope user
```

OAuth-capable HTTP server:

```powershell
claude mcp add-json oura '{"type":"http","url":"https://YOUR-OURA-MCP/mcp","oauth":{"clientId":"YOUR_CLIENT_ID","callbackPort":8080}}' --client-secret --scope user
```

## Safe fallback without MCP

Run these local tools instead:

```powershell
python .claude/tools/sync_external_signals.py --github --linear --slack
python .claude/tools/signal_triage.py --apply
python .claude/tools/health_state.py --manual HEALTH_STATE.md
python .claude/tools/browser_verify.py --config .agent-harness/browser_targets.json
```

The local tools use environment variables from `.env.example` and write non-secret runtime outputs under `.agent-harness/`.
