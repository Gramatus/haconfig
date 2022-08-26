# This script doesn't work, however the following recipe works: https://community.home-assistant.io/t/how-to-add-a-433-mhz-magnetic-door-switch-sensor-to-hass-io-and-tellstick-duo/71168/6
# > Log on to HA by ssh (i.e. enable "SSH" addon in sidebar and click on "terminal"
# >  run the command: nc core-tellstick 50801 > tellstick.txt
# > Sniff codes from there (might be a lot of jumble, but it gets the raw data)
# > Example YAML:
# - id: 2
#   name: NEXA Remote button one
#   protocol: arctech
#   model: selflearning-switch
#   house: "2790747"
#   unit: "1"

# https://github.com/magnushacker/tellcore-remote-spy
import tellcore.telldus as td
from tellcore.library import DirectCallbackDispatcher
# import sys
import logging
from collections import defaultdict

#_LOGGER = logging.getLogger(__name__)
#counter=defaultdict(int)

def raw_event(data, controller_id, cid):
  _LOGGER.info("----")
  key = data.replace("method:turnoff;", "").replace("method:turnon;", "")
  counter[key] += 1
  for key in sorted(counter.keys(), key=lambda x: counter[x]):
    _LOGGER.info("%s: %d" % (key, counter[key])  )

#dispatcher = DirectCallbackDispatcher()
#core = td.TelldusCore(callback_dispatcher=dispatcher)
#core.register_raw_device_event(raw_event)
#_LOGGER.info("started tellcor-remote-spy")

# import asyncio
# loop = asyncio.get_event_loop()
# dispatcher = td.AsyncioCallbackDispatcher(loop)
# if telldus.TelldusCore.callback_dispatcher is None:
# else:
# core = td.TelldusCore()
# core = td.TelldusCore(callback_dispatcher=dispatcher)
# try:
#     loop.run_forever()
# except KeyboardInterrupt:
#     pass
