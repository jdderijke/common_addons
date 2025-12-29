import os
os.environ["ENV"] = "PROD"
from common_addons.common_utils import get_logger
from test2 import testroutine


logger = get_logger()
logger.info("Hallo")
testroutine()
