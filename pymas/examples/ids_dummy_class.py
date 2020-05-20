import sys
import os

from IPython import embed


if __name__ == '__main__':
    root_path = os.path.abspath(os.path.join(__file__, '../../..'))
    sys.path.insert(0, root_path)
    from pymas.ids_classes import *
    class DummyIDS(IDSToplevel):
        def initIDS(self):
            self._ids_time = numpy.zeros(0, numpy.float64, order='C')

            self.ids_properties = ids_properties__structure('ids_properties')
            self.z_n = EMPTY_DOUBLE
            self.z_n_error_upper = EMPTY_DOUBLE
            self.z_n_error_lower = EMPTY_DOUBLE
            self.z_n_error_index = EMPTY_INT
            self.a = EMPTY_DOUBLE
            self.a_error_upper = EMPTY_DOUBLE
            self.a_error_lower = EMPTY_DOUBLE
            self.a_error_index = EMPTY_INT
            self.process = process__structArray('process')
            self.coordinate_system = coordinate_system__structArray('coordinate_system')
            self.release = release__structArray('release')
            self.code = code__structure('code')
            self.time = numpy.zeros(0, numpy.float64, order='C')
            self.setPulseCtx(self._idx)

        def copyValues(self, ids):
            self.ids_properties = copy.deepcopy(ids.ids_properties)
            self.z_n = ids.z_n
            self.z_n_error_upper = ids.z_n_error_upper
            self.z_n_error_lower = ids.z_n_error_lower
            self.z_n_error_index = ids.z_n_error_index
            self.a = ids.a
            self.a_error_upper = ids.a_error_upper
            self.a_error_lower = ids.a_error_lower
            self.a_error_index = ids.a_error_index
            self.process = copy.deepcopy(ids.process)
            self.coordinate_system = copy.deepcopy(ids.coordinate_system)
            self.release = copy.deepcopy(ids.release)
            self.code = copy.deepcopy(ids.code)
            self.time = ids.time

        def __str__(self, depth=0):
            space = depth*'\t'
            ret = space + 'class amns_data\n'
            ret = ret + space + 'Attribute ids_properties\n ' + self.ids_properties.__str__(depth+1)
            ret = ret + space + 'Attribute z_n: ' + str(self.z_n) + u'\n'
            ret = ret + space + 'Attribute z_n_error_upper: ' + str(self.z_n_error_upper) + u'\n'
            ret = ret + space + 'Attribute z_n_error_lower: ' + str(self.z_n_error_lower) + u'\n'
            ret = ret + space + 'Attribute a: ' + str(self.a) + u'\n'
            ret = ret + space + 'Attribute a_error_upper: ' + str(self.a_error_upper) + u'\n'
            ret = ret + space + 'Attribute a_error_lower: ' + str(self.a_error_lower) + u'\n'
            ret = ret + space + 'Attribute process\n ' + self.process.__str__(depth+1)
            ret = ret + space + 'Attribute coordinate_system\n ' + self.coordinate_system.__str__(depth+1)
            ret = ret + space + 'Attribute release\n ' + self.release.__str__(depth+1)
            ret = ret + space + 'Attribute code\n ' + self.code.__str__(depth+1)
            s = self.time.__str__()
            ret = ret + space + 'Attribute time\n' + space + s.replace('\n', '\n'+space) + '\n'
            return ret

        def get(self, occurence=0):
            self.initIDS()
            isnumeric(occurrence)
            if occurrence == 0:
                path='amns_data'
            else:
                path='amns_data'+ '/' + str(occurrence)

            status, ctx = ull.ual_begin_global_action(self._idx, path, READ_OP)
            if status != 0:
                raise ALException('Error calling ual_begin_global_action() for amns_data', status)

            # Do not try to read if IDS_TIME_MODE_UNKNOWN
            homogeneousTime = self.readHomogeneous(ctx)
            if homogeneousTime == IDS_TIME_MODE_UNKNOWN:
                ull.ual_end_action(ctx)
                return
            HLIUtils.data_dictionary_version = self.read_data_dictionary_version(ctx)

            # Then one-by-one grab the children. I kept:

            # Grabbing ids_properties, this uses python API, so use .get
            #### ids_properties : ids_properties : structure : 
            self.ids_properties.get(ctx, homogeneousTime)

            # A leaf which is a primitive type, use ual (or something else)

            #### z_n : z_n : FLT_0D : static
            strNodePath = "z_n"

            strTimeBasePath = ""

            status, data = ull.ual_read_data_scalar(ctx, strNodePath, strTimeBasePath, DOUBLE_DATA)
            if status == 0 and data is not None: 
                self.z_n = data

            # A struct array again! Use native API (gooooood!)
            #### [AoS 1] : coordinate_system : coordinate_system : struct_array : 
            self.coordinate_system.get(ctx, homogeneousTime)

            # Something dynamic needs some special 'timebasepath' magic
            #### time : time : flt_1d_type : dynamic
            strNodePath = "time"

            if homogeneousTime==IDS_TIME_MODE_HOMOGENEOUS:
                strTimeBasePath="/time"
            else:
                strTimeBasePath="time"

            if homogeneousTime != IDS_TIME_MODE_INDEPENDENT:
                status, data = ull.ual_read_data_array(ctx, strNodePath, strTimeBasePath, DOUBLE_DATA, 1)
                if status == 0 and data is not None: 
                    self.time = data

            # Anmd finally check if all went well
            status = ull.ual_end_action(ctx)
            if status != 0:
                raise ALException('Error calling ual_end_action() for amns_data', status)

        def get(self, occurrence=0):
            strFullNodeName = nodePath[0]
            strNodeName, nodeIndices = Traverser.parseName(strFullNodeName)


            #### ids_properties : ids_properties : structure : 
            if strNodeName == 'ids_properties':
             if len(nodePath) == 1:
              self.ids_properties.get(ctx, homogeneousTime==IDS_TIME_MODE_HOMOGENEOUS)
              return self.ids_properties
             else:
              return self.ids_properties._getData(ctx, homogeneousTime, nodePath[1:], analyzeTime)


            #### z_n : z_n : FLT_0D : static
            if strNodeName == 'z_n':
             strNodePath = "z_n"

             strTimeBasePath = ""

             status, data = ull.ual_read_data_scalar(ctx, strNodePath, strTimeBasePath, DOUBLE_DATA)
             if status == 0: 
              if data is not None and type(data) == np.ndarray :
               dataRange = Traverser.parseArrayIndices(nodeIndices)
               if dataRange is not None:
                data = data[dataRange]
              return data
             else: 
              raise ALException('ERROR: Requested field ["z_n"] cannot be read.')


             #### a_error_index : a_error_index : int_type : constant
             if strNodeName == 'a_error_index':
                strNodePath = "a_error_index"

                strTimeBasePath = ""

                status, data = ull.ual_read_data_scalar(ctx, strNodePath, strTimeBasePath, INTEGER_DATA)
                if status == 0: 
                 if data is not None and type(data) == np.ndarray :
                  dataRange = Traverser.parseArrayIndices(nodeIndices)
                  if dataRange is not None:
                   data = data[dataRange]
                 return data
                else: 
                 raise ALException('ERROR: Requested field ["a_error_index"] cannot be read.')

             #### [AoS 1] : process : process : struct_array : 
             if strNodeName == 'process':
              raise ALException('INTERNAL ERROR: Requested AOS ["process"] cannot be read from this level.')

             #### [AoS 1] : coordinate_system : coordinate_system : struct_array : 
             if strNodeName == 'coordinate_system':
              raise ALException('INTERNAL ERROR: Requested AOS ["coordinate_system"] cannot be read from this level.')

             #### code : code : structure : 
             if strNodeName == 'code':
              if len(nodePath) == 1:
               self.code.get(ctx, homogeneousTime==IDS_TIME_MODE_HOMOGENEOUS)
               return self.code
              else:
               return self.code._getData(ctx, homogeneousTime, nodePath[1:], analyzeTime)

        def getSlice(self, time_requested, interpolation_method, occurrence=0):
            #Retrieve IDS data time slice from the open database.
            # Similar to get, but for a timeslice
            raise NotImplementedError
            self.initIDS()
            isnumeric(occurrence)
            if occurrence == 0:
                path='amns_data'
            else:
                path='amns_data'+ '/' + str(occurrence)


            status, ctx = ull.ual_begin_slice_action(self._idx, path, READ_OP, time_requested, interpolation_method)
            if status != 0:
              raise ALException('Error calling ual_begin_slice_action() for amns_data', status)

            homogeneousTime = self.readHomogeneous(ctx)
            HLIUtils.data_dictionary_version = self.read_data_dictionary_version(ctx)


            #### ids_properties : ids_properties : structure : 
            self.ids_properties.get(ctx, homogeneousTime)

            #### z_n : z_n : FLT_0D : static
            strNodePath = "z_n"

            strTimeBasePath = ""

            status, data = ull.ual_read_data_scalar(ctx, strNodePath, strTimeBasePath, DOUBLE_DATA)
            if status == 0 and data is not None: 
             self.z_n = data


            #### time : time : flt_1d_type : dynamic
            strNodePath = "time"

            if homogeneousTime==IDS_TIME_MODE_HOMOGENEOUS:
             strTimeBasePath="/time"
            else:
             strTimeBasePath="time"

            if homogeneousTime != IDS_TIME_MODE_INDEPENDENT:
             status, data = ull.ual_read_data_array(ctx, strNodePath, strTimeBasePath, DOUBLE_DATA, 1)
             if status == 0 and data is not None: 
              self.time = data

            status = ull.ual_end_action(ctx)
            if status != 0:
             raise ALException('Error calling ual_end_action() for amns_data', status)

    dummy = DummyIDS()
    # MVP, get a slice
    # So for example be able to run
    # import pymas as imas
    # input = imas.ids(shot,run_in)
    # input.open_env(input_user_or_path,input_database,’3’)
    # input.equilibrium.getSlice(time_slice, 1)
    import pymas as imas
    inp = imas.ids
    inp.open_env(input_user_or_path, input_database, '3')
    embed()
