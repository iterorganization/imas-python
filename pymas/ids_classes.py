import abc
class IDSRoot():
 def __init__(self, s=-1, r=-1, rs=-1, rr=-1):
  self.shot = s
  self.refShot = rs
  self.run = r
  self.refRun = rr
  self.treeName = 'ids'
  self.connected = False
  self.expIdx = -1
  self.ddunits = DataDictionaryUnits()
  self.hli_utils = HLIUtils()
  self.amns_data = amns_data.amns_data()
  self.barometry = barometry.barometry()
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
  self.amns_data.setPulseCtx(ctx)
  # Etc. etc for all other IDSs

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

class IDSToplevel():
    _MAX_OCCURRENCES = None
    @abc.abstractmethod
    def __init__():
        return

    @abc.abstractclassmethod
    def getNodeType(cls):
        return

    @abc.abstractclassmethod
    def getMaxOccurrences(cls):
        return

    @abc.abstractmethod
    def __deepcopy__(self, memo):
        return

    @abc.abstractmethod
    def __copy__(self):
        return

    @abc.abstractmethod
    def __init__(self):
        return

    @abc.abstractmethod
    def initIDS(self):
        return

    @abc.abstractmethod
    def copyValues(self, ids):
        """ Not sure what this should do"""
        return

    @abc.abstractmethod
    def __str__(self, depth=0):
        """ Return a nice string representation """
        return

    def readHomogeneous(self, ctx):
        """ Read the value of homogeneousTime """
        raise NotImplementedError
        homogeneousTime = IDS_TIME_MODE_UNKNOWN
        status, homogeneousTime = ull.ual_read_data(ctx, "ids_properties/homogeneous_time", "", INTEGER_DATA, 0)
        if status != 0:
            raise ALException('ERROR: homogeneous_time cannot be read.', status) 
        return homogeneousTime

    def read_data_dictionary_version(self, ctx):
        """ Read the value of the DD version"""
        raise NotImplementedError
        data_dictionary_version = ''
        status, data_dictionary_version = ull.ual_read_data_string(ctx, "ids_properties/version_put/data_dictionary", "", CHAR_DATA, 1)
        if status != 0:
            raise ALException('ERROR: data_dictionary_version cannot be read.', status) 
        return data_dictionary_version

    def readTime(self, ctx):
        """ Read the value of /time, by convension the time coordinateversion"""
        raise NotImplementedError
        time = []
        status, time = ull.ual_read_data_array(ctx, "time", "/time", DOUBLE_DATA, 1)
        if status != 0:
            raise ALException('ERROR: TIME cannot be read.', status) 
        return time


    @abc.abstractmethod
    def get(self, occurrence=0):
        #Retrieve full IDS data from the open database.
        return

    @abc.abstractmethod
    def _getData(self, ctx, indexFrom, indexTo, homogeneousTime, nodePath, analyzeTime):
        """ A deeped way of getting data?? using 'traverser' whatever that is """
        return
    def put(self, occurrence=0):
        #Store full IDS data to the open database.
        raise NotImplementedError

    def putSlice(self, occurrence=0):
        #Store IDS data time slice to the open database.
        raise NotImplementedError

    def deleteData(self, occurrence=0):
        #Delete full IDS data from the open database.
        raise NotImplementedError

    def setExpIdx(self, idx):
        raise NotImplementedError

    def setPulseCtx(self, ctx):
        raise NotImplementedError

    def getPulseCtx(self):
        raise NotImplementedError

    def partialGet(self, dataPath, occurrence=0):
        raise NotImplementedError

    def getField(self, dataPath, occurrence=0):
        raise NotImplementedError

    def _getFromPath(self, dataPath,  occurrence, analyzeTime):
        #Retrieve partial IDS data without reading the full database content
        raise NotImplementedError
