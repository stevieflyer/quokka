import pathlib
import aiofiles
from typing import Union, List, Callable, Optional

import playwright.async_api
from gembox.debug_utils import Debugger
from gembox.io import ensure_pathlib_path, check_and_make_dir

from quokka.page_interactor.modules import CommonHandler, ScrollHandler, ClickHandler


class PageInteractor:
    def __init__(self, page, debug_tool: Optional[Debugger] = None):
        self._page: playwright.async_api.Page = page
        self._debug_tool = Debugger() if debug_tool is None else debug_tool
        self._common_handler = CommonHandler(page=self.page, debug_tool=self.debug_tool)
        self._scroll_handler = ScrollHandler(page=self.page, debug_tool=self.debug_tool)
        self._click_handler = ClickHandler(page=self.page, debug_tool=self.debug_tool)

    # common handler related operation
    async def get_element(self, selector: str, strict: bool = False) -> playwright.async_api.ElementHandle:
        """
        Get the element according to the selector.

        If `strict` is True, then when resolving multiple elements, the function will raise Error
        """
        return await self._common_handler.get_element(selector=selector, strict=strict)

    async def get_elements(self, selector: str) -> List[playwright.async_api.ElementHandle]:
        """
        Get the elements according to the selector.

        :param selector: (str) the selector
        :return: (List[playwright.async_api.ElementHandle]) the elements
        """
        return await self._common_handler.get_elements(selector=selector)

    async def count(self, selector: str) -> int:
        """
        Count the number of elements according to the selector.

        :param selector: (str) the selector
        :return: (int) the number of elements
        """
        return await self._common_handler.count(selector=selector)

    # Click related operation
    async def click(self, selector: str):
        return await self.page.click(selector=selector)

    async def click_until_element_visible(self, click_selector: str, visible_selector: str, max_retry: int = 5):
        """
        Keep clicking an element until another element becomes visible or until max retries.

        :param click_selector: Selector of the element to be clicked.
        :param visible_selector: Selector of the element that should become visible after the click.
        :param max_retry: Maximum number of click attempts.
        :return: (None)
        """
        return await self._click_handler.click_until_element_visible(click_selector=click_selector, visible_selector=visible_selector, max_retry=max_retry)

    # Scroll related operation
    async def scroll_to_bottom(self, elem: Optional[playwright.async_api.ElementHandle] = None):
        await self._scroll_handler.scroll_to_bottom(elem=elem)

    async def scroll_to_top(self, elem: Optional[playwright.async_api.ElementHandle] = None):
        await self._scroll_handler.scroll_to_top(elem=elem)

    async def scroll_by(self, x: int, y: int, elem: Optional[playwright.async_api.ElementHandle] = None):
        await self._scroll_handler.scroll_by(x=x, y=y, elem=elem)

    async def scroll_to(self, x: int, y: int, elem: Optional[playwright.async_api.ElementHandle] = None):
        await self._scroll_handler.scroll_to(x=x, y=y, elem=elem)

    async def scroll_load(self,
                          scroll_step: int = 400,
                          load_wait: int = 40,
                          same_th: int = 20,
                          scroll_step_callbacks: Optional[List[Callable]] = None,
                          elem: Optional[playwright.async_api.ElementHandle] = None) -> None:
        """
        Scroll and load all contents, until scrolling top does not change.

        :param scroll_step: (int) The number of pixels to scroll each time. If None, scroll to bottom.
        :param load_wait: (int) The time to wait after each scroll, in milliseconds. If none, the method will wait for 100 ms
        :param same_th: (int) The threshold of the number of same scroll top to stop scrolling.
        :param scroll_step_callbacks: (List[Callable]) A callback function to be called after each scroll.
        :param elem: (playwright.async_api.ElementHandler) The element to scroll. If None, scroll the whole page.
        :return:
        """
        return await self._scroll_handler.scroll_load(scroll_step=scroll_step, load_wait=load_wait, same_th=same_th,
                                                      scroll_step_callbacks=scroll_step_callbacks, elem=elem)

    async def scroll_load_selector(self,
                                   selector: str,
                                   threshold: Optional[int] = None,
                                   scroll_step: int = 400,
                                   load_wait: int = 40,
                                   same_th: int = 20,
                                   scroll_step_callbacks: List[Callable] = None,
                                   log_interval: int = 100,
                                   count_check_interval: int = 5,
                                   elem: Optional[playwright.async_api.ElementHandle] = None) -> List[playwright.async_api.ElementHandle]:
        """
        Scroll and load all contents, until no new content is loaded or enough specific items are collected.

        :param selector: (str) The selector of the element to scroll. If None, the method will just scroll to the bottom
        :param scroll_step: (int) The scroll step in pixels. If none, each scroll will be `scroll_to_bottom`
        :param load_wait: (int) The time to wait after each scroll, in milliseconds. If none, the method will wait for 100 ms
        :param same_th: (int) The threshold of the number of same scroll top to stop scrolling.
        :param threshold: (int) only valid when `selector` is not `None`, after loading `threshold` number of elements, the method will stop scrolling
        :param scroll_step_callbacks: (Callable) A callback function to be called after each scroll.
        :param log_interval: (int) The interval of logging the number of loaded elements.
        :param count_check_interval: (int) The interval of checking the number of loaded elements.
        :param elem: (ElementHandle) The element to scroll. If None, scroll the whole page.

        :return: (int) The number of elements matching the selector
        """
        return await self._scroll_handler.scroll_load_selector(selector=selector, threshold=threshold,
                                                               scroll_step=scroll_step, load_wait=load_wait,
                                                               same_th=same_th,
                                                               scroll_step_callbacks=scroll_step_callbacks,
                                                               log_interval=log_interval,
                                                               count_check_interval=count_check_interval, elem=elem)

    async def get_scroll_top(self, elem: playwright.async_api.ElementHandle = None) -> int:
        return await self._scroll_handler.get_scroll_top(elem=elem)

    async def get_scroll_height(self, elem: playwright.async_api.ElementHandle = None) -> int:
        return await self._scroll_handler.get_scroll_height(elem=elem)

    # Other operation
    async def type_input(self, selector: str, text: str):
        return await self.page.type(selector=selector, text=text)

    async def download_html(self,
                            file_path: Union[str, pathlib.Path],
                            elem: Optional[playwright.async_api.ElementHandle] = None,
                            encoding: str = "utf-8"):
        """
        Download the current web page or specific element.

        :param file_path: (str, pathlib.Path) the file path
        :param elem: (playwright.async_api.ElementHandle) the element to download
        :param encoding: (str, optional) the encoding of the file, default is utf-8
        :return: (None)
        """
        file_path = ensure_pathlib_path(file_path)
        check_and_make_dir(file_path.parent)

        elem_str = f"element {elem}" if elem is not None else "whole webpage"
        self.debug_tool.info(f"Downloading the {elem_str}, page url: {self.page.url}...")
        if elem is None:
            content = await self._page.content()
        else:
            content = await elem.inner_html()
        self.debug_tool.info(f"Pumping the content to {file_path}...")
        async with aiofiles.open(file_path, mode="w", encoding=encoding) as f:
            await f.write(content)
        self.debug_tool.info(f"Downloaded the {elem_str} successfully, page url: {self.page.url}, file_path: {file_path}")

    @property
    def page(self) -> playwright.async_api.Page:
        return self._page

    @property
    def debug_tool(self) -> Debugger:
        return self._debug_tool
