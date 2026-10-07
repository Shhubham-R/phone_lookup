# Production-Ready High-Speed Phone Number Lookup System

A modular, local, high-speed phone number search engine capable of sub-millisecond lookups across millions of sensitive user records using SQLite with WAL mode and B-Tree indexing.

---

## 1. Dataset Inspection & Architectural Analysis

Before building the system, the dataset located at `C:\Users\sp\Music\Paytm_Users_Database\Paytm_Users_Database` was inspected using cryptographic checksums and schema analysis:

### 1.1 Source File Inventory & Deduplication
| File Name | File Size | Classification | Status |
| :--- | :--- | :--- | :--- |
| `Merged_Master_Data.csv` | 572.98 MB | Merged Master Dataset (3,494,058 rows) | Primary Source |
| `Merged_Master_Data.xlsx` | 225.27 MB | Excel Master (4 sheets, 3.49M rows) | Master Excel |
| `Paytm_Final_Master.xlsx` | 225.46 MB | Excel Master variant (4 sheets, 60 cols) | Master Excel |
| `Paytm 10 Lakh.xlsx` | 72.04 MB | Raw User Records (1,004,415 rows) | Unique Source File |
| `Paytm 1004415.xlsx` | 66.67 MB | Raw User Records (1,004,415 rows) | Unique Source File |
| `Paytm Data 9.5 lakh.xlsx` | 69.99 MB | Raw User Records (1,032,057 rows) | Identical to `Paytm Data-1.xlsx` |
| `Paytm Data-10 lakh.xlsx` | 63.90 MB | Raw User Records (986,356 rows) | Identical to `Paytm Data-3.xlsx` |
| `Paytm Data- 5 lakh.xlsx` | 60.50 MB | Raw User Records (497,932 rows) | Identical to `Paytm Data-2.xlsx` |
| `Paytm 100653.xlsx` | 6.66 MB | Raw User Records (100,653 rows) | Unique Source File |
| `PAN India Paytm Users.xlsx` | 4.18 MB | Raw User Records (51,663 rows) | Unique Source File |
| `Maharastha 50K Paytm.xlsx` | 3.36 MB | Raw User Records (50,719 rows) | Unique Source File |
| `Paytm data New.xlsx` | 9.47 MB | E-commerce / Mall Users (50,846 rows) | Identical to `Paytm Mall Onlin shoping New.xlsx` |

### 1.2 Identified Phone Columns Across Source Files
Different Excel files use varying column headers for phone numbers:
- `Phone_Number` (in `Merged_Master_Data.csv` & master files)
- `Mobile No` / `Mobile No.` (in `Paytm 10 Lakh.xlsx`, `PAN India Paytm Users.xlsx`, `Paytm Data 9.5 lakh.xlsx`)
- `Customer_Mobile` (in `Maharastha 50K Paytm.xlsx`)
- `MOBILE NO` (in `Paytm Data- 5 lakh.xlsx`)
- `Billing_Phone` (in `Paytm data New.xlsx`)

### 1.3 Phone Number Storage & Format Anomalies
Our data quality audit across **3,494,058 records** revealed:
- **Clean 10-Digit Indian Numbers**: 2,975,960 (85.17%)
- **Prefixed with `91` (12 digits)**: 516,886 (14.80%)
- **Spaces / Hyphens / Parentheses**: 777 records (e.g. `022-25542869`, `079 - 23236989`)
- **Excel Scientific Notation / Float strings**: Present in raw data (e.g. `9.876543210E+09`, `9876543210.0`)
- **Multiple Numbers in One Cell**: 174 records (e.g. `9819969920 9833020247`, `9892207681, 9321020521`)
- **Duplicate Phone Numbers**: 36,670 phone keys associated with multiple distinct user profiles/transactions.

---

## 2. Benchmark & Performance Results

Lookups run directly against the B-Tree index on `users(phone_normalized)` with safe SQLite WAL mode optimizations:

```
=======================================================
           DATABASE LOOKUP BENCHMARK (10,000 Lookups)
=======================================================
Database File     : data/users.db (1.01 GB)
Total Records     : 3,493,875
Query Throughput  : 18,263.8 lookups/sec
-------------------------------------------------------
DATABASE QUERY TIME (Pure SQL Indexed Lookup):
  Minimum              : 0.020 ms
  Average              : 0.034 ms
  Median (P50)         : 0.029 ms
  95th Percentile (P95): 0.063 ms
  99th Percentile (P99): 0.091 ms
  Maximum              : 0.246 ms
-------------------------------------------------------
TOTAL APPLICATION TIME (Validation + Normalization + Query + Object Mapping):
  Minimum              : 0.032 ms
  Average              : 0.053 ms
  Median (P50)         : 0.045 ms
  95th Percentile (P95): 0.095 ms
  99th Percentile (P99): 0.132 ms
  Maximum              : 0.337 ms
=======================================================
```

---

## 3. Project Structure

```
phone_lookup/
│
├── data/
│   └── users.db             # 1.01 GB SQLite database with B-Tree indexes
│
├── src/
│   ├── __init__.py          # Package initialization
│   ├── database.py          # DatabaseRepository interface & SQLiteRepository implementation
│   ├── normalization.py     # Phone normalization & validation engine
│   ├── importer.py          # High-throughput streaming batch data ingestion
│   ├── lookup.py            # LookupEngine & result formatting
│   ├── schema.py            # UserRecord dataclass, SQL DDL, column mapping
│   └── validation.py        # Input sanitization and query validation
│
├── build_database.py        # Bulk ingestion script with progress indicator
├── lookup.py                # Interactive terminal search application
├── benchmark.py             # Latency & throughput benchmark suite
├── stats.py                 # Database statistics & integrity verification
├── data_quality.py          # Comprehensive data quality audit tool
├── requirements.txt         # Minimal dependencies (openpyxl)
├── README.md                # Comprehensive documentation
├── .gitignore               # Excludes sensitive data, DBs, and virtualenvs
└── tests/
    ├── test_normalization.py# Comprehensive normalization unit tests
    ├── test_database.py     # Repository and batch insert tests
    └── test_lookup.py       # Lookup query variations and engine tests
```

---

## 4. Phone Normalization Rules

The normalization engine handles:
1. **10-Digit Indian Mobile**: `9876543210` -> `9876543210`
2. **Country Code `+91`**: `+91 98765 43210`, `+91-9876543210`, `+919876543210` -> `9876543210`
3. **Prefix `91` (12 Digits)**: `919876543210` -> `9876543210`
4. **Leading Zero (11 Digits)**: `09876543210` -> `9876543210`
5. **Excel Scientific Notation / Float**: `9.876543210E+09` / `9876543210.0` -> `9876543210`
6. **Hyphens / Spaces / Parentheses**: `(022) 2554-2869` -> `02225542869`
7. **Multiple Phone Numbers**: Extracts primary number and supports extracting all tokens.
8. **International Formats**: Retains valid `+<country_code><number>` format (e.g. `+971 50 5651438` -> `+971505651438`).

---

## 5. Usage Instructions

### 5.1 Ingestion (Run Once)
To build and index the local SQLite database from the source files:
```bash
python build_database.py
```
*Note: The database is already pre-built and indexed at `data/users.db`.*

### 5.2 Terminal Search Application
Launch the interactive lookup terminal:
```bash
python lookup.py
```

**Interactive Example:**
```text
============================================================
        PHONE NUMBER LOOKUP SYSTEM
============================================================
Database     : data/users.db
Records      : 3,493,875
Indexed Field: phone_normalized (B-Tree index)
Status       : READY
------------------------------------------------------------
Enter phone number:
> +91 80000 04421

FOUND (2 records)
Normalized Key : 8000004421
---------------------------------------------
Result 1
-----------------------------------
Name                : Chitrank Murark
Phone (Normalized)  : 8000004421
Phone (Original)    : 918000004421
City                : Surat
Account Type        : Individual
Income              : Rs. 10.55 lacs annually
PAN                 : ABSPC5687Q
Profession          : Driving License
Profession 2        : Driving License
Source              : Merged_Master_Data.csv
Email Contact       : chitrank.m@gmail.com
Mobile Alerts       : Yes
-----------------------------------
Result 2
-----------------------------------
Name                : Muraka
Phone (Normalized)  : 8000004421
City                : Surat
Account Type        : OTHER
Income              : Rs. 15.0 lacs annually
Profession          : Voter ID Card
Profession 2        : Passport
Source              : Merged_Master_Data.csv
Email Contact       : chitrank@utsavfabrics.com
Mobile Alerts       : Yes
---------------------------------------------
Lookup time   : 2.49 ms (DB query: 0.20 ms)
Records found : 2
---------------------------------------------
```

**Direct Command-Line Lookup:**
```bash
python lookup.py 9876543210
python lookup.py "+91 98765 43210"
```

### 5.3 Database Statistics
```bash
python stats.py
```

### 5.4 Benchmarking
```bash
python benchmark.py --queries 10000
```

### 5.5 Data Quality Audit
```bash
python data_quality.py
```

### 5.6 Running Tests
```bash
python -m unittest discover -s tests -v
```

---

## 6. Multi-Record & Duplicate Handling Policy

The system adheres strictly to the rule:
> **One phone number != one person.**

- **Preservation**: All distinct user records sharing the same phone number are preserved in the database.
- **Reporting**: When a phone number matches multiple records, the lookup returns all matches with their individual details (PAN, name, account type, income, email, etc.).
- **No Silent Overwrites**: Ingestion uses `id AUTOINCREMENT` rather than a unique constraint on phone number, preventing data loss.

---

## 7. Future Production Architecture & PostgreSQL Migration

The architecture uses an abstract `DatabaseRepository` interface in `src/database.py`:

```
User Query / Client
       ↓
LookupEngine (Validation + Normalization)
       ↓
DatabaseRepository (Abstract Interface)
   ├── SQLiteRepository (Current Local Production)
   └── PostgresRepository (Future Scale-Out)
```

To migrate to PostgreSQL:
1. Implement `PostgresRepository` subclassing `DatabaseRepository`.
2. Connect using `psycopg2` or `asyncpg` connection pool.
3. Use `CREATE INDEX idx_users_phone ON users(phone_normalized);`.
4. Wrap in a FastAPI microservice with an optional Redis cache for frequent lookups.

---

## 8. Security & Data Protection
- **Local Isolation**: All ingestion, indexing, and lookup operations run strictly locally.
- **No Telemetry / Cloud Calls**: No external HTTP requests or third-party analytics are made.
- **Parameterized SQL**: All database operations use parameterized queries (`?`) to prevent SQL injection.
- **Git Protection**: Sensitive data files (`*.xlsx`, `*.csv`, `*.db`, `*.sqlite`) are ignored via `.gitignore`.
