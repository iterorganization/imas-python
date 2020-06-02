# Set up logging immediately
import logging
import copy

root_logger = logging.getLogger('pymas')
logger = root_logger
logger.setLevel(logging.WARNING)

import abc
import functools
import os
from IPython import embed
import numbers
import importlib
ull = importlib.import_module('ual_4_7_2._ual_lowlevel')
from pymas._libs.imasdef import MDSPLUS_BACKEND, OPEN_PULSE, DOUBLE_DATA, READ_OP, EMPTY_INT, FORCE_CREATE_PULSE, IDS_TIME_MODE_UNKNOWN,IDS_TIME_MODES, IDS_TIME_MODE_HOMOGENEOUS, WRITE_OP, CHAR_DATA, INTEGER_DATA, EMPTY_FLOAT, DOUBLE_DATA
import numpy as np
import xml
import xml.etree.ElementTree as ET
import pymas._libs.hli_utils as hli_utils

context_store = {}

class ALException(Exception):

   def __init__(self, message, errorStatus=None):
        if errorStatus is not None:
          Exception.__init__(self, message + "\nError status=" + str(errorStatus))
        else:
          Exception.__init__(self, message)

ids_type_to_default = {
    'STR': '',
    'INT': EMPTY_INT,
    'FLT': EMPTY_FLOAT,
}
#allowed_ids_types = ['STR_0D', 'INT_0D', 'FLT_0D', 'int_type', 'FLT_1D', 'FLT_2D', 'FLT_4D', 'flt_type']

def loglevel(func):
    @functools.wraps(func)
    def loglevel_decorator(*args, **kwargs):
        old_log_level = logger.level
        verbosity = kwargs.pop('verbosity', 0)
        if verbosity >= 1:
            logger.setLevel(logging.INFO)
        if verbosity >= 2:
            logger.setLevel(logging.DEBUG)
        value = func(*args, **kwargs)
        logger.setLevel(old_log_level)
        return value
    return loglevel_decorator

class IDSPrimitive():
    @loglevel
    def __init__(self, name, ids_type, ndims, parent=None, value=None, on_wrong_type='warn', timebasepath=None):
        if ids_type != 'STR' and ndims != 0 and self.__class__ == IDSPrimitive:
            raise Exception('{!s} should be 0D! Got ndims={:d}. Instantiate using IDSNumericArray instead'.format(self.__class__, ndims))
        if value is None:
            if ndims == 0:
                value = ids_type_to_default[ids_type]
            else:
                value = np.full((1, ) * ndims, ids_type_to_default[ids_type])
        self._ids_type = ids_type
        self._ndims = ndims
        self._name = name
        self._parent = parent
        self.value = value
        self.timebasepath = timebasepath

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        self.__value = self.cast_value(value)

    def cast_value(self, value):
        # Cast list-likes to arrays
        if isinstance(value, (list, tuple)):
            value = np.array(value)

        # Cast values to their IDS-python types
        if self._ids_type == 'STR' and self._ndims == 0:
            value = str(value)
        elif self._ids_type == 'INT' and self._ndims == 0:
            value = int(value)
        elif self._ids_type == 'FLT' and self._ndims == 0:
            value = float(value)
        elif self._ndims >= 1:
            if self._ids_type == 'FLT':
                value = np.array(value, dtype=np.float64)
            elif self._ids_type == 'INT':
                value = np.array(value, dtype=np.int64)
            else:
                logger.critical(
                    'Unknown numpy type {!s}, cannot convert from python to IDS type'.format(
                        value.dtype))
                embed()
                raise Exception
        else:
            logger.critical(
                'Unknown python type {!s}, cannot convert from python to IDS type'.format(
                    type(value)))
            embed()
            raise Exception
        return value

    @loglevel
    def put(self, ctx, homogeneousTime):
        if self._name is None:
            raise Exception('Location in tree undefined, cannot put in database')
        if self._ids_type == 'INT':
            scalar_type = 1
        elif self._ids_type == 'FLT':
            scalar_type = 2
        elif self._ids_type == 'CPX':
            scalar_type = 3

        if self._ids_type in ['INT', 'FLT', 'CPX'] and self._ndims == 0:
            data = hli_utils.HLIUtils.isScalarFinite(self.value, scalar_type)
        elif self._ids_type in ['INT', 'FLT', 'CPX']:
            if not hli_utils.HLIUtils.isTypeValid(self.value, self._name, 'NP_ARRAY'):
                raise Exception
            data = hli_utils.HLIUtils.isFinite(self.value, scalar_type)
        else:
            data = self.value

        dbg_str = ' ' * self.depth + '- ' + self._name
        dbg_str += (' {:' + str(max(0, 53 - len(dbg_str))) + 's}').format('(' + str(data) + ')')
        # Call signature
        #ual_write_data(ctx, pyFieldPath, pyTimebasePath, inputData, dataType=0, dim = 0, sizeArray = np.empty([0], dtype=np.int32))
        data_type = ull._getDataType(data)
        if self.timebasepath is None:
            strTimeBasePath = ''
        else:
            strTimeBasePath = self.timebasepath

        # Strip context from absolute path
        if self.path.startswith(context_store[ctx]):
            rel_path = self.path[len(context_store[ctx]) + 1:]
        else:
            raise Exception('Could not strip context from absolute path')

        logger.debug('{:51.51s} write'.format(dbg_str))
        status = ull.ual_write_data(ctx, rel_path, strTimeBasePath, data, dataType=data_type, dim=self._ndims)
        if status != 0:
            raise ALException('Error writing field "{!s}"'.format(self._name))

    @loglevel
    def get(self, ctx, homogeneousTime):
        # Strip context from absolute path
        if self.path.startswith(context_store[ctx]):
            strNodePath = self.path[len(context_store[ctx]) + 1:]
        else:
            raise Exception('Could not strip context from absolute path')
        if self.timebasepath is None:
            strTimeBasePath = ''
        else:
            strTimeBasePath = '/' + self.timebasepath
        if self._ids_type == 'STR' and self._ndims == 0:
            status, data = ull.ual_read_data_string(ctx, strNodePath, strTimeBasePath, CHAR_DATA, 1)
        elif self._ids_type == 'INT' and self._ndims == 0:
            status, data = ull.ual_read_data_scalar(ctx, strNodePath, strTimeBasePath, INTEGER_DATA)
        elif self._ids_type == 'FLT' and self._ndims == 0:
            status, data = ull.ual_read_data_scalar(ctx, strNodePath, strTimeBasePath, DOUBLE_DATA)
        elif self._ids_type == 'FLT' and self._ndims > 0:
            status, data = ull.ual_read_data_array(ctx, strNodePath, strTimeBasePath, DOUBLE_DATA, self._ndims)
        elif self._ids_type == 'INT' and self._ndims > 0:
            status, data = ull.ual_read_data_array(ctx, strNodePath, strTimeBasePath, INTEGER_DATA, self._ndims)
        else:
            logger.critical('Unknown type {!s} ndims {!s} of field {!s}, skipping for now'.format(
            self._ids_type, self._ndims, self._name))
            status = data = None
        return status, data

    @property
    def depth(self):
        my_depth = 0
        if hasattr(self, '_parent'):
            my_depth += self._parent.depth
        return my_depth

    @property
    def path(self):
        my_path = self._name
        if hasattr(self, '_parent'):
            my_path = self._parent.path + '/' + my_path
        return my_path

    def __repr__(self):
        return '%s("%s", %r)' % (type(self).__name__, self._name, self.value)

    @property
    def data_type(self):
        return '{!s}_{!s}D'.format(self._ids_type, self._ndims)


def create_leaf_container(name, data_type, **kwargs):
    if data_type == 'int_type':
        ids_type = 'INT'
        ndims = 0
    elif data_type == 'flt_type':
        ids_type = 'FLT'
        ndims = 0
    elif data_type == 'flt_1d_type':
        ids_type = 'FLT'
        ndims = 1
    else:
        ids_type, ids_dims = data_type.split('_')
        ndims = int(ids_dims[:-1])
    if ndims == 0:
        leaf = IDSPrimitive(name, ids_type, ndims, **kwargs)
    else:
        if ids_type == 'STR':
            # Array of strings should behave more like lists
            # this is an assumption on user expectation!
            leaf = IDSPrimitive(name, ids_type, ndims, **kwargs)
        else:
            leaf = IDSNumericArray(name, ids_type, ndims, **kwargs)
    return leaf

class IDSNumericArray(IDSPrimitive, np.lib.mixins.NDArrayOperatorsMixin):
    def __str__(self):
        return self.value.__str__()

    # One might also consider adding the built-in list type to this
    # list, to support operations like np.add(array_like, list)
    _HANDLED_TYPES = (np.ndarray, numbers.Number)

    def __array_ufunc__(self, ufunc, method, *inputs, **kwargs):
        out = kwargs.get('out', ())
        for x in inputs + out:
            # Only support operations with instances of _HANDLED_TYPES.
            # Use ArrayLike instead of type(self) for isinstance to
            # allow subclasses that don't override __array_ufunc__ to
            # handle ArrayLike objects.
            if not isinstance(x, self._HANDLED_TYPES + (IDSPrimitive,)):
                return NotImplemented

        # Defer to the implementation of the ufunc on unwrapped values.
        inputs = tuple(x.value if isinstance(x, IDSPrimitive) else x
                       for x in inputs)
        if out:
            kwargs['out'] = tuple(
                x.value if isinstance(x, IDSPrimitive) else x
                for x in out)
        result = getattr(ufunc, method)(*inputs, **kwargs)

        if type(result) is tuple:
            # multiple return values
            return tuple(type(self)(self._name, self._ids_type, self._ndims, value=x) for x in result)
        elif method == 'at':
            # no return value
            return None
        else:
            # one return value
            return type(self)(self._name, self._ids_type, self._ndims, value=result)

class IDSRoot():
 """ Root of IDS tree. Contains all top-level IDSs """

 depth = 0
 path = ''

 @loglevel
 def __init__(self, s=-1, r=-1, rs=-1, rr=-1, xml_path=None):
  setattr(self, 'shot', s)
  self.shot = s
  self.refShot = rs
  self.run = r
  self.refRun = rr
  self.treeName = 'ids'
  self.connected = False
  self.expIdx = -1
  XMLtreeIDSDef = ET.parse(xml_path)
  root = XMLtreeIDSDef.getroot()
  self._children = []
  logger.info('Generating IDS structures from XML file {!s}'.format(os.path.abspath(xml_path)))
  for ids in root:
      my_name = ids.get('name')
      if my_name is None:
          continue
      # Only build for equilibrium to KISS
      if my_name != 'equilibrium':
          continue
      logger.debug('{:42.42s} initialization'.format(my_name))
      self._children.append(my_name)
      setattr(self, my_name, IDSToplevel(self, my_name, ids))
  #self.equilibrium = IDSToplevel('equilibrium')

  # Do not use this now
  #self.ddunits = DataDictionaryUnits()
  #self.hli_utils = HLIUtils()
  #self.amns_data = amns_data.amns_data()
  #self.barometry = barometry.barometry()
  # etc. etc over all lower level IDSs


 def __str__(self, depth=0):
  space = ''
  for i in range(depth):
   space = space + '\t'

  ret = space + 'class ids\n'
  ret = ret + space + 'Shot=%d, Run=%d, RefShot%d RefRun=%d\n' % (self.shot, self.run, self.refShot, self.refRun)
  ret = ret + space + 'treeName=%s, connected=%d, expIdx=%d\n' % (self.treeName, self.connected, self.expIdx)
  ret = ret + space + 'Attribute amns_data\n' + self.amns_data.__str__(depth+1)
  ret = ret + space + 'Attribute barometry\n' + self.barometry.__str__(depth+1)
  # etc. etc over all lower level IDSs
  return ret

 def __del__(self):
  return 1

 def setShot(self, inShot):
  self.shot = inShot

 def setRun(self, inRun):
  self.run = inRun

 def setRefShot(self, inRefShot):
  self.refShot = inRefShot

 def setRefNum(self, inRefRun):
  self.refRun = inRefRun

 def setTreeName(self, inTreeName):
  self.treeName = inTreeName

 def getShot(self):
  return self.shot

 def getRun(self):
  return self.run

 def getRefShot(self):
  return self.refShot

 def getRefRun(self):
  return self.refRun

 def getTreeName(self):
  return self.treeName

 def isConnected(self):
  return self.connected

 def get_units(self, ids, field):
  return self.ddunits.get_units(ids, field)

 def get_units_parser(self):
  return self.ddunits

 def create_env(self, user, tokamak, version, silent=False):
  """Creates a new pulse.

  Parameters
  ----------
  user : string
      Owner of the targeted pulse.
  tokamak : string
      Tokamak name for the targeted pulse.
  version : string
      Data-dictionary major version number for the targeted pulse.
  silent : bool, optional
      Request the lowlevel to be silent (does not print error messages).
  """
  status, idx = ull.ual_begin_pulse_action(MDSPLUS_BACKEND, self.shot, self.run, user, tokamak, version)
  if status != 0:
   return (status, idx)
  opt = ''
  if silent:
   opt = '-silent'
  status = ull.ual_open_pulse(idx, FORCE_CREATE_PULSE, opt)
  if status != 0:
   return (status, idx)
  self.setPulseCtx(idx)
  return (status, idx)

 def create_env_backend(self, user, tokamak, version, backend_type, silent=False):
  """Creates a new pulse.

  Parameters
  ----------
  user : string
      Owner of the targeted pulse.
  tokamak : string
      Tokamak name for the targeted pulse.
  version : string
      Data-dictionary major version number for the targeted pulse.
  backend_type: integer
      One of the backend types (e.g.: MDSPLUS_BACKEND, MEMORY_BACKEND).
  silent : bool, optional
      Request the lowlevel to be silent (does not print error messages).
  """
  status, idx = ull.ual_begin_pulse_action(backend_type, self.shot, self.run, user, tokamak, version)
  if status != 0:
   return (status, idx)
  opt = ''
  if silent:
   opt = '-silent'
  status = ull.ual_open_pulse(idx, FORCE_CREATE_PULSE, opt)
  if status != 0:
   return (status, idx)
  self.setPulseCtx(idx)
  return (status, idx)

 def open_env(self, user, tokamak, version, silent=False):
  """Opens a new pulse.

  Parameters
  ----------
  user : string
      Owner of the targeted pulse.
  tokamak : string
      Tokamak name for the targeted pulse.
  version : string
      Data-dictionary major version number for the targeted pulse.
  silent : bool, optional
      Request the lowlevel to be silent (does not print error messages).
  """
  status, idx = ull.ual_begin_pulse_action(MDSPLUS_BACKEND, self.shot, self.run, user, tokamak, version)
  if status != 0:
   return (status, idx)
  opt = ''
  if silent:
   opt = '-silent'
  status = ull.ual_open_pulse(idx, OPEN_PULSE, opt)
  if status != 0:
   return (status, idx)
  self.setPulseCtx(idx)
  return (status, idx)

 def open_env_backend(self, user, tokamak, version, backend_type, silent=False):
  """Opens a new pulse.

  Parameters
  ----------
  user : string
      Owner of the targeted pulse.
  tokamak : string
      Tokamak name for the targeted pulse.
  version : string
      Data-dictionary major version number for the targeted pulse.
  backend_type: integer
      One of the backend types (e.g.: MDSPLUS_BACKEND, MEMORY_BACKEND).
  silent : bool, optional
      Request the lowlevel to be silent (does not print error messages).
  """
  status, idx = ull.ual_begin_pulse_action(backend_type, self.shot, self.run, user, tokamak, version)
  if status != 0:
   return (status, idx)
  opt = ''
  if silent:
   opt = '-silent'
  status = ull.ual_open_pulse(idx, OPEN_PULSE, opt)
  if status != 0:
   return (status, idx)
  self.setPulseCtx(idx)
  return (status, idx)

 def open_public(self, expName, silent=False):
  status, idx = ull.ual_begin_pulse_action(UDA_BACKEND, self.shot, self.run, '', expName, os.environ['IMAS_VERSION'])
  if status != 0:
   return (status, idx)
  opt = ''
  if silent:
   opt = '-silent'
  status = ull.ual_open_pulse(idx, OPEN_PULSE, opt)
  if status != 0:
   return (status, idx)
  self.setPulseCtx(idx)
  return (status, idx)

 def getPulseCtx(self):
  return self.expIdx

 def setPulseCtx(self, ctx):
  self.expIdx = ctx
  self.connected = True
  self.equilibrium.setPulseCtx(ctx)
  # Etc. etc for all other IDSs
  #self.amns_data.setPulseCtx(ctx)

 def close(self):
  if (self.expIdx != -1):
   status = ull.ual_close_pulse(self.expIdx, CLOSE_PULSE, '')
   if status != 0:
    return status
   self.connected = False
   self.expIdx = -1
   return status

 def enableMemCache(self):
  return 1

 def disableMemCache(self):
  return 1

 def discardMemCache(self):
  return 1

 def flushMemCache(self):
  return 1

 def getTimes(self, path):
  homogenousTime = IDS_TIME_MODE_UNKNOWN
  if self.expIdx < 0 :
   raise ALException('ERROR: backend not opened.')

  # Create READ context
  status, ctx = ull.ual_begin_global_action(self.expIdx, path, READ_OP)
  if status != 0:
    raise ALException('Error calling ual_begin_global_action() for ', status)

  # Check homogeneous_time
  status, homogenousTime = ull.ual_read_data(ctx, "ids_properties/homogeneous_time", "", INTEGER_DATA, 0)
  if status != 0:
   raise ALException('ERROR: homogeneous_time cannot be read.', status) 

  if homogenousTime == IDS_TIME_MODE_UNKNOWN:
   status = ull.ual_end_action(ctx)
   if status != 0:
    raise ALException('Error calling ual_end_action().', status) 
   return 0, [] 
  # Heterogeneous IDS #
  if homogenousTime == IDS_TIME_MODE_HETEROGENEOUS:
   status = ull.ual_end_action(ctx)
   if status != 0:
    raise ALException('ERROR calling ual_end_action().', status) 
   return 0, [np.NaN] 

  # Time independent IDS #
  if homogenousTime == IDS_TIME_MODE_INDEPENDENT:
   status = ull.ual_end_action(ctx)
   if status != 0:
    raise ALException('ERROR calling ual_end_action().', status) 
   return 0, [np.NINF] 

  # Get global time
  timeList = []
  status, data = ull.ual_read_data_array(ctx, "time", "/time", DOUBLE_DATA, 1)
  if status != 0:
   raise ALException('ERROR: Time vector cannot be read.', status)
  if data is not None:
   timeList = data
  status = ull.ual_end_action(ctx)
  if status != 0:
   raise ALException('ERROR calling ual_end_action().', status) 
  return status,timeList
import time
class Foo(object):
    global time
    asdf = time
    def thing(self):
        return self

def asdfy():
    return Foo


class IDSStructure():
    _MAX_OCCURRENCES = None

    def getNodeType(cls):
        raise NotImplementedError

    def getMaxOccurrences(cls):
        raise NotImplementedError

    #def __deepcopy__(self, memo):
    #    raise NotImplementedError

    #def __copy__(self):
    #    raise NotImplementedError

    @loglevel
    def __init__(self, parent, structure_name, structure_xml):
        self._convert_ids_types = False
        self._name = structure_name
        self._base_path = structure_name
        self._idx = EMPTY_INT
        self._parent = parent
        self._children = []
        for child in structure_xml.getchildren():
            my_name = child.get('name')
            if self.depth == 1 and my_name not in ['ids_properties', 'vacuum_toroidal_field', 'code', 'time', 'time_slice']:
                # Only build these to KISS
                continue
            dbg_str = ' ' * (self.depth + 1) + '- ' + my_name
            logger.debug('{:42.42s} initialization'.format(dbg_str))
            self._children.append(my_name)
            my_data_type = child.get('data_type')
            if my_data_type == 'structure':
                child_hli = IDSStructure(self, my_name, child)
                setattr(self, my_name, child_hli)
            elif my_data_type == 'struct_array':
                #if my_name not in ['time_slice', 'coodinate_system']:
                #    continue
                child_hli = IDSStructArray(self, my_name, child)
                setattr(self, my_name, child_hli)
            else:
                tbp = child.get('timebasepath')
                setattr(self, my_name, create_leaf_container(my_name, my_data_type, parent=self, timebasepath=tbp))
        self._convert_ids_types = True

    @property
    def depth(self):
        my_depth = 0
        if hasattr(self, '_parent'):
            my_depth += 1 + self._parent.depth
        return my_depth

    @property
    def path(self):
        my_path = self._name
        if hasattr(self, '_parent'):
            my_path = self._parent.path + '/' + my_path
        return my_path

    def initIDS(self):
        raise NotImplementedError

    def copyValues(self, ids):
        """ Not sure what this should do. Well, copy values of a structure!"""
        raise NotImplementedError

    def __str__(self):
        return '%s("%s", %r)' % (type(self).__name__, self._name, self.value)

    def __setattr__(self, key, value):
        if not key.startswith('_') and hasattr(self, '_convert_ids_types') and self._convert_ids_types:
            # Convert IDS type on set time. Never try this for hidden attributes!
            if hasattr(self, key):
                attr = getattr(self, key)
            else:
                # Structure does not exist. It should have been pre-generated
                raise NotImplementedError('generating new structure from scratch')
                attr = create_leaf_container(key, no_data_type_I_guess, parent=self)
            if isinstance(attr, IDSStructure) and not isinstance(value, IDSStructure):
                raise Exception('Trying to set structure field {!s} with non-structure.'.format(key))

            try:
                attr.value = value
            except Exception as ee:
                raise
            else:
                object.__setattr__(self, key, attr)
        else:
            object.__setattr__(self, key, value)

    @loglevel
    def readTime(self, occurrence):
        raise NotImplementedError
        time = []
        path = None
        if occurrence == 0:
            path='equilibrium'
        else:
            path='equilibrium'+ '/' + str(occurrence)

        status, ctx = ull.ual_begin_global_action(self._idx.values, path, READ_OP)
        if status != 0:
             raise ALException('Error calling ual_begin_global_action() in readTime() operation', status)
    
        status, time = ull.ual_read_data_array(ctx, "time", "/time", DOUBLE_DATA, 1)
        if status != 0:
         raise ALException('ERROR: TIME cannot be read.', status) 
        status = ull.ual_end_action(ctx)
        if status != 0:
         raise ALException('Error calling ual_end_action() in readTime() operation', status) 
        return time

    @loglevel
    def get(self, ctx, homogeneousTime):
        if len(self._children) == 0:
            logger.warning('Trying to get structure "{!s}" with 0 children'.format(self._name))
        for child_name in self._children:
            dbg_str = ' ' * self.depth + '- ' + child_name
            logger.debug('{:53.53s} get'.format(dbg_str))
            child = getattr(self, child_name)
            if isinstance(child, IDSStructure):
                child.get(ctx, homogeneousTime)
                continue # Nested struct will handle setting attributes
            if isinstance(child, IDSPrimitive):
                status, data = child.get(ctx, homogeneousTime)
            else:
                logger.critical('Unknown type {!s} for field {!s}! Skipping'.format(
                    type(child), child_name))
            if status == 0 and data is not None:
                setattr(self, child_name, data)
            elif status != 0:
                logger.critical(
                    'Unable to get simple field {!s}, UAL return code {!s}'.format(
                        child_name, status))
            else:
                logger.debug(
                    'Unable to get simple field {!s}, seems empty'.format(child_name))


    @loglevel
    def getSlice(self, time_requested, interpolation_method, occurrence=0):
        #Retrieve full IDS data from the open database.
        raise NotImplementedError

    @loglevel
    def _getData(self, ctx, indexFrom, indexTo, homogeneousTime, nodePath, analyzeTime):
        """ A deeped way of getting data?? using 'traverser' whatever that is """
        raise NotImplementedError

    @loglevel
    def put(self, ctx, homogeneousTime):
        if len(self._children) == 0:
            logger.warning(
                'Trying to put structure {!s} without children to data store'.format(
                    self._name))
        for child_name in self._children:
            child = getattr(self, child_name)
            dbg_str = ' ' * self.depth + '- ' + child_name
            if child is not None:
                if not isinstance(child, IDSPrimitive):
                    logger.debug('{:53.53s} put'.format(dbg_str))
                child.put(ctx, homogeneousTime)

    @loglevel
    def putSlice(self, occurrence=0):
        #Store IDS data time slice to the open database.
        raise NotImplementedError

    @loglevel
    def deleteData(self, occurrence=0):
        #Delete full IDS data from the open database.
        logger.critical('Not deleting any data from storage, everything is temporary!')

    def setExpIdx(self, idx):
        raise NotImplementedError

    def setPulseCtx(self, ctx):
        context_store[ctx] = self.path
        self._idx = ctx

    def getPulseCtx(self):
        raise NotImplementedError

    def partialGet(self, dataPath, occurrence=0):
        raise NotImplementedError

    def getField(self, dataPath, occurrence=0):
        raise NotImplementedError

    def _getFromPath(self, dataPath,  occurrence, analyzeTime):
        #Retrieve partial IDS data without reading the full database content
        raise NotImplementedError

class IDSStructArray(IDSStructure):
    def getNodeType(cls):
        raise NotImplementedError

    def getTimeBasePath(self, homogeneousTime, ignore_nbc_change=1):
        # TODO: This seems to be always "" for some reason
        strTimeBasePath = ""
        return strTimeBasePath

    @staticmethod
    def getBackendInfo(parentCtx, index, homogeneousTime):
       raise NotImplementedError

    @staticmethod
    def getAoSElement():
       raise NotImplementedError

    def __init__(self, parent, structure_name, structure_xml, base_path_in='element'):
        self._base_path = base_path_in
        self._convert_ids_types = False
        self._name = structure_name
        self._parent = parent
        # Initialize with an 1-lenght list of contained structure
        self._element_structure = IDSStructure(self, structure_name, structure_xml)
        self._element_structure._convert_ids_types = False # Enable converting after copy
        self._element_structure._parent = None # Set parent after copy; parent itself should not be copied
        self.value = []
        # For now, populate attributes with mirrors of their internal elements. Should probably be smarter!
        #for child_name in el._children:
        #    setattr(self, child_name, None)

        self._convert_ids_types = True

    def __setattr__(self, key, value):
        object.__setattr__(self, key, value)

    def __getattr__(self, key):
        object.__getattribute__(self, key)

    def __getitem__(self, item):
        return self.value[item]

    def __setitem__(self, item, value):
        if hasattr(self, '_convert_ids_types') and self._convert_ids_types:
            # Convert IDS type on set time. Never try this for hidden attributes!
            if item in self.value:
                struct = self.value[item]
                try:
                    struct.value = value
                except Exception as ee:
                    raise
        self.value[item] = value

    def append(self, elt):
        """Append elements to the end of the array of structures.

        Parameters
        ----------
        """
        if not isinstance(elt,list):
            elements = [elt]
        else:
            elements = elt
        for e in elements:
            # Just blindly append for now
            self.value.append(e)
            #else:
            #    raise TypeError('elt was expected to be instance of '+str(process__structArrayElement))

    def resize(self, nbelt, keep=False):
        """Resize an array of structures.

        Parameters
        ----------
        nbelt : int
            The number of elements for the targeted array of structure, 
            which can be smaller or bigger than the size of the current 
            array if it already exists.
        keep : bool, optional
            Specifies if the targeted array of structure should keep 
            existing data in remaining elements after resizing it.
        """
        if not keep:
            self.value = []
        cur = len(self.value)
        if nbelt > cur:
            new_els = []
            for ii in range(nbelt - cur):
                new_el = copy.deepcopy(self._element_structure)
                new_el._parent = self
                new_el._convert_ids_types = True
                new_els.append(new_el)
            self.append(new_els)
        elif nbelt < cur:
            raise NotImplementedError
            for i in range(nbelt, cur):
                self.value.pop()
        elif not keep:#case nbelt = cur
            raise NotImplementedError
            self.append([process_charge_state__structArrayElement(self._base_path) for i in range(nbelt)])

    def _getData(self, aosCtx, indexFrom, indexTo, homogeneousTime, nodePath, analyzeTime):
       raise NotImplementedError

    @loglevel
    def get(self, parentCtx, homogeneousTime):
        timeBasePath = self.getTimeBasePath(homogeneousTime, 0)
        nodePath = self._name
        status, aosCtx, size = ull.ual_begin_arraystruct_action(parentCtx, nodePath, timeBasePath, 0)
        context_store[aosCtx] = context_store[parentCtx] + '/' + nodePath
        if status < 0:
            raise ALException('ERROR: ual_begin_arraystruct_action failed for "process/products/element"', status)

        if size < 1:
            return
        self.resize(size)
        for i in range(size):
            self.value[i].get(aosCtx, homogeneousTime)
            ull.ual_iterate_over_arraystruct(aosCtx, 1)

        context_store.pop(aosCtx)
        if aosCtx > 0:
            ull.ual_end_action(aosCtx)

    def put(self, parentCtx, homogeneousTime):
        timeBasePath = self.getTimeBasePath(homogeneousTime)
        # TODO: This might be to simple for array of array of structures
        nodePath = self._name
        status, aosCtx, size = ull.ual_begin_arraystruct_action(parentCtx, nodePath, timeBasePath, len(self.value))
        context_store[aosCtx] = context_store[parentCtx] + '/' + nodePath
        if status != 0 or aosCtx < 0:
            raise ALException('ERROR: ual_begin_arraystruct_action failed for "{!s}"'.format(self._name), status)

        for i in range(size):
            dbg_str = ' ' * self.depth + '- [' + str(i) + ']'
            logger.debug('{:53.53s} put'.format(dbg_str))
            self.value[i].put(aosCtx, homogeneousTime)
            status = ull.ual_iterate_over_arraystruct(aosCtx, 1)
            if status != 0:
                raise ALException('ERROR: ual_iterate_over_arraystruct failed for "{!s}"'.format(self._name), status)

        context_store.pop(aosCtx)
        status = ull.ual_end_action(aosCtx)
        if status != 0:
            raise ALException('ERROR: ual_end_action failed for "{!s}"'.format(self._name), status)

    @property
    def path(self):
        my_path = ''
        if hasattr(self, '_parent'):
            my_path = self._parent.path
        return my_path

class IDSToplevel(IDSStructure):
    """ This is any IDS Structure which has ids_properties as child node

    At minium, one should fill ids_properties/homogeneous_time
    IF a quantity is filled, the coordinates of that quantity must be filled as well
    """

    @loglevel
    def readHomogeneous(self, occurrence):
        """ Read the value of homogeneousTime.

        Returns:
            0: IDS_TIME_MODE_HETEROGENEOUS; Dynamic nodes may be asynchronous, their timebase is located as indicted in the "Coordinates" column of the documentation
            1: IDS_TIME_MODE_HOMOGENEOUS; All dynamic nodes are synchronous, their common timebase is the "time" node that is the child of the nearest parent IDS
            2: IDS_TIME_MODE_INDEPENDENT; No dynamic node is filled in the IDS (dynamic nodes _will_ be skipped by the Access Layer)
        """
        homogeneousTime = IDS_TIME_MODE_UNKNOWN
        if occurrence == 0:
            path = self._name
        else:
            path = self._name + '/' + str(occurrence)

        status, ctx = ull.ual_begin_global_action(self._idx, path, READ_OP)
        if status != 0:
            raise ALException('Error calling ual_begin_global_action() in readHomogeneous() operation', status)

        status, homogeneousTime = ull.ual_read_data(ctx, "ids_properties/homogeneous_time", "", INTEGER_DATA, 0)
        if status != 0:
            raise ALException('ERROR: homogeneous_time cannot be read.', status) 
        status = ull.ual_end_action(ctx)
        if status != 0:
            raise ALException('Error calling ual_end_action() in readHomogeneous() operation', status) 
        return homogeneousTime

    @loglevel
    def read_data_dictionary_version(self, occurrence):
        data_dictionary_version = ''
        path = self._name
        if occurrence != 0:
            path += '/' + str(occurrence)

        status, ctx = ull.ual_begin_global_action(self._idx, path, READ_OP)
        if status != 0:
            raise ALException('Error calling ual_begin_global_action() in read_data_dictionary_version() operation', status)

        status, data_dictionary_version = ull.ual_read_data_string(ctx, "ids_properties/version_put/data_dictionary", "", CHAR_DATA, 1)
        if status != 0:
            raise ALException('ERROR: data_dictionary_version cannot be read.', status) 
        status = ull.ual_end_action(ctx)
        if status != 0:
            raise ALException('Error calling ual_end_action() in read_data_dictionary_version() operation', status) 
        return data_dictionary_version

    @loglevel
    def get(self, occurrence=0, **kwargs):
        path = None
        if occurrence == 0:
            path='equilibrium'
        else:
            path='equilibrium'+ '/' + str(occurrence)

        homogeneousTime = self.readHomogeneous(occurrence)
        if homogeneousTime == IDS_TIME_MODE_UNKNOWN:
            logger.error('Unknown time mode {!s}, stop getting of {!s}'.format(
                homogeneousTime, self._name))
            return
        data_dictionary_version = self.read_data_dictionary_version(occurrence)

        status, ctx = ull.ual_begin_global_action(self._idx, path, READ_OP)
        if status != 0:
          raise ALException('Error calling ual_begin_global_action() for equilibrium', status)
        context_store[ctx] = self.path

        logger.debug('{:53.53s} get'.format(self._name))
        super().get(ctx, homogeneousTime, **kwargs)

        status = ull.ual_end_action(ctx)
        context_store.pop(ctx)
        if status != 0:
            raise ALException('Error calling ual_end_action() for {!s}'.format(self._name), status)

    @loglevel
    def put(self, occurrence=0):
        # Store full IDS data to the open database.
        path = None
        homogeneousTime = 2
        if occurrence == 0:
            path = self._name
        else:
            path = self._name + '/' + str(occurrence)

        homogeneousTime = self.ids_properties.homogeneous_time.value
        if homogeneousTime == IDS_TIME_MODE_UNKNOWN:
            logger.warning("IDS equilibrium is found to be EMPTY (homogeneous_time undefined). PUT quits with no action.")
            return
        if homogeneousTime not in IDS_TIME_MODES:
            raise ALException('ERROR: ids_properties.homogeneous_time should be set to IDS_TIME_MODE_HETEROGENEOUS, IDS_TIME_MODE_HOMOGENEOUS or IDS_TIME_MODE_INDEPENDENT.')
        if homogeneousTime == IDS_TIME_MODE_HOMOGENEOUS and len(self.time)==0:
            raise ALException('ERROR: the IDS%time vector of an homogeneous_time IDS must have a non-zero length.')
        self.deleteData(occurrence)
        status, ctx = ull.ual_begin_global_action(self._idx, path, WRITE_OP)
        if status != 0:
            raise ALException('Error calling ual_begin_global_action() for {!s}'.format(self._name, status))

        context_store[ctx] = self.path
        for child_name in self._children:
            child = getattr(self, child_name)
            dbg_str = ' ' * self.depth + '- ' + child_name
            if not isinstance(child, IDSPrimitive):
                logger.debug('{:53.53s} put'.format(dbg_str))
            child.put(ctx, homogeneousTime)

        context_store.pop(ctx)
        status = ull.ual_end_action(ctx)
        if status != 0:
            raise ALException('Error calling ual_end_action() for {!s}'.format(self._name), status)

