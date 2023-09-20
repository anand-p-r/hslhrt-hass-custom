"""Sensor platform for HSL HRT routes."""

from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from homeassistant.const import ATTR_ATTRIBUTION

from .const import (
    _LOGGER,
    DOMAIN,
    COORDINATOR,
    STOP_GTFS,
    STOP_NAME,
    STOP_CODE,
    ROUTE,
    ATTR_ROUTE,
    ATTR_DEST,
    ATTR_ARR_TIME,
    ATTR_STOP_NAME,
    ATTR_STOP_CODE,
    ATTR_STOP_GTFS,
    DICT_KEY_ROUTE,
    DICT_KEY_ROUTES,
    DICT_KEY_DEST,
    DICT_KEY_ARRIVAL,
    ATTRIBUTION,
    ALL,
)

SENSOR_TYPES = {ROUTE: ["Route", None]}

PARALLEL_UPDATES = 1


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the HSL HRT Sensor."""
    name = config_entry.data.get(STOP_GTFS, "")

    coordinator = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR]

    entity_list = []

    for sensor_type in SENSOR_TYPES:
        entity_list.append(HSLHRTRouteSensor(name, coordinator, sensor_type))

    async_add_entities(entity_list, False)


class HSLHRTRouteSensor(CoordinatorEntity):
    """Implementation of a HSL HRT sensor."""

    def __init__(self, name, coordinator, sensor_type):
        """Initialize the sensor."""

        super().__init__(coordinator)
        self.client_name = name
        self._name = SENSOR_TYPES[sensor_type][0]
        self._state = None
        self._icon = None
        self.type = sensor_type
        self._unit_of_measurement = SENSOR_TYPES[sensor_type][1]

        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        if self.coordinator is not None:
            if self.coordinator.route_data is not None:
                ext = ""
                if (self.coordinator.route is not None) and (
                    self.coordinator.route != ALL
                ):
                    ext = self.coordinator.route.upper()
                elif (self.coordinator.dest is not None) and (
                    self.coordinator.dest != ALL
                ):
                    ext = self.coordinator.dest.upper()
                else:
                    ext = ALL
                return f"{self.coordinator.route_data[STOP_NAME]}({self.coordinator.route_data[STOP_CODE]}) {ext}"

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
    def extra_state_attributes(self):
        """Return the state attributes."""

        if (
            self.coordinator is not None
            and len(self.coordinator.route_data[DICT_KEY_ROUTES]) > 0
        ):
            routes = []
            for rt in self.coordinator.route_data[DICT_KEY_ROUTES][1:]:
                dest_str = "Unavailable"

                if rt[DICT_KEY_DEST] is not None:
                    dest_str = rt[DICT_KEY_DEST]

                route = {
                    ATTR_ROUTE: rt[DICT_KEY_ROUTE],
                    ATTR_DEST: dest_str,
                    ATTR_ARR_TIME: rt[DICT_KEY_ARRIVAL],
                }
                routes.append(route)

            dest_str = "Unavailable"

            if (
                self.coordinator.route_data[DICT_KEY_ROUTES][0][DICT_KEY_DEST]
                is not None
            ):
                dest_str = self.coordinator.route_data[DICT_KEY_ROUTES][0][
                    DICT_KEY_DEST
                ]

            return {
                ATTR_ROUTE: self.coordinator.route_data[DICT_KEY_ROUTES][0][
                    DICT_KEY_ROUTE
                ],
                ATTR_DEST: dest_str,
                ATTR_ARR_TIME: self.coordinator.route_data[DICT_KEY_ROUTES][0][
                    DICT_KEY_ARRIVAL
                ],
                "ROUTES": routes,
                ATTR_STOP_NAME: self.coordinator.route_data[STOP_NAME],
                ATTR_STOP_CODE: self.coordinator.route_data[STOP_CODE],
                ATTR_STOP_GTFS: self.coordinator.route_data[STOP_GTFS],
                ATTR_ATTRIBUTION: ATTRIBUTION,
            }

        return {ATTR_ATTRIBUTION: ATTRIBUTION}

    def update(self):
        """Get the latest data from HSL HRT and update the states."""

        if self.coordinator is None:
            self._state = None
            return

        if self.coordinator.route_data is None:
            self._state = None
            return

        if len(self.coordinator.route_data[DICT_KEY_ROUTES]) > 0:
            for rt in self.coordinator.route_data[DICT_KEY_ROUTES]:
                if rt[DICT_KEY_ROUTE] != "":
                    self._state = rt[DICT_KEY_ROUTE]
                    self._icon = "mdi:bus"
                    return
                else:
                    self._state = None
        else:
            self._state = None

        return
