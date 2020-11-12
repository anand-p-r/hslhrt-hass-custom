"""Constants for the FMI Weather and Sensor integrations."""
import logging
from datetime import timedelta

_LOGGER = logging.getLogger(__package__)

DOMAIN = "hslhrt"
NAME = "HSLHRT"
MANUFACTURER = "Helsinki Regional Transport Authority"

COORDINATOR = "coordinator"
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=15)
UNDO_UPDATE_LISTENER = "undo_update_listener"

DEFAULT_NAME = "HSLHRT"

ATTRIBUTION = "Real Time Route Info by HSL HRT"

BASE_URL = "https://api.digitransit.fi/routing/v1/routers/hsl/index/graphql"

GTFS_ID = "gtfsid"
ROUTE = "route"
ALL = "all"

ATTR_ROUTE = "ROUTE"
ATTR_DEST = "DESTINATION"
ATTR_ARR_TIME = "ARRIVAL TIME"
ATTR_STOP_NAME = "STOP NAME"
ATTR_STOP_CODE = "STOP CODE"


ATTRIBUTION = "Data provided by Helsinki Regional Transport(HSL HRT)"

STOP_CHECK_QUERY =  """
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

ROUTE_QUERY = """
    query ($id: String!, $sec_left_in_day: Int!) {
		stop (id: $id) {
			name
			code
			routes {
		  		shortName
		  		patterns {
					headsign
		  		}
			}
			stoptimesWithoutPatterns (numberOfDepartures: 500, timeRange: $sec_left_in_day){
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
			}
		}
	}
"""