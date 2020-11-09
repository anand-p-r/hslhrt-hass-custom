"""Config flow for FMI (Finnish Meteorological Institute) integration."""

import voluptuous as vol

from homeassistant import config_entries, core
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

from . import base_unique_id, graph_client, stop_check_query
from .const import (
    _LOGGER,
    STOP_CHECK_QUERY,
    DOMAIN
)


async def validate_user_config(hass: core.HomeAssistant, data):
    """Validate input configuration for HSL HRT.

    Data contains GTFS ID provided by user.
    """
    gtfs_id = data[GTFS_ID]

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

        return {"stop": "None", "err": errors}

    data_dict = hsl_data.get("data", None)

    if data_dict is not None:
        stop_data = data_dict.get("stop", None)

        if stop_data is not None:
            stop_name = stop_data.get("name", "")
                if stop_name != "":
                    return {"stop": stop_name, "err": ""}
                else:
                    errors = "stop_data=<blank>" 
        else:
            errors = "stop_data=None"
    else:
        errors = "data=None"

    return {"stop": "None", "err": errors}


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
                return self.async_create_entry(title=valid["stop"], data=user_input)

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

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Options callback for HSL HRT."""
        return HSLHRTOptionsFlowHandler(config_entry)


class HSLHRTOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options for HSL HRT."""

    def __init__(self, config_entry):
        """Initialize HSLHRT options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            return self.async_create_entry(title="Route Options", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                vol.Optional(ROUTE, default=self.config_entry.options.get(
                    ROUTE, "ALL")): str
                }
            )
        )
