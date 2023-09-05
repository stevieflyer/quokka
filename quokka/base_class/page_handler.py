import abc

from quokka.agent import Agent
from gembox.debug_utils import Debugger


class PageHandler(abc.ABC):
    """
    PageHandler is a base class for all page handlers.

    PageHandler is responsible for handling one type of page. Multiple PageHandlers can form up a quokka agent.
    """
    page_type = None

    def __init__(self, agent: Agent, debug_tool: Debugger):
        assert isinstance(agent, Agent), f"agent must be a `quokka.agent.Agent`, but {type(agent)}"
        self.agent = agent
        self.debug_tool = debug_tool

    def check_url(self, test_url: str = None) -> bool:
        """
        Check whether the current url is the expected type.

        :return: (bool) True when the url is acceptable
        """
        if self.page_type is None:
            return True
        else:
            return self._check_url(test_url=test_url)

    @abc.abstractmethod
    def _check_url(self, test_url: str) -> bool:
        """
        This method check whether the current url is the expected type.

        The expected type should be specified in class variable `page_type`.

        :param test_url: (str) the url to be tested
        :return: (bool) True when the url is acceptable
        """
        return True


__all__ = ['PageHandler']
