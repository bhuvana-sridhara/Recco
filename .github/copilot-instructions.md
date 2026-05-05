# Copilot / AI agent instructions for Recco.

Purpose
- Help AI coding agents become productive quickly in this repository. This project currently contains a minimal proof-of-concept: see `README.md` for the high-level goal (individual movie recommendations + friend decision helper).

Repository snapshot (current discoverable files)
- `README.md` — project description only. No source directories, build scripts, or tests were found.

Guiding principles for changes
- Do not assume hidden services, frameworks, or languages; ask the human owner before introducing major architecture (databases, cloud services, CI).
- Prefer small, incremental changes with explicit rationale in the PR body.
- Avoid reorganizing the repository without an explicit task or approval from the owner.

How to get started (agent workflow)
- Read `README.md` and list missing artifacts (source dir, language/runtime, tests, build commands). Example: this repo lacks `src/`, `package.json`, or `requirements.txt`.
- Ask a clarifying question: "Which language/runtime should I use (Node, Python, etc.)? Do you want me to scaffold a backend, web UI, or both?"
- If the owner approves scaffolding, create a short plan (3–6 steps) and post it as the first commit message and PR description.

When you find or add files
- Document any added entry points in `README.md` (short sentence + run commands). Keep `README.md` minimal and factual.
- If you add config or secret-related files, never commit secrets. Use `.gitignore` and note secrets in PR as required environment variables.

Conventions and expectations for this repo
- Branch: `main` is present and is the default branch. Create feature branches for work (e.g., `feature/add-recommender`).
- Commits: concise, imperative subject line and a short body when necessary.

Integration, tests, and CI
- No CI config discovered. Ask whether to add CI (GitHub Actions). If asked to add CI, implement a minimal workflow that just installs dependencies and runs tests (if tests exist).

Examples and references to the current codebase
- There are no source files to inspect beyond `README.md`. Reference `README.md` directly when describing the project's intent in PRs and commits.

Safety and permissions
- Request permission before provisioning external services (databases, hosted recommender APIs, 3rd-party keys).
- If you need sample data, generate synthetic data and make the generation script self-contained and documented.

What to do if you need to change structure
- Propose the new structure in a short RFC (one-file markdown) and get owner approval. Example RFC sections: motivation, proposed folders (`api/`, `recommender/`, `web/`), migration plan, and tests to validate.

If this file already exists when you run, merge policy
- Preserve existing human-written guidance. If creating similar content, open a PR that shows a side-by-side diff and explain edits in the PR description.

Questions for the owner (ask before major work)
- Which language/runtime should be primary for implementing the recommender?
- Do you want a simple CLI, a web UI, or both?
- Are there preferred libraries or infra (e.g., PostgreSQL, Firebase, AWS)?

— End of instructions —