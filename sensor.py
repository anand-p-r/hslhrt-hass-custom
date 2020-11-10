"""Sensor platform for HSL HRT routes."""

from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.const import (
    ATTR_ATTRIBUTION
)

from .const import (
    _LOGGER,
    DOMAIN,
    COORDINATOR,
    GTFS_ID,
    ROUTE_QUERY,
    ATTR_ROUTE,
    ATTR_DEST,
    ATTR_ARR_TIME,
    ATTRIBUTION,
    ALL
)

SENSOR_TYPES = {
    "route": ["Route", None]
}

PARALLEL_UPDATES = 1

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the HSL HRT Sensor."""
    name = config_entry.data[GTFS_ID]

    coordinator = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR]

    entity_list = []

    for sensor_type in SENSOR_TYPES:
        entity_list.append(
            HSLHRTRouteSensor(
                name, coordinator, sensor_type
            )
        )

    async_add_entities(entity_list, False)


class HSLHRTRouteSensor(CoordinatorEntity):
    """Implementation of a HSL HRT sensor."""

    def __init__(self, name, coordinator, sensor_type):
        """Initialize the sensor."""

        super().__init__(coordinator)
        self.client_name = name
        self._name = SENSOR_TYPES[sensor_type][0]
        self._hsl = coordinator
        self._state = None
        self._icon = None
        self.filt_routes = None
        self.type = sensor_type
        self._unit_of_measurement = SENSOR_TYPES[sensor_type][1]

        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        if self._hsl is not None:
            if self._hsl.route_data is not None:
                return f"{self._hsl.route_data['stop_name']} {self._hsl.route}"

        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def unit_of_measurement(self):
        """Return unit of measurement."""
        return self._unit_of_measurement

    @property
    def device_state_attributes(self):
        """Return the state attributes."""

        if self.filt_routes is not None and len(self.filt_routes) > 0:
            return {
                    ATTR_ROUTE: self.filt_routes[0]["route"],
                    ATTR_DEST: self.filt_routes[0]["destination"],
                    ATTR_ARR_TIME: self.filt_routes[0]["arrival"],
                    "ROUTES": [
                        {
                            ATTR_ROUTE: rt["route"],
                            ATTR_DEST: rt["destination"],
                            ATTR_ARR_TIME: rt["arrival"]
                        }
                        for rt in self.filt_routes[1:]
                        ],
                    ATTR_ATTRIBUTION: ATTRIBUTION
                }
        else:
            if self._hsl is not None and len(self._hsl.route_data["routes"]) > 0:
                return {
                    ATTR_ROUTE: self._hsl.route_data["routes"][0]["route"],
                    ATTR_DEST: self._hsl.route_data["routes"][0]["destination"],
                    ATTR_ARR_TIME: self._hsl.route_data["routes"][0]["arrival"],
                    "ROUTES": [
                        {
                            ATTR_ROUTE: rt["route"],
                            ATTR_DEST: rt["destination"],
                            ATTR_ARR_TIME: rt["arrival"]
                        }
                        for rt in self._hsl.route_data["routes"][1:]
                        ],
                    ATTR_ATTRIBUTION: ATTRIBUTION
                }

        return {ATTR_ATTRIBUTION: ATTRIBUTION}

    def update(self):
        """Get the latest data from HSL HRT and update the states."""

        if self._hsl is None:
            self._state = None
            return

        if self._hsl.route_data is None:
            self._state = None
            return

        if len(self._hsl.route_data["routes"]) > 0:
            if self._hsl.route == ALL:
                self._state = self._hsl.route_data["routes"][0]["route"]
                self._icon = "mdi:city-variant"
                self.filt_routes = None
                return
            else:
                self.filt_routes = []
                for rt in self._hsl.route_data["routes"]:
                    if self._hsl.route.lower() in rt["route"].lower():
                        self.filt_routes.append(rt)

                if len(self.filt_routes) > 0:
                    self._state = self.filt_routes[0]["route"]
                    self._icon = "mdi:city-variant"
                    return
        else:
            self._state = None

        return