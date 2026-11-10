# Directory Tree Generator
# ------------------------
# Author : Duong Tran Quang (refactor)
# GitHub : https://gist.github.com/DTDucas/23ce1c8dbe34bc47e6c64f87ed8e9f5c

# This script generates a visual representation of the directory structure,
# excluding common environment and build folders. Output is saved to a .md file.

import os
import sys
from pathlib import Path


class DirectoryTreeGenerator:
    def __init__(self, root_dir="../docs", output_file="directory_structure.md"):
        self.root_dir = Path(root_dir)
        self.output_file = Path(output_file)
        # Prefijos de dibujo del árbol
        self.pipe = "│   "
        self.blank = "    "
        self.branch = "├── "
        self.last = "└── "
        self.ignore_dirs = {
            ".dev-notes",
            ".git",
            ".hypothesis",
            ".idea",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            ".venv",
            ".vscode",
            "__pycache__",
            "build",
            "dist",
            "env",
            "htmlcov",
            "node_modules",
            "venv",
        }

    # ------------------------------------------------------------------ API
    def generate_tree(self) -> str:
        """Genera el árbol, lo escribe en disco y lo devuelve como string."""
        lines = [f"{self.root_dir.name}/"]
        self._walk(self.root_dir, [], lines)

        body = "\n".join(lines)
        content = f"# Directory Structure\n```\n{body}\n```"

        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        self.output_file.write_text(content, encoding="utf-8")
        print(content)
        return content

    # -------------------------------------------------------------- internals
    def _walk(self, directory: Path, prefix: list[str], lines: list[str]) -> None:
        """Recorre `directory` añadiendo líneas a `lines` con el prefijo dado."""
        entries = self._sorted_entries(directory)
        for index, entry in enumerate(entries):
            is_last = index == len(entries) - 1
            connector = self.last if is_last else self.branch
            suffix = "/" if entry.is_dir() else ""

            lines.append(f"{''.join(prefix)}{connector}{entry.name}{suffix}")

            if entry.is_dir():
                # El hijo hereda '│   ' si hay hermanos después, o '    ' si es el último.
                # Nota: NO se agrega ninguna línea aquí; los hijos se escriben directamente.
                next_prefix = prefix + [self.blank if is_last else self.pipe]
                self._walk(entry, next_prefix, lines)

    def _sorted_entries(self, directory: Path) -> list[Path]:
        """Directorios primero (alfabético), luego archivos (alfabético)."""
        entries = [e for e in directory.iterdir() if e.name not in self.ignore_dirs]
        entries.sort(key=lambda p: (not p.is_dir(), p.name.lower()))
        return entries


def main() -> None:
    try:
        target_arg = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
        target_path = Path(target_arg).resolve()

        if not target_path.exists():
            print(f"Error: El directorio '{target_arg}' no existe.")
            return
        if not target_path.is_dir():
            print(f"Error: '{target_arg}' no es un directorio.")
            return

        docs_dir = target_path / "docs"
        docs_dir.mkdir(parents=True, exist_ok=True)
        output_path = docs_dir / "directory_structure.md"

        generator = DirectoryTreeGenerator(
            root_dir=target_path, output_file=output_path
        )
        generator.generate_tree()
        print(f"\nDirectory structure has been saved to '{output_path}'")
    except Exception as exc:
        print(f"An error occurred: {exc!s}")


if __name__ == "__main__":
    main()
