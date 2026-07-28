"""Enforce English-only public prose and New Zealand spelling in Markdown."""

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
    "outros",
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
    "arquivo",
    "arquivos",
    "fase de grupos",
    "qual seleção",
    "quem chega",
    "mais provável",
    "maximiza",
    "dados",
    "resultado",
    "resultados",
    "probabilidade",
    "probabilidades",
    "grupo",
    "grupos",
    "gerado",
    "gerada",
    "gerar",
    "aposta",
    "apostas",
    "correto",
    "incorreto",
    "salvos",
]

PORTUGUESE_PATTERN = re.compile(
    r"(?:" + "|".join(re.escape(term) for term in PORTUGUESE_TERMS) + r")",
    flags=re.IGNORECASE,
)

# These replacements are checked only in Markdown prose. Code blocks, inline
# identifiers, and link targets are stripped before scanning so historical paths
# and stable APIs can retain their original spelling.
US_TO_NZ = {
    "optimization": "optimisation",
    "optimizer": "optimiser",
    "optimized": "optimised",
    "optimize": "optimise",
    "maximization": "maximisation",
    "maximized": "maximised",
    "maximizing": "maximising",
    "maximize": "maximise",
    "modeling": "modelling",
    "behavior": "behaviour",
    "artifact": "artefact",
    "artifacts": "artefacts",
    "analyzed": "analysed",
    "analyzing": "analysing",
    "analyze": "analyse",
    "normalized": "normalised",
    "normalization": "normalisation",
    "normalize": "normalise",
    "realized": "realised",
    "favor": "favour",
    "favored": "favoured",
    "favorable": "favourable",
    "labeled": "labelled",
}

US_PATTERN = re.compile(
    r"\b(?:" + "|".join(re.escape(term) for term in US_TO_NZ) + r")\b",
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


def markdown_prose_lines(text: str):
    """Yield Markdown lines with code and link targets removed."""
    in_fence = False
    for line_number, line in enumerate(text.splitlines(), start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        prose = re.sub(r"`[^`]*`", "", line)
        prose = re.sub(r"\]\([^)]*\)", "]", prose)
        yield line_number, prose


def main() -> int:
    findings: list[tuple[Path, int, str, str, str]] = []

    for path in iter_text_files(PROJECT_ROOT):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for line_number, line in enumerate(text.splitlines(), start=1):
            for match in PORTUGUESE_PATTERN.finditer(line):
                findings.append(
                    (
                        path.relative_to(PROJECT_ROOT),
                        line_number,
                        match.group(0),
                        "translate Portuguese prose",
                        line.strip(),
                    )
                )

        if path.suffix.lower() == ".md":
            for line_number, prose in markdown_prose_lines(text):
                for match in US_PATTERN.finditer(prose):
                    replacement = US_TO_NZ[match.group(0).lower()]
                    findings.append(
                        (
                            path.relative_to(PROJECT_ROOT),
                            line_number,
                            match.group(0),
                            f"use New Zealand spelling: {replacement}",
                            prose.strip(),
                        )
                    )

    if findings:
        print("Public-language audit failed:\n")
        for path, line_number, term, action, line in findings:
            print(f"- {path}:{line_number}: {term!r}; {action} -> {line}")
        return 1

    print(
        "Public-language audit passed: no targeted Portuguese prose or "
        "US spellings were found in public Markdown."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
