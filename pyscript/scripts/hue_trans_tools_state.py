import logging
import asyncio
import datetime

_LOGGER = logging.getLogger(__name__)

entity_prefix = "huetrans"
state_prefix = "pyscript." + entity_prefix
room_prefix = "pyscript.transrooms_"

state.persist("pyscript.transtools_debugmode","on",{
    "icon": "mdi:bug-check"
})
state.persist("pyscript.transtools_settings","n/a",{
    "icon": "mdi:table-settings"
})

state.persist("pyscript.active_trans_scenes","n/a",{
    "icon": "mdi:led-strip"
})

ikea_scenes_kveldslys = [
                {
                    "index": 1,
                    "name": "IKEA 2890K 100 %",
                    "timeinseconds": (60*60)+(0),
                    "brightness": 255,
                    "kelvin": 2890
                },
                {
                    "index": 2,
                    "name": "IKEA 2300K 75 %",
                    "timeinseconds": (60*60)+(0),
                    "brightness": 191,
                    "kelvin": 2300
                },
                {
                    "index": 3,
                    "name": "IKEA 2150K 50 %",
                    "timeinseconds": (30*60)+(0),
                    "brightness": 127,
                    "kelvin": 2150
                },
                {
                    "index": 4,
                    "name": "IKEA Kveldsoransj 25 % (color 40 %)",
                    "timeinseconds": (30*60)+(0),
                    "brightness": 102,
                    "kelvin": 2150,
                    "hue": 4041,
                    "sat": 255
                },
                {
                    "index": 5,
                    "name": "IKEA Kveldsrød 1 %",
                    "timeinseconds": (30*60)+(0),
                    "brightness": 25,
                    "kelvin": 2150,
                    "hue": 2442,
                    "sat": 255
                }
            ]
state.persist(state_prefix+"_hoved_kveldslys","off",{
    "friendly_name": "Fadeoppsett: Kveldslys",
    "device_class": "Fadeoppsett",
    "icon": "mdi:table-settings",
    "endtime_entity": entity_prefix+"_kveldslys_endtime",
    "starttime_entity": entity_prefix+"_kveldslys_starttime",
    "unique_id": entity_prefix+"_settings_kveldslys",
    "Scenes": [
        {
            "index": 1,
            "name": "2890K 100 %",
            "bridgeName": "FadeKveldslys !start",
            "id": "KMVf61DE0jXA9b4",
            "timeinseconds": (60*60)+(0)
        },
        {
            "index": 2,
            "name": "2300K 75 %",
            "bridgeName": "FadeKveldslys 1t0min",
            "id": "fVqEsKelwr0BLv3",
            "timeinseconds": (60*60)+(0)
        },
        {
            "index": 3,
            "name": "2150K 50 %",
            "bridgeName": "FadeKveldslys 2t0min",
            "id": "rtH7xu7qvsv3PPv",
            "timeinseconds": (30*60)+(0)
        },
        {
            "index": 4,
            "name": "Kveldsoransj 25 % (color 40 %)",
            "bridgeName": "FadeKveldslys 2t30min",
            "id": "uofrddCzHp-x0vF",
            "timeinseconds": (30*60)+(0)
        },
        {
            "index": 5,
            "name": "Kveldsrød 1 %",
            "bridgeName": "FadeKveldslys 3t0min",
            "id": "iVcGM9UbJtc34TF",
            "timeinseconds": (30*60)+(0)
        }
    ],
    "Rooms": [
        "light.gang_nede",
        "light.bad",
        "light.stue",
        "light.kontor",
        "light.kjokken"
    ],
    "IKEA": [
        {
            "room": "light.gang_nede",
            "lights": [
                "light.gang_nede_1",
                "light.gang_nede_2",
                "light.gang_nede_3"
            ],
            "Scenes": ikea_scenes_kveldslys
        },
        {
            "room": "light.kjokken",
            "lights": [
                "light.kjokkenbenk_komfyr",
                "light.kjokkenbenk_vindu",
                "light.kjokken_oppa_skap",
                "light.kjokken_hylle"
            ],
            "Scenes": ikea_scenes_kveldslys
        },
        {
            "room": "light.kontor",
            "lights": [
                "light.kontor_hoyre",
                "light.kontor_venstre"
            ],
            "Scenes": [
                {
                    "index": 1,
                    "name": "IKEA Kontor Off",
                    "timeinseconds": (60*60)+(0),
                    "brightness": 0
                },
            ]
        }
    ]
})

ikea_scenes_vekking = [
                {
                    "index": 1,
                    "name": "IKEA Kveldsrød 1 %",
                    "timeinseconds": (0*60)+(10),
                    "brightness": 25,
                    "hue": 2442,
                    "sat": 255
                },
                {
                    "index": 2,
                    "name": "IKEA Kveldsoransj 25 %",
                    "timeinseconds": (14*60)+(50),
                    "brightness": 102,
                    "hue": 4041,
                    "sat": 255
                },
                {
                    "index": 3,
                    "name": "IKEA 2300K 100 %",
                    "timeinseconds": (15*60)+(0),
                    "brightness": 255,
                    "kelvin": 2300
                },
                {
                    "index": 4,
                    "name": "IKEA 3000K 100 %",
                    "timeinseconds": (30*60)+(0),
                    "brightness": 255,
                    "kelvin": 3000
                }
            ]
state.persist(state_prefix+"_hoved_vekking","off",{
    "friendly_name": "Fadeoppsett: Vekking",
    "device_class": "Fadeoppsett",
    "icon": "mdi:table-settings",    
    "endtime_entity": "sensor.template_huetrans_vekking_endtime_auto",
    "unique_id": entity_prefix+"_settings_vekking",
    "force_run": True,
    "Scenes": [
        {
            "index": 1,
            "name": "Kveldsrød 1 %",
            "bridgeName": "FadeVekking !start",
            "id": "PlnpsZgSQpM4Wuf",
            "timeinseconds": (0*60)+(10),
            "delay": 1*60
        },
        {
            "index": 2,
            "name": "Kveldsoransj 25 %",
            "bridgeName": "FadeVekking 0t0min",
            "id": "BuR1zzZQsVdYYiz",
            "timeinseconds": (14*60)+(50)
        },
        {
            "index": 3,
            "name": "2300K 100 %",
            "bridgeName": "FadeVekking 0t15min",
            "id": "CjbNTvFRZpZ8Xys",
            "timeinseconds": (15*60)+(0)
        },
        {
            "index": 4,
            "name": "3000K 100 %",
            "bridgeName": "FadeVekking 0t30min",
            "id": "qF0HQCCfXKI-H58",
            "timeinseconds": (30*60)+(0)
        }
    ],
    "Rooms": [
        "light.gang_nede",
        "light.bad",
        "light.stue",
        "light.soverom",
        "light.kontor",
        "light.kjokken"
    ],
    "IKEA": [
        {
            "room": "light.gang_nede",
            "lights": [
                "light.gang_nede_1",
                "light.gang_nede_2",
                "light.gang_nede_3"
            ],
            "Scenes": ikea_scenes_vekking
        },
        {
            "room": "light.kjokken",
            "lights": [
                "light.kjokkenbenk_komfyr",
                "light.kjokkenbenk_vindu",
                "light.kjokken_oppa_skap",
                "light.kjokken_hylle"
            ],
            "Scenes": ikea_scenes_vekking
        }
    ]
})

state.persist(state_prefix+"_hoved_bonnetid","off",{
    "friendly_name": "Fadeoppsett: Bønnetid",
    "device_class": "Fadeoppsett",
    "icon": "mdi:table-settings",
    "Scenes": []
})

ikea_scenes_arbeidslys = [
                {
                    "index": 1,
                    "name": "IKEA 4291K 100 %",
                    "timeinseconds": (30*60)+(0),
                    "brightness": 255,
                    "kelvin": 4291
                }
            ]
state.persist(state_prefix+"_hoved_arbeidslys","off",{
    "friendly_name": "Fadeoppsett: Arbeidslys",
    "device_class": "Fadeoppsett",
    "icon": "mdi:table-settings",
    "endtime_entity": "sensor.template_huetrans_arbeidslys_endtime_auto",
    "normal_endtime_entity": entity_prefix+"_arbeidslys_endtime",
    "after_entity": "sensor.template_huetrans_vekking_endtime_auto",
    "min_diff": 60*60,
    "unique_id": entity_prefix+"_settings_arbeidslys",
    "Scenes": [
        {
            "index": 1,
            "name": "4291K 100 %",
            "bridgeName": "FadeArbeidslys !start",
            "id": "a5QgoQtTS4v8EEb",
            "timeinseconds": (30*60)+(0)
        }
    ],
    "Rooms": [
        "light.gang_nede",
        "light.bad",
        "light.stue",
        "light.kontor",
        "light.kjokken"
    ],
    "IKEA": [
        {
            "room": "light.gang_nede",
            "lights": [
                "light.gang_nede_1",
                "light.gang_nede_2",
                "light.gang_nede_3"
            ],
            "Scenes": ikea_scenes_arbeidslys
        },
        {
            "room": "light.kjokken",
            "lights": [
                "light.kjokkenbenk_komfyr",
                "light.kjokkenbenk_vindu",
                "light.kjokken_oppa_skap",
                "light.kjokken_hylle"
            ],
            "Scenes": ikea_scenes_arbeidslys
        },
        {
            "room": "light.kontor",
            "lights": [
                "light.kontor_hoyre",
                "light.kontor_venstre"
            ],
            "Scenes": ikea_scenes_arbeidslys
        }
    ]
})

state.persist(state_prefix+"_fastelys_morgen","off",{
    "friendly_name": "Fadeoppsett: Basislys morgen",
    "device_class": "Fadeoppsett",
    "icon": "mdi:table-settings",
    "endtime_entity": "sensor.template_huetrans_fastelys_morgen_endtime_auto",
    "normal_endtime_entity": entity_prefix+"_arbeidslys_endtime",
    "after_entity": "sensor.template_huetrans_vekking_endtime_auto",
    "min_diff": -30*60,
    "unique_id": entity_prefix+"_settings_basislys_morgen",
    "Scenes": [
        {
            "index": 1,
            "name": "2300K 100 %",
            "bridgeName": "FdBasislys morg !start",
            "id": "LVeXeatgJKfWFgm",
            "timeinseconds": (15*60)+(0)
        }
    ],
    "Rooms": [
        "light.gang_oppe",
        "light.stue_hjorne"
    ],
    "IKEA": [
        {
            "Scenes": [
                {
                    "index": 1,
                    "name": "IKEA 2300K 100 %",
                    "timeinseconds": (15*60)+(0),
                    "brightness": 255,
                    "kelvin": 2300
                }
            ],
            "room": "light.gang_nede_vindu",
            "lights": [
                "light.gang_nede_vindu"
            ]
        }
    ]
})
state.persist(state_prefix+"_fastelys_dag","off",{
    "friendly_name": "Fadeoppsett: Basislys dag",
    "device_class": "Fadeoppsett",
    "icon": "mdi:table-settings",
    "endtime_entity": "sensor.template_huetrans_fastelys_dag_endtime_auto",
    "normal_endtime_entity": entity_prefix+"_arbeidslys_endtime",
    "after_entity": "sensor.template_huetrans_fastelys_morgen_endtime_auto",
    "min_diff": 1*60*60+15*60,
    "unique_id": entity_prefix+"_settings_basislys_dag",
    "Scenes": [
        {
            "index": 1,
            "name": "4291K 100 %",
            "bridgeName": "FdBasislys dag !start",
            "id": "hQN3vsGzphwsW-J",
            "timeinseconds": (60*60)+(0)
        }
    ],
    "Rooms": [
        "light.gang_oppe",
        "light.stue_hjorne",
        "light.gang_nede_vindu"
    ],
    "IKEA": [
        {
            "Scenes": [
                {
                    "index": 1,
                    "name": "IKEA 4291K 100 %",
                    "timeinseconds": (60*60)+(0),
                    "brightness": 255,
                    "kelvin": 4291
                }
            ],
            "room": "light.gang_nede_vindu",
            "lights": [
                "light.gang_nede_vindu"
            ]
        }
    ]
})
state.persist(state_prefix+"_fastelys_ettermiddag","off",{
    "friendly_name": "Fadeoppsett: Basislys ettermiddag",
    "device_class": "Fadeoppsett",
    "icon": "mdi:table-settings",
    "endtime_entity": entity_prefix+"_basislys_ettermiddag_endtime",
    "unique_id": entity_prefix+"_settings_basislys_ettermiddag",
    "Scenes": [
        {
            "index": 1,
            "name": "2650K 100 %",
            "bridgeName": "FdBasislys ette !start",
            "id": "kIlOTymVC3NVMs4",
            "timeinseconds": (60*60)+(0)
        }
    ],
    "Rooms": [
        "light.gang_oppe",
        "light.stue_hjorne",
        "light.gang_nede_vindu"
    ],
    "IKEA": [
        {
            "Scenes": [
                {
                    "index": 1,
                    "name": "IKEA 2650K 100 %",
                    "timeinseconds": (60*60)+(0),
                    "brightness": 255,
                    "kelvin": 2650
                }
            ],
            "room": "light.gang_nede_vindu",
            "lights": [
                "light.gang_nede_vindu"
            ]
        }
    ]
})
state.persist(state_prefix+"_fastelys_kveld","off",{
    "friendly_name": "Fadeoppsett: Basislys kveld",
    "device_class": "Fadeoppsett",
    "icon": "mdi:table-settings",
    "endtime_entity": entity_prefix+"_basislys_kveld_endtime",
    "unique_id": entity_prefix+"_settings_basislys_kveld",
    "Scenes": [
        {
            "index": 1,
            "name": "2300K 10 %",
            "bridgeName": "FdBasislys kvel !start",
            "id": "Q5b79H077cy6Jn3",
            "timeinseconds": (60*60)+(0)
        }
    ],
    "Rooms": [
        "light.gang_oppe",
        "light.stue_hjorne",
        "light.gang_nede_vindu"
    ],
    "IKEA": [
        {
            "Scenes": [
                {
                    "index": 1,
                    "name": "IKEA 2300K 10 %",
                    "timeinseconds": (60*60)+(0),
                    "brightness": 25,
                    "kelvin": 2300
                }
            ],
            "room": "light.gang_nede_vindu",
            "lights": [
                "light.gang_nede_vindu"
            ]
        }
    ]
})

@service
def update_room_entities():
    ha_uptime_seconds = datetime.datetime.now().timestamp() - datetime.datetime.strptime(state.get("sensor.oppetid_ha"), "%Y-%m-%dT%H:%M:%S%z").timestamp()
    if ha_uptime_seconds < 5*60:
        _LOGGER.info("Started to update room entities - waiting 30 seconds")
        asyncio.sleep(30)
    else:
        _LOGGER.info("Started to update room entities")
    all_rooms = list()
    for val in state.names(domain="pyscript"):
        if entity_prefix+"_" in val:
            data = state.getattr(val)
            if "Rooms" in data:
                for room in data["Rooms"]:
                    if room not in all_rooms:
                        all_rooms.append(room)
    _LOGGER.info(all_rooms)
    for room in all_rooms:
        state.persist(room_prefix + room.replace(".","_") + "_fadeend","idle",{
            "icon": "mdi:lighthouse",
            "friendly_name": room + ": fader til scene",
            "duration": "0:00:00",
            "start_time": "0:00:00",
            "end_time": "0:00:00"
        })
        state.persist(room_prefix + room.replace(".","_") + "_trans_active","true",{
            "friendly_name": room + ": lys skal fade",
            "device_class": "trans_active"
        })
        state.persist(room_prefix + room.replace(".","_"),"n/a",{
            "friendly_name": state.getattr(room)["friendly_name"],
            "device_class": "trans_room",
            "entity_id": room
        })
    _LOGGER.info("Finished updating room entities")

pyscript.update_room_entities()
