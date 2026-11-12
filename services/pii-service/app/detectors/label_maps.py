"""Mappings from model labels (without B-/I-/E-/S- prefixes) to API categories."""

from collections.abc import Mapping
from types import MappingProxyType

from app.detectors.base import PiiCategory

# https://huggingface.co/openai/privacy-filter
OPENAI_PRIVACY_FILTER_LABELS: Mapping[str, PiiCategory] = MappingProxyType(
    {
        "private_person": PiiCategory.PERSON,
        "private_email": PiiCategory.EMAIL,
        "private_phone": PiiCategory.PHONE,
        "private_address": PiiCategory.ADDRESS,
        "private_url": PiiCategory.URL,
        "private_date": PiiCategory.DATE,
        "account_number": PiiCategory.ACCOUNT_NUMBER,
        "secret": PiiCategory.SECRET,
    }
)

# https://huggingface.co/bardsai/eu-pii-anonimization-multilang-v3
# Labels missing here (organisations, GDPR special categories, amounts, ...)
# are reported as OTHER with their original name in ``source_label``.
BARDSAI_EU_PII_LABELS: Mapping[str, PiiCategory] = MappingProxyType(
    {
        "PERSON_NAME": PiiCategory.PERSON,
        "PERSON_ALIAS": PiiCategory.PERSON,
        "EMAIL_ADDRESS": PiiCategory.EMAIL,
        "PHONE_NUMBER": PiiCategory.PHONE,
        "POSTAL_ADDRESS": PiiCategory.ADDRESS,
        "LOCATION": PiiCategory.LOCATION,
        "GEO_LOCATION": PiiCategory.LOCATION,
        "URL": PiiCategory.URL,
        "IDENTIFYING_LINK": PiiCategory.URL,
        "DATE_OF_BIRTH": PiiCategory.DATE,
        "DATE_TIME": PiiCategory.DATE,
        "ACCOUNT_IDENTIFIER": PiiCategory.ACCOUNT_NUMBER,
        "BANK_ACCOUNT_IDENTIFIER": PiiCategory.ACCOUNT_NUMBER,
        "PAYMENT_CARD": PiiCategory.ACCOUNT_NUMBER,
        "PERSON_IDENTIFIER": PiiCategory.ID_NUMBER,
        "DOCUMENT_IDENTIFIER": PiiCategory.ID_NUMBER,
        "AUTH_SECRET": PiiCategory.SECRET,
        "PAYMENT_CARD_SECURITY": PiiCategory.SECRET,
    }
)
