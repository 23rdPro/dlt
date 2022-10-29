import os
import tempfile
import shutil
import pathvalidate
from typing import IO, Any, List

from dlt.common.utils import encoding_for_mode


class FileStorage:
    def __init__(self,
                 storage_path: str,
                 file_type: str = "t",
                 makedirs: bool = False) -> None:
        # make it absolute path
        self.storage_path = os.path.join(os.path.realpath(storage_path), '')
        self.file_type = file_type
        if makedirs:
            os.makedirs(storage_path, exist_ok=True)

    def save(self, relative_path: str, data: Any) -> str:
        return self.save_atomic(self.storage_path, relative_path, data, file_type=self.file_type)

    @staticmethod
    def save_atomic(storage_path: str, relative_path: str, data: Any, file_type: str = "t") -> str:
        mode = "w" + file_type
        with tempfile.NamedTemporaryFile(dir=storage_path, mode=mode, delete=False, encoding=encoding_for_mode(mode)) as f:
            tmp_path = f.name
            f.write(data)
        try:
            dest_path = os.path.join(storage_path, relative_path)
            # os.rename reverts to os.replace on posix. on windows this operation is not atomic!
            os.replace(tmp_path, dest_path)
            return dest_path
        except Exception:
            if os.path.isfile(tmp_path):
                os.remove(tmp_path)
            raise

    def load(self, relative_path: str) -> Any:
        # raises on file not existing
        with self.open_file(relative_path) as text_file:
            return text_file.read()

    def delete(self, relative_path: str) -> None:
        file_path = self.make_full_path(relative_path)
        if os.path.isfile(file_path):
            os.remove(file_path)
        else:
            raise FileNotFoundError(file_path)

    def delete_folder(self, relative_path: str, recursively: bool = False) -> None:
        folder_path = self.make_full_path(relative_path)
        if os.path.isdir(folder_path):
            if recursively:
                shutil.rmtree(folder_path)
            else:
                os.rmdir(folder_path)
        else:
            raise NotADirectoryError(folder_path)

    def open_file(self, realtive_path: str, mode: str = "r") -> IO[Any]:
        mode = mode + self.file_type
        return open(self.make_full_path(realtive_path), mode, encoding=encoding_for_mode(mode))

    def open_temp(self, delete: bool = False, mode: str = "w", file_type: str = None) -> IO[Any]:
        mode = mode + file_type or self.file_type
        return tempfile.NamedTemporaryFile(dir=self.storage_path, mode=mode, delete=delete, encoding=encoding_for_mode(mode))

    def has_file(self, relative_path: str) -> bool:
        return os.path.isfile(self.make_full_path(relative_path))

    def has_folder(self, relative_path: str) -> bool:
        return os.path.isdir(self.make_full_path(relative_path))

    def list_folder_files(self, relative_path: str, to_root: bool = True) -> List[str]:
        """List all files in ``relative_path`` folder

        Args:
            relative_path (str): A path to folder, relative to storage root
            to_root (bool, optional): If True returns paths to files in relation to root, if False, returns just file names. Defaults to True.

        Returns:
            List[str]: A list of file names with optional path as per ``to_root`` parameter
        """
        scan_path = self.make_full_path(relative_path)
        if to_root:
            # list files in relative path, returning paths relative to storage root
            return [os.path.join(relative_path, e.name) for e in os.scandir(scan_path) if e.is_file()]
        else:
            # or to the folder
            return [e.name for e in os.scandir(scan_path) if e.is_file()]

    def list_folder_dirs(self, relative_path: str, to_root: bool = True) -> List[str]:
        # list content of relative path, returning paths relative to storage root
        scan_path = self.make_full_path(relative_path)
        if to_root:
            # list folders in relative path, returning paths relative to storage root
            return [os.path.join(relative_path, e.name) for e in os.scandir(scan_path) if e.is_dir()]
        else:
            # or to the folder
            return [e.name for e in os.scandir(scan_path) if e.is_dir()]

    def create_folder(self, relative_path: str, exists_ok: bool = False) -> None:
        os.makedirs(self.make_full_path(relative_path), exist_ok=exists_ok)

    def link_hard(self, from_relative_path: str, to_relative_path: str) -> None:
        # note: some interesting stuff on links https://lightrun.com/answers/conan-io-conan-research-investigate-symlinks-and-hard-links
        os.link(
            self.make_full_path(from_relative_path),
            self.make_full_path(to_relative_path)
        )

    def atomic_rename(self, from_relative_path: str, to_relative_path: str) -> None:
        os.rename(
            self.make_full_path(from_relative_path),
            self.make_full_path(to_relative_path)
        )

    def in_storage(self, path: str) -> bool:
        file = os.path.realpath(path)
        # return true, if the common prefix of both is equal to directory
        # e.g. /a/b/c/d.rst and directory is /a/b, the common prefix is /a/b
        return os.path.commonprefix([file, self.storage_path]) == self.storage_path

    def to_relative_path(self, path: str) -> str:
        if not self.in_storage(path):
            raise ValueError(path)
        return os.path.relpath(path, start=self.storage_path)

    def make_full_path(self, path: str) -> str:
        # try to make a relative path if paths are absolute or overlapping
        try:
            path = self.to_relative_path(path)
        except ValueError:
            # if path is absolute and cannot be made relative to the storage then cannot be made full path with storage root
            if os.path.isabs(path):
                raise ValueError(path)

        # then assume that it is a path relative to storage root
        return os.path.join(self.storage_path, path)

    @staticmethod
    def get_file_name_from_file_path(file_path: str) -> str:
        return os.path.basename(file_path)

    @staticmethod
    def validate_file_name_component(name: str) -> None:
        # Universal platform bans several characters allowed in POSIX ie. | < \ or "COM1" :)
        pathvalidate.validate_filename(name, platform="Universal")
        # component cannot contain "."
        if "." in name:
            raise pathvalidate.error.InvalidCharError(reason="Component name cannot contain . (dots)")
