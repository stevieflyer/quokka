from typing import List

import playwright.async_api

from .handler import Handler


class CommonHandler(Handler):
    async def get_element(self, selector: str, strict: bool = False) -> playwright.async_api.ElementHandle:
        """
        Get the element according to the selector.

        If `strict` is True, then when resolving multiple elements, the function will raise Error
        """
        return await self.page.query_selector(selector=selector, strict=strict)

    async def get_elements(self, selector: str) -> List[playwright.async_api.ElementHandle]:
        """
        Get the elements according to the selector.

        :param selector: (str) the selector
        :return: (List[playwright.async_api.ElementHandle]) the elements
        """
        return await self.page.query_selector_all(selector=selector)

    async def count(self, selector: str) -> int:
        """
        Count the number of elements according to the selector.

        :param selector: (str) the selector
        :return: (int) the number of elements
        """
        return len(await self.get_elements(selector=selector))
