from functools import wraps

from rossum import extraction


# noinspection PyProtectedMember
def _lazy_extraction_api_instance():
    if _lazy_extraction_api_instance._instance is None:
        _lazy_extraction_api_instance._instance = extraction.ElisExtractionApi()
    return _lazy_extraction_api_instance._instance


_lazy_extraction_api_instance._instance = None


@wraps(extraction.ElisExtractionApi.extract)
def extract(*args, **kwargs):
    return _lazy_extraction_api_instance().extract(*args, **kwargs)


__all__ = ['extraction', 'extract']
