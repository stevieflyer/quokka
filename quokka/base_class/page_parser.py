import abc
import pathlib
import traceback

from bs4 import BeautifulSoup
from gembox.debug_utils import Debugger
from gembox.io import ensure_pathlib_path

from .exception import FailedToLoadWebpageException


class PageParser(abc.ABC):
    """
    The base class of all page parsers, built upon BeautifulSoup.

    Page Parser is responsible for reading webpages from local files, and parsing the webpages to get the information.

    After `load_webpage`, you can always access the `soup` property to get the BeautifulSoup object.
    """

    def __init__(self, debug_tool: Debugger = None, encoding="utf-8"):
        self._encoding = encoding
        self._debug_tool = debug_tool if debug_tool is not None else Debugger()
        self._file_path = None
        self._soup = None

    def load_webpage(self, file_path: (str, pathlib.Path)):
        """
        Load webpage from local file.

        :param file_path: (str, pathlib.Path) the path to the local file
        :return: (None)
        """
        self.debug_tool.info(f"[{self.__class__.__name__}] Loading webpage from {file_path}...")
        try:
            self._file_path = ensure_pathlib_path(file_path)
            self._soup = self._read_webpage_from_file(file_path=file_path)
            self.debug_tool.info(f"[{self.__class__.__name__}] Loaded webpage from {file_path} successfully")
        except Exception as e:
            self._soup = None
            self._file_path = None
            self.debug_tool.error(f"[{self.__class__.__name__}] Failed to load webpage from {file_path}, error: {str(e)}")
            self.debug_tool.error(f"Traceback: {traceback.format_exc()}")
            raise FailedToLoadWebpageException(f"Failed to load webpage from {file_path}")

    def _read_webpage_from_file(self, file_path: (str, pathlib.Path)) -> BeautifulSoup:
        self.debug_tool.info(f"[{self.__class__.__name__}] Reading webpage from {file_path}...")
        with open(file_path, "r", encoding=self._encoding) as file:
            content = file.read()
        self.debug_tool.info(f"[{self.__class__.__name__}] Transforming {file_path} to BeautifulSoup...")
        return BeautifulSoup(content, 'lxml')

    @property
    def debug_tool(self) -> Debugger:
        return self._debug_tool

    @property
    def encoding(self) -> str:
        return self._encoding

    @property
    def file_path(self) -> pathlib.Path:
        return self._file_path

    @property
    def soup(self) -> BeautifulSoup:
        return self._soup
