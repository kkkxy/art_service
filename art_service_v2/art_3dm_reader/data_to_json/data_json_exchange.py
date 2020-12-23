"""
for reading or writing data to json or from json
"""
import pathlib
import json
from typing import *
from art_3dm_reader.rhino_reader_constant import STYLE_JSON_PATH
from art_3dm_reader.data_to_json.style_json_template import OBJ_STYLE_TEMPLATE

def input_json(file_path: str) -> Dict:  # 读取json文件
    """
    用于读取从rhino写入的json文件
    :param file_path:
    :return:
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def output_json(data, file_path: str):  # write your data to json file
    with open(file_path, 'w') as f:
        json.dump(data,f)
        print('->>>>>>>>>>>json文件写入完毕')


class JsonFileProcessor:

    @staticmethod
    def create_style_json(file_path:str, data:list):
        # 获取当前3dm的文件名
        file_name = file_path.split('/')[-1]
        # 检查该路径是否存在该文件，不存在就创建，存在就不创建
        style_json_name = file_name.split('.')[0]+'.json'
        path = pathlib.Path(f'{STYLE_JSON_PATH}/{style_json_name}')
        if path.is_file():   # 如果已经存在该文件跳过
            print(f'指定路径中已经存在{style_json_name}!')
        else:      # 这个地方开始创建所有的对象)
            all_layers = set([each['layer'] for each in data])
            style_dict = {}
            for each in all_layers:
                style_dict[each] = OBJ_STYLE_TEMPLATE
            output_json(data=style_dict, file_path=f'{STYLE_JSON_PATH}/{style_json_name}')


