from quokka.page_interactor.modules.handler import Handler


class ClickHandler(Handler):
    async def click_until_element_visible(self, click_selector: str, visible_selector: str, max_retry: int = 5):
        """
        Keep clicking an element until another element becomes visible or until max retries.

        :param click_selector: Selector of the element to be clicked.
        :param visible_selector: Selector of the element that should become visible after the click.
        :param max_retry: Maximum number of click attempts.
        :return: (None)
        """
        self.debug_tool.debug(f"Clicking {click_selector} until {visible_selector} becomes visible, max_retry: {max_retry}...")
        n_retry = 0
        while not await self.page.is_visible(visible_selector) and n_retry < max_retry:
            if await self.page.is_visible(click_selector):
                element_to_click = await self.page.query_selector(click_selector)
                await element_to_click.scroll_into_view_if_needed()
                await element_to_click.click()
                try:
                    await self.page.wait_for_selector(visible_selector, state='visible', timeout=5000)
                except Exception:
                    pass
            else:
                self.debug_tool.error(f"Cannot find the clicking element: {click_selector}")
                raise RuntimeError(f"Cannot find the clicking element: {click_selector}")
            n_retry += 1

        if n_retry >= max_retry:
            self.debug_tool.error(f"Cannot make {visible_selector} visible after {max_retry} tries.")
            raise RuntimeError(f"Cannot make {visible_selector} visible after {max_retry} tries.")
        else:
            self.debug_tool.debug(f"Make {visible_selector} visible after {n_retry} / {max_retry} tries.")


__all__ = ['ClickHandler']
