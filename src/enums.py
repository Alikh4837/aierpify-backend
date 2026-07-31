# src\enums.py

from enum import Enum, StrEnum
from typing import TypeVar

TENUM = TypeVar("TENUM", bound=Enum)


# -------------------------------- Order Enum -------------------------------- #
class OrderEnum(StrEnum):
    """
    Enum representing the order of items in a list.

    Attributes:
        ASC (str): Represents ascending order.
        DESC (str): Represents descending order.
    """

    ASC = "asc"
    DESC = "desc"


class ProvinceEnum(StrEnum):
    PUNJAB = "Punjab"
    SINDH = "Sindh"
    KHYBER_PAKHTUNKHWA = "Khyber Pakhtunkhwa"
    BALOCHISTAN = "Balochistan"
    CAPITAL_TERRITORY = "Capital Territory"
    GILGIT_BALTISTAN = "Gilgit-Baltistan"
    AZAD_JAMMU_KASHMIR = "Azad Jammu and Kashmir"


class SaleTypeEnum(StrEnum):
    GOODS_STANDARD_RATE = "Goods at standard rate (default)"
    STEEL_MELTING_REROLLING = "Steel melting and re-rolling"
    SHIP_BREAKING = "Ship breaking"
    GOODS_REDUCED_RATE = "Goods at Reduced Rate"
    EXEMPT_GOODS = "Exempt goods"
    GOODS_ZERO_RATE = "Goods at zero-rate"
    THIRD_SCHEDULE_GOODS = "3rd Schedule Goods"
    COTTON_GINNERS = "Cotton ginners"
    TELECOMMUNICATION_SERVICES = "Telecommunication services"
    TOLL_MANUFACTURING = "Toll Manufacturing"
    PETROLEUM_PRODUCTS = "Petroleum Products"
    ELECTRICITY_SUPPLY_RETAILERS = "Electricity Supply to Retailers"
    GAS_CNG_STATIONS = "Gas to CNG stations"
    MOBILE_PHONES = "Mobile Phones"
    PROCESSING_CONVERSION_GOODS = "Processing/Conversion of Goods"
    GOODS_FED_ST_MODE = "Goods (FED in ST Mode)"
    SERVICES_FED_ST_MODE = "Services (FED in ST Mode)"
    SERVICES = "Services"
    ELECTRIC_VEHICLE = "Electric Vehicle"
    CEMENT_CONCRETE_BLOCK = "Cement /Concrete Block"
    POTASSIUM_CHLORATE = "Potassium Chlorate"
    CNG_SALES = "CNG Sales"
    GOODS_SRO_297_2023 = "Goods as per SRO.297(|)/2023"
    NON_ADJUSTABLE_SUPPLIES = "Non-Adjustable Supplies"
    DTRE_GOODS = "DTRE goods"
    SIM = "SIM"
