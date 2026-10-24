#!/usr/bin/env python3
# Copyright 2026 Robby
# SPDX-License-Identifier: Apache-2.0
"""Fetch the exact upstream Jetty models without building the Open-RMF demos."""
from pathlib import Path
import shutil
import tarfile
import tempfile
import urllib.request

REVISION = 'b576ffc435661cdac3123f6ff91a18a22cd1278a'
ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / 'assets/jetty_models'
MARKER = DESTINATION / '.upstream-revision'


def main():
    if MARKER.is_file() and MARKER.read_text().strip() == REVISION:
        if (DESTINATION / 'Distribution_Warehouse/model.sdf').is_file():
            print('Jetty models are already available.')
            return
    if DESTINATION.exists():
        raise SystemExit(f'Existing unverified assets: {DESTINATION}. Move that directory before fetching.')
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    url = f'https://github.com/gazebosim/jetty_demo/archive/{REVISION}.tar.gz'
    with tempfile.TemporaryDirectory(prefix='tiago-jetty-') as temporary:
        temporary = Path(temporary)
        archive_path = temporary / 'jetty.tar.gz'
        print(f'Downloading official Jetty models at {REVISION[:12]}...')
        with urllib.request.urlopen(url, timeout=120) as response, archive_path.open('wb') as target:
            shutil.copyfileobj(response, target)
        models = temporary / 'models'
        models.mkdir()
        prefix = f'jetty_demo-{REVISION}/jetty_demo/models/'
        with tarfile.open(archive_path) as archive:
            for member in archive:
                if not member.name.startswith(prefix) or not member.isfile():
                    continue
                relative = Path(member.name[len(prefix):])
                target = (models / relative).resolve()
                if not target.is_relative_to(models.resolve()):
                    raise RuntimeError('Invalid upstream archive member.')
                target.parent.mkdir(parents=True, exist_ok=True)
                source = archive.extractfile(member)
                if source is None:
                    raise RuntimeError(f'Cannot read {member.name}')
                with source, target.open('wb') as destination:
                    shutil.copyfileobj(source, destination)
        if not (models / 'Distribution_Warehouse/model.sdf').is_file():
            raise RuntimeError('The upstream archive does not contain the expected warehouse model.')
        (models / '.upstream-revision').write_text(REVISION + '\n')
        shutil.move(str(models), str(DESTINATION))
    print('Jetty world models are ready.')


if __name__ == '__main__':
    main()
