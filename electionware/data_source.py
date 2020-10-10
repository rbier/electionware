from abc import abstractmethod
from typing import IO


class DataSource:
    """
    A lazy loading IO stream for processing PDFs
    """
    @abstractmethod
    def get_file_like_object(self) -> IO:
        raise NotImplementedError


class FileSource(DataSource):
    """
    Lazy loader of a file on disk
    """
    def __init__(self, filename: str):
        self._filename: str = filename

    def get_file_like_object(self) -> IO:
        return open(self._filename, 'rb')
