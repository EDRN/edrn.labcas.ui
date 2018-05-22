# encoding: utf-8

from ._about import AboutView
from ._accept import AcceptView
from ._authentication import AuthenticationView
from ._collection import CollectionView
from ._collections import CollectionsView
from ._completions import PeopleCompletionsView, ProtocolCompletionsView, LDAPGroupsCompletionsView
from ._dataset import DatasetView
from ._download import DownloadView
from ._favicon import favicon_view
from ._file import FileView
from ._help import HelpView
from ._metadata import MetadataView
from ._search import SearchView
from ._upload import UploadView
from ._wfmetadata import WFMetadataView


__all__ = (
    AboutView,
    AcceptView,
    AuthenticationView,
    CollectionsView,
    CollectionView,
    DatasetView,
    DownloadView,
    favicon_view,
    FileView,
    HelpView,
    LDAPGroupsCompletionsView,
    MetadataView,
    PeopleCompletionsView,
    ProtocolCompletionsView,
    SearchView,
    UploadView,
    WFMetadataView
)
