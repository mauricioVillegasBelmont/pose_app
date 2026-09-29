# Directory Tree Generator
# ------------------------
# Author : Duong Tran Quang
# GitHub : https://gist.github.com/DTDucas/23ce1c8dbe34bc47e6c64f87ed8e9f5c

# This script generates a visual representation of the directory structure,
# excluding common environment and build folders. Output is saved to 'directory_structure.txt'.

import os
from pathlib import Path


class DirectoryTreeGenerator:
    def __init__(self, root_dir=".", output_file="directory_structure.txt"):
        self.root_dir = Path(root_dir)
        self.output_file = output_file
        self.indent_prefix = "│   "
        self.branch_prefix = "├── "
        self.last_prefix = "└── "
        self.ignore_dirs = {
            ".git",
            ".vscode",
            "__pycache__",
            "node_modules",
            "dist",
            "build",
            ".venv",
            "env",
            "venv",
            ".idea",
        }

    def generate_tree(self):
        tree_content = [f"{self.root_dir.name}/\n│"]
        self._generate_tree_recursive(self.root_dir, [], tree_content)
        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(tree_content))
        print("\n".join(tree_content))

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
        current_dir = os.getcwd()
        tree_generator = DirectoryTreeGenerator(current_dir)
        tree_generator.generate_tree()
        print(f"\nDirectory structure has been saved to 'directory_structure.txt'")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()