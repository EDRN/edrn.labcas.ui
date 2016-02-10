# encoding: utf-8

from ._accept import AcceptView
from ._authentication import AuthenticationView
from ._dataset import DatasetView
from ._datasets import DatasetsView
from ._home import HomeView
from ._metadata import MetadataView
from ._upload import UploadView


__all__ = (
    AcceptView,
    AuthenticationView,
    DatasetsView,
    DatasetView,
    HomeView,
    MetadataView,
    UploadView
)
