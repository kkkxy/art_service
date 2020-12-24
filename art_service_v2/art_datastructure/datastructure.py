"""
@ART 基础数据数据结构
"""
from uuid import uuid1
from dataclasses import dataclass, field
from typing import *
from shapely.geometry import Point, LineString, Polygon

from treelib import Tree, Node


class GlobalTree:

    def __init__(self, tree=None, data_objects=None):
        self.tree = tree
        self.data_objects = data_objects

    # # 添加object
    # def add_object(self, one_object: DataObject, level):
    #     if self.tree.depth > 1:
    #         pass
    #
    # # 删除object
    # def delete_object(self, object_index: int):
    #     if tree.contains(object_index):
    #         tree.remove_node(object_index)
    #
    #
    # def insert_object(self, object_index: int, position):
    #
    #
    # def replace_object(self, one_object: DataObject, position):
    #
    #
    # def move_object_to_another_tree_position(self, position):



@dataclass(order=True, unsafe_hash=True)
class DataElement:
    """
    数据结构中最小的图形和语义信息储存类
    结构特征：用于存储每一个最基本的geometry对象（点/线/几何形状）；其中包含语义属性及几何属性；不存在任何嵌套与包含关系
    """
    # 几何属性
    geometry: Union[Point, LineString, Polygon] = field(default=None)
    shadow: Polygon = field(default=None)  # 几何物件对应的阴影, 仅包括geometry_realistic_state为True的Polygon

    # 语义属性
    id: str = field(default_factory=uuid1)     # 物件ID
    type: str = field(default="")             # 图层名
    group_list: tuple = field(default=None)  # 编组信息
    has_shadow: bool = field(default=False)    # 几何对象是否有阴影

@dataclass(order=True, unsafe_hash=True)
class DataObject:
    """
    物件类，逻辑结构
    结构特征：1.用于存储dxf文件中的一个Group单元；
            2.可以由ObjectElement组成，可以由DataObject组成，也可以两者共同组成
    """
    # 几何属性
    elements: List = field(default_factory=list)  # 所有dataElements

    # 语义属性
    id: str = field(default_factory=uuid1)  # 物件ID
    index: int = field(default=0)  # 組索引
    name: str = field(default=None)  # 编组名字
    global_tree: GlobalTree = field(default_factory=GlobalTree) # 全局树
    # tree: Tree = field(default_factory=Tree) # 关系树
    floor: int = field(default=0)  # 层数
    height: float = field(default=0.0)  # 高度
    annotations: str = field(default=None)  # 所有文字标注

    # 基准渲染层级
    zorder: int = field(default=0)

    @property
    def tree(self):
        if self.global_tree.tree.depth() > 1 and self.index in self.global_tree.tree.nodes:
            return self.global_tree.tree.subtree(self.index)
        else:
            return None

    # 所有DataElement
    def all_elements(self) -> List[DataElement]:
        elements = []
        object_indexes = self.tree.all_nodes()
        for index in object_indexes:
            elements.extend(self.global_tree.data_objects[index].elements)
        return elements

    # 所有DataObject
    def all_objects(self) -> List[DataElement]:
        objects = []
        object_indexes = self.tree.all_nodes()
        for index in object_indexes:
            objects.extend(self.global_tree.data_objects[index])
        return objects

    # 添加element
    def add_element(self, element: DataElement):
        if isinstance(element, DataElement) and element.geometry is not None:
            self.elements.append(element)
        else:
            raise Exception("物件中没有输入的元素ID")

    # 删除element
    def delete_element(self, element_id: str):
        if element_id in [item.id for item in self.elements]:
            index = max(self.elements, key=lambda x: x.id == element_id)
            self.elements.pop(index)
        else:
            raise Exception("物件中没有输入的元素ID")

def assemble_tree(data_elements:List[DataElement], data_objects:dict):
    """
    用于组装data_objects的关系树，传入是目前已有的element元素以及obj字典
    :param data_elements:
    :param data_objects:
    :return:
    """
    group_info = [each.group_list for each in data_elements]
    group_info = list(set(filter(lambda each: len(each)>0, group_info)))

    # 先构造一个全局的树，包含所有的树结构和层级
    global_tree = Tree() # 全局树
    global_tree.create_node("global_tree", "root")
    # 组装树
    for each in group_info:
        cur_order = list(each)
        cur_order.reverse()
        for i in range(len(cur_order)):
            all_node_tag = [node.tag for node in global_tree.all_nodes()]
            if i == 0 and cur_order[i] not in all_node_tag:
                global_tree.create_node(cur_order[i],cur_order[i],parent="root")
            elif i!=0 and cur_order[i] not in all_node_tag:
                global_tree.create_node(cur_order[i],cur_order[i],parent=cur_order[i-1])
    # 创建一个全局树，并把所有的对应的data object放进去
    cur_global_tree = GlobalTree(tree=global_tree, data_objects=data_objects)

    # 遍历全部data_objects对象，把全局树先放进去
    for each in data_objects.values():
        each.global_tree=cur_global_tree
