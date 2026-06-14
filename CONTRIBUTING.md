# Contributing to quickwit-mcp

Thanks for your interest! This project is small and read-only by design — contributions that
keep it that way are very welcome.

## Workflow: Issue → PR → Review → Merge

Every change starts with an **issue** and lands via a **pull request** reviewed and merged by a
maintainer.

1. **Find or open an issue.** New to the project? Look for
   [`good first issue`](https://github.com/agarwalvivek29/quickwit-mcp/labels/good%20first%20issue).
   Comment to claim it.
2. **Branch** off `main`: `feat/<short>`, `fix/<short>`, `docs/<short>`, `ci/<short>`, `chore/<short>`.
3. **Open a PR** that references the issue: put `Closes #<n>` in the body.
4. A maintainer reviews and merges.

> Branch protection is not yet enabled (single maintainer) — the flow above is followed by
> convention. It will be enforced once a second maintainer joins (see [ROADMAP](./ROADMAP.md)).

## Commit & PR titles: Conventional Commits

Use [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`,
`ci:`, `chore:`, `refactor:`, `test:`. This drives the [CHANGELOG](./CHANGELOG.md) and versioning.

Do **not** add `Co-Authored-By` trailers.

## Local development

Requires **Python ≥ 3.10**.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install        # optional: runs ruff on commit
```

Checks (all must pass — this is what CI runs):

```bash
ruff check .
ruff format --check .
pytest -q
```

## Verify against live Quickwit — required

Unit tests prove the logic; they do **not** prove it works against real Quickwit (response
shapes, wire formats, and sort/aggregation semantics have surprised us before). For any change
that touches the client, a tool, or the server:

```bash
scripts/dev-quickwit.sh up        # local Quickwit + seeded logs-demo
# exercise your change against http://localhost:7280, capture the output in your PR
scripts/dev-quickwit.sh down
```

Include the real output in your PR's verification section. Pure-logic changes (no Quickwit
interaction) can note "unit-only".

## PR checklist

- [ ] Linked to an issue (`Closes #N`)
- [ ] Conventional Commits title
- [ ] `ruff check .` and `ruff format --check .` pass
- [ ] Tests added/updated; `pytest` passes
- [ ] Verified against live Quickwit (or noted unit-only)
- [ ] Docs updated if behavior/config changed

## Scope

v0.0.1 is **read-only**. Write/admin capabilities are intentionally out of scope; see the
[ROADMAP](./ROADMAP.md) for what's planned.
