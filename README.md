# Little List — agent-driven todo loop

Little List is a deliberately small FastAPI + SQLite todo app. It keeps the supplied **little list** visual language—warm paper, editorial typography, progress card, filters, and light task rows—while making persistence and API behaviour real enough for agents to inspect.

## Run it

```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000`. Todos persist to `data/little_list.db`; set `TODO_DATABASE` to use another SQLite file.

## Development loop

1. **Plan and claim.** Claude Code connects to Linear's remote MCP server, creates/summarises the small feature tickets, selects one, and moves it to **In Progress**.
2. **Implement.** Claude Code is given the ticket acceptance criteria, modifies only that scope, runs `ruff check .` and `pytest`, pushes a branch, creates a PR, then moves the Linear ticket to **In Review**.
3. **Verify and review.** `.github/workflows/ci.yml` runs deterministic lint and tests. `.github/workflows/review.yml` invokes Claude Code to review same-repository PRs and submit either an approval or requested changes.
4. **Merge and close.** Protect `main` in GitHub with the CI status check and one approving review, and enable repository auto-merge. An approving review triggers `.github/workflows/auto-merge.yml`, which enables squash auto-merge; GitHub waits for CI. After the merge, run `py linear_update.py LIT-12` from a trusted automation environment to move the ticket to **Done**.
5. **Discover.** Trigger a separate, narrow audit prompt on demand: “Inspect this repository for dead code, missing tests, or persistence/API risks. Report only verifiable findings and create one Linear ticket per finding.” This is intentionally a different auditor role from the implementation agent.

The review workflow needs the repository secret `ANTHROPIC_API_KEY`. The Linear closing helper needs `LINEAR_API_KEY`. Neither belongs in the repository. For a full autonomous post-merge close, invoke `linear_update.py` from a protected GitHub Action after extracting the linked Linear identifier from the PR body.

## Connect the app MCP server

`little_list_mcp.py` is a read-only Python MCP server. Its tools return application source or implementation-grounded answers rather than hand-written summaries:

- `app_architecture`
- `read_source(path)`
- `search_code(query)`
- `explain_persistence`

### Codex

Copy `codex-mcp.example.toml` into `.codex/config.toml`, or run:

```bash
codex mcp add little-list -- py little_list_mcp.py
```

Then ask: “Where are todos stored, and what happens when I delete one?”

### Claude Code

```bash
claude mcp add --transport stdio little-list -- py little_list_mcp.py
```

Then ask the same question. Both answers are grounded in the same live source.

## Suggested Linear tickets

- **LIT-1:** Create Todo API and SQLite schema.
- **LIT-2:** Add the browser UI with add, complete, delete, and clear-finished actions.
- **LIT-3:** Add lifecycle/error tests and CI.
- **LIT-4:** Audit the app for an actionable test or resilience gap.

## Scope and honest limits

The full ticket-to-PR-to-CI-to-review-to-auto-merge loop is configured, but it needs a real GitHub repository with branch protection and secrets plus a Linear workspace to execute. Linear's interactive MCP connection is used for the demonstrated agent work; the tiny API helper is used for dependable non-interactive post-merge status changes. With more time, I would add a protected post-merge Linear workflow, PR-to-ticket identifier validation, and a persisted decision log for the planner/auditor agents.
