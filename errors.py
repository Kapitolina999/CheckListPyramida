from datetime import date
from typing import Dict, List

from openpyxl.cell import Cell
from openpyxl.styles import PatternFill
from openpyxl.utils import column_index_from_string
from pydantic import ValidationError
from pydantic_core import ErrorDetails

from meter import Meter


def convert_errors(e: List[ValidationError], custom_messages: Dict[str, str] = None) -> List[ValidationError]:
    """Изменяет сообщение ошибки на кастомное"""

    CUSTOM_MESSAGES = {
        'string_type': 'Некорректное значение',
        'date_past': 'Дата должна быть в прошлом',
        'date_type': 'Указано некорректное значение даты',
        'ip_any_address': 'IP указан не в формате IPv4',
        'date_from_datetime_parsing': 'Указано некорректное значение даты',
        'string_pattern_mismatch': 'Указано некорректное значение',
        'less_than': f'Дата должна быть не раннее, чем {date.today()}'
    }

    if custom_messages is None:
        custom_messages = CUSTOM_MESSAGES
    for error in e:
        custom_message = custom_messages.get(error['type'])
        if custom_message:
            ctx = error.get('ctx')
            error['msg'] = (
                custom_message.format(**ctx) if ctx else custom_message
            )
    return e


def mark_error(row: tuple[Cell], errors, note_col="S") -> None:
    """
    :param note_col: столбец комментариев
    :param row: текущая строка
    :param errors: сообщение об ошибке
    """
    fl = PatternFill(fill_type='solid', start_color='00FFFF00')  # заливка ячейки в случае ошибки
    for cell in row:
        cell.fill = fl

    note_cell = row[column_index_from_string(note_col) - 1]

    for error in errors:
        if error['loc']:
            note_cell.value += f'{error["loc"][0]}: {error["msg"]}\n'
        else:
            note_cell.value += f'{error["type"]}: {error["msg"]}\n'
