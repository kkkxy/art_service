"""
@ART 基础数据数据结构
"""
from uuid import uuid1, UUID
from dataclasses import dataclass, field
from typing import *
from shapely.geometry import Point, LineString, Polygon
from treelib import Tree


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
    id: str = field(default_factory=uuid1)  # 物件ID
    type: str = field(default="")  # 图层名
    group_list: tuple = field(default=None)  # 编组信息
    has_shadow: bool = field(default=False)  # 几何对象是否有阴影


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
    global_tree: Tree = field(default_factory=Tree)  # 全局树
    floor: int = field(default=0)  # 层数
    height: float = field(default=0.0)  # 高度
    annotations: str = field(default=None)  # 所有文字标注

    # 基准渲染层级
    zorder: int = field(default=0)

    @property
    def tree(self):
        if self.index in self.global_tree.nodes:
            return self.global_tree.subtree(self.index)
        else:
            return None

    # 自己+下级的所有DataElement
    def all_elements(self) -> List[DataElement]:
        elements = []
        object_nodes = self.tree.all_nodes()
        for node in object_nodes:
            elements.extend(node.data.elements)
        return elements

    # 自己+下级的所有DataObject
    def all_objects(self) -> List[DataElement]:
        objects = []
        object_nodes = self.tree.all_nodes()
        for node in object_nodes:
            objects.append(node.data)
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
            self.elements.remove(index)
        else:
            raise Exception("物件中没有输入的元素ID")


class DataTemplate:
    def __init__(self, tree=None, data_objects=None):
        self.tree = tree
        self.data_objects = data_objects

    def assemble_tree(self, data_elements: List[DataElement], data_objects: dict):
        """
        用于组装data_objects的关系树，传入是目前已有的element元素以及obj字典
        :param data_elements:
        :param data_objects:
        :return:
        """
        group_info = [each.group_list for each in data_elements]
        group_info = list(set(filter(lambda each: len(each) > 0, group_info)))

        # 先构造一个全局的树，包含所有的树结构和层级
        global_tree = Tree()  # 全局树
        global_tree.create_node("global_tree", "root")
        # 组装树
        for each in group_info:
            cur_order = list(each)
            cur_order.reverse()
            for i in range(len(cur_order)):
                all_node_tag = [node.tag for node in global_tree.all_nodes()]
                if i == 0 and cur_order[i] not in all_node_tag:
                    global_tree.create_node(cur_order[i], cur_order[i], parent="root", data=data_objects[cur_order[i]])
                elif i != 0 and cur_order[i] not in all_node_tag:
                    global_tree.create_node(cur_order[i], cur_order[i], parent=cur_order[i - 1],
                                            data=data_objects[cur_order[i]])

        # 创建DataTemplate
        self.tree = global_tree
        self.data_objects = [value for value in data_objects.values()]

        # 遍历全部data_objects对象，把全局树先放进去
        for each in data_objects.values():
            each.global_tree = self.tree
        return self

    # # 查找指定物件
    # def find_object(self, arg: int or str):
    #     target_object = None
    #     if isinstance(arg, int):
    #         search_object = max(self.data_objects, key=lambda x: x.index == arg)  # 这里还需要需要修改一下！！！
    #         if search_object.index == arg:
    #             target_object = search_object
    #     elif isinstance(arg, str):
    #         search_object = max(self.data_objects, key=lambda x: x.name == arg)  # 这里还需要需要修改一下！！！
    #         if search_object.name == arg:
    #             target_object = search_object
    #
    #     if target_object is None:
    #         print("没有找到任何信息为{}的物件".format(arg))
    #     return target_object

    # 查找指定物件
    def find_object(self, arg):
        if isinstance(arg, int):
            target = self.tree.expand_tree(filter=lambda x: x.identifier == arg)  # 这里还需要需要修改一下！！！
            for i in target:
                target_object = i
            print("找到物件index, 物件{}".format(target_object))
        elif isinstance(arg, str):
            print(self.tree)
            target = self.tree.expand_tree(filter=lambda x: x.data.name == arg)  # 这里还需要需要修改一下！！！
            for i in target:
                target_object = i
            print("找到物件name, 物件{}".format(target_object))
        else:
            target_object = None
            print("没有找到任何信息为{}的物件".format(arg))
        return target_object

    # # 查找指定物件
    # def find_object(self, arg):
    #     if isinstance(arg, int):
    #         target_object = max(self.data_objects, key=lambda x: x.index == arg)  # 这里还需要需要修改一下！！！
    #         print("找到物件index, 物件{}".format(arg))
    #     elif isinstance(arg, str):
    #         target_object = max(self.data_objects, key=lambda x: x.name == arg)  # 这里还需要需要修改一下！！！
    #         print("找到物件name, 物件{}".format(target_object.index))
    #     else:
    #         target_object = None
    #         print("没有找到任何信息为{}的物件".format(arg))
    #     return target_object


    # # 条件筛选object，需要修改
    # def filter_object(self, tree: Tree,  args):
    #     tree.expand_tree(filter=lambda x: x.data.height > 10)

    # 查重object
    def _check_repetition(self, one_object: DataObject):
        for node in self.tree.all_nodes():
            if one_object.index == node.identifier:
                raise Exception("输入物件已经包含在一个副物件中")
            else:
                pass

    # 添加object
    def add_object(self, one_object: DataObject, parent_index: int):
        self._check_repetition(one_object)
        self.tree.create_node(tag=one_object.index, identifier=one_object.index, parent=parent_index, data=one_object)
        self.data_objects.append(one_object)

    # 插入object
    def insert_object(self, one_object: DataObject, parent_index: int, child_index: int):
        self._check_repetition(one_object)
        self.add_object(one_object, parent_index)
        self.move_object(child_index, one_object.index)

    # 删除object
    def delete_object(self, arg):
        obj = self.find_object(arg)
        if obj is not None:
            removed_objects = obj.all_objects()
            if self.tree.contains(obj.index):
                self.tree.remove_node(obj.index)
            for i in removed_objects:
                self.data_objects.remove(i)
        else:
            raise Exception("找不到要删除的物件")

    # 移动object
    def move_object(self, object_index: int, new_parent_index: int):
        self.tree.move_node(object_index, new_parent_index)