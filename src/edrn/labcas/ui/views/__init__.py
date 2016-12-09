# encoding: utf-8

from ._accept import AcceptView
from ._authentication import AuthenticationView
from ._collection import CollectionView
from ._collections import CollectionsView
from ._completions import PeopleCompletionsView, ProtocolCompletionsView, LDAPGroupsCompletionsView
from ._dataset import DatasetView
from ._file import FileView
from ._home import HomeView
from ._metadata import MetadataView
from ._upload import UploadView


__all__ = (
    AcceptView,
    AuthenticationView,
    CollectionsView,
    CollectionView,
    DatasetView,
    FileView,
    HomeView,
    LDAPGroupsCompletionsView,
    MetadataView,
    PeopleCompletionsView,
    ProtocolCompletionsView,
    UploadView
)
