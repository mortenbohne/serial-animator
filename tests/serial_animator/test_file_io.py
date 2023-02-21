import pytest

import serial_animator.file_io


@pytest.fixture()
def tmp_archive_with_preview(tmp_path, get_test_data_preview):
    out_path = tmp_path / "tmp_archive.tar"
    serial_animator.file_io.archive_files(
        files=[get_test_data_preview], out_path=out_path
    )
    yield out_path


def test_archive_files(tmp_archive_with_preview):
    assert tmp_archive_with_preview.is_file()


def test_extract_file_from_archive(tmp_archive_with_preview, tmp_path):
    file_name = "preview.jpg"
    out_path = serial_animator.file_io.extract_file_from_archive(
        tmp_archive_with_preview, out_dir=tmp_path, file_name=file_name
    )
    assert out_path.is_file()
