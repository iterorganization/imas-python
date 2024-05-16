from imaspy.ids_factory import IDSFactory
from imaspy.netcdf.nc_metadata import NCMetadata


def test_generate_nc_metadata(ids_name):
    ids = IDSFactory().new(ids_name)
    NCMetadata(ids.metadata)
