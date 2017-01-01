# Stubs for bleachbit.FileUtilities (Python 2)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

from typing import Any, Optional, Union, Iterable
import six

def open_files_linux(): ...
def open_files_lsof(run_lsof: Optional[Any] = ...): ...
def open_files(): ...

class OpenFiles:
    last_scan_time = ...  # type: Any
    files = ...  # type: Any
    def __init__(self) -> None: ...
    def file_qualifies(self, filename): ...
    def scan(self): ...
    def is_open(self, filename): ...

def bytes_to_human(bytes_i: int) -> six.binary_type: ...
def children_in_directories(tops: Iterable[six.text_type], list_directories: bool = ...) -> Iterable[six.text_type]: ...
def children_in_directory(top: six.text_type, list_directories: bool = ...) -> Iterable[six.text_type]: ...
def clean_ini(path: six.text_type, section, parameter): ...
def clean_json(path: six.text_type, target): ...
def delete(path: six.text_type, shred: bool = ..., ignore_missing: bool = ..., allow_shred: bool = ...): ...
def ego_owner(filename): ...
def exists_in_path(filename): ...
def exe_exists(pathname): ...
def execute_sqlite3(path: six.text_type, cmds: six.text_type): ...
def expand_glob_join(pathname1, pathname2): ...
def expandvars(path): ...
def extended_path(path): ...
def free_space(pathname): ...
def getsize(path): ...
def getsizedir(path): ...
def globex(pathname, regex): ...
def guess_overwrite_paths(): ...
def human_to_bytes(human, hformat: Any = ...): ...
def listdir(directory): ...
def same_partition(dir1, dir2): ...
def sync(): ...
def whitelisted(path): ...
def wipe_contents(path: six.text_type, truncate: bool = ...): ...
def wipe_name(pathname1): ...
def wipe_path(pathname: six.text_type, idle: bool = ...): ...
def vacuum_sqlite3(path): ...

