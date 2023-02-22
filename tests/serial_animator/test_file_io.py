import pytest
import serial_animator.file_io
import logging

_logger = logging.getLogger(__name__)
_logger.setLevel(logging.DEBUG)


@pytest.fixture()
def tmp_archive(tmp_path, test_json, test_data_preview):
    out_path = tmp_path / "tmp_archive.tar"
    serial_animator.file_io.archive_files(
        files=[test_data_preview, test_json], out_path=out_path
    )
    yield out_path


def test_archive_files(tmp_archive):
    assert tmp_archive.is_file()


def test_extract_file_from_archive(tmp_archive, tmp_path):
    file_name = "preview.jpg"
    out_path = serial_animator.file_io.extract_file_from_archive(
        tmp_archive, out_dir=tmp_path, file_name=file_name
    )
    assert out_path.is_file()


def test_write_json_data(tmp_path):
    out_json = tmp_path / "test_json.json"
    data = {"Hello": 1, "Dolly": 2, "This is": "Louis"}
    serial_animator.file_io.write_json_data(data=data, path=out_json)
    assert out_json.is_file()


@pytest.fixture()
def test_json(tmp_path, get_test_data):
    path = tmp_path / "test.json"
    serial_animator.file_io.write_json_data(data=get_test_data, path=path)
    return path


def test_read_data_from_archive(tmp_archive, get_test_data):
    data = serial_animator.file_io.read_data_from_archive(tmp_archive, "test.json")
    assert data == get_test_data
