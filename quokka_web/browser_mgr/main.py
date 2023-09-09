from typing import Union

import playwright
from fake_useragent import UserAgent
from playwright.async_api import async_playwright
from gembox.debug_utils import Debugger

from .exception import NoActivePageError

ua = UserAgent()


class SingleBrowserManager:
    def __init__(self,
                 wright: playwright.async_api.Playwright,
                 headless=True,
                 debug_tool: Debugger = None) -> None:
        """
        Initialize the SingleBrowserManager.

        **Note: You should create an instance by calling `SingleBrowserManager.create()` instead of `SingleBrowserManager()`**
        """
        self._wright = wright
        self._headless: bool = headless
        self._debug_tool = debug_tool if debug_tool is not None else Debugger()
        self._is_running: bool = False
        self._browser: [playwright.async_api.Browser, None] = None
        self._context: [playwright.async_api.BrowserContext, None] = None
        self._page: [playwright.async_api.Page, None] = None

    @property
    def headless(self) -> bool:
        """whether browser is headless"""
        return self._headless

    @property
    def debug_tool(self):
        """the debugger"""
        return self._debug_tool

    @property
    def wright(self) -> playwright.async_api.Playwright:
        """the playwright instance"""
        return self._wright

    @property
    def is_running(self) -> bool:
        """whether the browser is running"""
        return self._is_running

    @property
    def browser(self) -> Union[playwright.async_api.Browser, None]:
        """the context manager"""
        return self._browser

    @property
    def context(self) -> Union[playwright.async_api.BrowserContext, None]:
        return self._context

    @property
    def page(self) -> Union[playwright.async_api.Page, None]:
        """the page"""
        return self._page

    @classmethod
    async def instantiate(cls, headless=True, debug_tool: Debugger = None) -> 'SingleBrowserManager':
        wright = await (async_playwright().start())
        instance = cls(wright=wright, headless=headless, debug_tool=debug_tool)
        return instance

    async def start(self, viewport: dict = None, **kwargs):
        """
        Start the browser.

        :param viewport: (dict) the viewport, default is {'width': 1360, 'height': 900}
        :param kwargs: (dict) the kwargs for `playwright.launch()`
        :return: (None)
        """
        self.debug_tool.info(f"[Browser Manager]: Starting browser...")
        if self.is_running is True:
            self.debug_tool.warn(f"[Browser Manager]: Browser is already running, no need to start_browser.")
            return

        if viewport is None:
            viewport = {'width': 1360, 'height': 900}
        self._browser = await self.wright.chromium.launch(headless=self.headless, **kwargs)
        self._context = await self._browser.new_context(viewport=viewport, user_agent=ua.random)  # randomize user agent
        self._page = await self._context.new_page()
        self._is_running = True
        self.debug_tool.info(f"[Browser Manager]: Browser started successfully.")

    async def close(self):
        self.debug_tool.info(f"[Browser Manager]: Closing browser...")
        if self.is_running is False:
            self.debug_tool.warn(f"Browser is not running, no need to close_browser.")
            return
        await self.browser.close()
        self._browser = None
        self._context = None
        self._page = None
        self._is_running = False
        self.debug_tool.info(f"[Browser Manager]: Browser closed successfully.")

    async def restart(self):
        await self.close()
        await self.start()

    async def go(self, url: str, **kwargs):
        """
        Go to the url.

        :param url: (str) the url to go
        :param kwargs: (dict) the kwargs for `playwright.Page.goto()`
        :return: (None)
        """
        self.debug_tool.info(f"[Browser Manager]: Go to {url}...")
        if self.page is None:
            self.debug_tool.error(f"[Browser Manager]: No active page found.")
            raise NoActivePageError
        await self.page.goto(url=url, **kwargs)
        self.debug_tool.info(f"[Browser Manager]: Go to {url} successfully")

    async def go_back(self, **kwargs):
        """
        Go back to the previous page.

        :param kwargs: (dict) the kwargs for `playwright.Page.go_back()`
        :return: (None)
        """
        self.debug_tool.info(f"[Browser Manager]: Go back...")
        if self.page is None:
            self.debug_tool.error(f"[Browser Manager]: No active page found.")
            raise NoActivePageError
        await self.page.go_back(**kwargs)
        self.debug_tool.info(f"[Browser Manager]: Go back successfully")

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
