import logging

@service
def come_home():
    """yaml
name: Come home
description: Actions to perform when coming home
"""
    log.info("Came home")

@service
def leave_home():
    """yaml
name: Leave home
description: Actions to perform when leaving home
"""
    log.info("Left home")
