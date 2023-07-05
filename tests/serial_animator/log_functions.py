import serial_animator.log

logger = serial_animator.log.log(__name__)
logger2 = serial_animator.log.log("logger2")
logger.setLevel("DEBUG")
logger2.setLevel("INFO")


def log_output():
    with logger.at_level("INFO"):
        logger.info("logger info showing")
        logger.debug("logger debug silenced")
    logger2.info("I'm info from log2")
    logger.debug("I'm debug from logger")
    with logger2.all_log_levels("CRITICAL"):
        logger2.warning("logger2 silenced")
        logger.info("logger info silenced")
    logger2.info("Info from 2 still here")
    logger.debug("Debug from 1 still here")
