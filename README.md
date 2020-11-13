# hslhrt-hass-custom
`hslhrt-hass-custom` is a Home Assistant custom component for real time public transsport information in Helsinki Metropoliton Area. Data is provided via [Digitransit platform](https://digitransit.fi/en/) APIs.

## Installation

    1. Using a tool of choice open the directory (folder) for HA configuration (where you find configuration YAML file).
    2. If `custom_components` directory does not exist, create one.
    3. In the `custom_components` directory create a new folder called `hslhrt`.
    4. Download all the files from the this repository and place the files in the new directory created.
    5. Restart Home Assistant
    6. Install integration from UI (Configuration --> Intergations --> + --> Search for `hsl`)
    7. Specify stop name (e.g. töölöntori) or stop code (e.g. H0209) and optionally the route number (e.g. 8) 

## Sensor

Sensor provides real time arrival information of a `line` (bus/tram) if available. If real time info is unavailable, it provides the scheduled arrival time of the line. If integration is configured with a `line`, sensor provides arrival times filtered for that `line` only. If the integration is configured without a `line`, it provides arrival times for all `line` arriving at the given stop, in order of their arrival time. Sensor attributes provide the `Stop Name`, `Stop Code`, `Stop GTFS ID` and a list of upcoming `lines` with their arrival times for the day.

## Original Author
Anand Radhakrishnan [@anand-p-r](https://github.com/anand-p-r)