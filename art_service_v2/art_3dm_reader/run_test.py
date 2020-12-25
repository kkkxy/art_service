"""
DataTemplate和DataObject的基本使用方法

"""
from art_3dm_reader.rhino_file_reader import Read3dmFile
from art_datastructure.data_structure import DataObject, DataElement
from shapely.geometry import Point, LineString, Polygon


# 用来打印结果的函数
def print_result():
    for each in template.data_objects:
        if each.tree.depth() > 0:
            print(each.tree)
        # for node in each.tree.nodes.values():
        #     print(node.identifier, node.data)


#  DataStructure的基本使用方法

# ---READ3DM CLASS---
# 1. 读取3dm文件 -> DataTemplate
TEST_FILE_PATH = "../test_files/3dm_files/site_plan_example_1.3dm"
template = Read3dmFile(TEST_FILE_PATH).read_3dm_file()

# ---DATAELEMENT CLASS---
# 1. 创建额外的DataElement和DataObject
geo = Polygon([(0, 1), (2, 3), (4, 5), (0, 5)])
new_element = DataElement(geometry=geo)
new_object1 = DataObject(index=100, elements=[new_element], global_tree=template.tree)
new_object2 = DataObject(index=101, elements=[new_element], global_tree=template.tree)
new_object3 = DataObject(index=102, elements=[new_element], global_tree=template.tree)

# ---DATATEMPLATE CLASS---
# 1. 查找指定物件  ->  DataObject
test_object1 = template.find_object('写字楼1')  # 输入物件名称查询
test_object = template.find_object(23)  # 输入物件index查询

# 2. 增删物件
template.add_object(new_object1, 21)  # 在指定物件下面添加一个子物件
template.delete_object(15)  # 删除指定objects - by index
template.delete_object('写字楼2')  # 删除指定object - by id
template.insert_object(new_object2, 21, 20)  # 在指定两个物件中间插入一个物件


# 3. 找到指定物件下所有DataObjects或者DataElements -> list
all_object_list = template.find_object(23).all_objects()  # 找到指定物件下所有DataObjects
all_element_list = template.find_object(3).all_elements()  # 找到指定物件下所有DataElements

# 4. 移动物件到新的父物件下
template.move_object(21, 23)

# ---OBJECT CLASS---
# 1. 增删元素
test_object.add_element(new_element)  # 添加elements
test_object.delete_element(new_element.id)  # 删除element

# 2. 找到自己+下级的所有DataObjects或者DataElements -> list
object_list = test_object.all_objects()
element_list = test_object.all_elements()

print_result()
