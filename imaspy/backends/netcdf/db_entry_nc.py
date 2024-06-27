"""DBEntry implementation using NetCDF as a backend."""

import logging

from imaspy.ids_factory import IDSFactory

logger = logging.getLogger(__name__)

try:
    import netCDF4
except ImportError:
    netCDF4 = None
    logger.debug("Could not import netCDF4", exc_info=True)


class NCDBEntryImpl:
    @classmethod
    def from_uri(cls, uri: str, mode: str, factory: IDSFactory) -> "NCDBEntryImpl": ...
