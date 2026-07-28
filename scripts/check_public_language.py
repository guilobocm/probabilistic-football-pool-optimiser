"""Fail when Portuguese prose appears in public, human-readable repository files."""

from __future__ import annotations

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

TEXT_EXTENSIONS = {
    ".csv",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

EXCLUDED_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
}

EXCLUDED_FILES = {Path(__file__).resolve()}

# Target Portuguese prose rather than personal names or legitimate local aliases.
PORTUGUESE_TERMS = [
    "bolão",
    "bónus",
    "bônus",
    "palpite",
    "palpites",
    "pontuação",
    "pontos esperados",
    "tendência",
    "placar",
    "jogo",
    "jogos",
    "seleção",
    "seleções",
    "equipa",
    "equipas",
    "golo",
    "golos",
    "campeão",
    "artilheiro",
    "empate",
    "vitória",
    "derrota",
    "semifinalistas",
    "alternativas",
    "carregando",
    "salvando",
    "buscando odds",
    "otimizando",
    "concluído",
    "executando testes",
    "não encontrado",
    "não existe",
    "ingestão pulada",
    "erro ao",
    "falha ao",
    "registos de odds",
    "ficheiro",
    "fase de grupos",
    "qual seleção",
    "quem chega",
    "mais provável",
    "maximiza",
]

PATTERN = re.compile(
    r"(?:" + "|".join(re.escape(term) for term in PORTUGUESE_TERMS) + r")",
    flags=re.IGNORECASE,
)


def iter_text_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        if path.resolve() in EXCLUDED_FILES:
            continue
        if any(part in EXCLUDED_DIRECTORIES for part in path.parts):
            continue
        yield path


def main() -> int:
    findings: list[tuple[Path, int, str, str]] = []

    for path in iter_text_files(PROJECT_ROOT):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in PATTERN.finditer(line):
                findings.append(
                    (
                        path.relative_to(PROJECT_ROOT),
                        line_number,
                        match.group(0),
                        line.strip(),
                    )
                )

    if findings:
        print("Public-language audit failed. Portuguese prose was found:\n")
        for path, line_number, term, line in findings:
            print(f"- {path}:{line_number}: {term!r} -> {line}")
        return 1

    print("Public-language audit passed: no targeted Portuguese prose was found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
