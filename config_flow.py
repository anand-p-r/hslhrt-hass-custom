"""Config flow for FMI (Finnish Meteorological Institute) integration."""

import voluptuous as vol

from homeassistant import config_entries, core
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

from . import base_unique_id, graph_client

from .const import (
    _LOGGER,
    STOP_CHECK_QUERY,
    DOMAIN,
    GTFS_ID,
    ALL,
    ROUTE
)


async def validate_user_config(hass: core.HomeAssistant, data):
    """Validate input configuration for HSL HRT.

    Data contains GTFS ID provided by user.
    """
    gtfs_id = data[GTFS_ID]
    route = data[ROUTE]

    errors = ""

    # Check if there is a valid dtop for the given gtfs_id
    try:
        variables = {"id": gtfs_id.upper()}
        hsl_data = await graph_client.execute_async(query=STOP_CHECK_QUERY, variables=variables)

    except Exception as err:
        err_string = (
            "Client error with status "
            + str(err.status_code)
            + " and message "
            + err.message
        )
        errors = "client_connect_error"
        _LOGGER.error(err_string)

        return {"stop": None, "route": None, "err": errors}

    data_dict = hsl_data.get("data", None)

    if data_dict is not None:
        stop_data = data_dict.get("stop", None)

        if stop_data is not None:
            stop_name = stop_data.get("name", "")
            if stop_name != "":
                ret_route = None
                if route.lower() != ALL:
                    routes = stop_data.get("routes", None)
                    if routes is not None:
                        for rt in routes:
                            rt_name = rt.get("shortName", "")
                            if rt_name != "":
                                if rt_name.lower() == route.lower():
                                    ret_route = route
                else:
                    ret_route = route

                return {"stop": stop_name, "route": ret_route, "err": ""}
            else:
                errors = "stop_data=<blank>" 
        else:
            errors = "stop_data=None"
    else:
        errors = "data=None"

    return {"stop": None, "route": None, "err": errors}


class HSLHRTConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow handler for FMI."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle user step."""
        # Display an option for the user to provide GtfsId for the integration
        errors = {}
        if user_input is not None:

            await self.async_set_unique_id(
                base_unique_id(user_input[GTFS_ID], user_input[ROUTE])
            )
            self._abort_if_unique_id_configured()

            valid = await validate_user_config(self.hass, user_input)

            if valid.get("err", "") == "":
                title = f"{valid['stop']} {valid['route']}"
                return self.async_create_entry(title=title, data=user_input)

            errors[DOMAIN] = valid["err"]

        data_schema = vol.Schema(
            {
                vol.Required(GTFS_ID, default=""): str,
                vol.Optional(ROUTE, default="ALL"): str
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )