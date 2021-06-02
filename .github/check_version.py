# -*- coding: utf-8 -*-
"""Check that version numbers match.

Check version number in setup.json and aiida_restapi/__init__.py and make sure
they match.
"""
import json
import re
import sys
from pathlib import Path
from typing import Optional

VERSION_RE = re.compile(r"__version__\s*=\s*['\"]([0-9a-z\.]+)['\"]")


def test_version(
    setup_json: Path, python_init: Path, git_tag: Optional[str] = None
) -> None:
    """Test that the version specified in setup.json and __init__.py are in-sync."""
    # get setup version
    setup_version = json.loads(setup_json.read_text())["version"]
    # get init version
    python_content = python_init.read_text()
    match = VERSION_RE.search(python_content, re.MULTILINE)
    if not match:
        print(f"Could not find version in: {python_init}")
        sys.exit(1)
    python_version = match.group(1)
    if setup_version != python_version:
        print("Version number mismatch detected:")
        print(f"  Version number in '{setup_json}': {setup_version}")
        print(f"  Version number in '{python_init}': {python_version}")
        sys.exit(1)
    if git_tag is not None and python_version != git_tag[1:]:  # strip the leading 'v'
        print("Version number mismatch detected:")
        print(f"  Version number in '{python_init}': {python_version}")
        print(f"  Version number in git tag: {git_tag[1:]}")
        sys.exit(1)


if __name__ == "__main__":
    _git_tag = None
    try:
        _git_tag = sys.argv[3]
    except IndexError:
        pass
    test_version(Path(sys.argv[1]), Path(sys.argv[2]), _git_tag)
