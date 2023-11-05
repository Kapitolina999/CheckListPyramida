from typing import Optional, Annotated, Union

from pydantic import BaseModel, field_validator, computed_field, ConfigDict, StringConstraints, Strict

from pydantic_core import PydanticCustomError
from pydantic_core.core_schema import ValidationInfo


class Client(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, validate_default=False)

    type: Annotated[str, StringConstraints(to_upper=True)]
    address: str
    flat: Optional[str]
    account: Annotated[str, StringConstraints(to_lower=True)]
    name: Optional[str]

    @field_validator('type', mode='before')
    def check_type(cls, type_client: Optional[str]) -> str:
        if not type_client:
            raise PydanticCustomError('type', 'Не указан тип клиента "ФЛ"/"ЮЛ"')
        return type_client

    @field_validator('account')
    def check_account(cls, account: str, values) -> str:
        if values.data.get('type') == 'ЮЛ':
            if account.isdigit() and (not account.startswith('74') or len(account) != 14):
                raise PydanticCustomError('account', 'Некорректный лицевой счет')
        elif values.data.get('type') == 'ФЛ':
            if account.isdigit() and len(account) != 12:
                raise PydanticCustomError('account', 'Некорректный лицевой счет')
        return account

    @field_validator('account', mode='after')
    def get_account(cls, account: str, values) -> str:
        if values.data.get('type') == 'ЮЛ':
            if 'общежит' in account:
                return 'Без номера, расчет в БФЛ'
            if 'нсу' in account or 'не на расчет' in account:
                return 'Без номера, на самоуправлении'
        if values.data.get('type') == 'ФЛ' and not account.isdigit():
            return values.data.get('address')
        return account

    @field_validator('name')
    def name(cls, name: str, info: ValidationInfo) -> str:
        if info.data.get('account') == 'Без номера, расчет в БФЛ':
            return 'Общежития'
        if info.data.get('account') == '74000000001000':
            return 'Челябинск: МКД по адресам'
        if info.data.get('account') == 'Без номера, на самоуправлении':
            return 'МКД с НСУ'
        return name

    @field_validator('flat')
    def flat(cls, flat: Optional[str], values) -> Union[str, PydanticCustomError]:
        if values.data.get('type') == 'ЮЛ':
            flat = 'ЮЛ'
        elif values.data.get('type') == 'ФЛ':
            if flat is None and values.data.get('address'):
                raise PydanticCustomError('flat', 'Не указан номер квартиры')
        return flat

    @computed_field
    @property
    def short_account(self) -> str:
        return self.account[2:] if self.account.isdigit() and self.type == 'ФЛ' else self.account
