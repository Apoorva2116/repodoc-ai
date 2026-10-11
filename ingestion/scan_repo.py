from pathlib import Path
from collections import Counter

REPO = Path("corpus")

EXCLUDED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
}

EXCLUDED_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".pyc",
}

INCLUDED_EXTENSIONS = {
    ".py",
    ".md",
    ".yml",
    ".yaml",
    ".json",
    ".toml",
    ".ini",
    ".sh",
    ".txt",
}

INCLUDED_FILENAMES = {
    "Dockerfile",
    "README",
    "LICENSE",
}


def should_include(path: Path) -> bool:
    if any(part in EXCLUDED_DIRS for part in path.parts):
        return False

    if path.name == ".env":
        return False

    if path.suffix.lower() in EXCLUDED_EXTENSIONS:
        return False

    if path.name in INCLUDED_FILENAMES:
        return True

    return path.suffix.lower() in INCLUDED_EXTENSIONS


files = [
    path for path in REPO.rglob("*")
    if path.is_file() and should_include(path)
]

extensions = Counter(
    path.suffix.lower() or "[no extension]"
    for path in files
)

print("=" * 60)
print("RepoDoc AI - Repository Scanner")
print("=" * 60)

print(f"\nIncluded files: {len(files)}")

print("\nFiles by type:")
for ext, count in sorted(extensions.items()):
    print(f"  {ext:15} {count}")

print("\nIncluded files:")
for path in sorted(files):
    print(f"  {path}")

print("\n" + "=" * 60)
