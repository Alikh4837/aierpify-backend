# src\invoices\enums.py
from enum import StrEnum


class InvoiceFieldsEnum(StrEnum):
    ID = "id"
    USER_ID = "user_id"
    CUSTOMER_ID = "customer_id"
    INVOICE_NUMBER = "invoice_number"
    ISSUE_DATE = "issue_date"
    DUE_DATE = "due_date"
    SUBTOTAL = "subtotal"
    DISCOUNT_AMOUNT = "discount_amount"
    TAX_AMOUNT = "tax_amount"
    TOTAL_AMOUNT = "total_amount"
    STATUS = "status"
    NOTES = "notes"
    INVOICE_TYPE = "invoice_type"
    EXTRA_TAX_AMOUNT = "extra_tax_amount"
    FURTHER_TAX_AMOUNT = "further_tax_amount"
    FEDERAL_ADVANCE_DUTY_PAYABLE_AMOUNT = "federal_advance_duty_payable_amount"
    FBR_VALIDATED = "fbr_validated"
    FBR_STATUS = "fbr_status"
    FBR_REFERENCE = "fbr_reference"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class InvoiceItemFieldsEnum(StrEnum):
    ID = "id"
    INVOICE_ID = "invoice_id"
    PRODUCT_ID = "product_id"
    SALE_TYPE = "sale_type"
    QUANTITY = "quantity"
    UNIT_PRICE = "unit_price"
    RETAIL_PRICE = "retail_price"
    DISCOUNT_PERCENTAGE = "discount_percentage"
    TAX_RATE = "tax_rate"
    LINE_TOTAL = "line_total"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"


class InvoiceStatusEnum(StrEnum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"


class InvoiceFBRStatusEnum(StrEnum):
    PENDING = "pending"
    VALIDATED = "validated"
    SUBMITTED = "submitted"


class InvoiceTypeEnum(StrEnum):
    SALE_INVOICE = "Sale Invoice"
    DEBIT_NOTE = "Debit Note"


class AdditionalTaxTypeEnum(StrEnum):
    NONE = "none"
    _236H = "236H"
    _236G = "236G"
