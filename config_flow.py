"""Config flow for FMI (Finnish Meteorological Institute) integration."""

import voluptuous as vol

from homeassistant import config_entries, core
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

from . import base_unique_id, graph_client

from .const import (
    _LOGGER,
    STOP_ID_QUERY,
    DOMAIN,
    NAME_CODE,
    STOP_CODE,
    STOP_NAME,
    STOP_GTFS,
    ERROR,
    ALL,
    VAR_NAME_CODE,
    ROUTE,
    DESTINATION,
    APIKEY,
)

api_key = None


async def validate_user_config(hass: core.HomeAssistant, data):
    """Validate input configuration for HSL HRT.

    Data contains Stop Name/Code provided by user.
    """
    name_code = data[NAME_CODE]
    route = data[ROUTE]
    dest = data[DESTINATION]
    apikey = data[APIKEY]

    errors = ""
    stop_code = None
    stop_name = None
    stop_gtfs = None
    ret_route = None
    ret_dest = None
    stops_data = {}

    # Check if there is a valid stop for the given name/code
    try:
        # If name is given, it is case in-sensitive. If stop code is given
        # that is case sensitive. For e.g. Si2223 is valid stop bu si2223
        # and SI2223 are not!
        # Therefore we have 3 options to check:
        # 1 --> Same code/name as given by user
        # 2 --> Upper case code/name as given by user
        # 3 --> Lower case code/name as given by user

        # Option-1 --> As given by user
        variables = {VAR_NAME_CODE: name_code}
        valid_opt_count = 1
        while True:
            graph_client.headers["digitransit-subscription-key"] = apikey
            hsl_data = await graph_client.execute_async(
                query=STOP_ID_QUERY, variables=variables
            )

            data_dict = hsl_data.get("data", None)
            if data_dict is not None:
                stops_data = data_dict.get("stops", None)
                if stops_data is not None:
                    if len(stops_data) > 0:
                        ## Reset errors
                        errors = ""
                        break
                    else:
                        _LOGGER.debug(
                            "no data in stops for %s",
                            variables.get(VAR_NAME_CODE, "-NA-"),
                        )
                        errors = "invalid_name_code 1"
                else:
                    _LOGGER.debug(
                        "no key stops for %s", variables.get(VAR_NAME_CODE, "-NA-")
                    )
                    errors = "invalid_name_code 2"
            else:
                _LOGGER.debug(
                    "no key data for %s", variables.get(VAR_NAME_CODE, "-NA-")
                )
                errors = "invalid_name_code 3"

            if valid_opt_count == 3:
                return {
                    STOP_CODE: stop_code,
                    STOP_NAME: stop_name,
                    STOP_GTFS: stop_gtfs,
                    ROUTE: ret_route,
                    DESTINATION: ret_dest,
                    ERROR: errors,
                    APIKEY: apikey,
                }
            elif valid_opt_count == 1:
                # Option-2: --> Upper case of user value
                variables = {VAR_NAME_CODE: name_code.upper()}
                valid_opt_count = 2
            else:
                # Option-3: --> Lower case of user value
                variables = {VAR_NAME_CODE: name_code.lower()}
                valid_opt_count = 3

    except Exception as err:
        err_string = f"Client error with message {err.message}"
        errors = "client_connect_error"
        _LOGGER.error(err_string)

        return {
            STOP_CODE: None,
            STOP_NAME: None,
            STOP_GTFS: None,
            ROUTE: None,
            DESTINATION: None,
            ERROR: errors,
            APIKEY: apikey,
        }

    stop_data = stops_data[0]
    stop_gtfs = stop_data.get("gtfsId", "")
    stop_name = stop_data.get("name", "")
    stop_code = stop_data.get("code", "")
    if stop_name != "" and stop_gtfs != "":
        ## Specific route should be checked
        ## Ignore destination filter
        if (route.lower() != ALL) or (dest.lower() != ALL):
            routes = stop_data.get("routes", None)
            if routes is not None:
                for rt in routes:
                    if route.lower() != ALL:
                        rt_name = rt.get("shortName", "")
                        if rt_name != "":
                            if rt_name.lower() == route.lower():
                                ret_route = route
                                break
                    else:
                        patterns = rt.get("patterns", None)
                        if patterns is not None:
                            break_loop = False
                            for pattern in patterns:
                                head_sign = pattern.get("headsign", "")
                                if head_sign != "":
                                    if dest.lower() in head_sign.lower():
                                        ret_dest = head_sign
                                        break_loop = True
                                        break

                            if break_loop:
                                break
        else:
            ret_route = route

        if (route.lower() != ALL) and (ret_route == None):
            errors = "invalid_route"
        else:
            if (dest.lower() != ALL) and (ret_dest == None):
                errors = "invalid_destination"
    else:
        _LOGGER.error("Name or gtfs is blank")
        errors = "invalid_name_code 4"

    return {
        STOP_CODE: stop_code,
        STOP_NAME: stop_name,
        STOP_GTFS: stop_gtfs,
        ROUTE: ret_route,
        DESTINATION: ret_dest,
        ERROR: errors,
        APIKEY: apikey,
    }


class HSLHRTConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow handler for FMI."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle user step."""
        # Display an option for the user to provide Stop Name/Code for the integration
        errors = {}
        valid = {}

        if user_input is not None:
            valid = await validate_user_config(self.hass, user_input)
            await self.async_set_unique_id(
                base_unique_id(valid[STOP_GTFS], valid[ROUTE], valid[DESTINATION])
            )
            self._abort_if_unique_id_configured()
            if valid.get(ERROR, "") == "":
                title = ""
                if valid[ROUTE] is not None:
                    title = f"{valid[STOP_NAME]}({valid[STOP_CODE]}) {valid[ROUTE]}"
                elif valid[DESTINATION] is not None:
                    title = (
                        f"{valid[STOP_NAME]}({valid[STOP_CODE]}) {valid[DESTINATION]}"
                    )
                else:
                    title = f"{valid[STOP_NAME]}({valid[STOP_CODE]}) ALL"
                return self.async_create_entry(title=title, data=valid)
            else:
                reason = valid.get(ERROR, "Configuration Error!")
                _LOGGER.error(reason)
                return self.async_abort(reason=reason)

        data_schema = vol.Schema(
            {
                vol.Required(NAME_CODE, default=""): str,
                vol.Required(ROUTE, default="ALL"): str,
                vol.Required(DESTINATION, default="ALL"): str,
                vol.Required(APIKEY, default=""): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
