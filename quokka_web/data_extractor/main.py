import playwright.async_api
from gembox.debug_utils import Debugger

from .utils import *


class DataExtractor:
    def __init__(self, page: playwright.async_api.Page, debug_tool: Debugger):
        assert isinstance(page, playwright.async_api.Page), f"page is not a playwright.async_api.Page, but {type(page)}"
        assert isinstance(debug_tool, Debugger), f"debug_tool is not a Debugger, but {type(debug_tool)}"
        self._page = page
        self._debug_tool = debug_tool

    async def get_attr(self, selector: str, attr: str, strict: bool = False) -> str:
        element = await self._page.query_selector(selector=selector, strict=strict)
        return await get_elem_attr(elem=element, attr=attr)

    async def get_attrs(self, selector, attr: str) -> List[str]:
        elements = await self._page.query_selector_all(selector=selector)
        return [await element.get_attribute(attr) for element in elements]

    async def get_class_list(self, selector, strict: bool = False):
        element = await self._page.query_selector(selector=selector, strict=strict)
        return await get_elem_class_list(elem=element)

    @property
    def page(self) -> playwright.async_api.Page:
        return self._page

    @property
    def debug_tool(self) -> Debugger:
        return self._debug_tool
