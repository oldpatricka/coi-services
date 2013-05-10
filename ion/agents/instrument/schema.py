#!/usr/bin/env python

"""
from ion.agents.instrument.schema import get_schemna, pp_schema
pp_schema()
x = get_schemna()
"""


import json

from ion.agents.alerts.alerts import get_alerts_schema
from ion.agents.instrument.instrument_agent import InstrumentAgentCapability
from ion.agents.instrument.instrument_agent import InstrumentAgentState
from ion.agents.instrument.driver_process import DriverProcessType
from interface.objects import DeviceStatusType
from interface.objects import AggregateStatusType
from interface.objects import StreamAlertType

"""
"value" : {
    'parsed' : ['quality_flag', 'preferred_timestamp', 'temp',
    'density', 'port_timestamp', 'lon', 'salinity', 'pressure',
    'internal_timestamp', 'time', 'lat', 'driver_timestamp',
    'conductivity','ingestion_timestamp'],
'raw' : ['quality_flag', 'preferred_timestamp', 'port_timestamp',
    'lon', 'raw', 'internal_timestamp', 'time',
    'lat', 'driver_timestamp','ingestion_timestamp']
}
"""

COMMS_CONFIG = {
    "display_name" : "Driver Comms Config",
    "description" : "Driver communications configuration parameters.",
    "type" : {
        "addr" : {
            "display_name" : "Address",
            "description" : "Address of port agent process.",
            "required" : True,
            "type" : "str"
        },
        "port"  : {
            "display_name" : "Data port",
            "description" : "Port agent data port.",
            "required" : True,
            "type" : "int"
        },
        "cmd_port" : {
            "display_name" : "Command port",
            "description" : "Port agent command port.",
            "required" : True,
            "type" : "int"            
        }
    }
}

DRIVER_CONFIG = {
    "display_name" : "Driver Config",
    "description" : "Driver configuration parameters.",
    "type" : {
        "dvr_egg" : {
            "display_name" : "Driver egg",
            "description" : "URI of the driver egg.",
            "required" : True,
            "type" : "str"
        },
        "dvr_mod" : {
            "display_name" : "Driver module",
            "description" : "Module of the driver.",
            "required" : True,
            "type" : "str"
        },
        "dvr_cls" : {
            "display_name" : "Driver class",
            "description" : "Class of the driver.",
            "required" : True,
            "type" : "str"
        },
        "workdir" : {
            "display_name" : "Work directory",
            "description" : "Address of port agent process.",
            "required" : True,
            "type" : "str"
        },
        "process_type" : {
            "display_name" : "Address",
            "description" : "Address of port agent process.",
            "required" : True,
            "type" : "str",
            "valid_values" : [
                DriverProcessType.EGG,
                DriverProcessType.PYTHON_MODULE
            ]
        },
        "mi_repo" : {
            "display_name" : "Driver Repository",
            "description" : "Filesystem path of the driver repository if driver launched from a python module.",
            "required" : False,
            "type" : "str"     
        },
        "comms_config" : "/command_args/comms_config"
    }
}

ALERTS = get_alerts_schema()    

AGENT_SCHEMA_V1 = {
    "commands" : {
        InstrumentAgentCapability.INITIALIZE :
            {
                "display_name" : "Initialize",
                "description" : "Start the driver process.",
                "args" :
                    [
                        {
                            "required" : False,
                            "type" : "/command_args/driver_config"
                        }
                    ],
                "kwargs" : {}
            },
        InstrumentAgentCapability.GO_ACTIVE :
            {
                "display_name" : "Activate",
                "description" : "Activate device connection.",
                "args" : [],
                "kwargs" : {}
            },
        InstrumentAgentCapability.RUN :
            {
                "display_name" : "Run",
                "description" : "Enter command mode.",
                "args" : [],
                "kwargs" : {}
            },
        InstrumentAgentCapability.PAUSE :
            {
                "display_name" : "Pause",
                "description" : "Pause command mode.",
                "args" : [],
                "kwargs" : {}
            },
        InstrumentAgentCapability.RESUME :
            {
                "display_name" : "Resume",
                "description" : "Resume command mode.",
                "args" : [],
                "kwargs" : {}
            },
        InstrumentAgentCapability.CLEAR :
            {
                "display_name" : "Clear",
                "description" : "Stop the agent and go idle.",
                "args" : [],
                "kwargs" : {}
            },
        InstrumentAgentCapability.GO_INACTIVE :
            {
                "display_name" : "Deactivate",
                "description" : "Deactivate agent device connection.",
                "args" : [],
                "kwargs" : {}
            },
        InstrumentAgentCapability.GO_DIRECT_ACCESS :
            {
                "display_name" : "Direct Access",
                "description" : "Activate direct access mode.",
                "args" : [],
                "kwargs" : {}
            },
        InstrumentAgentCapability.GO_COMMAND :
            {
                "display_name" : "Go Command",
                "description" : "Deactivate direct access mode.",
                "args" : [],
                "kwargs" : {}
            },
        InstrumentAgentCapability.RESET :
            {
                "display_name" : "Reset",
                "description" : "Stop the driver process.",
                "args" : [],
                "kwargs" : {}
            }            
        },
    "parameters" : {
        "streams" :
            {
                "display_name" : "Data Streams",
                "description" : "Data streams and fields published by agent.",
                "visibility" : "READ_ONLY",
                "type" : "dict",
                "valid_values" : [{
                    "key" : {
                        "display_name" : "Stream Name",
                        "discription" : "Data stream published by agent.",
                        "type" : "str"                    
                     },
                    "value" : {
                        "display_name" : "Field Names",
                        "discription" : "List of data fields published by agent on the stream.",
                        "type" : "list",
                        "valid_values" : [
                            "str"
                            ]
                    }
                }]
            },
        "pubrate" :
            {
                "display_name" : "Stream Publication Rate",
                "description" : "Delay in seconds between stream granule publicaitons.",
                "visibility" : "READ_WRITE",
                "type" : "dict",
                "valid_values" : [{
                    "key" : {
                        "display_name" : "Stream Name",
                        "description" : "A valid stream name published by this agent.",
                        "type" : "str",
                        "valid_values" : [
                            "/parameters/streams/keys"
                            ]
                    },
                    "value" : {
                        "display_name" : "Publication Rate",
                        "description" : "Nonnegative publication rate in seconds.",
                        "type" : "float",
                        "minimum" : 0.0                        
                    }
                }]
            },
        "alerts" :
            {
                "display_name" : "Agent Alerts.",
                "description" : "Definition and status of agent alerts.",
                "visibility" : "READ_WRITE",
                "type" : "list",
                "valid_values" : [
                    "/alert_defs/values*",
                    "'set', /alert_defs/values*",
                    "'add', /alert_defs/values+",
                    "'remove', /parameters/alerts/alert_name+",
                    "'clear'"
                    ],
                "set_options" : {
                    "set" : {
                        "display_name" : "Set",
                        "description" : "Reset all alerts to the new definitions."
                    },
                    "add" : {
                        "display_name" : "Add",
                        "description" : "Add alerts to the existing set."
                    },
                    "remove" : {
                        "display_name" : "Remove",
                        "description" : "Remove alerts with the supplied names."
                    },
                    "clear" : {
                        "display_name" : "Clear",
                        "description" : "Clear all alerts."
                    }
                }
            },
        "aggstatus" :
            {
                "display_name" : "Aggregate Status.",
                "description" : "Aggregate status of agent functions.",
                "visibility" : "READ_ONLY",
                "type" : "dict",
                "valid_values" :[{
                    "key" : {
                        "type" : "enum",
                        "string_map" : AggregateStatusType._str_map,
                        "value_map" : AggregateStatusType._value_map
                        },
                    "value" : {
                        "type" : "enum",
                        "string_map" : DeviceStatusType._str_map,
                        "value_map" : DeviceStatusType._value_map
                        }                    
                    }]
                }
        },
    "states" : {
        InstrumentAgentState.UNINITIALIZED : {
            "display_name" : "Uninitialized",
            "description" : "The agent has no resource loaded."
            },
        InstrumentAgentState.INACTIVE : {
            "display_name" : "Inactive",
            "description" : "The agent is not connected to its resource."
            },
        InstrumentAgentState.IDLE : {
            "display_name" : "Idle",
            "description" : "The agent is connected and idle."
            },
        InstrumentAgentState.STOPPED : {
            "display_name" : "Stopped",
            "description" : "Agent command mode is paused."
            },
        InstrumentAgentState.COMMAND : {
            "display_name" : "Command",
            "description" : "Agent resource can accept interactive resource commands."
            },
        InstrumentAgentState.STREAMING : {
            "display_name" : "Streaming",
            "description" : "Agent resource is autostreaming data."
            },
        InstrumentAgentState.TEST : {
            "display_name" : "Test",
            "description" : "Agent resource conducting self test."
            },
        InstrumentAgentState.CALIBRATE : {
            "display_name" : "Calibrate",
            "description" : "Agent resource conducting self-calibration."
            },
        InstrumentAgentState.BUSY : {
            "display_name" : "Busy",
            "description" : "Agent resource is busy."
            },
        InstrumentAgentState.LOST_CONNECTION : {
            "display_name" : "Lost Connection",
            "description" : "The resource connection has been lost."
            },
        InstrumentAgentState.ACTIVE_UNKNOWN : {
            "display_name" : "Active Unknown",
            "description" : "The agent is connected but resource state is unknown."
            },
        },
    "command_args" : {
        "driver_config" : DRIVER_CONFIG,
        "comms_config" : COMMS_CONFIG
        },
    "alert_defs" : ALERTS
    }

def get_schema():
    return AGENT_SCHEMA_V1

def get_schema_json():
    return json.dumps(AGENT_SCHEMA_V1)
    
def pp_schema():
    print json.dumps(AGENT_SCHEMA_V1, indent=4)