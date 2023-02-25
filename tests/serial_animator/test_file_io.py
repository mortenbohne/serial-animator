from pathlib import Path
import pytest
import serial_animator.file_io
import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


def test_archive_files(tmp_archive, tmp_path, json_file):
    assert tmp_archive.is_file()
    out_path = tmp_path / "non_existent_dir" / "tmp_archive.tar"
    assert (
            serial_animator.file_io.archive_files(files=[json_file], out_path=out_path)
            == out_path
    )


def test_extract_file_from_archive(tmp_archive, tmp_path):
    file_name = "preview.jpg"
    out_path = serial_animator.file_io.extract_file_from_archive(
        archive=tmp_archive, out_dir=tmp_path, file_name=file_name
    )
    assert isinstance(out_path, Path)
    assert out_path.is_file()


def test_write_json_data(tmp_path):
    out_json = tmp_path / "test_json.json"
    data = {"Hello": 1, "Dolly": 2, "This is": "Louis"}
    serial_animator.file_io.write_json_data(data=data, path=out_json)
    assert out_json.is_file()


def test_read_data_from_archive(tmp_archive, cube_keyable_data):
    data = serial_animator.file_io.read_data_from_archive(tmp_archive, "test.json")
    assert isinstance(data, dict)
    assert data == cube_keyable_data


@pytest.fixture()
def json_file(tmp_path, cube_keyable_data):
    path = tmp_path / "test.json"
    serial_animator.file_io.write_json_data(data=cube_keyable_data, path=path)
    return path


@pytest.fixture()
def tmp_archive(tmp_path, json_file, data_preview):
    out_path = tmp_path / "tmp_archive.tar"
    serial_animator.file_io.archive_files(
        files=[data_preview, json_file], out_path=out_path
    )
    yield out_path
