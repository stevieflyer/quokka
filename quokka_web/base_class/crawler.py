import abc
import logging
import pathlib
import traceback
from typing import List, Dict, Type

from quokka_web import Agent
from gembox.io import check_and_make_dir
from gembox.multiprocess import Task, ParallelExecutor
from gembox.debug_utils import Debugger, FileConsoleDebugger, FileDebugger


class BaseCrawler(abc.ABC):
    """
    Base Crawler class.

    Now, the crawler can only interact with the browser agent until some requirements are satisfied, then download it.

    Crawler is responsible for interacting with the browser, save the webpage and parse the webpage to get data.

    **Note: The default browser agent is `quokka_web.agent.Agent`, you can replace it by specify `agent_cls` class variable.**
    """
    agent_cls: Type[Agent] = Agent
    """the browser agent class, it should be a subclass of `quokka_web.agent.Agent`"""

    def __init__(self, browser_agent, debug_tool: Debugger):
        self._browser_agent = browser_agent
        self._debug_tool = debug_tool

    async def crawl(self, *args, **kwargs):

        if self.is_running is False:
            self.debug_tool.error(
                f"{self.__class__.__name__} cannot start crawling, since the crawler hasn't started yet. Please start the crawler by calling `start()` or using `async with`.")
        await self._crawl(*args, **kwargs)

    @abc.abstractmethod
    async def _crawl(self, *args, **kwargs):
        """
        The core logic of the crawler.

        Usually, you should use `self.browser_agent` to interact with the browser and download the webpage properly.
        """
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def _crawler_args_str(cls, **crawler_args) -> str:
        """
        Generate a string based on the crawler args
        """
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def required_fields(cls) -> dict:
        """
        The required fields listed in the `self.crawl method.
        """
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def optional_fields(cls) -> dict:
        """
        The optional fields listed in the `self.crawl` method
        """
        raise NotImplementedError

    async def start(self, viewport: dict = None, **kwargs):
        """
        Start the crawler.

        :param viewport: (dict) the viewport, default is {'width': 1360, 'height': 900}
        :return: (None)
        """
        if self.is_running:
            self.debug_tool.warn(f"{self.__class__.__name__} is already running. No need to start again")
            return
        self.debug_tool.info(f"Starting {self.__class__.__name__}...")
        # core starting logic, now, it is just starting the browser_agent
        await self.browser_agent.start(viewport=viewport, **kwargs)
        self.debug_tool.info(f"Start {self.__class__.__name__} successfully")

    async def stop(self):
        if self.is_running is False:
            self.debug_tool.warn(f"{self.__class__.__name__} is not running. No need to stop")
            return
        self.debug_tool.info(f"Stopping {self.__class__.__name__}...")
        # core stopping logic, now it is just stopping the browser_agent
        await self.browser_agent.stop()
        self.debug_tool.info(f"Stop {self.__class__.__name__} successfully")

    @classmethod
    async def instantiate(cls, headless=False, debug_tool: Debugger = None) -> 'BaseCrawler':
        """
        Instantiate a crawler instance.

        :param headless: (bool) Whether to run the browser in headless mode.
        :param debug_tool: (Debugger) The debugger instance.

        :return: (BaseCrawler) The crawler instance.
        """
        if not hasattr(cls, 'agent_cls'):
            raise NotImplementedError(f"agent_cls is not specified in {cls.__name__}, Please specify it first.")
        assert issubclass(cls.agent_cls,
                          Agent), f"agent_cls must be a subclass of `quokka_web.agent.Agent`, but got {cls.agent_cls.__name__}"

        debug_tool = Debugger() if debug_tool is None else debug_tool
        browser_agent = await cls.agent_cls.instantiate(headless=headless, debug_tool=debug_tool)
        instance = cls(browser_agent=browser_agent, debug_tool=debug_tool)
        return instance

    @classmethod
    async def parallel_crawl(cls,
                             crawl_args_list: List[Dict],
                             log_dir: (str, pathlib.Path),
                             headless: bool = True,
                             verbose: bool = False,
                             max_retry: int = 5,
                             n_workers: int = 1) -> None:
        """
        Parallel crawl function.

        To enable parallel crawling, just specify a `log_dir` and `crawl_args_list`. (You must enable logging for later debugging convenience)

        The result will be output to `output_dir`. And logs will be saved to `output_dir/logs`.

        :param crawl_args_list: (list<dict>) List of parameter dictionaries
        :param log_dir: (str, pathlib.Path) the directory to save the crawler logs
        :param headless: (bool) Whether to run the browser in headless mode.
        :param verbose: (bool) Whether to print the log on the console.
        :param max_retry: (int) maximum number of retry for each crawl
        :param n_workers: (int) Number of parallel workers.
        """
        # 1. Parameter validation, the key must be one of the async def crawl's parameters
        assert len(crawl_args_list) > 0, "The parameter list must not be empty."
        for crawl_args in crawl_args_list:
            cls._validate_crawl_args(**crawl_args)

        # 2. Create task parameters
        worker_args_list = [
            {
                **crawl_args,
                # we use __ variables to avoid name conflict with crawl_args
                "_quokka_log_dir": log_dir,
                "_quokka_verbose": verbose,
                "_quokka_headless": headless,
                "_quokka_max_retry": max_retry,
            }
            for crawl_args in crawl_args_list
        ]

        tasks = [Task(cls._crawl_worker, params=worker_args) for worker_args in worker_args_list]
        await ParallelExecutor.run(tasks, n_workers=n_workers)

    @classmethod
    async def _crawl_worker(cls,
                            _quokka_log_dir: (str, pathlib.Path),
                            _quokka_verbose: bool,
                            _quokka_headless: bool,
                            _quokka_max_retry: int = 5,
                            **crawl_args) -> None:
        """
        Generic crawler worker for building parallel crawler.

        **Note: This function should not be called directly. It is used by `parallel_crawl` function.**

        :param _quokka_log_dir: (str, pathlib.Path) the directory to save the log
        :param _quokka_verbose: (bool) whether to print the log to the console
        :param _quokka_headless: (bool) whether the browser is headless
        :param _quokka_max_retry: (int) maximum number of retry
        :param crawl_args: (dict) the arguments for the crawler
        :return: (None)
        """
        # 0. 参数检查
        assert isinstance(_quokka_max_retry,
                          int) and _quokka_max_retry > 0, f"max_retry must be a positive integer, got {_quokka_max_retry}"
        cls._validate_crawl_args(**crawl_args)

        # 1. 生成必要的变量及文件夹
        file_name = cls._crawler_args_str(**crawl_args)  # 生成文件名, 用于命名 log 文件, html 文件
        _quokka_log_dir = check_and_make_dir(_quokka_log_dir)
        log_path = _quokka_log_dir / f"{file_name}.log"
        debugger = FileConsoleDebugger(filepath=log_path, level=logging.DEBUG) if _quokka_verbose \
            else FileDebugger(filepath=log_path, level=logging.DEBUG)

        # 2. 可重试的抓取
        finished, n_retry = False, 0
        while n_retry < _quokka_max_retry and not finished:
            crawler = None
            try:
                crawler = await cls.instantiate(debug_tool=debugger, headless=_quokka_headless)
                # core logic: `crawl` is called HERE!
                async with crawler:
                    await crawler.crawl(**crawl_args)
                    finished = True
            except Exception as e:
                if crawler is not None:
                    debugger.info(f"Stopping crawler... in except")
                    await crawler.stop()
                else:
                    debugger.info(f"Crawler is None... in except")
                error_message = str(e)
                stack_trace = traceback.format_exc()
                debugger.error(f"Error while crawling. Error: {error_message}")
                debugger.error(f"Stack Trace: {stack_trace}")
                debugger.warn(f"Retrying {n_retry + 1}/{_quokka_max_retry}...")
                n_retry += 1
            debugger.info(f"Finished after {n_retry}/{_quokka_max_retry} retrie, finished_flag: {finished}")

    @classmethod
    def _validate_crawl_args(cls, **crawl_args):
        """
        Validate all crawl arguments.

        1. check all required_fields are filled and in proper type
        2. make sure there are no extra fields
        3. for optional_fields that are filled, make sure they're in proper type
        """

        required_fields = cls.required_fields()
        all_fields = cls.crawler_fields()

        # 1. Check all required_fields are filled and in proper type
        missing_fields = set(required_fields.keys()) - set(crawl_args.keys())
        if missing_fields:
            raise AssertionError(f"Missing required fields: {', '.join(missing_fields)}")

        # 2. Make sure there are no extra fields
        extra_fields = set(crawl_args.keys()) - set(all_fields.keys())
        if extra_fields:
            raise AssertionError(f"Unknown fields: {', '.join(extra_fields)}")

        # 3. Check for proper types
        for field_name, field_value in crawl_args.items():
            expected_type = all_fields[field_name]
            if not isinstance(field_value, expected_type):
                raise AssertionError(
                    f"{field_name} should be {expected_type}, but got {type(field_value)}, value: {field_value}")

    @classmethod
    def crawler_fields(cls) -> dict:
        return {
            **cls.required_fields(),
            **cls.optional_fields(),
        }

    # getters
    @property
    def browser_agent(self):
        """
        The browser interaction agent instance.
        """
        return self._browser_agent

    @property
    def debug_tool(self) -> Debugger:
        return self._debug_tool

    @property
    def is_running(self) -> bool:
        return self.browser_agent.is_running

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()


__all__ = ['BaseCrawler']
