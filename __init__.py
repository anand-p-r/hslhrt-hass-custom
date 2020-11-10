from homeassistant.core import Config, HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from async_timeout import timeout
import datetime

from python_graphql_client import GraphqlClient

from .const import (
	BASE_URL,
	DOMAIN,
	GTFS_ID,
	ROUTE,
	ROUTE_QUERY,
	MIN_TIME_BETWEEN_UPDATES,
	COORDINATOR,
	UNDO_UPDATE_LISTENER,
	ALL,
	_LOGGER
)


PLATFORMS = ["sensor"]


graph_client = GraphqlClient(endpoint=BASE_URL)


def base_unique_id(gtfs_id, route=None):
    """Return unique id for entries in configuration."""
    if route is None or route.lower() == ALL:
    	return f"{gtfs_id} all"
    else:
    	return f"{gtfs_id} {route}"


async def async_setup(hass: HomeAssistant, config: Config) -> bool:
    """Set up configured FMI."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass, config_entry) -> bool:
    """Set up HSLHRT as config entry."""
    websession = async_get_clientsession(hass)

    coordinator = HSLHRTDataUpdateCoordinator(
        hass, websession, config_entry
    )
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

        _LOGGER.debug("Using gtfs_id: %s and route: %s", 
            config_entry.data[GTFS_ID], config_entry.data[ROUTE])

        self.gtfs_id = config_entry.data[GTFS_ID]
        self.route = config_entry.data[ROUTE].lower()
        self.unique_id = str(self.gtfs_id) + ":" + str(self.route)

        self.route_data = None
        self.lines = None
        self._hass = hass

        _LOGGER.debug("Data will be updated every %s min", MIN_TIME_BETWEEN_UPDATES)

        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=MIN_TIME_BETWEEN_UPDATES
        )


    async def _async_update_data(self):
        """Update data via HSl HRT Open API."""

        def parse_data(data):

            parsed_data = {}
            bus_lines = {}

            graph_data = data.get("data", None)

            if graph_data is not None:
                hsl_stop_data = graph_data.get("stop", None)

                if hsl_stop_data is not None:

                    parsed_data["stop_name"] = hsl_stop_data.get("name", "")
                    parsed_data["stop_code"] = hsl_stop_data.get("code", "")

                    bus_lines = hsl_stop_data.get("routes", None)
                    route_data = hsl_stop_data.get("stoptimesWithoutPatterns", None)

                    if route_data is not None:

                        routes = []
                        for route in route_data:
                            route_dict = {}
                            arrival = route.get("realtimeArrival", None)

                            if arrival == None:
                            	arrival = route.get("scheduledArrival", 0)

                            route_dict["arrival"] = str(datetime.timedelta(seconds=arrival))
                            route_dict["destination"] = route.get("headsign", "")

                            route_dict["route"] = ""
                            if route_dict["destination"] != "":
                            	for bus in bus_lines:
                            		patterns = bus.get("patterns", None)
                            		line = bus.get("shortName", None)

                            		if line is None:
                            			continue

                            		if patterns is None:
                            			continue

                            		for pattern in patterns:
                            			headsign = pattern.get("headsign", "")
                            			if headsign != "":
                            				if headsign.lower() in route_dict["destination"].lower():
                            					route_dict["route"] = line


                            routes.append(route_dict)

                        parsed_data["routes"] = routes
                else:
                    _LOGGER.error("Invalid GTFS Id")
                    return

                return parsed_data, bus_lines

        try:
            async with timeout(10):

            	variables = {"id": self.gtfs_id.upper()}

            	# Asynchronous request
            	data = await self._hass.async_add_executor_job(
            		graph_client.execute, ROUTE_QUERY, variables
            		)
            	
            	self.route_data, self.lines = parse_data(data)
            	_LOGGER.debug(f"DATA: {self.route_data} - {self.lines}")

        except Exception as error:
            raise UpdateFailed(error) from error
        return {}