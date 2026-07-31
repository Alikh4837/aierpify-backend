# src\customers\enums.py
from enum import StrEnum


class CustomerFieldsEnum(StrEnum):
    """
    Enumeration of customer fields.
    """

    ID = "id"
    USER_ID = "user_id"
    NAME = "name"
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    PROVINCE = "province"
    REGISTRATION_TYPE = "registration_type"
    NATIONAL_TAX_NUMBER = "national_tax_number"
    SALES_TAX_REGISTRATION_NUMBER = "sales_tax_registration_number"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class RegistrationTypeEnum(StrEnum):
    """
    Enumeration of registration types.
    """

    REGISTERED = "Registered"
    UNREGISTERED = "Unregistered"
