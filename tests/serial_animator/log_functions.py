import serial_animator.log

logger = serial_animator.log.log(__name__)
logger2 = serial_animator.log.log("logger2")
logger.setLevel("DEBUG")


def log_output():
    logger2.info("I'm info from log2")
    with logger2.all_log_levels("CRITICAL"):
        logger2.warning("logger2 silenced")
        logger.info("logger info silenced")
    logger2.info("Info from 2 still here")

    with logger2.at_level("INFO"):
        logger.debug("this debug message shouldn't be seen")
    # with logger2.change_all_logs():
    #     logger2.warning("logger2 silenced")
    #     logger.warning("logger silenced")
    # logger.debug("and this logs again")
