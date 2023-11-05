import json
import re
from typing import ClassVar, Annotated

from dadata import Dadata
from pydantic import BaseModel, field_validator, computed_field, Field, model_validator, ConfigDict, StringConstraints
from pydantic_core import PydanticCustomError

from client_dadata import dadata


class Address(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    dadata: ClassVar[Dadata] = dadata

    raw_adr: Annotated[str, StringConstraints(to_lower=True)]
    region: str = Field(default='Челябинская обл')
    _data_dadata: dict = {}

    @field_validator('raw_adr', mode='before')
    def check_address(cls, address: str):
        if not address:
            raise PydanticCustomError('address', 'Не указан адрес')
        return address

    @field_validator('raw_adr')
    def remove_trash_address(cls, address: str) -> str:
        """
        Добавляет пробелы после ',' и '.', удаляет двойные пробелы и символ '№'
        :return: откорректированный адрес
        """
        address = re.sub(r',', ', ', address)
        address = re.sub(r'\.', '. ', address)
        address = re.sub(r'\s+', ' ', address)
        address = re.sub(r'№', '', address)
        return address

    @field_validator('raw_adr')
    def check_liter(cls, address: str) -> str:
        result = re.findall(r'((([,.]*)(\sстр(оение)*\.*|,*\sлит(ер)*(а)*\.*))\s([А-ЯЁа-яё]))', address)
        if result:
            return re.sub(result[0][0], result[0][-1], address)
        return address

    @field_validator('raw_adr')
    def check_flat(cls, address: str) -> str:
        if result := re.findall(r'([,.]*\s(ком(н)*(ата)*)\.*,*\s([0-9]))', address):
            return re.sub(result[0][0], f'/{result[0][-1]}', address)
        if result := re.findall(r'(([0-9]+)-([0-9]+)-([0-9]+))', address):
            return re.sub(result[0][0], f'д {result[0][1]}, кв {result[0][2]}/{result[0][3]}', address)
        if result := re.findall(r'((([0-9]+)(,*\s*(кв|квартира)\.*\s*|,*\s))(([0-9]+)-([0-9]+)))', address):
            return re.sub(result[0][0], f'д {result[0][2]}, кв {result[0][-2]}/{result[0][-1]}', address)
        return address

    def save_data(self) -> None:
        with open(f'./data/data_dadata/address.json', encoding='UTF-8') as json_file:
            data = json.load(json_file)
            data.append(self._data_dadata)

        with open(f'./data/data_dadata/address.json', 'w', encoding='UTF-8') as json_file:
            json.dump(data, json_file, ensure_ascii=False, indent=2)

    # @computed_field
    # @property
    # def valid_address(self) -> bool:
    #     if not any((self._data_dadata['city_fias_id'], self._data_dadata['settlement_fias_id'])):
    #         raise PydanticCustomError('address', 'Не указан или не найден населенный пункт')
    #     if not self._data_dadata['street_fias_id']:
    #         raise PydanticCustomError('address', 'Не указана или не найдена улица')
    #     if not self._data_dadata['house_fias_id']:
    #         raise PydanticCustomError('address', 'Не найден дом')
    #     return True

    @computed_field
    @property
    def address(self) -> str:   # Добавить замену: с -> село, д -> деревня и пр
        address = self._data_dadata['result']
        if self.region in address:
            address = address.replace(f'{self.region}, ', '')
        if self._data_dadata['flat']:
            address = address.replace(f', {self._data_dadata["flat_type"]} {self._data_dadata["flat"]}', '')
        return address

    @computed_field
    @property
    def flat(self) -> str | None:
        return self._data_dadata["flat"]

    @model_validator(mode='after')
    def set_data_dadata(self):
        self._data_dadata = self.dadata.clean('address', f'{self.region}, {self.raw_adr}')
        self.save_data()  # после обкатки удалить
        return self

    @model_validator(mode='after')
    def valid_address(self) -> bool:
        if not any((self._data_dadata['city_fias_id'], self._data_dadata['settlement_fias_id'])):
            raise PydanticCustomError('address', 'Не указан или не найден населенный пункт')
        if not self._data_dadata['street_fias_id']:
            raise PydanticCustomError('address', 'Не указана или не найдена улица')
        if not self._data_dadata['house_fias_id']:
            raise PydanticCustomError('address', 'Не найден дом')
        return True

    # @computed_field
    # @property
    # def flag(self) -> bool:
    #     if self._data_dadata['qc'] != 0:
    #         raise PydanticCustomError('address', '')
    #     if self._data_dadata['qc_house'] == 10 and self._data_dadata['qc_geo'] == 1:
    #         raise PydanticCustomError('address', 'Дом не найден в ФИАС, '
    #                                      'но есть похожий на картах')
    #     if self._data_dadata['qc_house'] == 10 and self._data_dadata['qc_geo'] >= 2:
    #         raise PydanticCustomError('address', 'Дом не найден в ФИАС и на картах')
    #     return True
    #
    # @model_validator(mode='after')
    # def check_flag(self):
    #     return self.flag


qc = {
    0: 'Адрес распознан уверенно',
    2: 'Адрес пустой или заведомо «мусорный»',
    1: 'Остались «лишние» части',
    3: 'Есть альтернативные варианты. Пример: «Москва Тверская-Ямская» — в Москве четыре Тверских-Ямских улицы'
}

qc_complete = {
    0: 'Пригоден для почтовой рассылки',
    10:	'Дома нет в ФИАС',
    5: 'Нет квартиры. Подходит для юридических лиц или частных владений',
    8:	'До почтового отделения — абонентский ящик или адрес до востребования. Подходит для писем, но не для курьерской доставки.',
    9:	'Сначала проверьте, правильно ли Дадата разобрала исходный адрес',
    1:	'Нет региона',
    2:	'Нет города',
    3:	'Нет улицы',
    4:	'Нет дома',
    6:	'Адрес неполный'
}

qc_geo = {
    0: 'Точные координаты',
    1: 'Ближайший дом',
    2: 'Улица',
    3: 'Населенный пункт',
    4: 'Город',
    5: 'Координаты не определены'
}
# qc_house=2, qc_geo=любой - Высокая. Дом найден в ФИАС
# qc_house=10, qc_geo=0 - Высокая. Высокая	Дом не найден в ФИАС, но есть на картах
# qc_house=10, qc_geo=1 - Средняя.	Дом не найден в ФИАС, но есть похожий на картах
# qc_house=10, qc_geo>=2 - Низкая.	Дом не найден в ФИАС и на картах
