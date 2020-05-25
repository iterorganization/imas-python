import abc
from IPython import embed
import numbers
import importlib
ull = importlib.import_module('ual_4_7_2._ual_lowlevel')
from pymas._libs.imasdef import MDSPLUS_BACKEND, OPEN_PULSE, DOUBLE_DATA, READ_OP, EMPTY_INT, FORCE_CREATE_PULSE, IDS_TIME_MODE_UNKNOWN,IDS_TIME_MODES, IDS_TIME_MODE_HOMOGENEOUS, WRITE_OP, CHAR_DATA, INTEGER_DATA
import numpy as np
import xml
import xml.etree.ElementTree as ET
import pymas._libs.hli_utils as hli_utils

class ALException(Exception):

   def __init__(self, message, errorStatus=None):
        if errorStatus is not None:
          Exception.__init__(self, message + "\nError status=" + str(errorStatus))
        else:
          Exception.__init__(self, message)

data_type_to_default = {
    'STR_0D': '',
    'INT_0D': EMPTY_INT,
}
ids_type_to_default = {
    'STR': '',
    'INT': EMPTY_INT,
}
python_type_to_ual = {
    str: 'STR_0D',
    int: 'INT_0D',
}
allowed_ids_types = ['STR_0D', 'INT_0D']

class IDSPrimitive():
    def __init__(self, name, ids_type, ndims, parent=None, value=None, on_wrong_type='warn'):
        if value is None:
            value = ids_type_to_default[ids_type]
        self._ids_type = ids_type
        self._ndims = ndims
        self._name = name
        self.value = value

    def put(self, ctx, homogeneousTime):
        if self._name is None:
            raise Exception('Location in tree undefined, cannot put in database')
        if self._ids_type == 'INT':
            scalar_type = 1
            data = hli_utils.HLIUtils.isScalarFinite(self.value, scalar_type)
        else:
            data = self.value

        status = ull.ual_write_data(ctx, 'ids_properties/' + self._name, '', data)
        if status != 0:
            raise ALException('Error writing field "{!s}"'.format(self._name))

    def get(self, ctx, homogeneousTime):
        strNodeRoot = 'ids_properties/'
        strNodePath = strNodeRoot + self._name
        strTimeBasePath = ''
        if self._ids_type == 'STR' and self._ndims == 0:
            status, data = ull.ual_read_data_string(ctx, strNodePath, strTimeBasePath, CHAR_DATA, 1)
        elif self._ids_type == 'INT' and self._ndims == 0:
            status, data = ull.ual_read_data_scalar(ctx, strNodePath, strTimeBasePath, INTEGER_DATA)
        else:
            print('Unknown type {!s} for field {!s}! Not sure now..'.format(type(child), child_name))
        return status, data


    def __repr__(self):
        return '%s("%s", %r)' % (type(self).__name__, self._name, self.value)

    @property
    def data_type(self):
        return '{!s}_{!s}D'.format(self._ids_type, self._ndims)


def create_leaf_container(name, data_type, **kwargs):
    ids_type, ids_dims = data_type.split('_')
    ndims = int(ids_dims[:-1])
    return IDSPrimitive(name, ids_type, ndims, **kwargs)

def python_to_ids_type(value):
    if isinstance(value, str):
        ids_type = 'STR'
        ndims = 0
    elif isinstance(value, int):
        ids_type = 'INT'
        ndims = 0
    else:
        print('Unknown python type {!s}', type(value))
        embed()
    return ids_type, ndims


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
            return tuple(type(self)(x) for x in result)
        elif method == 'at':
            # no return value
            return None
        else:
            # one return value
            return type(self)(result)

class IDSRoot():

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
  for ids in root:
      my_name = ids.get('name')
      if my_name is None:
          continue
      # Only build for equilibrium to KISS
      if my_name != 'equilibrium':
          continue
      self._children.append(my_name)
      setattr(self, my_name, IDSToplevel(my_name, ids))
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

    def __deepcopy__(self, memo):
        raise NotImplementedError

    def __copy__(self):
        raise NotImplementedError

    def __init__(self, structure_name, structure_xml):
        self._convert_ids_types = False
        self._name = structure_name
        self._children = []
        for child in structure_xml.getchildren():
            my_name = child.get('name')
            print('IDSStructure name', my_name)
            self._children.append(my_name)
            my_data_type = child.get('data_type')
            if my_data_type == 'structure':
                child_hli = IDSStructure(my_name, child)
                setattr(self, my_name, child_hli)
            elif my_data_type in allowed_ids_types:
                setattr(self, my_name, create_leaf_container(my_name, my_data_type, parent=self))
                self._children.append(my_name)
            else:
                print('What to do? Unknown type!', my_data_type)
                embed()
        self._convert_ids_types = True


    def initIDS(self):
        raise NotImplementedError

    def copyValues(self, ids):
        """ Not sure what this should do. Well, copy values of a structure!"""
        raise NotImplementedError

    def __str__(self, depth=0):
        """ Return a nice string representation """
        raise NotImplementedError

    def __setattr__(self, key, value):
        if hasattr(self, '_convert_ids_types') and self._convert_ids_types:
            ids_type, ndims = python_to_ids_type(value)
            if hasattr(self, key):
                attr = getattr(self, key)
            else:
                attr = IDSPrimitive(ids_type, ndims, name=key, parent=self)
            if isinstance(attr, IDSStructure) and not isinstance(value, IDSStructure):
                print('Trying to set structure field with non-structure, not converting anything')
                object.__setattr__(self, key, value)
                return
            if ids_type != attr._ids_type:
                raise ValueError('Cannot set key {!s} with value {!s}, would change type'.format(key, value))
            if ndims != attr._ndims:
                raise ValueError('Cannot set key {!s} with value {!s}, would change ndims'.format(key, value))

            attr.value = value
            object.__setattr__(self, key, attr)
        else:
            object.__setattr__(self, key, value)

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

    def get(self, ctx, homogeneousTime):
        for child_name in self._children:
            child = getattr(self, child_name)
            if isinstance(child, IDSPrimitive):
                status, data = child.get(ctx, homogeneousTime)
            else:
                print('Unknown type {!s} for field {!s}! Not sure now..'.format(type(child), child_name))
                embed()
            if status == 0 and data is not None:
                setattr(self, child_name, data)
            else:
                print('Warning! Unable to have grabbed simple type {!s}'.format(child_name))

    def getSlice(self, time_requested, interpolation_method, occurrence=0):
        #Retrieve full IDS data from the open database.
        raise NotImplementedError

    def _getData(self, ctx, indexFrom, indexTo, homogeneousTime, nodePath, analyzeTime):
        """ A deeped way of getting data?? using 'traverser' whatever that is """
        raise NotImplementedError

    def put(self, ctx, homogeneousTime):
        homogenousTime = None
        # Do not check if type is valid, just go for it
        for child_name in self._children:
            child = getattr(self, child_name)
            if isinstance(child, IDSStructure):
                print('Not yet putting IDS structures')
                continue
            elif not hli_utils.HLIUtils.isTypeValid(child, child_name, child.data_type):
                print('child {!s} of type {!s} has an invalid type, skip'.format(child_name, type(child)))
                continue
            if child is not None and child != '':
                print('Trying to write {!s}'.format(child_name))
                child.put(ctx, homogenousTime)

                if isinstance(child, int):
                    scalar_type = 1
                    data = hli_utils.HLIUtils.isScalarFinite(child, scalar_type)
                else:
                    data = child


    def putSlice(self, occurrence=0):
        #Store IDS data time slice to the open database.
        raise NotImplementedError

    def deleteData(self, occurrence=0):
        #Delete full IDS data from the open database.
        print('Not deleting data, everything is temporary atm!')

    def setExpIdx(self, idx):
        raise NotImplementedError

    def setPulseCtx(self, ctx):
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

class IDSToplevel(IDSStructure):
    """ This is any IDS Structure which has ids_properties as child node

    At minium, one should fill ids_properties/homogeneous_time
    IF a quantity is filled, the coordinates of that quantity must be filled as well
    """
    def __init__(self, ids_name, ids_xml_element):
        self.__name__ = ids_name
        self._base_path = ids_name
        self._idx = EMPTY_INT
        self._children = []
        for child in ids_xml_element.getchildren():
            my_name = child.get('name')
            if my_name != 'ids_properties':
                # Only build ids_properties to KISS
                continue
            my_data_type = child.get('data_type')
            self._children.append(my_name)
            if my_data_type == 'structure':
                child_hli = IDSStructure(my_name, child)
            else:
                print('Unknown type ', my_data_type)
                embed()
            setattr(self, my_name, child_hli)
        #self.initIDS()

    def readHomogeneous(self, occurrence):
        """ Read the value of homogeneousTime.

        Returns:
            0: IDS_TIME_MODE_HETEROGENEOUS; Dynamic nodes may be asynchronous, their timebase is located as indicted in the "Coordinates" column of the documentation
            1: IDS_TIME_MODE_HOMOGENEOUS; All dynamic nodes are synchronous, their common timebase is the "time" node that is the child of the nearest parent IDS
            2: IDS_TIME_MODE_INDEPENDENT; No dynamic node is filled in the IDS (dynamic nodes _will_ be skipped by the Access Layer)
        """
        homogeneousTime = IDS_TIME_MODE_UNKNOWN
        path = self.__name__
        if occurrence != 0:
            path += '/' + str(occurrence)

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

    def read_data_dictionary_version(self, occurrence):
        data_dictionary_version = ''
        path = self.__name__
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

    def get(self, occurrence=0):
        path = None
        if occurrence == 0:
            path='equilibrium'
        else:
            path='equilibrium'+ '/' + str(occurrence)

        homogeneousTime = self.readHomogeneous(occurrence)
        if homogeneousTime == IDS_TIME_MODE_UNKNOWN:
            print('Unknown time mode, not getting')
            return
        data_dictionary_version = self.read_data_dictionary_version(occurrence)

        status, ctx = ull.ual_begin_global_action(self._idx, path, READ_OP)
        if status != 0:
          raise ALException('Error calling ual_begin_global_action() for equilibrium', status)

        for child_name in self._children:
            print('Trying to grab {!s}'.format(child_name))
            child = getattr(self, child_name)
            child.get(ctx, homogeneousTime)

    def put(self, occurrence=0):
        # Store full IDS data to the open database.
        path = None
        homogeneousTime = 2
        if occurrence == 0:
            path = self.__name__
        else:
            path = self.__name__ + '/' + str(occurrence)

        homogeneousTime = self.ids_properties.homogeneous_time.value
        if homogeneousTime == IDS_TIME_MODE_UNKNOWN:
            print("IDS equilibrium is found to be EMPTY (homogeneous_time undefined). PUT quits with no action.")
            return
        if homogeneousTime not in IDS_TIME_MODES:
            raise ALException('ERROR: ids_properties.homogeneous_time should be set to IDS_TIME_MODE_HETEROGENEOUS, IDS_TIME_MODE_HOMOGENEOUS or IDS_TIME_MODE_INDEPENDENT.')
        if homogeneousTime == IDS_TIME_MODE_HOMOGENEOUS and len(self.time)==0:
            raise ALException('ERROR: the IDS%time vector of an homogeneous_time IDS must have a non-zero length.')
        self.deleteData(occurrence)
        status, ctx = ull.ual_begin_global_action(self._idx, path, WRITE_OP)
        if status != 0:
            raise ALException('Error calling ual_begin_global_action() for {!s}'.format(self.__name__, status))

        for child_name in self._children:
            child = getattr(self, child_name)
            if isinstance(child, IDSStructure):
                child.put(ctx, homogeneousTime)
