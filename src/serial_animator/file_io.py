import os
import tarfile
import json

import logging

_logger = logging.getLogger(__name__)


# _logger.setLevel("DEBUG")


def archive_files(files, out_path, compression="") -> str:
    """Creates a tar-archive at out_path containing specified files"""
    tf = None
    try:
        for f in files:
            if os.path.isfile(f):
                if not tf:
                    out_dir = os.path.dirname(out_path)
                    if not os.path.exists(out_dir):
                        os.makedirs(out_dir)
                    tf = tarfile.open(out_path, mode="w:{0}".format(compression))
                tf.add(f, os.path.basename(f))
    finally:
        if tf:
            tf.close()
    return out_path


def extract_file_from_archive(path, out_dir, file_name="preview.jpg") -> str:
    tar = tarfile.open(path)
    try:
        tar.extract(file_name, out_dir)
        out = os.path.normpath(os.path.join(out_dir, file_name))
    finally:
        tar.close()
    return out


def read_data_from_archive(archive_path, json_name) -> dict:
    with tarfile.open(archive_path) as tf:
        j_data = tf.extractfile(json_name)
        data = json.load(j_data)
    return data


def write_json_data(data, path, encoder=json.JSONEncoder):
    with open(path, "w") as f:
        json.dump(data, fp=f, indent=4, cls=encoder)
    _logger.debug("Wrote data to file: {}".format(path))


def write_pynode_data_to_json(data, path):
    clean_data = dict()
    for k, v in data.items():
        try:
            clean_data[k.fullPath()] = v
        except AttributeError:
            clean_data[k.name()] = v
    write_json_data(clean_data, path)


def node_dict_to_path_dict(node_dict):
    node_path_data = dict()
    for k, v in node_dict.items():
        try:
            node_path_data[k.fullPath()] = v
        except AttributeError:
            node_path_data[k.name()] = v
    return node_path_data
