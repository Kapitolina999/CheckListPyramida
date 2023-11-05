import csv
import json
import re
from datetime import date
from typing import Optional, Any, Union, List

from openpyxl.cell import Cell
from openpyxl.styles import PatternFill
from openpyxl.utils import column_index_from_string
from pydantic import ValidationError


def get_install_date(act: str) -> Optional[date]:
    """
    Возвращает дату установки из акта ввода в эксплуатацию
    :param act:
    :return: дата установки ПУ из акта ввода в эксплуатацию
    """
    if act is None:
        return None

    act_date = re.findall(r'(\d+\.\d+\.\d+)', act)

    if act_date:
        act_date = act_date[0]
        act_date.strip(' ')
        act_date = act_date.split('.')
        if len(act_date[2]) == 2:
            act_date[2] = f'20{act_date[2]}'

        act_date = [int(i) for i in act_date]
        return date(act_date[2], act_date[1], act_date[0])


def use_ip(serial_sim: str):
    with open('./data/IP/ip.json', encoding='UTF-8') as json_file:
        ip_data = json.load(json_file)

        for i in ip_data:
            i['used'] = True if i['serial'] == serial_sim else i['used']

        json.dump(ip_data, open('./data/IP/ip.json', 'w', encoding='UTF-8'), indent=2)


def change_dictionary(dictionary: dict) -> dict:
    for key in dictionary.keys():
        if key == 'used':
            if dictionary['used'] == 'true':
                dictionary['used'] = True
            else:
                dictionary['used'] = False
    return dictionary


def csv_to_json(file_csv: str) -> list:
    """
    :param file_csv: файл, из которого необходимо импортировать данные
    :return: список словарей вида {'serial': 'value_serial', 'ip': 'value_ip', 'used': bool}
    """
    with open(f'./data/IP/{file_csv}', encoding='UTF-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        return list(map(lambda i: change_dictionary(i), csv_reader))


def write_to_json(data: list, file_json: str):
    """
    Создает json-файл и записывает в него данные
    :param data: список словарей вида {'serial': 'value_serial', 'ip': 'value_ip', 'used': bool}
    """
    with open(f'./data/IP/{file_json}', 'w', encoding='UTF-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=2)


# write_to_json(csv_to_json('1.csv'), 'ip.json')


def append_to_json(new_data: list, file_json: str):
    """
    :param new_data: список словарей вида {'serial': 'value_serial', 'ip': 'value_ip', 'used': bool}, которые
    необходимо добавить в json-файл
    :param file_json: имя файла, в который необходимо добавить записи
    """
    with open(f'data/IP/{file_json}', encoding='UTF-8') as json_file:
        data = json.load(json_file)
        data.extend(new_data)

    with open(f'data/IP/{file_json}', 'w', encoding='UTF-8') as json_file:
        json.dump(data, json_file, indent=2)


# append_to_json(csv_to_json('IP.csv'), 'ip.json')


class NotValue(ValueError):
    def __init__(self, message='Нет данных'):
        self.message = message

    def __str__(self):
        return self.message


def delete_space(v: Union[str, int]) -> str:
    return str(v).strip('\n').strip()


def get_type_client(cell: str) -> str | None:
    res = re.findall('ФЛ|ЮЛ', cell.upper())
    return res[0] if res else None
