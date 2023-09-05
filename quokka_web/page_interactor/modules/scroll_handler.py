import asyncio
from typing import List, Callable

import playwright.async_api
from gembox.debug_utils import Debugger

from .common_handler import CommonHandler
from .handler import Handler


class ScrollHandler(Handler):
    def __init__(self, page: playwright.async_api.Page, debug_tool: Debugger):
        super(ScrollHandler, self).__init__(page=page, debug_tool=debug_tool)
        self._common_handler = CommonHandler(page=page, debug_tool=debug_tool)

    async def scroll_to_bottom(self, elem: playwright.async_api.ElementHandle = None):
        if elem:
            await self._page.evaluate("elem => elem.scrollTop = elem.scrollHeight", elem)
        else:
            await self._page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    async def scroll_to_top(self, elem: playwright.async_api.ElementHandle = None):
        if elem:
            await self._page.evaluate("elem => elem.scrollTop = 0", elem)
        else:
            await self._page.evaluate("window.scrollTo(0, 0)")

    async def scroll_by(self, x: int, y: int, elem: playwright.async_api.ElementHandle = None):
        if elem:
            await self._page.evaluate("args => { args.elem.scrollLeft += args.x; args.elem.scrollTop += args.y; }",
                                      {"elem": elem, "x": x, "y": y})
        else:
            await self._page.evaluate("args => window.scrollBy(args.x, args.y)", {"x": x, "y": y})

    async def scroll_to(self, x: int, y: int, elem: playwright.async_api.ElementHandle = None):
        if elem:
            await self._page.evaluate("args => { args.elem.scrollLeft = args.x; args.elem.scrollTop = args.y; }",
                                      {"elem": elem, "x": x, "y": y})
        else:
            await self._page.evaluate("args => window.scrollTo(args.x, args.y)", {"x": x, "y": y})

    async def get_scroll_height(self, elem: playwright.async_api.ElementHandle = None) -> int:
        """
        Get the scroll height of the element or the whole page.

        :param elem: ElementHandle of the specific element or None for the whole page.
        :return: Scroll height.
        """
        if elem:
            return await self._page.evaluate("elem => elem.scrollHeight", elem)
        else:
            return await self._page.evaluate("document.body.scrollHeight")

    async def get_scroll_top(self, elem: playwright.async_api.ElementHandle = None) -> int:
        """
        Get the scroll position (scrollTop) of the element or the whole page.

        :param elem: ElementHandle of the specific element or None for the whole page.
        :return: Current scroll position from the top.
        """
        if elem:
            return await self._page.evaluate("elem => elem.scrollTop", elem)
        else:
            # You can also use `window.pageYOffset` which is equivalent to `window.scrollY`.
            return await self._page.evaluate("window.scrollY")

    async def scroll_load(self,
                          scroll_step: int = 400,
                          load_wait: int = 40,
                          same_th: int = 20,
                          scroll_step_callbacks: List[Callable] = None,
                          elem: playwright.async_api.ElementHandle = None) -> None:
        """
        Scroll and load all contents, until scrolling top does not change.

        :param scroll_step: (int) The number of pixels to scroll each time. If None, scroll to bottom.
        :param load_wait: (int) The time to wait after each scroll, in milliseconds. If none, the method will wait for 100 ms
        :param same_th: (int) The threshold of the number of same scroll top to stop scrolling.
        :param scroll_step_callbacks: (List[Callable]) A callback function to be called after each scroll.
        :param elem: (playwright.async_api.ElementHandler) The element to scroll. If None, scroll the whole page.
        :return:
        """
        self.debug_tool.info(f"Scrolling and loading... scroll_step: {scroll_step}, load_wait: {load_wait}, same_th: {same_th}, elem: {elem}")
        return await self._scroll_load(scroll_step=scroll_step, load_wait=load_wait, same_th=same_th, scroll_step_callbacks=scroll_step_callbacks, elem=elem)

    async def scroll_load_selector(self,
                                   selector: str,
                                   threshold: int = None,
                                   scroll_step: int = 400,
                                   load_wait: int = 40,
                                   same_th: int = 20,
                                   scroll_step_callbacks: List[Callable] = None,
                                   log_interval: int = 100,
                                   count_check_interval: int = 5,
                                   elem: playwright.async_api.ElementHandle = None) -> List[playwright.async_api.ElementHandle]:
        """
        Scroll and load all contents, until no new content is loaded or enough specific items are collected.

        :param selector: (str) The selector of the element to scroll. If None, the method will just scroll to the bottom
        :param scroll_step: (int) The scroll step in pixels. If none, each scroll will be `scroll_to_bottom`
        :param load_wait: (int) The time to wait after each scroll, in milliseconds. If none, the method will wait for 100 ms
        :param same_th: (int) The threshold of the number of same scroll top to stop scrolling.
        :param threshold: (int) only valid when `selector` is not `None`, after loading `threshold` number of elements, the method will stop scrolling
        :param scroll_step_callbacks: (Callable) A callback function to be called after each scroll.
        :param log_interval: (int) The interval of logging the number of loaded elements.
        :param count_check_interval: (int) The interval of checking the number of elements.
        :param elem: (ElementHandle) The element to scroll. If None, scroll the whole page.

        :return: (int) The number of elements matching the selector
        """
        self.debug_tool.info(f'Scrolling and loading {selector}... threshold: {threshold}, scroll_step: {scroll_step}, load_wait: {load_wait}, same_th: {same_th}, elem: {elem}')
        await self._scroll_load(selector=selector, threshold=threshold, scroll_step=scroll_step, load_wait=load_wait,
                                same_th=same_th, scroll_step_callbacks=scroll_step_callbacks, log_interval=log_interval,
                                elem=elem, count_check_interval=count_check_interval)
        elements = await self._common_handler.get_elements(selector=selector)
        n_elements = len(elements)
        self.debug_tool.info(f'Loaded {n_elements} elements')
        return elements

    async def _scroll_load(self,
                           selector: str = None,
                           scroll_step: int = None,
                           load_wait: int = 40,
                           same_th: int = 20,
                           threshold: int = None,
                           scroll_step_callbacks: List[Callable] = None,
                           log_interval: int = 100,
                           count_check_interval: int = 5,
                           elem: playwright.async_api.ElementHandle = None):
        """
        Scroll and load all contents.

        It's very common to scroll to the bottom and wait for the page to load until no new content is loaded or enough
        specific items are collected.
        Or you just want to load the whole page.
        This method is to do that.

        :param selector: (str) the selector to listen to
        :param scroll_step: (int) the scroll step in pixels
        :param load_wait: (int) the time to wait after each scroll, in milliseconds
        :param same_th: (int) the threshold of the number of same scroll top to stop scrolling
        :param threshold: (int) only valid when `selector` is not `None`, after loading `threshold` number of elements, the method will stop scrolling
        :param scroll_step_callbacks: (List[Callable]) A callback function to be called after each scroll.
        :param log_interval: (int) The interval of logging the number of loaded elements.
        :param count_check_interval: (int) The interval of checking the number of elements.
        :param elem: (ElementHandler) The element to scroll. If None, scroll the whole page.
        :return:
        """
        same_count = 0
        last_top = None
        count_check_counter = 0
        n_selector, prev_n_selector = 0, 0
        same_sel_count, same_sel_count_th = 0, 10

        while True:
            if selector is not None:
                count_check_counter += 1

                if count_check_counter >= count_check_interval:
                    n_selector = await self._common_handler.count(selector=selector)
                    count_check_counter = 0

                    if n_selector == prev_n_selector:
                        same_sel_count += 1
                        self.debug_tool.info(f"Same selector count: {same_sel_count}, before: {prev_n_selector}, after: {n_selector}, threshold: {threshold}")
                    else:
                        self.debug_tool.info(f"Current n_selector: {n_selector}, previous n_selector: {prev_n_selector}, threshold: {threshold} , same selector count: {same_sel_count} / {same_sel_count_th}")
                        same_sel_count = 0
                        prev_n_selector = n_selector

                    if same_sel_count >= same_sel_count_th:
                        self.debug_tool.info(f"Same selector count: {same_sel_count}, same_sel_count_th: {same_sel_count_th}, stopping!! count: {n_selector}, threshold: {threshold}")
                        break

                    if threshold is not None and n_selector >= threshold:
                        self.debug_tool.info(f'Loaded {n_selector} elements, reached threshold {threshold}, stopping.')
                        break

                    elif n_selector - prev_n_selector >= log_interval:
                        self.debug_tool.info(f'Loaded {n_selector} elements so far, threshold: {threshold}.')
                        prev_n_selector = n_selector

            await self._scroll_step(elem=elem, scroll_step=scroll_step)

            # Calling callbacks
            if scroll_step_callbacks:
                for callback in scroll_step_callbacks:
                    if asyncio.iscoroutinefunction(callback):
                        await callback()
                    else:
                        callback()

            await asyncio.sleep(load_wait / 1000.)

            top = await self.get_scroll_top(elem=elem)

            if top == last_top:
                same_count += 1
                self.debug_tool.info(f"Same top count: {same_count}, same_threshold: {same_th}, top = {top}")
                if same_count >= same_th:
                    self.debug_tool.info(f'Top unchanged for {same_count} times, stopping.')
                    break
            else:
                same_count = 0

            last_top = top

    async def _scroll_step(self, scroll_step: int = None, elem: playwright.async_api.ElementHandle = None):
        """
        Scroll by `scroll_step` pixels, if scroll_step is `None`, scroll to bottom.
        """
        if scroll_step is None:
            await self.scroll_to_bottom(elem=elem)
        else:
            await self.scroll_by(0, scroll_step, elem=elem)


__all__ = ['ScrollHandler']
