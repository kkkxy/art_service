"""
读取rhino的3dm文件
并封装成对应data structure
"""
from dataclasses import dataclass, field
from typing import Tuple, List, Any
import re
import rhino3dm
from rhino3dm._rhino3dm import File3dm, TextDot
from shapely.geometry import Polygon, LineString, Point
from art_3dm_reader.rhino_reader_constant import HEIGHT_PATTERN, FLOOR_PATTERN, READ_OPTION, READABLE_OBJ
from art_datastructure.data_structure import DataElement, DataObject, DataTemplate
from art_3dm_reader.data_to_json.data_json_exchange import JsonFileProcessor


class Read3dmFile():
    def __init__(self, file_path: str):
        self.file_path = file_path

    # 导出该3dm文件中所有的group的index以及其名字，并返回
    def __export_file_groups(self, doc: File3dm) -> dict:
        group_index = [each.Index for each in doc.Groups]
        group_name = [each.Name for each in doc.Groups]
        groups_info = dict(map(lambda index, name: (index, name), group_index, group_name))
        return groups_info

    # 导出该3dm文件中所有layer的名字以及其index,并返回
    def __export_file_layers(self, doc: File3dm) -> dict:
        layer_index = [each.Index for each in doc.Layers]
        layer_name = [each.Name for each in doc.Layers]
        layer_info = dict(map(lambda index, name: (index, name), layer_index, layer_name))
        return layer_info

    # 导出该3dm文件中所有文字(文字对应的group上)
    def __export_file_text(self, doc: File3dm) -> dict:
        text_info = {}
        rhino_objects = doc.Objects
        for obj in rhino_objects:
            group_depth = obj.Attributes.GroupCount
            group_indexes = obj.Attributes.GetGroupList()
            geometry = obj.Geometry
            if isinstance(geometry, TextDot) and group_depth > 0:
                text_info[int(group_indexes[0])] = geometry.Text.replace(" ", "")
        return text_info

    # 处理文本中跟高度相关的信息
    def __text_processor(self, text_info: dict, pattern: str) -> dict:
        text_res = {}
        for index, text in text_info.items():
            pattern = re.compile(pattern)
            text = pattern.findall(text)
            num = re.findall(r'[-+]?\d*\.\d+|\d+', text[0])[0]
            text_res[index] = float(num if num != 0 else 0)
        return text_res

    # 将rhino的对象转换成shapely的几何对象
    def __convert_rhino_obj_to_shapely_obj(self,
                                           obj: rhino3dm._rhino3dm.ObjectType) -> None or Point or LineString or Polygon:
        rhino_geometry = obj.Geometry
        # 处理 curve
        if str(rhino_geometry.ObjectType) == 'ObjectType.Curve':
            # 两个点的直线->直线
            if rhino_geometry.IsLinear():
                shapely_geometry = LineString([(rhino_geometry.Line.PointAt(0).X, rhino_geometry.Line.PointAt(0).Y),
                                               (rhino_geometry.Line.PointAt(1).X, rhino_geometry.Line.PointAt(1).Y)])
                return shapely_geometry
            # 闭合曲线->polygon
            elif rhino_geometry.IsPolyline() and rhino_geometry.IsClosed:
                polyline_points = [l for l in rhino_geometry.ToPolyline()]
                shapely_geometry = Polygon([(point.X, point.Y) for point in polyline_points])
                return shapely_geometry
            # 不闭合的多段线->多段线
            elif rhino_geometry.IsPolyline() and rhino_geometry.IsClosed == False:
                polyline_points = [l for l in rhino_geometry.ToPolyline()]
                shapely_geometry = LineString([(point.X, point.Y) for point in polyline_points])
                return shapely_geometry
            else:
                return None
        # 处理点
        elif str(rhino_geometry.ObjectType) == 'ObjectType.Point3d':
            shapely_geometry = Point((rhino_geometry.X, rhino_geometry.Y))
            return shapely_geometry

        # 把TextDot转换成点，渲染的时候把文字渲染到对应的位置上
        elif str(rhino_geometry.ObjectType) == 'ObjectType.TextDot':
            shapely_geometry = Point(
                (rhino_geometry.GetBoundingBox().Center.X, rhino_geometry.GetBoundingBox().Center.Y))
            return shapely_geometry

        # 把文字对象转换成点，渲染的时候把文字渲染到对应的位置上
        elif str(rhino_geometry.ObjectType) == 'ObjectType.Annotation':
            # 暂时无法处理这个东西
            pass

        # TODO 增加更多类型对象的处理方式

        else:
            return None

    # 读取和转换所有的rhino对象
    def __rhino_objects_processor(self, doc: File3dm, layers_info: dict) -> list:
        res = []
        rhino_objects = doc.Objects
        valid_objs = list(filter(lambda each: str(each.Geometry.ObjectType) in READABLE_OBJ, rhino_objects))
        for obj in valid_objs:
            # 给每个对象创建对应的字典
            obj_structure = {}
            # 一些属性
            obj_id = obj.Attributes.Id
            obj_group_depth = obj.Attributes.GroupCount
            obj_group_index = obj.Attributes.GetGroupList()
            obj_layer = layers_info[obj.Attributes.LayerIndex]
            obj_geometry = self.__convert_rhino_obj_to_shapely_obj(obj)
            # 组装中间过程的数据结构
            obj_structure['id'] = obj_id
            obj_structure['geometry'] = obj_geometry
            obj_structure['layer'] = obj_layer
            obj_structure['group_index'] = obj_group_index
            obj_structure['group_depth'] = obj_group_depth
            res.append(obj_structure)
        return res

    # 用DataElements和DataObject封装我们的数据
    def __data_structure_processor(self, raw_data: list, groups_info: dict, text_info: dict, height_info: dict,
                                   floor_info: dict) -> List[DataObject]:
        # 先组装DataElement
        data_elements = []
        for obj in raw_data:
            cur_data_element = DataElement()
            cur_data_element.geometry = obj['geometry']
            cur_data_element.type = obj['layer']
            cur_data_element.group_list = obj['group_index']
            data_elements.append(cur_data_element)
        # 先根据group的名字创建DataObject
        data_objects = {}
        for i in range(len(groups_info)):
            cur_data_object = DataObject()
            cur_data_object.index = i
            cur_data_object.name = groups_info[i]
            if i in floor_info.keys():
                cur_data_object.floor = int(floor_info[i])
            if i in height_info.keys():
                cur_data_object.height = height_info[i]
            if i in text_info.keys():
                cur_data_object.annotations = text_info[i]
            data_objects[cur_data_object.index] = cur_data_object
        # 然后根据group list来把对应的data element放到data object里面
        for element in data_elements:
            if len(element.group_list) > 0:
                data_object_index = element.group_list[0]
                data_objects[data_object_index].elements.append(element)
        # 这里创建关系树，并放到每个data_objects中
        data_template = DataTemplate().assemble_tree(data_elements=data_elements, data_objects=data_objects)

        # 这里把当前文件创建一个style.json
        JsonFileProcessor.create_style_json(file_path=self.file_path, data=raw_data)

        # 返回一个包含所有data object的list
        return data_template

    # 直接调用该函数读取3dm文件
    def read_3dm_file(self):
        # 读取文档
        doc = rhino3dm.File3dm.Read(self.file_path)
        # 解包所有的groups
        groups_info = self.__export_file_groups(doc=doc)
        layers_info = self.__export_file_layers(doc=doc)
        text_info = self.__export_file_text(doc=doc)
        # 处理文本中的高度信息
        height_info = self.__text_processor(text_info=text_info, pattern=HEIGHT_PATTERN)
        floor_info = self.__text_processor(text_info=text_info, pattern=FLOOR_PATTERN)
        # 读取并转换所有的rhino对象
        raw_data = self.__rhino_objects_processor(doc=doc, layers_info=layers_info)
        # 根据选项输出不同的数据
        if READ_OPTION == 0:  # 使用我们的数据结构打包
            return self.__data_structure_processor(raw_data=raw_data, groups_info=groups_info, text_info=text_info,
                                                   height_info=height_info, floor_info=floor_info)
        else:
            return raw_data


# some test for rhino 3dm reader
if __name__ == "__main__":
    TEST_FILE_PATH = "../test_files/3dm_files/site_plan_example_1.3dm"
    template = Read3dmFile(TEST_FILE_PATH).read_3dm_file()
    for each in template.data_objects:
        print(each.tree)
        for node in each.tree.nodes.values():
            print(node.identifier, node.data)
