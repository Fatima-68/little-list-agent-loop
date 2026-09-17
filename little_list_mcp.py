"""Read-only MCP tools that ground agent answers in this repository's source."""

from pathlib import Path

from fastmcp import FastMCP

PROJECT_ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = PROJECT_ROOT / "app"
mcp = FastMCP("Little List")


def _source_file(path: str) -> Path:
    file = (PROJECT_ROOT / path).resolve()
    if SOURCE_ROOT not in file.parents or not file.is_file():
        raise ValueError("Only existing files under app/ can be read")
    return file


@mcp.tool()
def app_architecture() -> str:
    """Describe Little List's framework, storage, API, and frontend."""
    return "Little List uses FastAPI, a server-rendered HTML shell, vanilla JavaScript, and SQLite. Todos are in TODO_DATABASE or data/little_list.db. See app/main.py and app/database.py."


@mcp.tool()
def read_source(path: str) -> str:
    """Read a real app source file, for example app/main.py."""
    return _source_file(path).read_text(encoding="utf-8")


@mcp.tool()
def search_code(query: str) -> list[str]:
    """Find a query in application source, returning path, line, and excerpt."""
    if not query.strip():
        raise ValueError("Provide a non-empty query")
    matches = []
    for file in SOURCE_ROOT.rglob("*"):
        if file.suffix not in {".py", ".js", ".html", ".css"}:
            continue
        for number, line in enumerate(file.read_text(encoding="utf-8").splitlines(), 1):
            if query.lower() in line.lower():
                matches.append(f"{file.relative_to(PROJECT_ROOT)}:{number}: {line.strip()}")
    return matches[:40]


@mcp.tool()
def explain_persistence() -> str:
    """Explain the actual SQLite-backed todo persistence semantics."""
    return "Todos are stored in SQLite, not localStorage. POST inserts title; PATCH updates completed; DELETE /api/todos/{id} deletes one; DELETE /api/todos deletes completed tasks only. All SQL uses parameters."


if __name__ == "__main__":
    mcp.run()
