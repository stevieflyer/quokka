from typing import List
import playwright.async_api


async def get_elem_attr(elem: playwright.async_api.ElementHandle, attr: str) -> str:
    return await elem.get_attribute(attr)


async def get_elem_class_list(elem: playwright.async_api.ElementHandle) -> List[str]:
    cls_str = await get_elem_attr(elem, "class")
    return cls_str.split(" ")
