import abc
import playwright.async_api
from gembox.debug_utils import Debugger


class Handler(abc.ABC):
    def __init__(self, page: playwright.async_api.Page, debug_tool: Debugger):
        """
        Initialize the Handler.

        :param page: (playwright.async_api.Page) the page
        :param debug_tool: (Debugger) the debug tool
        """
        self._page = page
        self._debug_tool = debug_tool

    @property
    def page(self) -> playwright.async_api.Page:
        return self._page

    @property
    def debug_tool(self) -> Debugger:
        return self._debug_tool


__all__ = ['Handler']
