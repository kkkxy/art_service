# 读取模式0为直接自动转换成art的数据结构，1为把所有信息原汁原味写成包含若干个字典的list
READ_OPTION = 0
# 用于匹配高度值
HEIGHT_PATTERN = r'[H][=][0-9]*.[0-9]*(?=[m])'
# 用于匹配楼层数
FLOOR_PATTERN = r'[0-9]*[F]'
# 暂时可以转换的3dm数据
READABLE_OBJ = ['ObjectType.Curve']
# 指定style.json保存的文件夹
STYLE_JSON_PATH = './'