import io
import importlib
import os

from os.path import expanduser

from pymas.backends.common import WritableIMASDataStore
from pymas._libs.imasdef import *
from pymas.ids_classes import ALException
from pymas.backends.file_manager import DummyFileManager

class Environment:
    """ An environment identifies a unique location `Pulse`s are saved

    """

    def __init__(self, user, tokamak, version):
        pass

class Pulse:
    """ A pulse identifies a collection of related IDSs

    """
    def __init__(tokamak):
        embed()
    def create_env(self, user, tokamak, version, silent=False, options=None):
        pass

    @property
    def uid(self):
        return '/'.join()

def _find_user_name():
    if 'USER' in os.environ:
        user_name = os.environ['USER']
    else:
        raise Exception('Could not determine user_name automatically.')
    return user_name

def _find_data_version():
    if 'IMAS_VERSION' in os.environ:
        data_version = os.environ['IMAS_VERSION']
    else:
        raise Exception('Could not determine version of data automatically.')
    return data_version

def _find_ual_version():
    if 'UAL_VERSION' in os.environ:
        ual_version = os.environ['UAL_VERSION']
    else:
        raise Exception('Could not determine UAL version automatically.')
    return ual_version


class ALError(Exception):

   def __init__(self, message, errorStatus=None):
       self.message = message
       self.errorStatus = errorStatus

   def __str__(self):
       return '{!s} (error status={!s})'.format(self.message, self.errorStatus)

class PulseNotFoundError(ALError):
    pass

UAL_BACKENDS = [
    NO_BACKEND,
    ASCII_BACKEND,
    MDSPLUS_BACKEND,
    HDF5_BACKEND,
    MEMORY_BACKEND,
    UDA_BACKEND,
]
PULSE_ACTIONS = [
    OPEN_PULSE,
    FORCE_OPEN_PULSE,
    CREATE_PULSE,
    FORCE_CREATE_PULSE,
    CLOSE_PULSE,
    ERASE_PULSE,
]

def get_user_db_directory(user=None):
    """Get the IMAS database directory root for the user.
    If user is omitted, the current user is used."""
    if not user: user = os.getlogin()
    if user == "public":
        publichome = os.getenv("IMAS_HOME")
        if publichome is None:
            raise Exception("Environment variable IMAS_HOME is not defined. Quitting.")
        return publichome + '/shared/imasdb'
    else:
        return os.path.expanduser("~" + user + "/public/imasdb")

class UALFile():
    """ A UAL file-like object. """
    # From the python glossary:

    #An object exposing a file-oriented API (with methods such as read()
    #or write()) to an underlying resource. Depending on the way it was created,
    #a file object can mediate access to a real on-disk file or to another type
    #of storage or communication device (for example standard input/output,
    #in-memory buffers, sockets, pipes, etc.). File objects are also called
    #file-like objects or streams.
    #
    #There are actually three categories of file objects: raw binary files,
    # buffered binary files and text files. Their interfaces are defined in the
    #io module. The canonical way to create a file object is by using the open()
    # function.

    # We implement here the needed methods and properties as needed
    # We use delegation instead of inheriting from io.IOBase
    # 
    def __init__(self, backend_id, db_name, shot, run,
                 user_name,
                 data_version,
                 ual_version,
                 mode='r',
                 options=''):
        # Check sanity of input arguments
        if shot < 1:
            raise Exception('Shot should be above 1')
        if run > 9999:
            raise Exception('Shot should be below 9999')


        try:
            major, minor, patch = ual_version.split('.')
        except:
            raise Exception("Could not determine UAL version. Should be of format x.x.x")
        sanitized_ual_version = '_'.join([major, minor, patch])

        if backend_id not in UAL_BACKENDS:
            raise Exception("Given backend_id '{!s}' not in allowed backends".format(backend_id))

        self.db_name = db_name
        self.shot = shot
        self.run = run
        self.user_name = user_name
        self.data_version = data_version
        self.options = options
        self.ual_version = ual_version
        self.backend_id = backend_id

        # Import pymas UAL library
        ull = importlib.import_module(
            'ual_{!s}._ual_lowlevel'.format(sanitized_ual_version))

        # Begin the pulse action
        status, idx = ull.ual_begin_pulse_action(backend_id, shot, run,
                                                 user_name, db_name,
                                                 data_version)
        if status != 0:
            raise ALError("Error calling ual_begin_pulse_action("
                            "{!s},{!s},'{!s}','{!s}','{!s}')".format(
                                backend_id, shot, run, user_name, db_name,
                                data_version),
                          status)

        # OPEN_PULSE: Openes the access to the data only if the Data Entry
        #    exists, returns error otherwise
        # FORCE_OPEN_PULSE: Opens access to the data, creates the Data Entry
        #    if it does not exist yet
        # CREATE_PULSE: Creates a new empty Data Entry (returns error if
        #    Data Entry already exists) and opens it at the same time
        # FORCE_CREATE_PULSE: Creates an empty Data Entry (overwrites if
        #    Data Entry already exists) and opens it at the same time
        if mode == 'r':
            status = ull.ual_open_pulse(idx, OPEN_PULSE, options)
            if status != 0:
                raise PulseNotFoundError('No such pulse {!s}'.format(self), status)
        elif mode == 'w':
            status = ull.ual_open_pulse(idx, FORCE_CREATE_PULSE, options)
        elif mode == 'a':
            status = ull.ual_open_pulse(idx, FORCE_OPEN_PULSE, options)
        elif mode == 'x':
            status = ull.ual_open_pulse(idx, CREATE_PULSE, options)
        else:
            raise ValueError("Invalid mode: '{!s}'".format(mode))

        if status != 0:
            raise Exception('Error calling ull.ual_open_pulse('
                            '{!s},{!s},{!s})'.format(idx, OPEN_PULSE, options))

        self.closed = False
        self._context_idx = idx
        self._attrs_locked = True

    @property
    def readable(self):
        # An UALFile is automatically readable if it is open
        return not self.closed

    @property
    def writeable(self):
        # An UALFile is automatically writable if it is open
        return not self.closed

    @classmethod
    def open(cls, backend_id, db_name, shot, run,
             mode='r',
             user_name=None,
             data_version=None,
             options='',
             ual_version=None):
        # Try to automatically find not-given kwargs
        user_name = user_name or _find_user_name()
        data_version = data_version or _find_data_version()
        ual_version = ual_version or _find_ual_version()
        return cls(backend_id, db_name, shot, run, user_name, data_version,
                   ual_version, mode=mode, options=options)
    @classmethod
    def create(cls, options=''):
        raise Exception("Create a using {!s}.open(*args, mode='w', **kwargs)".format(cls))

    def __repr__(self):
        return '%s(context=%r)' % (type(self).__name__, self._context_idx)

    def __str__(self):
        return '%s(shot=%r, run=%r)' % (type(self).__name__, self.shot, self.run)

    def close(self, options=None):
        if (self.db_ctx != -1):
            old_attrs_locked = self._attrs_locked
            self._attrs_locked = False
            ull.ual_close_pulse(self.db_ctx, CLOSE_PULSE, options)
            self.db_ctx = -1
            self.closed = True
            self._attrs_locked = old_attrs_locked

    def filepath(self):
        if self.backend_id in (MDSPLUS_BACKEND, MEMORY_BACKEND):
            # MDSPlus Pulsefules come are named name-of-the-tree_shot-specifier
            # name-of-the-tree is always ids for these file
            # shot-specifier has special values:
            # * -1 - model
            # * 0 - current shot
            # * >1 - pulse files
            # Our UALFile should be a 'pulse file', so >1
            # The last four digits are the run number.
            home = expanduser("~{!s}".format(self.user_name))
            dbdir = get_user_db_directory(self.user_name)
            mdsplusdir = os.path.join(dbdir, self.db_name, self.data_version)
            treedir = os.path.join(mdsplusdir, str(int(self.run / 10000)))
            run_string = str(self.run % 10000)
            if self.shot == 0:
                stem = os.path.join(treedir, 'ids_' + run_string.zfill(3) + '.*')
            else:
                stem = os.path.join(treedir, 'ids_' + str(self.shot) + run_string.zfill(4) + '.*')
            return stem

#    def get(self, ids_name, occurrence=0):
#        import imas
#        try:
#            imas_module = sys.modules[imas.__name__ ]
#            ids_class = getattr(imas_module, ids_name)
#            ids = ids_class()
#        except Exception as exc:
#            raise NameError('IDS "' + ids_name + '" cannot be found!')
#        ids.get(occurrence, self)
#        return ids
#
#    def put(self, ids, occurrence=0):
#        ids.put(occurrence, self)
#        return ids
#
#    def get_slice(self, ids_name, time_requested, interpolation_method, occurrence=0):
#        raise NotImplementedError()
#        import imas
#        try:
#            imas_module = sys.modules[imas.__name__ ]
#            ids_class = getattr(imas_module, ids_name)
#            ids = ids_class()
#        except Exception as exc:
#            raise NameError('IDS "' + ids_name + '" cannot be found!')
#        ids.getSlice(time_requested, interpolation_method, occurrence, self)
#        return ids
#
#    def put_slice(self, ids, occurrence = 0):
#        ids.put(occurrence, self)
#        return ids
#

    def __setattr__(self, key, value):
        # Prevent user from trying to change what this file points to by
        # changing its attributes
        if hasattr(self, '_attributes_locked') and self._attributes_locked:
            raise AttributeError("attribute '{!s}' of '{!s}' objects is not writable".format(key, type(self)))
        else:
            super().__setattr__(key, value)

# This interface _heavily_ borrows from NetCDF4DataStore, as it is
# very similar to how IDSs in UAL are represented. However, all
# currently not needed functionality has been removed.
class UALDataStore(WritableIMASDataStore):
    """Store for reading and writing data via the UAL Low-Level interface."""

    __slots__ = (
        "autoclose",
        "format",
        "is_remote",
        "lock",
        "_filename",
        "_group",
        "_manager",
        "_mode",
    )

    def __init__(
        self, manager,
        # group=None,
        # mode=None,
        # lock=NETCDF4_PYTHON_LOCK, Do use locking
        # autoclose=False
    ):
        self._manager = manager
        #self._group = group
        #self._mode = mode
        #self.format = self.ds.data_model
        self._filename = self.ds.filepath()
        #self.is_remote = is_remote_uri(self._filename)
        self.is_remote = False
        self.lock = False
        self.autoclose = False

    @classmethod
    def open(
        cls,
        backend_id,
        db_name,
        shot,
        run,
        user_name=None,
        data_version=None,
        mode="r",
        # format="NETCDF4", # There is only one format, UAL
        # group=None, # All sub-level access is handeled by the UAL directly
        # clobber=False, # Other level?
        # diskless=False, # Handled by UAL?
        # persist=False, # No idea what this does
        # lock=None, # File locking handeled by the UAL
        # lock_maker=None, # File locking handeled by the UAL
        # autoclose=False, # Nope
        options=None,
        ual_version=None,
    ):
        """ Open the UAL store"""
        ual_file = UALFile.open(backend_id, db_name, shot, run,
             mode=mode,
             user_name=user_name,
             data_version=data_version,
             options=options,
             ual_version=ual_version)
        manager = DummyFileManager(ual_file)
        return cls(manager)

    def _acquire(self, needs_lock=True):
        """ Acquire a reference to this specific UALDataStore
        """
        # Get the context from the manager and use it as root
        with self._manager.acquire_context() as root:
            # As we only _allow_ to grab internal structures like this, the
            # following code is easier than in the xarray netCDF4 case
            ds = root
        return ds

    @property
    def ds(self):
        return self._acquire()

    def open_store_variable(self, name, var):
        dimensions = var.dimensions
        data = indexing.LazilyOuterIndexedArray(NetCDF4ArrayWrapper(name, self))
        attributes = {k: var.getncattr(k) for k in var.ncattrs()}
        _ensure_fill_value_valid(data, attributes)
        # netCDF4 specific encoding; save _FillValue for later
        encoding = {}
        filters = var.filters()
        if filters is not None:
            encoding.update(filters)
        chunking = var.chunking()
        if chunking is not None:
            if chunking == "contiguous":
                encoding["contiguous"] = True
                encoding["chunksizes"] = None
            else:
                encoding["contiguous"] = False
                encoding["chunksizes"] = tuple(chunking)
        # TODO: figure out how to round-trip "endian-ness" without raising
        # warnings from netCDF4
        # encoding['endian'] = var.endian()
        pop_to(attributes, encoding, "least_significant_digit")
        # save source so __repr__ can detect if it's local or not
        encoding["source"] = self._filename
        encoding["original_shape"] = var.shape
        encoding["dtype"] = var.dtype

        return Variable(dimensions, data, attributes, encoding)

    def get_variables(self):
        dsvars = FrozenDict(
            (k, self.open_store_variable(k, v)) for k, v in self.ds.variables.items()
        )
        return dsvars

    def get_attrs(self):
        attrs = FrozenDict((k, self.ds.getncattr(k)) for k in self.ds.ncattrs())
        return attrs

    def get_dimensions(self):
        dims = FrozenDict((k, len(v)) for k, v in self.ds.dimensions.items())
        return dims

    def get_encoding(self):
        encoding = {}
        encoding["unlimited_dims"] = {
            k for k, v in self.ds.dimensions.items() if v.isunlimited()
        }
        return encoding

    def set_dimension(self, name, length, is_unlimited=False):
        dim_length = length if not is_unlimited else None
        self.ds.createDimension(name, size=dim_length)

    def set_attribute(self, key, value):
        if self.format != "NETCDF4":
            value = encode_nc3_attr_value(value)
        if _is_list_of_strings(value):
            # encode as NC_STRING if attr is list of strings
            self.ds.setncattr_string(key, value)
        else:
            self.ds.setncattr(key, value)

    def encode_variable(self, variable):
        variable = _force_native_endianness(variable)
        if self.format == "NETCDF4":
            variable = _encode_nc4_variable(variable)
        else:
            variable = encode_nc3_variable(variable)
        return variable

    def prepare_variable(
        self, name, variable, check_encoding=False, unlimited_dims=None
    ):
        datatype = _get_datatype(
            variable, self.format, raise_on_invalid_encoding=check_encoding
        )
        attrs = variable.attrs.copy()

        fill_value = attrs.pop("_FillValue", None)

        if datatype is str and fill_value is not None:
            raise NotImplementedError(
                "netCDF4 does not yet support setting a fill value for "
                "variable-length strings "
                "(https://github.com/Unidata/netcdf4-python/issues/730). "
                "Either remove '_FillValue' from encoding on variable %r "
                "or set {'dtype': 'S1'} in encoding to use the fixed width "
                "NC_CHAR type." % name
            )

        encoding = _extract_nc4_variable_encoding(
            variable, raise_on_invalid=check_encoding, unlimited_dims=unlimited_dims
        )

        if name in self.ds.variables:
            nc4_var = self.ds.variables[name]
        else:
            nc4_var = self.ds.createVariable(
                varname=name,
                datatype=datatype,
                dimensions=variable.dims,
                zlib=encoding.get("zlib", False),
                complevel=encoding.get("complevel", 4),
                shuffle=encoding.get("shuffle", True),
                fletcher32=encoding.get("fletcher32", False),
                contiguous=encoding.get("contiguous", False),
                chunksizes=encoding.get("chunksizes"),
                endian="native",
                least_significant_digit=encoding.get("least_significant_digit"),
                fill_value=fill_value,
            )

        nc4_var.setncatts(attrs)

        target = NetCDF4ArrayWrapper(name, self)

        return target, variable.data

    def sync(self):
        self.ds.sync()

    def close(self, **kwargs):
        self._manager.close(**kwargs)

    @property
    def _idx(self):
        pulse_file = self._manager.acquire()
        return pulse_file._context_idx


#class UALStore(DataStore):
#    def __init__(self, backend_id, db_name, shot, run, user_name=None, data_version=None, ual_version=None):
#     #al_status = ual.ual_begin_pulse_action(backendID, shot, run, user.encode('UTF-8'), tokamak.encode('UTF-8'), version.encode('UTF-8'), &pulseCtx)
#        self.backend_id = backend_id
#        self.db_name = db_name
#        self.shot = shot
#        self.run = run
#
#        self.db_ctx = -1
#
#    def __str__(self, depth=0):
#        #space = ''
#        #for i in range(depth):
#        #    space = space + '\t'
#
#        #ret = space + 'class ids\n'
#        #ret = ret + space + 'Shot=%d, Run=%d\n' % (self.shot, self.run)
#        #ret = ret + space + 'treeName=%s, connected=%d, db_ctx=%d\n' % (self.treeName, self.connected, self.db_ctx)
#        return ret
#
#    def __del__(self):
#        return 1
#        #if self.db_ctx != -1:
#            #ull.imas_close(self.db_ctx)
#
#    def create(self, options=None):
#        """Creates a new db entry.
#
#        """
#        status, idx = ull.ual_begin_pulse_action(self.backend_id, self.shot, self.run, self.user_name, self.db_name, self.data_version)
#        if status != 0:
#            raise Exception('Error calling ual_begin_pulse_action()')
#        status = ull.ual_open_pulse(idx, FORCE_CREATE_PULSE, options)
#        self.db_ctx = idx
#        return (status, idx)
#
#    def open(self, options=None):
#        """Opens an existing db.
#
#        """
#        status, idx = ull.ual_begin_pulse_action(self.backend_id, self.shot, self.run, self.user_name, self.db_name, self.data_version)
#        if status != 0:
#            raise Exception('Error calling ual_begin_pulse_action()')
#        status = ull.ual_open_pulse(idx, OPEN_PULSE, options)
#        self.db_ctx = idx
#        return (status, idx)
#
#    def get(self, ids_name, occurrence=0):
#        import imas
#        try:
#            imas_module = sys.modules[imas.__name__ ]
#            ids_class = getattr(imas_module, ids_name)
#            ids = ids_class()
#        except Exception as exc:
#            raise NameError('IDS "' + ids_name + '" cannot be found!')
#        ids.get(occurrence, self)
#        return ids
#
#    def put(self, ids, occurrence=0):
#        ids.put(occurrence, self)
#        return ids
#
#    def get_slice(self, ids_name, time_requested, interpolation_method, occurrence=0):
#        raise NotImplementedError()
#        import imas
#        try:
#            imas_module = sys.modules[imas.__name__ ]
#            ids_class = getattr(imas_module, ids_name)
#            ids = ids_class()
#        except Exception as exc:
#            raise NameError('IDS "' + ids_name + '" cannot be found!')
#        ids.getSlice(time_requested, interpolation_method, occurrence, self)
#        return ids
#
#    def put_slice(self, ids, occurrence = 0):
#        ids.put(occurrence, self)
#        return ids
#
#    def close(self, options=None):
#        if (self.db_ctx != -1):
#            ull.ual_close_pulse(self.db_ctx, CLOSE_PULSE, options)
#            self.db_ctx = -1

#class DataStore(Mapping):
#    """ A DataStore identifies a unique collection of related IDSs
#
#    Similar concepts are pyal.Client.__db_key, idstools.ids_tools.ImasDb,
#    and imas.DBEntry. However, here we explicitly do not assume any underlying
#    database, access layer, or file structure.
#
#    Borrows from xarray.DataSet, but instead of matching an in-memory netCDF 
#    file, it matches an in-memory IDS collection
#
#    Can usually be matched to a specific path where the data files will be
#    stored.
#    For example, for UALs MDSPLUS backend the default will be:
#    <home of given user>/public/imasdb/<tokamak>/<version>
#
#    However, the location can also be virtual, e.g. not on disk, for example
#    for UALs MEMORY backend.
#
#    Args:
#      - path: The path to where the different IDSs will be stored
#      - shot:    Number of the represented shot
#      - run:     Runnumber of the represented run
#    """

#from IPython import embed
#embed()
