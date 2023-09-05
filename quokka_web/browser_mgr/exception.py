class BrowserNotRunningError(Exception):
    def __init__(self, message=f"Browser is not running"):
        super().__init__(message)


class NoActivePageError(Exception):
    def __init__(self, message=f"No active page found"):
        super().__init__(message)


class NonSingletonError(Exception):
    def __init__(self, message=f"Only one browser instance and one page is allowed"):
        super().__init__(message)
