# utils/build_tree_sitter.py

from tree_sitter_languages import get_parser

LANGUAGES = [
    "python",
    "java",
    "javascript",
    "typescript",
    "c",
    "cpp",
]

for lang in LANGUAGES:
    try:
        parser = get_parser(lang)
        print(f"[OK] {lang}")
    except Exception as e:
        print(f"[FAIL] {lang}: {e}")
