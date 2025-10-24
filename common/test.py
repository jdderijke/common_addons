import os
os.environ["ENV"] = "PROD"
import Common_Utils
from Common_Utils import get_logger
from test2 import testroutine


logger = get_logger()
logger.info("Hallo")
testroutine()
