"""Writes the app's interactive tutorials from the documentation (MD/INTERACTIVE_TUTORIALS_DESIGN.md).

    python tools/make_tutorials.py

Reads the tutorial blocks of every page in the docs/src/index.md table of contents and writes
EasyReflectometryApp/Tutorials/index.json (the tutorial ids in display order) and one
<id>.json per tutorial, and copies the data files they load from examples/datasets to
EasyReflectometryApp/Tutorials/data. The output is committed; tests/test_tutorials.py fails when it is
out of date with the Markdown.
"""

import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tutorial_steps import parse_page  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / 'docs' / 'src'
DATASETS_DIR = ROOT / 'examples' / 'datasets'
OUTPUT_DIR = ROOT / 'EasyReflectometryApp' / 'Tutorials'
DATA_DIR = OUTPUT_DIR / 'data'
FORMAT = 1


def documentation_pages(docs_dir: Path = DOCS_DIR) -> list[str]:
    """The pages of the table of contents, in order, without the '.md' suffix."""
    index = (docs_dir / 'index.md').read_text(encoding='utf-8')
    return re.findall(r'^\s*([\w/.-]+)\.md\s*$', index, flags=re.MULTILINE)


def build(docs_dir: Path = DOCS_DIR) -> dict[str, object]:
    """File name -> content of every file the generator writes."""
    files = {}
    ids = []
    for doc_name in documentation_pages(docs_dir):
        source = docs_dir / f'{doc_name}.md'
        tutorial = parse_page(source.read_text(encoding='utf-8'), doc_name, source=str(source))
        if tutorial is None:
            continue
        if tutorial['id'] in ids:
            raise ValueError(f'{source}: tutorial id "{tutorial["id"]}" is used twice')
        ids.append(tutorial['id'])
        missing = [name for name in tutorial['data'] if not (DATASETS_DIR / name).is_file()]
        if missing:
            raise ValueError(f'{source}: data files not in {DATASETS_DIR}: {", ".join(missing)}')
        files[f'{tutorial["id"]}.json'] = {'format': FORMAT, 'doc': doc_name, **tutorial}
    files['index.json'] = ids
    return files


def data_files(files: dict[str, object]) -> set[str]:
    """The data files the tutorials load, by name in examples/datasets."""
    return {name for content in files.values() if isinstance(content, dict) for name in content['data']}


def serialize(content: object) -> str:
    return json.dumps(content, indent=2, ensure_ascii=False) + '\n'


def main() -> None:
    files = build()
    OUTPUT_DIR.mkdir(exist_ok=True)
    for stale in set(path.name for path in OUTPUT_DIR.glob('*.json')) - set(files):
        (OUTPUT_DIR / stale).unlink()
    for name, content in files.items():
        (OUTPUT_DIR / name).write_text(serialize(content), encoding='utf-8')
        print(f'Wrote {OUTPUT_DIR / name}')
    needed = data_files(files)
    DATA_DIR.mkdir(exist_ok=True)
    for stale in set(path.name for path in DATA_DIR.iterdir()) - needed:
        (DATA_DIR / stale).unlink()
    for name in sorted(needed):
        shutil.copyfile(DATASETS_DIR / name, DATA_DIR / name)
        print(f'Copied {DATA_DIR / name}')


if __name__ == '__main__':
    main()
