import datetime
import json
import random
from datetime import date
from ipaddress import IPv4Address, IPv6Address
from typing import ClassVar, Optional, Union

from pydantic import (
    BaseModel,
    PastDate,
    constr,
    IPvAnyAddress,
    field_validator,
    computed_field,
    Field,
    AfterValidator, ValidationError, StringConstraints, BeforeValidator, condate, model_validator, ConfigDict
)
from pydantic_core import PydanticCustomError
from pydantic_core.core_schema import ValidationInfo, ComputedField


def get_ip(ser_sim, path_ip_file):
    with open(path_ip_file, "r", encoding="UTF-8") as json_file:
        ip_data = json.load(json_file)
        for i in ip_data:
            if i["serial"] == ser_sim and i["used"] is False:
                return i['ip']
            elif i["serial"] == ser_sim and i["used"] is True:
                raise PydanticCustomError("ip_error", "IP используется")
        raise PydanticCustomError('ip_error', 'IP не найден')


class Meter(BaseModel, validate_assignment=True):
    model_config = ConfigDict(str_strip_whitespace=True)

    PATH_IP_FILE: ClassVar[str] = './data/IP/ip.json'
    DICT_TYPES: ClassVar[dict] = {
        "ЭМИС-971": "Приборы с поддержкой протокола СПОДЭС - Универсальный счетчик СПОДЭС однофазный",
        "ЭМИС-976": "Приборы с поддержкой протокола СПОДЭС - Универсальный счетчик СПОДЭС трехфазный",
        "СЕ208": "Приборы с поддержкой протокола СПОДЭС - СЕ208 (СПОДЭС)",
    }

    num: str = Field(pattern=r'^[0-9]+$')
    muster_date: condate(lt=date.today())
    install_date: condate(lt=date.today())
    ip: str = Field(pattern=r'^[0-9]+\.*$')
    port: str = Field(default='7012', pattern=r'^[0-9]+$')
    time_zone: str = Field(default='5', pattern=r'^[0-9]{1,2}$')
    user: str = "Высокий уровень доступа (HLS)"

    @field_validator('ip')
    def check_ip(cls, v: str) -> IPv4Address | IPv6Address:
        if v.isdigit():
            with open(cls.PATH_IP_FILE, "r", encoding="UTF-8") as json_file:
                ip_data = json.load(json_file)
                for i in ip_data:
                    if i["serial"] == v and i["used"] is False:
                        return IPvAnyAddress(i['ip'])
                    elif i["serial"] == v and i["used"] is True:
                        raise PydanticCustomError("ip_error", "IP используется")
                raise PydanticCustomError('ip_error', 'IP не найден')
        return IPvAnyAddress(v)

    @field_validator("install_date", mode='after')
    @classmethod
    def install_date_later_muster_date(cls, d: date, info: ValidationInfo) -> date:
        if info.data.get("muster_date") and info.data.get("muster_date") > d:
            raise PydanticCustomError('install_date', 'Дата поверки позже даты установки')
        return d

    @field_validator("num", mode='after')
    @classmethod
    def len_num(cls, num: str) -> str:
        if num.startswith(('971', '976')) and len(num) != 11 or \
                num.startswith(('012', '013')) and len(num) != 15 or \
                num.startswith(('32', '42')) and len(num) != 13 or \
                num.startswith('4') and len(num) != 8:
            raise PydanticCustomError('meter_num', 'Некорректный серийный номер ПУ')
        return num

    @computed_field
    @property
    def manuf_date(self) -> date:
        return self.muster_date - datetime.timedelta(days=random.randint(1, 5))

    @computed_field
    @property
    def title(self) -> str:
        if self.num.startswith("971"):
            return "ЭМИС-971"
        elif self.num.startswith("976"):
            return "ЭМИС-976"
        elif self.num.startswith(("012", "013")):
            return "СЕ208"
        elif self.num.startswith(("42", "32")):
            return "МИРТЕК-12-РУ"
        elif len(self.num) == 8 and self.num.startswith("4"):
            return "Меркурий 234"

    @computed_field
    @property
    def password(self) -> str:
        if 'ЭМИС' in self.title:
            return '0000000000000000'
        elif 'СЕ' in self.title:
            return '1234567812345678'

    @computed_field
    @property
    def type(self) -> str:
        return self.DICT_TYPES[f'{self.title}']

    @computed_field
    @property
    def connect_num(self) -> str:
        if 'ЭМИС' in self.title:
            return str(1000 + int(self.num[-4:]))
        if 'СЕ' in self.title:
            connect_num = int(self.num[-5:])

            while connect_num > 16381:
                connect_num -= 10000
            return str(connect_num)

        if 'МИРТЕК' in self.title:
            connect_num = int(self.num[-5:])

            while connect_num > 65000:
                connect_num -= 10000
            return str(connect_num)

    @computed_field
    @property
    def route(self) -> str:
        return f'{self.ip}:{self.port}'
