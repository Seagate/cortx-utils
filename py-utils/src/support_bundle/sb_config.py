import os

BASE_DIR = "/opt/"
CURR_DIR = os.getcwd()
UTILS_TEST_DIR = CURR_DIR + "/py-utils/test"
SB_FILE_PATH = BASE_DIR + "support_bundle.tar.gz"
SB_TAG = "1.1"
PV_CLAIM_LIST = ['read-pv-claim', 'sb-write-pv-claim']

