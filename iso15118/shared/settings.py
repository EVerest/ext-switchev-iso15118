import os
SHARED_CWD = os.path.dirname(os.path.abspath(__file__))
JAR_FILE_PATH = SHARED_CWD + "/EXICodec.jar"

WORK_DIR = os.getcwd()

ENV_PATH = WORK_DIR + "/libexec/everest/3rd_party/josev/.env"

PKI_Path = ""

def set_PKI_PATH(path: str) -> None:
    global PKI_Path
    PKI_Path = path

def get_PKI_PATH() -> str:
    return PKI_Path

MESSAGE_LOG_JSON = True
MESSAGE_LOG_EXI = False

V20_EVSE_SERVICES_CONFIG = SHARED_CWD + "/examples/secc/15118_20/service_config.json"

enabled_tls_1_3 = False

def enable_tls_1_3() -> None:
    global enabled_tls_1_3
    enabled_tls_1_3 = True

def is_tls_1_3_enabled() -> bool:
    return enabled_tls_1_3

shared_settings = None

ignoring_value_range = False

def set_ignoring_value_range(ignoring):
    global ignoring_value_range 
    ignoring_value_range = ignoring

def get_ignoring_value_range() -> bool:
    return ignoring_value_range
