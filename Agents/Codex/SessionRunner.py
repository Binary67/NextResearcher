from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from .Agent import CodexAgent, CodexTurnResult

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROMPTS_DIR = PROJECT_ROOT / "Prompts"


@dataclass(frozen=True)
class CodexSessionRunResult:
    turn_result: CodexTurnResult
    session_log_path: Path | None


def _load_instructions(role: str | None) -> str:
    """Load base and optional role instructions from Prompts/ directory."""
    parts = []

    base_path = PROMPTS_DIR / "base.md"
    if base_path.exists():
        base = base_path.read_text(encoding="utf-8").strip()
        if base:
            parts.append(base)

    if role:
        role_path = PROMPTS_DIR / f"{role}.md"
        if role_path.exists():
            role_text = role_path.read_text(encoding="utf-8").strip()
            if role_text:
                parts.append(role_text)

    return "\n\n".join(parts)


def _build_session_environment(environment: Mapping[str, str] | None) -> dict[str, str]:
    session_environment = dict(os.environ)
    active_virtual_env = session_environment.get("VIRTUAL_ENV", "")

    if active_virtual_env:
        active_virtual_env_path = Path(active_virtual_env).resolve()
        filtered_path_entries: list[str] = []
        for raw_entry in session_environment.get("PATH", "").split(os.pathsep):
            if not raw_entry:
                continue
            try:
                entry_path = Path(raw_entry).resolve()
            except OSError:
                filtered_path_entries.append(raw_entry)
                continue

            try:
                is_inside_active_env = entry_path.is_relative_to(active_virtual_env_path)
            except AttributeError:
                is_inside_active_env = str(entry_path).startswith(str(active_virtual_env_path))

            if not is_inside_active_env:
                filtered_path_entries.append(raw_entry)

        session_environment["PATH"] = os.pathsep.join(filtered_path_entries)

    if environment:
        session_environment.update(environment)

    for key in ("VIRTUAL_ENV", "PYTHONHOME", "__PYVENV_LAUNCHER__"):
        session_environment.pop(key, None)

    return session_environment


def run_codex_session(
    cwd: Path,
    instruction: str,
    *,
    role: str | None = None,
    codex_executable: str | None = None,
    logs_root: Path | str | None = None,
    environment: Mapping[str, str] | None = None,
    dynamic_tools: list[dict[str, Any]] | None = None,
    tool_handler: Callable[[str, Any], dict[str, Any]] | None = None,
) -> CodexSessionRunResult:
    preamble = _load_instructions(role)
    full_instruction = f"{preamble}\n\n{instruction}" if preamble else instruction
    session_environment = _build_session_environment(environment)

    agent = CodexAgent(
        codex_executable=codex_executable,
        logs_root=logs_root,
        environment=session_environment,
        tool_handler=tool_handler,
    )
    try:
        agent.start_session(str(cwd), dynamic_tools=dynamic_tools)
        turn_result = agent.run_instruction(full_instruction)
        session_log_path = agent.session_log_path
        agent.end_session()
    finally:
        agent.close()

    return CodexSessionRunResult(turn_result=turn_result, session_log_path=session_log_path)
