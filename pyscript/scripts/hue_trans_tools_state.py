import logging

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
    ]
})
state.persist(state_prefix+"_hoved_vekking","off",{
    "friendly_name": "Fadeoppsett: Vekking",
    "device_class": "Fadeoppsett",
    "icon": "mdi:table-settings",    
    "endtime_entity": entity_prefix+"_vekking_endtime",
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
    ]
})
state.persist(state_prefix+"_hoved_bonnetid","off",{
    "friendly_name": "Fadeoppsett: Bønnetid",
    "device_class": "Fadeoppsett",
    "icon": "mdi:table-settings",
    "Scenes": []
})
state.persist(state_prefix+"_hoved_arbeidslys","off",{
    "friendly_name": "Fadeoppsett: Arbeidslys",
    "device_class": "Fadeoppsett",
    "icon": "mdi:table-settings",
    "endtime_entity": entity_prefix+"_arbeidslys_endtime",
    "unique_id": entity_prefix+"_settings_arbeidslys",
    "Scenes": [
        {
            "index": 1,
            "name": "4291K 100 %",
            "bridgeName": "FadeArbeidslys !start",
            "id": "a5QgoQtTS4v8EEb",
            "timeinseconds": (30*60)+(0)
        }
    ]
})

state.persist(state_prefix+"_fastelys_morgen","off",{
    "friendly_name": "Fadeoppsett: Basislys morgen",
    "device_class": "Fadeoppsett",
    "icon": "mdi:table-settings",
    "endtime_entity": entity_prefix+"_basislys_morgen_endtime",
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
    ]
})
state.persist(state_prefix+"_fastelys_dag","off",{
    "friendly_name": "Fadeoppsett: Basislys dag",
    "device_class": "Fadeoppsett",
    "icon": "mdi:table-settings",
    "endtime_entity": entity_prefix+"_basislys_dag_endtime",
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
        "light.stue_hjorne"
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
        "light.stue_hjorne"
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
        "light.stue_hjorne"
    ]
})



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
