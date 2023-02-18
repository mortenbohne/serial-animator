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
                    out_dir = os.path.dirname(out_path)
                    if not os.path.exists(out_dir):
                        os.makedirs(out_dir)
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


def write_pynode_data_to_json(data: dict, path: Path):
    clean_data = dict()
    for k, v in data.items():
        try:
            clean_data[k.fullPath()] = v
        except AttributeError:
            clean_data[k.name()] = v
    write_json_data(clean_data, path)


def node_dict_to_path_dict(node_dict: dict) -> dict:
    node_path_data = dict()
    for k, v in node_dict.items():
        try:
            node_path_data[k.fullPath()] = v
        except AttributeError:
            node_path_data[k.name()] = v
    return node_path_data
