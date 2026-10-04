"""Check RST syntax and local file links; external URLs need no network."""

import argparse
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

from docutils import nodes
from docutils.core import publish_doctree


def check_link(document, target):
    url = urlsplit(target)
    if url.scheme or url.netloc or not url.path:
        return
    path = document.parent / unquote(url.path)
    if not path.exists():
        raise ValueError(f"{document}: missing local target {target}")


def check_document(path):
    source = path.read_text()
    if path.suffix == ".rst":
        document = publish_doctree(source, source_path=str(path), settings_overrides={"halt_level": 2})
        for node in document.findall(nodes.reference):
            if "refuri" in node:
                check_link(path, node["refuri"])
        for node in document.findall(nodes.image):
            check_link(path, node["uri"])
    else:
        # Policy files use inline Markdown links; ignore fenced examples.
        source = re.sub(r"```.*?```", "", source, flags=re.DOTALL)
        for target in re.findall(r"\]\((<[^>]+>|[^\s)]+)(?:\s+\"[^\"]*\")?\)", source):
            check_link(path, target.strip("<>"))
    print(f"Documentation verified: {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    paths = args.paths or sorted([*root.glob("*.md"), *root.glob("docs/*.rst"),
                                 *root.glob("docs/*.md"), *root.glob(".github/**/*.md")])
    for path in paths:
        check_document(path)


if __name__ == "__main__":
    main()
