# -*- coding: utf-8 -*-

import sys
import json

# 读取用户输入的关键字
# query = sys.argv[1]
query = 'test'

# 处理输入并生成输出结果
results = [
    {
        "title": "结果1",
        "subtitle": "这是结果1的描述",
        "arg": "结果1的参数",
        "icon": {"path": "icon.png"}
    },
    {
        "title": "结果2",
        "subtitle": "这是结果2的描述",
        "arg": "结果2的参数",
        "icon": {"path": "icon.png"}
    }
]

# 将结果输出为 Alfred 可识别的 JSON 格式
output = {"items": results}
print(json.dumps(output))
