from backend.driver.move import Model

CHIP_POINTER_TABLE = {}
FUNCTION_TABLE = {}
MOVE_MODEL = Model()
CAMERA = None
WARNING_COUNT = {}

# 摄像头上次保存历史图片时间
CAMERA_LAST_IMG = {}

# 摄像头上次上传历史图片时间
CAMERA_LAST_UPLOAD = {}

# 摄像头历史图片存储已达到存储限额，且设置为存满停止
# 这两个字典有线程安全问题，目前其写操作只在sweeper task的clean_by_quota中执行来避免线程安全问题
CAMERA_HISTORY_QUOTA = {}

# 摄像头告警存储是否已达到限额，且设置为存满停止
CAMERA_ALERT_QUOTA = {}

# TD201 ai结果最后一次id
TD201_AI_ID = None
