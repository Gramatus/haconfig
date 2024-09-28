# Configuration

Communication with the Tellstick is done by the [Tellstick Add-on](https://github.com/home-assistant/addons/blob/master/tellstick/CHANGELOG.md). This is deprecated, but will hopefully keep working. If not, I probably need to create a HACS version of it.

# Listing devices

This is kinda strange, but basically:
1. Go to [actions](http://homeassistant.local:8123/developer-tools/action).
2. Select action `hassio.addon_stdin`.
3. Use the following YAML:
```
addon: core_tellstick
input:
  function: list
```
4. Go to the [Tellstick Addon logs](http://homeassistant.local:8123/hassio/addon/core_tellstick/logs) and read a device list.

Example output:
```
PROTOCOL            	MODEL               	ID   	TEMP 	HUMIDITY	RAIN                	WIND                	LAST UPDATED
fineoffset          	temperaturehumidity 	167  	25.2°	47%     	                    	                    	2024-09-28 23:02:20
fineoffset          	temperaturehumidity 	183  	22.3°	52%     	                    	                    	2024-09-28 23:01:46
fineoffset          	temperaturehumidity 	135  	14.8°	20%     	                    	                    	2024-09-28 23:01:51
mandolyn            	temperaturehumidity 	21   	4.4°	58%     	                    	                    	2024-09-28 23:01:50
fineoffset          	temperaturehumidity 	151  	17.2°	73%     	                    	                    	2024-09-28 23:01:42
mandolyn            	temperaturehumidity 	34   	15.2°	45%     	                    	                    	2024-09-28 23:01:58
fineoffset          	temperaturehumidity 	231  	24.4°	51%     	                    	                    	2024-09-28 22:53:09
```

# Adding devices to HA

Using "named devices", the following requirements needs to be met for devices to show up:
- Device only shows up after a sensor event has happened (e.g. "dead" devices will not be added to HA)
- Device needs to be added to the `only_named` key in `sensors.yaml` like this:
```
- platform: tellstick
  only_named:
    - id: 34
      name: Kontoret
    - id: 112
      name: Stua
```

## Sensor name

Basically the sensor name is defined as [sensor.<name>_<type>](https://github.com/home-assistant/core/blob/545dae2e7f2e1d077ca0724f471e7b0ed9f45aff/homeassistant/components/tellstick/sensor.py#L137).

> The sensors are only mapped through the `only_named` key, so they may be easily swapped by simply changing which `id` is connected to which `name`.

The two configs below will swap which physical sensor is connected to which entity in HA:
```
    - id: 34
      name: Kontoret
    - id: 112
      name: Stua
```
vs.
```
    - id: 112
      name: Kontoret
    - id: 34
      name: Stua
```
