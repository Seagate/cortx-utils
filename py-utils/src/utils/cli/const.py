BASE_DIR = "/opt/seagate/cortx"
UTILS_DIR = f"{BASE_DIR}/utils"
COMMAND_DIRECTORY = f"{UTILS_DIR}/cli/schema"
SUB_COMMANDS_PERMISSIONS = "permissions_tag"
NO_AUTH_COMMANDS = ["support_bundle", "bundle_generate", "csm_bundle_generate",
                    "-h", "--help", "system"]
EXCLUDED_COMMANDS=[]
HIDDEN_COMMANDS = ["bundle_generate", "csm_bundle_generate",]
CSM_OPERATION_SUCESSFUL     = 0x0000