CONCEPT_HIERARCHY = {
    "目标": ["人", "车辆", "动物", "建筑", "树"],
    "电力设备": ["绝缘子", "变压器", "导线", "电线杆"],
    "场景": ["室内", "室外", "电力场景"],
}

ATTRIBUTE_RELATIONS = {
    "发热": ["发热的", "高温", "过热"],
    "正常": ["正常的", "正常温度", "无异常"],
    "异常": ["异常的", "故障", "问题"],
    "距离": ["远处的", "远距离", "较远"],
    "遮挡": ["隐蔽的", "隐藏", "被遮挡"],
}

LOCATION_MODIFIERS = {
    "前景": "位于图像前景",
    "背景": "位于图像背景",
    "中央": "位于图像中央",
    "边缘": "位于图像边缘",
    "左上": "位于图像左上区域",
    "右上": "位于图像右上区域",
    "左下": "位于图像左下区域",
    "右下": "位于图像右下区域",
}


def load_knowledge_base():
    return {
        "CONCEPT_HIERARCHY": CONCEPT_HIERARCHY,
        "ATTRIBUTE_RELATIONS": ATTRIBUTE_RELATIONS,
        "LOCATION_MODIFIERS": LOCATION_MODIFIERS,
    }
