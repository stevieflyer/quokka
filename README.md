# Quokka - Browser Automation Library with Playwright

Quokka is a powerful Python library built on top of Playwright, designed to simplify browser automation and manipulation tasks. It provides a convenient facade for various browser interactions, making it easier to navigate web pages, extract data, and interact with page elements.

## Key Features

- **Asynchronous and Parallel Execution:** Quokka operates entirely in an asynchronous manner. Leveraging the power of Playwright, it utilizes multiple processes, each containing a single coroutine, for efficient parallel execution. This architecture excels in handling both IO and CPU-bound workloads when ample resources are available.
- **Multi-threaded Crawling with Ease:** Quokka's `BaseCrawler` class enables users to effortlessly transition from single-threaded to multi-threaded crawling. By taking advantage of the provided crawler template, you can seamlessly convert a single-threaded crawler into a multi-threaded one.
- Easy Browser Management: Quokka's `Agent` class provides a streamlined interface for managing browser instances, including starting, stopping, and page navigation.
- Data Extraction: With the `data_extractor` module, Quokka allows you to easily extract data from web pages using customizable selectors and extraction patterns.
- Page Interaction: The `page_interactor` module enables you to interact with web page elements, such as clicking, typing, and scrolling, making automation tasks a breeze.
- Custom Hooks: Quokka supports customizable hooks, allowing you to extend and customize the behavior of the `Agent` class to fit your specific needs.
- Extensible: Quokka exposes Playwright's `playwright` and `page` instances, enabling users to extend the library's functionality as required.

## Installation

```bash
pip install quokka
```

## Getting Started
Quokka's intuitive API makes browser automation a straightforward process. Here's a simple example:
```python
from quokka import Agent

async def main():
    agent = await Agent.instantiate(headless=True)
    await agent.start()

    # Your automation code here

    await agent.stop()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Documentation

For detailed usage instructions, examples, and customization options, please refer to the [Documentation](link_to_documentation).

## Examples

Base Crawler Example:

```python
from quokka import BaseCrawler, Debugger

class MyCrawler(BaseCrawler):
    async def _crawl(self, *args, **kwargs):
        # Core crawling logic using browser_agent

if __name__ == "__main__":
    import asyncio
    async def main():
        crawler = await MyCrawler.instantiate(debug_tool=Debugger(verbose=True))
        await crawler.start()
        await crawler.crawl()
        await crawler.stop()
    asyncio.run(main())
```
## Contributing

Contributions to Quokka are welcome! Please read our [Contribution Guidelines](link_to_contribution_guidelines) for more information on how to contribute to the project.

## License

This project is licensed under the [MIT License](link_to_license).
