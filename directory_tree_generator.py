# Directory Tree Generator
# ------------------------
# Author : Duong Tran Quang
# GitHub : https://gist.github.com/DTDucas/23ce1c8dbe34bc47e6c64f87ed8e9f5c

# This script generates a visual representation of the directory structure,
# excluding common environment and build folders. Output is saved to a .md file.

import os
import sys
from pathlib import Path


class DirectoryTreeGenerator:
    def __init__(self, root_dir="./docs", output_file="directory_structure.md"):
        self.root_dir = Path(root_dir)
        self.output_file = output_file
        self.indent_prefix = "│   "
        self.branch_prefix = "├── "
        self.last_prefix = "└── "
        self.ignore_dirs = {
            ".git",
            ".hypothesis",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            ".vscode",
            "__pycache__",
            "node_modules",
            "dist",
            "htmlcov",
            "build",
            ".venv",
            "env",
            "venv",
            ".idea",
        }

    def generate_tree(self):
        tree_content = [f"{self.root_dir.name}/\n│"]
        self._generate_tree_recursive(self.root_dir, [], tree_content)

        # Prefijo y sufijo para Markdown
        prefix = "# Directory Structure\n```\n"
        suffix = "\n```"

        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write(prefix + "\n".join(tree_content) + suffix)
        print(prefix + "\n".join(tree_content) + suffix)

    def _generate_tree_recursive(self, directory, prefix, output):
        entries = [e for e in directory.iterdir() if e.name not in self.ignore_dirs]
        entries.sort(key=lambda x: (not x.is_dir(), x.name))
        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            current_prefix = self.last_prefix if is_last else self.branch_prefix
            line = "".join(prefix + [current_prefix + entry.name])
            if entry.is_dir():
                line += "/"
            output.append(line)
            if entry.is_dir():
                output.append(
                    "".join(prefix + [self.indent_prefix if not is_last else "    "])
                )
                new_prefix = prefix + [self.indent_prefix if not is_last else "    "]
                self._generate_tree_recursive(entry, new_prefix, output)


def main():
    try:
        # Directorio de destino (por defecto el directorio actual)
        target_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
        target_path = Path(target_dir).resolve()

        if not target_path.exists():
            print(f"Error: El directorio '{target_dir}' no existe.")
            return

        if not target_path.is_dir():
            print(f"Error: '{target_dir}' no es un directorio.")
            return

        # Nombre base del directorio para el archivo de salida
        output_filename = f"{target_path.name}_directory_structure.md"
        output_path = target_path / output_filename

        tree_generator = DirectoryTreeGenerator(
            root_dir=target_path, output_file=str(output_path)
        )
        tree_generator.generate_tree()
        print(f"\nDirectory structure has been saved to '{output_path}'")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()
