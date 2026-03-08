"""Generate the fine_tuning_bible.ipynb notebook — Part builder."""
import json
from pathlib import Path


def md(source: str) -> dict:
    lines = source.strip().split("\n")
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": [l + "\n" for l in lines[:-1]] + [lines[-1]],
    }


def code(source: str) -> dict:
    lines = source.strip().split("\n")
    return {
        "cell_type": "code",
        "metadata": {},
        "source": [l + "\n" for l in lines[:-1]] + [lines[-1]],
        "execution_count": None,
        "outputs": [],
    }


def build_cells() -> list[dict]:
    cells = []
    # Load cell sources from part files (sorted to include 04b, 04c, etc.)
    parts_dir = Path("_nb_parts")
    part_files = sorted(parts_dir.glob("section_*.py"))
    for part_file in part_files:
        print(f"  Loading {part_file.name}...")
        exec(part_file.read_text(), {"cells": cells, "md": md, "code": code})
    return cells


def main():
    cells = build_cells()

    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.11.0",
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "pygments_lexer": "ipython3",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }

    out = Path("fine_tuning_bible.ipynb")
    out.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Written {len(cells)} cells to {out}")


if __name__ == "__main__":
    main()
