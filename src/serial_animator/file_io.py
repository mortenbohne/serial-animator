import os
from typing import List
from pathlib import Path
import tarfile
import json

import logging

_logger = logging.getLogger(__name__)

_logger.setLevel("DEBUG")


def archive_files(files: List[Path], out_path: Path, compression="") -> Path:
    """Creates a tar-archive at out_path containing specified files"""
    tf = None
    try:
        for f in files:
            if f.is_file():
                if not tf:
                    out_dir = out_path.parent
                    out_dir.mkdir(parents=True, exist_ok=True)
                    tf = tarfile.open(out_path, mode="w:{0}".format(compression))
                tf.add(f, f.name)
    finally:
        if tf:
            tf.close()
    return out_path


def extract_file_from_archive(
        archive: Path, out_dir: Path, file_name="preview.jpg"
) -> Path:
    tar = tarfile.open(str(archive))
    try:
        tar.extract(file_name, str(out_dir))
        out = out_dir / file_name
    finally:
        tar.close()
    return out


def read_data_from_archive(archive_path: Path, json_name: str) -> dict:
    with tarfile.open(str(archive_path)) as tf:
        j_data = tf.extractfile(json_name)
        data = json.load(j_data)
    return data


def write_json_data(data: dict, path: Path, encoder=json.JSONEncoder):
    with open(path, "w") as f:
        json.dump(data, fp=f, indent=4, cls=encoder)
    _logger.debug("Wrote data to file: {}".format(path))
