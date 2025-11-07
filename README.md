```markdown
# Vehicle Service Management System
DBMS Mini Project
PES University Bangalore

## Team Members
| Name | SRN |
|------|------|
| **Jaypal Reddy** | PES1UG23AM125 |
| **Manu Prasad H S** | PES1UG23AM167 |

---

## Overview
A **Vehicle Service Management System** with **Python GUI** and **MySQL backend**. It handles customers, vehicles, mechanics, spare parts, service records, and generates **PDF bills**.

---

## Technologies
| Component | Technology |
|----------|------------|
| **Frontend GUI** | Python Tkinter + **ttkbootstrap** (flatly theme) |
| **Backend** | Python |
| **Database** | MySQL |
| **PDF Bill** | **FPDF** |
| **Images** | **Pillow** (PIL) |

---

## Features
* Customers/Vehicle/Mechanic/Parts **CRUD** (Create, Read, Update, Delete)
* Create **Service Record** with spare parts
* **Automatic stock deduction** with **triggers**
* **Automatic total cost** with **triggers**
* **PDF bill generation**
* Login screen

---

## How to Run

### Install modules
```

pip install mysql-connector-python
pip install ttkbootstrap
pip install pillow
pip install fpdf

```

### Steps
1) Create database `VehicleServiceManagement` in MySQL
2) Run all SQL (tables + triggers) from `SQL_code.sql`
3) Open `app.py`
4) Set mysql password inside code
5) Run:
```

python app.py

```

### Login Credentials
```

username: admin
password: admin

```

---

## PDF Bill Details
The PDF bill contains the following header:
```

Prime Auto Care Service Center
Bangalore, Karnataka

```
File name format:
```

service\_bill\_\<ID\>.pdf

```

---

## Files
| File | Description |
|------|-------------|
| **app.py** | Main GUI application |
| **SQL_code.sql** | Database tables + triggers code |
| **README.md** | Documentation (This file) |

---

## Conclusion
This project demonstrates **full DBMS application integration**: **GUI** + **MySQL** + **triggers** + **billing**.
```

