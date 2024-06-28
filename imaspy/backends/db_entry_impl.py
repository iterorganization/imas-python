# This file is part of IMASPy.
# You should have received the IMASPy LICENSE file with this project.

from abc import ABC, abstractmethod
from typing import Any, List, Optional

from imaspy.ids_convert import NBCPathMap
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
    def close(self, *, erase: bool = False) -> None:
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
        destination: IDSToplevel,
        lazy: bool,
        nbc_map: Optional[NBCPathMap],
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
            nbc_map: NBCPathMap to use for implicit conversion. When None, no implicit
                conversion needs to be done.
        """

    @abstractmethod
    def read_dd_version(self, ids_name: str, occurrence: int) -> str:
        """Read data dictionary version that the requested IDS was stored with.

        This method should raise a DataEntryException if the specified ids/occurrence is
        not filled.
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
    def list_all_occurrences(self, ids_name: str) -> List[int]:
        """Implement DBEntry.list_all_occurrences()"""