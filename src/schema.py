"""Schema definitions, column mappings, and record dataclasses."""

from __future__ import annotations
import re
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List


# DDL for SQLite database
CREATE_USERS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone_normalized TEXT NOT NULL,
    phone_raw TEXT,
    name TEXT,
    email TEXT,
    city TEXT,
    state TEXT,
    address TEXT,
    gender TEXT,
    dob TEXT,
    bank TEXT,
    account_type TEXT,
    income TEXT,
    pan TEXT,
    profession_1 TEXT,
    profession_2 TEXT,
    mobile_alerts TEXT,
    extra_data TEXT,
    source_file TEXT
);
"""

CREATE_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_users_phone_normalized ON users(phone_normalized);",
    "CREATE INDEX IF NOT EXISTS idx_users_name ON users(name);",
    "CREATE INDEX IF NOT EXISTS idx_users_city ON users(city);",
]


@dataclass
class UserRecord:
    phone_normalized: str
    phone_raw: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    address: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[str] = None
    bank: Optional[str] = None
    account_type: Optional[str] = None
    income: Optional[str] = None
    pan: Optional[str] = None
    profession_1: Optional[str] = None
    profession_2: Optional[str] = None
    mobile_alerts: Optional[str] = None
    extra_data: Optional[str] = None
    source_file: Optional[str] = None
    id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Exclude None or empty values for clean presentation
        return {k: v for k, v in d.items() if v is not None and str(v).strip() != ""}

    def to_tuple(self) -> tuple:
        return (
            self.phone_normalized,
            self.phone_raw,
            self.name,
            self.email,
            self.city,
            self.state,
            self.address,
            self.gender,
            self.dob,
            self.bank,
            self.account_type,
            self.income,
            self.pan,
            self.profession_1,
            self.profession_2,
            self.mobile_alerts,
            self.extra_data,
            self.source_file,
        )


def clean_col_name(col: str) -> str:
    """Normalize a column header for flexible matching."""
    return re.sub(r"[\s_\-\.\:]", "", str(col)).lower()


# Map standard fields to possible column headers found in files
COLUMN_ALIASES = {
    "phone": {
        "phone", "phonenumber", "mobile", "mobilenumber", "mobileno",
        "customermobile", "billingphone", "contactnumber", "contact",
    },
    "name": {
        "name", "customername", "paytmcustomername", "paytmusername",
        "paytmholdername", "accountholdername", "username", "holdername",
    },
    "email": {
        "email", "emailcontact", "customeremail", "emailid", "mail",
    },
    "city": {
        "city", "shippingcity", "shipping_city",
    },
    "state": {
        "state", "shippingstate",
    },
    "address": {
        "address", "shippingaddress", "custaddress",
    },
    "gender": {
        "gender", "productgender", "sex",
    },
    "dob": {
        "dob", "dateofbirth", "birthdate",
    },
    "bank": {
        "bank", "bankname",
    },
    "account_type": {
        "typofac", "accounttype", "acctype", "type_of_account",
    },
    "income": {
        "incomedeclared", "income", "annualincome",
    },
    "pan": {
        "pan", "pannumber", "panno",
    },
    "profession_1": {
        "proff1", "profession1", "occupation",
    },
    "profession_2": {
        "proff2", "profession2",
    },
    "mobile_alerts": {
        "mobilealerts", "alerts",
    },
}


def match_column(col_name: str) -> Optional[str]:
    """Match a raw column header to a standardized field name."""
    cleaned = clean_col_name(col_name)
    for field_name, aliases in COLUMN_ALIASES.items():
        if cleaned in aliases:
            return field_name
        # Substring heuristics
        if field_name == "phone" and any(k in cleaned for k in ("mobile", "phone", "contact")):
            return field_name
        if field_name == "name" and any(k in cleaned for k in ("customername", "holdername", "username")):
            return field_name
        if field_name == "email" and "email" in cleaned:
            return field_name
        if field_name == "income" and "income" in cleaned:
            return field_name
        if field_name == "pan" and cleaned == "pan":
            return field_name
    return None
