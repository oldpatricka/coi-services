#!/usr/bin/env python

'''
@author David Stuebe <dstuebe@asascience.com>
@file ion/processes/data/vis_stream_publisher.py
@description A simple example process which publishes prototype ctd data for visualization

To Run:
bin/pycc --rel res/deploy/r2dm.yml
pid = cc.spawn_process(name='ctd_test',module='ion.processes.data.vis_stream_publisher',cls='SimpleCtdPublisher')

'''

from pyon.public import log

import time
import math
import random
import threading
import gevent

from pyon.service.service import BaseService
from pyon.ion.process import StandaloneProcess
from pyon.public import PRED,RT,Container, log, IonObject, StreamPublisherRegistrar
from interface.services.dm.ipubsub_management_service import PubsubManagementServiceClient
from interface.services.coi.iresource_registry_service import ResourceRegistryServiceClient
from prototype.sci_data.stream_defs import ctd_stream_packet, ctd_stream_definition

#Instrument related imports
from interface.services.sa.iinstrument_management_service import InstrumentManagementServiceClient
from interface.services.dm.iingestion_management_service import IngestionManagementServiceClient
from prototype.sci_data.stream_defs import ctd_stream_definition
from prototype.sci_data.stream_defs import SBE37_CDM_stream_definition, SBE37_RAW_stream_definition
from interface.services.sa.idata_acquisition_management_service import DataAcquisitionManagementServiceClient
from interface.services.sa.idata_product_management_service import IDataProductManagementService, DataProductManagementServiceClient
from interface.objects import HdfStorage, CouchStorage


# NetCDF related imports
from netCDF4 import Dataset
from datetime import datetime, timedelta
from netCDF4 import num2date, date2num


class VisStreamPublisher(StandaloneProcess):
    """
    VizStreamProducer emulates a stream source from a NetCDF file. It emits a record of data every few seconds on a
    stream identified by a routing key.

    """


    def on_init(self):
        log.debug("VizStreamProducer init. Self.id=%s" % self.id)

    def on_start(self):

        log.debug("VizStreamProducer start")
        self.interval = self.CFG.get('interval')
        self.data_source_name = self.CFG.get('name')
        self.dataset = self.CFG.get('dataset')

        # create a pubsub client and a resource registry client
        self.rrclient = ResourceRegistryServiceClient(node=self.container.node)
        self.pubsubclient = PubsubManagementServiceClient(node=self.container.node)

        # Dummy instrument related clients
        self.imsclient = InstrumentManagementServiceClient(node=self.container.node)
        self.damsclient = DataAcquisitionManagementServiceClient(node=self.container.node)
        self.dpclient = DataProductManagementServiceClient(node=self.container.node)
        self.IngestClient = IngestionManagementServiceClient(node=self.container.node)

        # create the pubsub client
        self.pubsubclient = PubsubManagementServiceClient(node=self.container.node)


        # Additional code for creating a dummy instrument

        # Set up the preconditions. Look for an existing ingestion config
        while True:
            log.warn("VisStreamPublisher:on_start: Waiting for an ingestion configuration to be available.")
            ingestion_cfgs, _ = self.rrclient.find_resources(RT.IngestionConfiguration, None, None, True)

            if len(ingestion_cfgs) > 0:
                break
            else:
                gevent.sleep(1)


        """
        # ingestion configuration parameters
        self.exchange_point_id = 'science_data'
        self.number_of_workers = 2
        self.hdf_storage = HdfStorage(relative_path='ingest')
        self.couch_storage = CouchStorage(datastore_name='test_datastore')
        self.XP = 'science_data'
        self.exchange_name = 'ingestion_queue'

        # Create ingestion configuration and activate it
        ingestion_configuration_id =  self.IngestClient.create_ingestion_configuration(
            exchange_point_id=self.exchange_point_id,
            couch_storage=self.couch_storage,
            hdf_storage=self.hdf_storage,
            number_of_workers=self.number_of_workers
        )
        print 'test_activateInstrument: ingestion_configuration_id', ingestion_configuration_id

        # activate an ingestion configuration
        ret = self.IngestClient.activate_ingestion_configuration(ingestion_configuration_id)
        log.debug("test_activateInstrument: activate = %s"  % str(ret))
        """

        # Create InstrumentModel
        instModel_obj = IonObject(RT.InstrumentModel, name=self.data_source_name, description=self.data_source_name, model_label=self.data_source_name)
        instModel_id = self.imsclient.create_instrument_model(instModel_obj)

        # Create InstrumentAgent. Maybe optional for the viz_data_producers
        #instAgent_obj = IonObject(RT.InstrumentAgent, name='agent007', description="SBE37IMAgent", driver_module="ion.services.mi.instrument_agent", driver_class="InstrumentAgent" )
        #instAgent_id = self.imsclient.create_instrument_agent(instAgent_obj)

        #assign instr model to agent
        #self.imsclient.assign_instrument_model_to_instrument_agent(instModel_id, instAgent_id)

        # Create InstrumentDevice
        instDevice_obj = IonObject(RT.InstrumentDevice, name=self.data_source_name, description=self.data_source_name, serial_number="12345" )

        instDevice_id = self.imsclient.create_instrument_device(instrument_device=instDevice_obj)
        self.imsclient.assign_instrument_model_to_instrument_device(instModel_id, instDevice_id)

        # create a stream definition for the data from the ctd simulator
        ctd_stream_def = SBE37_CDM_stream_definition()
        ctd_stream_def_id = self.pubsubclient.create_stream_definition(container=ctd_stream_def)

        print 'Creating new CDM data product with a stream definition'
        dp_obj = IonObject(RT.DataProduct,name=self.data_source_name,description='ctd stream test')
        data_product_id1 = self.dpclient.create_data_product(dp_obj, ctd_stream_def_id)

        self.damsclient.assign_data_product(input_resource_id=instDevice_id, data_product_id=data_product_id1)
        self.dpclient.activate_data_product_persistence(data_product_id=data_product_id1, persist_data=True, persist_metadata=True)

        print 'new dp_id = ', data_product_id1


        # Retrieve the id of the OUTPUT stream from the out Data Product
        stream_ids, _ = self.rrclient.find_objects(data_product_id1, PRED.hasStream, None, True)
        print 'Data product streams1 = ', stream_ids

        # register the current process as a publisher using the stream_id that was created for it
        #this_process = self.container.proc_manager.procs[self.id]
        publisher_registrar = StreamPublisherRegistrar(process=self, node=self.container.node)
        self.pub = publisher_registrar.create_publisher(stream_id=stream_ids[0])


        if self.dataset == 'sinusoidal':
            # initialize a sine wave generator
            self.sine_ampl = self.CFG.get('amplitude') # Amplitude in both directions
            self.samples = self.CFG.get('samples')
            self.sine_curr_deg = 0 # varies from 0 - 360
        else:
            # using NetCDF4	library to read up a .nc file
            ncFile = Dataset(self.dataset, 'r', format='NETCDF4')
            self.varList = ncFile.variables.keys()

            # force the data to be loaded up in memory since the netCDF library uses a lazy approach and
            # does not seem to respond to random seeks
            timeSteps = ncFile.variables['time'][:]

            self.varData = [[None] * len(self.varList)] * len(timeSteps)  # Create an empty list of lists for storing the data
            # Load up all the numerical variables into memory
            num = 0
            for i in self.varList:
                varObj = ncFile.variables[str(i)]

                # treat time as a one dimensional array, Everything else is two dimensional
                if i == 'time' or i == 'depth' or i == 'latitude' or i == 'longitude':
                    self.varData[num] = list([ float(e) for e in varObj[:] ])
                else :
                    self.varData[num] = list([ float(e) for e in varObj[0,:] ])

                num += 1


        self.count = 0

        # Threads become efficent Greenlets with gevent
        self.producer_proc = threading.Thread(target=self._trigger_func)
        self.producer_proc.start()


    def on_quit(self):
        log.debug("VizStreamProducer quit")

    def _trigger_func(self):

        # The main loop that generates realtime streams
        num = 0
        self.count = 0
        c = t = p = lat = lon = timestamp = 0.0
        while True:

            # Format a message string
            self.msgStr = ''

            # generate/prepare a record of data for every iteration
            if self.dataset == 'sinusoidal':
                self.sine_curr_deg = (self.count % self.samples) * 360 / self.samples
                self.msgStr = 'time = ' + str(self.count) +  ' ; Sine = ' + str(self.sine_ampl * math.sin(math.radians(self.sine_curr_deg)))
            else:
                for j in range(len(self.varList)):

                    if self.varList[j] == 'latitude' or self.varList[j] == 'longitude' or self.varList[j] == 'depth':
                        continue # some variables only have one value and do not vary with time

                    self.msgStr += str(self.varList[j]) + ' = ' + str(self.varData[j][num]) + ' ; '

            self.count = self.count + 1
            #msg = dict(num=self.msgStr)
            msg=self.msgStr
            self.pub.publish(msg)
            log.debug("{ %s }:Message %s published", self.data_source_name, num)
            num += 1
            time.sleep(1) # sleep for one second. Do not change this without changing other stuff above



