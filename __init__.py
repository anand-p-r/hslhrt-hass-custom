from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from async_timeout import timeout
import datetime
import time

from python_graphql_client import GraphqlClient

from .const import (
    BASE_URL,
    DESTINATION,
    DOMAIN,
    STOP_NAME,
    STOP_GTFS,
    STOP_CODE,
    ROUTE,
    DESTINATION,
    ROUTE_QUERY_WITH_LIMIT,
    MIN_TIME_BETWEEN_UPDATES,
    COORDINATOR,
    UNDO_UPDATE_LISTENER,
    DICT_KEY_ROUTE,
    DICT_KEY_ROUTES,
    DICT_KEY_DEST,
    DICT_KEY_ARRIVAL,
    ALL,
    VAR_ID,
    VAR_CURR_EPOCH,
    VAR_LIMIT,
    LIMIT,
    SECS_IN_DAY,
    _LOGGER,
    APIKEY,
)


PLATFORMS = ["sensor"]

graph_client = GraphqlClient(endpoint=BASE_URL)


def base_unique_id(gtfs_id, route=None, dest=None):
    """Return unique id for entries in configuration."""
    if (route is not None) and (route.lower() != ALL):
        return f"{gtfs_id} {route.upper()}"
    elif (dest is not None) and (dest.lower() != ALL):
        return f"{gtfs_id} {dest.upper()}"
    else:
        return f"{gtfs_id} ALL"


async def async_setup(hass: HomeAssistant, config: Config) -> bool:
    """Set up configured HSL HRT."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass, config_entry) -> bool:
    """Set up HSLHRT as config entry."""

    websession = async_get_clientsession(hass)

    coordinator = HSLHRTDataUpdateCoordinator(hass, websession, config_entry)
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    undo_listener = config_entry.add_update_listener(update_listener)

    hass.data[DOMAIN][config_entry.entry_id] = {
        COORDINATOR: coordinator,
        UNDO_UPDATE_LISTENER: undo_listener,
    }

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(config_entry, component)
        )

    return True


async def async_unload_entry(hass, config_entry):
    """Unload an HSLHRT config entry."""
    for component in PLATFORMS:
        await hass.config_entries.async_forward_entry_unload(config_entry, component)

    hass.data[DOMAIN][config_entry.entry_id][UNDO_UPDATE_LISTENER]()
    hass.data[DOMAIN].pop(config_entry.entry_id)

    return True


async def update_listener(hass, config_entry):
    """Update FMI listener."""
    await hass.config_entries.async_reload(config_entry.entry_id)


class HSLHRTDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching HSL HRT data API."""

    def __init__(self, hass, session, config_entry):
        """Initialize."""

        ##if config_entry.data.get(STOP_NAME, "None") is not None:
        _LOGGER.debug("Using Name/Code: %s", config_entry.data.get(STOP_NAME, "None"))

        ##if config_entry.data.get(ROUTE, "None") is not None:
        _LOGGER.debug("Using Route: %s", config_entry.data.get(ROUTE, "None"))

        ##if config_entry.data.get(DESTINATION, "None") is not None:
        _LOGGER.debug(
            "Using Destination: %s", config_entry.data.get(DESTINATION, "None")
        )

        self.gtfs_id = config_entry.data.get(STOP_GTFS, "")
        self.route = config_entry.data.get(ROUTE, "")
        self.dest = config_entry.data.get(DESTINATION, "")
        self.apikey = config_entry.data.get(APIKEY, "")

        self.route_data = None
        self._hass = hass

        _LOGGER.debug("Data will be updated every %s min", MIN_TIME_BETWEEN_UPDATES)

        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=MIN_TIME_BETWEEN_UPDATES
        )

    async def _async_update_data(self):
        """Update data via HSl HRT Open API."""

        def parse_data(data=None, line_from_user=None, dest_from_user=None):
            parsed_data = {}
            bus_lines = {}

            graph_data = data.get("data", None)

            if graph_data is not None:
                hsl_stop_data = graph_data.get("stop", None)

                if hsl_stop_data is not None:
                    parsed_data[STOP_NAME] = hsl_stop_data.get("name", "")
                    parsed_data[STOP_CODE] = hsl_stop_data.get("code", "")
                    parsed_data[STOP_GTFS] = hsl_stop_data.get("gtfsId", "")

                    bus_lines = hsl_stop_data.get("routes", None)
                    route_data = hsl_stop_data.get("stoptimesWithoutPatterns", None)

                    if route_data is not None:
                        routes = []
                        for route in route_data:
                            route_dict = {}
                            arrival = route.get("realtimeArrival", None)

                            if arrival is None:
                                arrival = route.get("scheduledArrival", 0)

                            ## Arrival time is num of secs from midnight when the trip started.
                            ## If the trip starts on this day and arrival time is next day (e.g late night trips)
                            ## the arrival time shows the number of secs more than 24hrs ending up with a
                            ## 1 day, hh:mm:ss on the displays. This corrects it.
                            if arrival >= SECS_IN_DAY:
                                arrival = arrival - SECS_IN_DAY

                            route_dict[DICT_KEY_ARRIVAL] = str(
                                datetime.timedelta(seconds=arrival)
                            )
                            route_dict[DICT_KEY_DEST] = route.get("headsign", "")

                            route_dict[DICT_KEY_ROUTE] = ""
                            if route_dict[DICT_KEY_DEST] != "":
                                for bus in bus_lines:
                                    line = bus.get("shortName", None)

                                    if line is None:
                                        continue

                                    # Check if the line and trip route names match for this
                                    # schedule
                                    trip = route.get("trip", "")
                                    if trip != "":
                                        trip_route = trip.get("route", "")
                                        if trip_route != "":
                                            trip_route_shortname = trip_route.get(
                                                "shortName", ""
                                            )
                                            if trip_route_shortname != "":
                                                if (
                                                    trip_route_shortname.lower()
                                                    == line.lower()
                                                ):
                                                    route_dict[DICT_KEY_ROUTE] = line

                            routes.append(route_dict)

                        parsed_data[DICT_KEY_ROUTES] = routes
                else:
                    _LOGGER.error("Invalid GTFS Id")
                    return

            time_line_parsed_data = []
            if line_from_user is not None:
                if line_from_user.lower() != ALL.lower():
                    if line_from_user.lower() != "":
                        routes = parsed_data.get(DICT_KEY_ROUTES, None)
                        if routes is not None:
                            for rt in routes:
                                line_in_data = rt.get(DICT_KEY_ROUTE, None)
                                if line_in_data is not None:
                                    if line_from_user.lower() == line_in_data.lower():
                                        time_line_parsed_data.append(rt)

                            parsed_data[DICT_KEY_ROUTES] = time_line_parsed_data
            elif dest_from_user is not None:
                if dest_from_user.lower() != ALL.lower():
                    if dest_from_user.lower() != "":
                        routes = parsed_data.get(DICT_KEY_ROUTES, None)
                        if routes is not None:
                            for rt in routes:
                                dest_in_data = rt.get(DICT_KEY_DEST, None)
                                if dest_in_data is not None:
                                    if dest_from_user.lower() in dest_in_data.lower():
                                        time_line_parsed_data.append(rt)

                            parsed_data[DICT_KEY_ROUTES] = time_line_parsed_data
            else:
                routes = parsed_data.get(DICT_KEY_ROUTES, None)
                if routes is not None:
                    for rt in routes:
                        line_in_data = rt.get(DICT_KEY_ROUTE, None)
                        dest_in_data = rt.get(DICT_KEY_DEST, None)
                        if line_in_data is not None and dest_in_data is not None:
                            if line_in_data != "" and dest_in_data != "":
                                time_line_parsed_data.append(rt)

                    parsed_data[DICT_KEY_ROUTES] = time_line_parsed_data

            return parsed_data

        try:
            async with timeout(10):
                # Find all the trips for the day
                current_epoch = int(time.time())
                variables = {
                    VAR_ID: self.gtfs_id.upper(),
                    VAR_CURR_EPOCH: current_epoch,
                    VAR_LIMIT: LIMIT,
                }

                graph_client.headers["digitransit-subscription-key"] = self.apikey

                # Asynchronous request
                data = await self._hass.async_add_executor_job(
                    graph_client.execute, ROUTE_QUERY_WITH_LIMIT, variables
                )

                self.route_data = parse_data(
                    data=data, line_from_user=self.route, dest_from_user=self.dest
                )
                _LOGGER.debug(f"DATA: {self.route_data}")

        except Exception as error:
            raise UpdateFailed(error) from error
            return {}
