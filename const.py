"""Constants for the FMI Weather and Sensor integrations."""
import logging

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

GTFS_ID = "GTFS_ID"
ROUTE = "ROUTE"

STOP_CHECK_QUERY =  """
        query ($id: String!) {
            stop (id: $id) {
                name
                code
            }
        }
    """
