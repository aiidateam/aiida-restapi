#!/usr/bin/env python
"""Download benchmark archives and initialise an AiiDA profile with them.

Usage:
    python benchmarks/setup_benchmarks.py

Reads URLs from benchmarks/config.json, downloads each .aiida archive,
and creates an AiiDA profile backed by the archive via ``core.sqlite_zip``.

The profile name defaults to ``benchmark-restapi`` (configurable in config.json).
"""

import json
import sys
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / 'config.json'


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        sys.exit(f'Config not found: {CONFIG_PATH}')
    with open(CONFIG_PATH) as fh:
        return json.load(fh)


def download(url: str, dest: Path) -> Path:
    """Download *url* to *dest* if not already present. Returns *dest*."""
    if dest.exists():
        print(f'  [cached] {dest.name}')
        return dest
    print(f'  Downloading {url} ...')
    dest.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, dest)
    print(f'  Saved to {dest}')
    return dest


def _filename_from_url(url: str) -> str:
    """Extract a clean filename from a URL, stripping query parameters."""
    path = urlparse(url).path
    return path.rsplit('/', 1)[-1]


def main() -> None:
    from aiida import load_profile
    from aiida.manage.configuration import create_profile, get_config

    cfg = load_config()
    profile_name = cfg['profile_name']
    archive_urls: list[str] = cfg['archive_urls']
    downloads_dir = SCRIPT_DIR / cfg.get('downloads_dir', '.cache/archives')

    # -- download archives ---------------------------------------------------
    print('==> Downloading archives ...')
    archive_paths: list[Path] = []
    for url in archive_urls:
        archive_paths.append(download(url, downloads_dir / _filename_from_url(url)))
    print()

    if len(archive_paths) > 1:
        sys.exit('Multiple archives not supported for sqlite_zip storage (one zip = one profile).')

    archive_path = archive_paths[0]

    # -- create profile backed by the archive --------------------------------
    config = get_config()

    print(f'==> Creating profile "{profile_name}" backed by {archive_path.name} ...')
    create_profile(
        config,
        name=profile_name,
        email='benchmark@localhost',
        first_name='Benchmark',
        last_name='User',
        institution='Benchmark',
        storage_backend='core.sqlite_zip',
        storage_config={'filepath': str(archive_path)},
    )
    print()

    # -- verify --------------------------------------------------------------
    load_profile(profile_name)

    from aiida.orm import Node, QueryBuilder

    qb = QueryBuilder()
    qb.append(Node)
    total_nodes = qb.count()
    print(f'Done.  Profile "{profile_name}" ready with {total_nodes} nodes.')
    print('Run benchmarks with:  pytest benchmarks/ --benchmark-enable')


if __name__ == '__main__':
    main()
