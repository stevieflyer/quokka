from typing import List, Optional, Callable, Union

import pathlib
import playwright.async_api
from gembox.debug_utils import Debugger
from playwright.async_api import async_playwright, Playwright

from .browser_mgr import SingleBrowserManager
from .page_interactor import PageInteractor
from .data_extractor import DataExtractor


class Agent:
    """
    Agent is designed to be a facade class for browser manipulation. It wraps all the interactions with the browser, and
    provides a facade for `browser_mgr`, `data_extractor` and `page_interactor`.

    - `browser_mgr` is responsible for managing the browser instance. including starting, stopping and page navigation.
    - `data_extractor` is responsible for extracting data from the page.
    - `page_interactor` is responsible for interacting with the page.

    In addition, due to the power of playwright, we also expose the playwright instance and page instance used by the agent,
    so that users can extend the functionality by themselves.

    - `self.wright` is the playwright instance.
    - `self.page` is the page instance.

    Agent has a series of hooks, which can be used to customize the agent's behavior.

    - `_init_hook` is called at the end of the `__init__` function.
    - `_start_hook` is called after the agent is started, just before setting `self._is_running` to True.
    - `_stop_hook` is called after the agent is stopped, just before setting `self._is_running` to False.
    """
    def __init__(self,
                 wright: Playwright,
                 headless: bool,
                 debug_tool: Debugger):
        """
        Initialize the Agent.

        **Note: Usually, you need to instantiate an agent by Calling `Agent.instantiate()` rather than `Agent()`**

        :param wright: (Playwright) the playwright instance
        :param headless: (bool) whether the browser is headless
        :param debug_tool: (Debugger) the debugger
        """
        assert isinstance(wright, Playwright), f"wright should be a Playwright instance, but got {wright.__class__.__name__}"
        assert isinstance(debug_tool, Debugger), f"debug_tool should be a Debugger instance, but got {debug_tool.__class__.__name__}"

        self._wright = wright
        self._headless = headless
        self._debug_tool = debug_tool
        self._browser_mgr = SingleBrowserManager(wright=wright, headless=headless, debug_tool=debug_tool)
        self._page_interactor = None
        self._data_extractor = None
        self._is_running = False

        # init hook
        self._init_hook()

    @classmethod
    async def instantiate(cls, headless=True, debug_tool=None) -> 'Agent':
        """
        Instantiate an agent.

        :param headless: (bool) whether the browser is headless
        :param debug_tool: (Debugger) the debugger
        :return: (Agent) the agent instance
        """
        wright = await (async_playwright().start())
        debug_tool = Debugger() if debug_tool is None else debug_tool
        instance = cls(wright=wright, headless=headless, debug_tool=debug_tool)
        return instance

    async def start(self, viewport: dict = None, **kwargs):
        if self.is_running:
            self.debug_tool.warn(f"{self.__class__.__name__} is already running. No need to start again")
            return

        self.debug_tool.info(f"Starting {self.__class__.__name__}...")
        await self.browser_mgr.start(viewport=viewport, **kwargs)
        self._page_interactor = PageInteractor(page=self.page, debug_tool=self.debug_tool)
        self._data_extractor = DataExtractor(page=self.page, debug_tool=self.debug_tool)
        # start hook
        await self._start_hook()
        self._is_running = True
        self.debug_tool.info(f"{self.__class__.__name__} started successfully")

    async def stop(self):
        if self.is_running is False:
            self.debug_tool.warn("Agent is not running. No need to stop")
        else:
            self.debug_tool.info(f"Stopping agent...")
            await self.browser_mgr.close()
            self._page_interactor = None
            self._data_extractor = None
            # stop hook
            await self._stop_hook()
            self._is_running = False
            self.debug_tool.info(f"Agent stopped successfully")

    # page interactor related operation
    async def get_element(self, selector: str, strict: bool = False) -> playwright.async_api.ElementHandle:
        """
        Get the element according to the selector.

        If `strict` is True, then when resolving multiple elements, the function will raise Error
        """
        return await self.page_interactor.get_element(selector=selector, strict=strict)

    async def get_elements(self, selector: str) -> List[playwright.async_api.ElementHandle]:
        """
        Get the elements according to the selector.

        :param selector: (str) the selector
        :return: (List[playwright.async_api.ElementHandle]) the elements
        """
        return await self.page_interactor.get_elements(selector=selector)

    async def count(self, selector: str) -> int:
        """
        Count the number of elements according to the selector.

        :param selector: (str) the selector
        :return: (int) the number of elements
        """
        return await self.page_interactor.count(selector=selector)

    async def click(self, selector: str):
        return await self.page_interactor.click(selector=selector)

    async def click_until_element_visible(self, click_selector: str, visible_selector: str, max_retry: int = 5):
        """
        Keep clicking an element until another element becomes visible or until max retries.

        :param click_selector: Selector of the element to be clicked.
        :param visible_selector: Selector of the element that should become visible after the click.
        :param max_retry: Maximum number of click attempts.
        :return: (None)
        """
        return await self.page_interactor.click_until_element_visible(click_selector=click_selector, visible_selector=visible_selector, max_retry=max_retry)

    async def scroll_to_bottom(self, elem: Optional[playwright.async_api.ElementHandle] = None):
        await self.page_interactor.scroll_to_bottom(elem=elem)

    async def scroll_to_top(self, elem: Optional[playwright.async_api.ElementHandle] = None):
        await self.page_interactor.scroll_to_top(elem=elem)

    async def scroll_by(self, x: int, y: int, elem: Optional[playwright.async_api.ElementHandle] = None):
        await self.page_interactor.scroll_by(x=x, y=y, elem=elem)

    async def scroll_to(self, x: int, y: int, elem: Optional[playwright.async_api.ElementHandle] = None):
        await self.page_interactor.scroll_to(x=x, y=y, elem=elem)

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
        await self.page_interactor.scroll_load(scroll_step=scroll_step,
                                               load_wait=load_wait,
                                               same_th=same_th,
                                               scroll_step_callbacks=scroll_step_callbacks,
                                               elem=elem)

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
        return await self.page_interactor.scroll_load_selector(selector=selector, threshold=threshold,
                                                               scroll_step=scroll_step, load_wait=load_wait,
                                                               same_th=same_th,
                                                               scroll_step_callbacks=scroll_step_callbacks,
                                                               log_interval=log_interval,
                                                               count_check_interval=count_check_interval,
                                                               elem=elem)

    async def get_scroll_top(self, elem: playwright.async_api.ElementHandle = None) -> int:
        return await self.page_interactor.get_scroll_top(elem=elem)

    async def get_scroll_height(self, elem: playwright.async_api.ElementHandle = None) -> int:
        return await self.page_interactor.get_scroll_height(elem=elem)

    async def type_input(self, selector: str, text: str):
        return await self.page_interactor.type_input(selector=selector, text=text)

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
        return await self.page_interactor.download_html(file_path=file_path, elem=elem, encoding=encoding)

    # browser mgr related operation
    async def go(self, url: str, **kwargs):
        """
        Go to the url.

        :param url: (str) the url to go
        :param kwargs: (dict) the kwargs for `playwright.Page.goto()`
        :return: (None)
        """
        return await self.browser_mgr.go(url=url, **kwargs)

    # getters
    @property
    def wright(self):
        """the playwright instance"""
        return self._wright

    @property
    def browser_mgr(self) -> SingleBrowserManager:
        return self._browser_mgr

    @property
    def page_interactor(self) -> PageInteractor:
        return self._page_interactor

    @property
    def data_extractor(self) -> DataExtractor:
        return self._data_extractor

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def page(self) -> playwright.async_api.Page:
        return self.browser_mgr.page

    @property
    def debug_tool(self) -> Debugger:
        return self._debug_tool

    # hooks
    def _init_hook(self) -> None:
        """
        Hook function called at the end of the __init__ functions.

        When calling this hook, the agent already has `self.wright`, `self.debug_tool` and `self.browser_mgr` equipped.
        :return: (None)
        """
        pass

    async def _start_hook(self) -> None:
        """
        Hook function called after the agent is started, just before setting self._is_running to True.

        After starting the agent, the agent now have the browser instance and a blank page instance.
        :return: (None)
        """
        pass

    async def _stop_hook(self) -> None:
        """
        Hook function called after the agent is stopped, just before setting self._is_running to False.

        After stopping the agent, the agent now have no browser instance and no page instance.
        :return: (None)
        """
        pass

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()


__all__ = ['Agent']
