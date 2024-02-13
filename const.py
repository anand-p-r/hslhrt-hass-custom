"""Constants for the FMI Weather and Sensor integrations."""
import logging
from datetime import timedelta

_LOGGER = logging.getLogger(__package__)

DOMAIN = "hslhrt"
NAME = DEFAULT_NAME = "HSLHRT"
MANUFACTURER = "Helsinki Regional Transport Authority"

COORDINATOR = "coordinator"
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=1)
UNDO_UPDATE_LISTENER = "undo_update_listener"

BASE_URL = "https://api.digitransit.fi/routing/v1/routers/hsl/index/graphql"

NAME_CODE = "user_name_code"
STOP_CODE = "stop_code"
STOP_NAME = "stop_name"
STOP_GTFS = "stop_gtfs"
ROUTE = "route"
ROUTE_DEST = "route_destination"
DESTINATION = "destination"
ALL = "all"
ERROR = "err"
APIKEY = "apikey"

# Graphql variables
VAR_NAME_CODE = "name_code"
VAR_ID = "id"
VAR_SECS_LEFT = "sec_left_in_day"
VAR_CURR_EPOCH = "current_epoch"
VAR_LIMIT = "limit"

# Dict keys
DICT_KEY_ROUTE = "route"
DICT_KEY_ROUTES = "routes"
DICT_KEY_DEST = "destination"
DICT_KEY_ARRIVAL = "arrival"

ATTR_ROUTE = "ROUTE"
ATTR_DEST = "DESTINATION"
ATTR_ARR_TIME = "ARRIVAL TIME"
ATTR_STOP_NAME = "STOP NAME"
ATTR_STOP_CODE = "STOP CODE"
ATTR_STOP_GTFS = "GTFS ID"

ATTRIBUTION = "Data provided by Helsinki Regional Transport(HSL HRT)"

LIMIT = 1500
SECS_IN_DAY = 24 * 60 * 60

STOP_ID_QUERY = """
    query ($name_code: String!) {
        stops (name: $name_code) {
            gtfsId
            name
            code
			routes {
		  		shortName
				patterns {
            		headsign
          		}
			}
        }
    }
	"""

STOP_CHECK_QUERY = """
    query ($id: String!) {
        stop (id: $id) {
            name
            code
			routes {
		  		shortName
			}
        }
    }
	"""

ROUTE_QUERY_WITH_RANGE = """
    query ($id: String!, $current_epoch: Long!, $sec_left_in_day: Int!) {
		stop (id: $id) {
			name
			code
			gtfsId
			routes {
		  		shortName
		  		patterns {
					headsign
		  		}
			}
			stoptimesWithoutPatterns (startTime: $current_epoch, numberOfDepartures: 500, timeRange: $sec_left_in_day){
				scheduledArrival
	  			realtimeArrival
	  			arrivalDelay
	  			scheduledDeparture
	  			realtimeDeparture
	  			departureDelay
	  			realtime
	  			realtimeState
	  			serviceDay
				headsign
				trip {
					route {
						shortName
					}
				}
			}
		}
	}
"""

ROUTE_QUERY_WITH_LIMIT = """
    query ($id: String!, $current_epoch: Long!, $limit: Int!) {
		stop (id: $id) {
			name
			code
			gtfsId
			routes {
		  		shortName
		  		patterns {
					headsign
		  		}
			}
			stoptimesWithoutPatterns (startTime: $current_epoch, numberOfDepartures: $limit){
				scheduledArrival
	  			realtimeArrival
	  			arrivalDelay
	  			scheduledDeparture
	  			realtimeDeparture
	  			departureDelay
	  			realtime
	  			realtimeState
	  			serviceDay
				headsign
				trip {
					route {
						shortName
					}
				}
			}
		}
	}
"""
