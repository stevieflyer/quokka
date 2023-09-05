class SoupNotLoadedException(Exception):
    """Raised when soup is not loaded"""
    pass


class FailedToLoadWebpageException(Exception):
    """Raised when failed to load webpage"""
    pass


__all__ = ['SoupNotLoadedException', 'FailedToLoadWebpageException']
