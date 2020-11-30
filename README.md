# hslhrt-hass-custom
`hslhrt-hass-custom` is a Home Assistant custom component for real time public transsport information in Helsinki Metropoliton Area. Data is provided via [Digitransit platform](https://digitransit.fi/en/) APIs.

## Installation

    1. Using a tool of choice open the directory (folder) for HA configuration (where you find configuration YAML file).
    2. If "custom_components" directory does not exist, create one.
    3. In the "custom_components" directory create a new folder called "hslhrt".
    4. Download all the files from the this repository and place the files in the new directory created.
    5. Restart Home Assistant
    6. Install integration from UI (Configuration --> Intergations --> + --> Search for "hsl")
    7. Specify stop name (e.g. töölöntori) or stop code (e.g. H0209) and optionally the route number (e.g. 8) 

## Sensor

Sensor provides real time arrival information of a `route` (bus/tram) if available. If real time info is unavailable, it provides the scheduled arrival time of the `route`. If integration is configured with a `route`, sensor provides arrival times filtered for that `route` only. If the integration is configured without a `route`, it provides arrival times for all `routes` arriving at the given stop, in order of their arrival time. Sensor attributes provide the `Stop Name`, `Stop Code`, `Stop GTFS ID` and a list of upcoming `routes` with their arrival times for the day.

## UI Options (Entities Card Configuration)

#### Option-1

![Option-1](resources/images/ui-option-1.jpg?raw=true)

```
type: entities
entities:
  - entity: sensor.toolontori_h0209_2
  - entity: sensor.toolontori_h0209_all
  - entity: sensor.toolontori_h0209_8
  - entity: sensor.jupperi_e1465_all
title: HSL Lines
show_header_toggle: false
```


#### Option-2

![Option-2](resources/images/ui-option-2.jpg?raw=true)

```
type: entities
title: HSL - Route - 8
entities:
  - type: attribute
    icon: 'mdi:city-variant'
    entity: sensor.toolontori_h0209_8
    attribute: STOP NAME
    name: Stop Name
  - type: attribute
    icon: 'mdi:format-title'
    entity: sensor.toolontori_h0209_8
    attribute: STOP CODE
    name: Stop Code
  - type: attribute
    icon: 'mdi:bus'
    entity: sensor.toolontori_h0209_8
    attribute: ROUTE
    name: Next Line
  - type: attribute
    icon: 'mdi:city'
    entity: sensor.toolontori_h0209_8
    attribute: DESTINATION
    name: Destination
  - type: attribute
    icon: 'mdi:clock'
    entity: sensor.toolontori_h0209_8
    attribute: ARRIVAL TIME
    name: Arrival Time
```

#### Option-3
With a template sensor, more UI options are possible, such as displaying remaining time until next arrival and next two upcoming arrival times as shown below:

```
  - platform: template
    sensors:
      next_route_1:
        friendly_name: Next Route - 1
        value_template: "{% if state_attr('sensor.henttaanaukio_e3313_533', 'ROUTES') != None %}
                           {% if state_attr('sensor.henttaanaukio_e3313_533', 'ROUTES') | length > 0 %}
                             {{ state_attr('sensor.henttaanaukio_e3313_533', 'ROUTES')[0]['ARRIVAL TIME'] }}
                           {% else %}
                             'No more lines today'
                           {% endif %}
                         {% else %}
                           'No more lines today'
                         {% endif %}"
        attribute_templates:
          route: "{% if state_attr('sensor.henttaanaukio_e3313_533', 'ROUTES') != None %}
                    {% if state_attr('sensor.henttaanaukio_e3313_533', 'ROUTES') | length > 0 %}
                      {{ state_attr('sensor.henttaanaukio_e3313_533', 'ROUTES')[0]['ROUTE'] }}
                    {% else %}
                      'Unavailable'
                    {% endif %}
                  {% else %}
                    'Unavailable'
                  {% endif %}"
          destination: "{% if state_attr('sensor.henttaanaukio_e3313_533', 'ROUTES') != None %}
                          {% if state_attr('sensor.henttaanaukio_e3313_533', 'ROUTES') | length > 0 %}
                            {{ state_attr('sensor.henttaanaukio_e3313_533', 'ROUTES')[0]['DESTINATION'] }}
                          {% else %}
                            'Unavailable'
                          {% endif %}
                        {% else %}
                          'Unavailable'
                        {% endif %}"
      next_route_2:
        friendly_name: Next Route - 2
        value_template: "{% if state_attr('sensor.henttaanaukio_e3313_533', 'ROUTES') != None %}
                           {% if state_attr('sensor.henttaanaukio_e3313_533', 'ROUTES') | length > 1 %}
                             {{ state_attr('sensor.henttaanaukio_e3313_533', 'ROUTES')[1]['ARRIVAL TIME'] }}
                           {% else %}
                             'No more lines today'
                           {% endif %}
                         {% else %}
                           'No more lines today'
                         {% endif %}"
        attribute_templates:
          route: "{% if state_attr('sensor.henttaanaukio_e3313_533', 'ROUTES') != None %}
                    {% if state_attr('sensor.henttaanaukio_e3313_533', 'ROUTES') | length > 1 %}
                      {{ state_attr('sensor.henttaanaukio_e3313_533', 'ROUTES')[1]['ROUTE'] }}
                    {% else %}
                      'Unavailable'
                    {% endif %}
                  {% else %}
                    'Unavailable'
                  {% endif %}"
          destination: "{% if state_attr('sensor.henttaanaukio_e3313_533', 'ROUTES') != None %}
                          {% if state_attr('sensor.henttaanaukio_e3313_533', 'ROUTES') | length > 1 %}
                            {{ state_attr('sensor.henttaanaukio_e3313_533', 'ROUTES')[1]['DESTINATION'] }}
                          {% else %}
                            'Unavailable'
                          {% endif %}
                        {% else %}
                          'Unavailable'
                        {% endif %}"
      time_remaining:
        friendly_name: "Time Until Next Arrival"
        value_template: "{% if state_attr('sensor.henttaanaukio_e3313_533', 'ARRIVAL TIME') != None %}
                           {% set curr_time = now().replace(tzinfo=None) %}
                           {% set time_str = state_attr('sensor.henttaanaukio_e3313_533', 'ARRIVAL TIME') %}
                           {% set time_obj = strptime(time_str, '%H:%M:%S') %}
                           {% set right_time = time_obj.replace(year=curr_time.year, day=curr_time.day, month=curr_time.month) %}
                           {% set td = right_time - curr_time %}
                           {{ td.seconds | int| timestamp_custom('%H:%M:%S', false) }}
                         {% else %}
                           'Unavailable'
                         {% endif %}"
```

On the dashboard it shows up as:

![Option-3](resources/images/ui-option-3.jpg?raw=true)


**Note**: Sometimes the API query returns wierd results such as blank destinations or route numbers. If you see something like this, leave a comment and I can take a look at pruning the results further.

## Original Author
Anand Radhakrishnan [@anand-p-r](https://github.com/anand-p-r)
