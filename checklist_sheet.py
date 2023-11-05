from abc import ABC, abstractmethod
from datetime import date
from typing import ClassVar

from pydantic import BaseModel, computed_field, InstanceOf, model_validator
from pydantic_core import PydanticCustomError

from client import Client
from meter import Meter


class Sheet(BaseModel, ABC):
    number: ClassVar[int] = 0
    columns: ClassVar[list] = ['A']

    @abstractmethod
    @model_validator(mode='after')
    def count_number(self):
        pass

    @computed_field
    @property
    def A(self) -> int:
        return self.number

    def write(self):
        return {col: self.__getattribute__(col) for col in self.columns}


class GeneralSheet(Sheet):
    columns: ClassVar[list] = ['A', 'AB', 'AC', 'AD', 'AE', 'AF', 'AG', 'AH', 'AJ', 'AS', 'AT', 'AU', 'AV', 'AX']

    meter: InstanceOf[Meter]
    client: InstanceOf[Client]

    @model_validator(mode='after')
    def count_number(self):
        GeneralSheet.number += 1
        return self

    @computed_field
    @property
    def AB(self) -> str:
        return self.client.address
    
    @computed_field
    @property
    def AC(self) -> str:
        return self.client.flat
    
    @computed_field
    @property
    def AD(self) -> str:
        return self.meter.type

    @computed_field
    @property
    def AE(self) -> str:
        return self.meter.num

    @computed_field
    @property
    def AF(self) -> date:
        return self.meter.manuf_date

    @computed_field
    @property
    def AG(self) -> date:
        return self.meter.install_date

    @computed_field
    @property
    def AH(self) -> date:
        return self.meter.muster_date

    @computed_field
    @property
    def AJ(self) -> str:
        return self.meter.time_zone

    @computed_field
    @property
    def AS(self) -> str:
        return self.meter.connect_num

    @computed_field
    @property
    def AT(self) -> str:
        return self.meter.user

    @computed_field
    @property
    def AU(self) -> str:
        return self.meter.password

    @computed_field
    @property
    def AV(self) -> str:
        return self.meter.route
    
    @computed_field
    @property
    def AX(self) -> str:
        return self.client.short_account


class IndividualSheet(Sheet):
    cache: ClassVar[tuple] = tuple()
    columns: ClassVar[list] = ['A', 'B', 'C', 'G']

    client: InstanceOf[Client]

    @model_validator(mode='before')
    def check_unique(cls, client):
        if client.get('client').short_account in cls.cache:
            raise PydanticCustomError('account', 'Не уникальный клиент')
        cls.cache += (client.get('client').short_account, )
        return client

    @model_validator(mode='after')
    def count_number(self):
        IndividualSheet.number += 1
        return self

    @computed_field
    @property
    def B(self) -> str:
        return self.client.account

    @computed_field
    @property
    def C(self) -> str:
        return self.B

    @computed_field
    @property
    def G(self) -> str:
        return self.client.short_account


class EntitySheet(Sheet):
    cache: ClassVar[tuple] = tuple()
    columns: ClassVar[list] = ['A', 'B', 'F']

    client: InstanceOf[Client]

    @model_validator(mode='before')
    def check_unique(cls, client):
        if client.get('client').short_account in cls.cache:
            raise PydanticCustomError('account', 'Не уникальный клиент')
        cls.cache += (client.get('client').short_account,)
        return client

    @model_validator(mode='after')
    def count_number(self):
        EntitySheet.number += 1
        return self

    @computed_field
    @property
    def B(self) -> str:
        return self.client.name

    @computed_field
    @property
    def F(self) -> str:
        return self.client.short_account

def reset_cache():
    GeneralSheet.number = 0
    EntitySheet.number = 0
    IndividualSheet.number = 0
    EntitySheet.cache = tuple()
    IndividualSheet.cache = tuple()
