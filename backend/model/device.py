from backend.settings import SYS_CONF
from backend.driver import camera as camctl

def is_edge_ipc():
    # TD201/202等
    return 'device' in SYS_CONF and 'TD' in SYS_CONF['device']

def is_edge_proxy():
    # 阵列服务器或者盒子
    return 'device' not in SYS_CONF or 'ZL' in SYS_CONF['device'] or 'DK' in SYS_CONF['device']

def get_edge_ipc_cam():
    # 这里假设TD201/202等设备只有一个摄像头
    return camctl.get_rand_one()