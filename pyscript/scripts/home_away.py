import logging

_LOGGER = logging.getLogger(__name__)

@service
def come_home():
    """yaml
name: Come home
description: Actions to perform when coming home
"""
    _LOGGER.info("Came home")

@service
def leave_home():
    """yaml
name: Leave home
description: Actions to perform when leaving home
"""
    _LOGGER.info("Left home")
