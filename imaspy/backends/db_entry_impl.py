# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.

from abc import ABC, abstractmethod
from typing import Any, Optional

from imaspy.ids_factory import IDSFactory
from imaspy.ids_toplevel import IDSToplevel


class DBEntryImpl(ABC):
    """Interface for DBEntry implementations."""

    @classmethod
    @abstractmethod
    def from_uri(cls, uri: str, mode: str, factory: IDSFactory) -> "DBEntryImpl":
        """Open a datasource by URI."""

    @classmethod
    @abstractmethod
    def from_pulse_run(
        cls,
        backend_id: int,
        db_name: str,
        pulse: int,
        run: int,
        user_name: Optional[str],
        data_version: Optional[str],
        mode: int,
        options: Any,
        factory: IDSFactory,
    ) -> "DBEntryImpl":
        """Open a datasource with pulse, run and other legacy arguments."""

    @abstractmethod
    def close(self, *, erase=False):
        """Close the data source.

        Keyword Args:
            erase: The Access Layer allowed a parameter to erase data files when
                closing. This parameter may be ignored when implementing a backend.
        """

    @abstractmethod
    def get(
        self,
        ids_name: str,
        occurrence: int,
        time_requested: Optional[float],
        interpolation_method: int,
        destination: Optional[IDSToplevel],
        lazy: bool,
        autoconvert: bool,
        ignore_unknown_dd_version: bool,
    ) -> None:
        """Implement DBEntry.get()/get_slice(). Load data from the data source.

        Args:
            ids_name: Name of the IDS to load.
            occurrence: Which occurence of the IDS to load.
            time_requested: None for get(), requested time slice for get_slice().
            interpolation_method: Requested interpolation method (ignore when
                time_requested is None).
            destination: IDS object to store data in.
            lazy: Use lazy loading.
            autoconvert: Automatically convert between on-disk and requested version.
            ignore_unknown_dd_version: When an IDS is stored with an unknown DD version,
                do not attempt automatic conversion and fetch the data in the Data
                Dictionary version attached to this Data Entry.
        """

    @abstractmethod
    def put(self, ids: IDSToplevel, occurrence: int, is_slice: bool) -> None:
        """Implement DBEntry.put()/put_slice(): store data.

        Args:
            ids: IDS to store in the data source.
            occurrence: Which occurrence of the IDS to store to.
            is_slice: True: put_slice(), False: put()
        """

    @abstractmethod
    def access_layer_version(self) -> str:
        """Get the access layer version used to store data."""

    @abstractmethod
    def delete_data(self, ids_name: str, occurrence: int) -> None:
        """Implement DBEntry.delete_data()"""

    @abstractmethod
    def list_all_occurrences(self, ids_name):
        """Implement DBEntry.list_all_occurrences()"""
