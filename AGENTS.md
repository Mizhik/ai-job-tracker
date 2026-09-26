# Project instructions for Codex and Jules

## Skills and codebase navigation

- Codex uses the installed `karpathy-guidelines` skill when planning, writing, or reviewing code. Follow that skill for assumptions, simplicity, focused changes, and verifiable success criteria instead of repeating its rules here.
- Codex uses the installed `codebase-memory` skill and MCP for structural codebase exploration, call tracing, and impact analysis. Verify material findings against source files.
- Local Codex skills are not installed in Jules. When delegating, Codex includes any relevant skill guidance in the Jules prompt.
- Jules reads this `AGENTS.md` from its selected GitHub branch. Include task-specific context in each Jules prompt.

## Clean Architecture

- Codex uses the installed `clean-architecture` skill when planning or reviewing backend changes. Jules follows the project rules below.
- Follow the project's existing layers: `backend/core` for domain models and repository ports, `backend/app` for use cases and application services, `backend/infrastructure` for database and external-service adapters, and `backend/api` for HTTP endpoints, schemas, and dependency wiring.
- Dependencies point toward the core. Keep business decisions out of HTTP handlers and persistence adapters. Application use cases depend on core ports, not concrete database implementations.
- Put new framework-specific schemas and validation at the API boundary. Avoid adding new FastAPI, database, or other infrastructure dependencies to the core. Existing core models use Pydantic; do not perform a broad migration unless the task calls for it.
- Inject external dependencies through ports or constructors. Keep I/O asynchronous where the surrounding code is asynchronous.
- Add focused tests for meaningful domain or use-case behavior and integration tests where adapter behavior matters. Verify the relevant checks and report what actually ran.

## Working with Jules

- Codex defines a narrow task, acceptance criteria, the GitHub source and starting branch, and any necessary context that exists only locally. Never send secrets or local credential files.
- Create Jules sessions with plan approval required. Codex reviews the plan, requests corrections when needed, and approves a suitable plan before implementation.
- Jules implements in its isolated session. A completed session may return a change set without creating a branch or pull request; verify the actual output before describing it as published.
- Codex reviews the resulting diff, checks the architecture rules and acceptance criteria, and runs relevant local checks when the change is available locally. Ask Jules to correct defects found in review.
- Do not merge changes before review. Report the final result, evidence from checks, and any remaining limitations to the user.
- Jules works from the connected GitHub repository. Files available only in the local checkout are absent from its environment unless their relevant contents are supplied in the task prompt.

## Commit messages

- Use the next sequential `0.0.N` number at the start of the subject. Check recent Git history before choosing `N`.
- Subject format: `0.0.N Short English summary`. Do not add parentheses or an `AI` label.
- Write the commit body in English. Keep it brief and describe the implemented changes at a level useful to other developers.
- Do not include conversation details, user decisions, local-only notes, or lists of files added to the commit.
- Keep Jules API keys and other credentials out of the repository, task prompts, commits, and logs.
