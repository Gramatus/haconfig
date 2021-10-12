import logging

_LOGGER = logging.getLogger(__name__)

@service
def reset_log():
    """yaml
name: Reset log
description: Backs up log and then empties it
"""
    _LOGGER.info("Will backup log and then empty the log file")
    shell_command.backup_ha_log()
    system_log.clear()
    shell_command.empty_ha_log()
