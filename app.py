# app.py - Complete application (ttkbootstrap flatly theme)
# Features:
# - Login (hardcoded admin/admin)
# - Tabs: Customers, Vehicles, Mechanics, Spare Parts, Service Records
# - Add Service with parts selection (inserts into Service_Parts so DB triggers run)
# - PDF bill generation
# - Uses ttkbootstrap (flatly), pillow, fpdf, mysql-connector

import os
import tkinter as tk
from tkinter import messagebox, simpledialog, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from PIL import Image, ImageTk
from fpdf import FPDF
import mysql.connector
from datetime import date

# ---------------- CONFIGURATION ----------------
DB_USER = "root"
DB_PASS = "Manu@7204416352"           # <-- change this to your MySQL root password if different
DB_HOST = "localhost"
DB_NAME = "VehicleServiceManagement"

THEME_NAME = "flatly"      # chosen theme

# ----------------- Bootstrap App Init -----------------
style = ttk.Style(THEME_NAME)
root = style.master
root.title("Vehicle Service Management System")
root.geometry("1200x700")

# ---------------- DB HELPERS -------------------
def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )

def db_query(query, params=None, fetch=False):
    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, params or ())
        if fetch:
            rows = cur.fetchall()
            cur.close()
            conn.close()
            return rows
        else:
            conn.commit()
            cur.close()
            conn.close()
            return None
    except Exception as e:
        if conn:
            try: conn.close()
            except: pass
        raise

def get_next_id(table, col):
    rows = db_query(f"SELECT IFNULL(MAX({col}),0) FROM {table}", fetch=True)
    return rows[0][0] + 1

def safe_int(x, default=0):
    try:
        return int(x)
    except:
        return default

# ---------------- PDF Utility -----------------
def save_pdf_for_service(service_id):
    try:
        svc = db_query("SELECT Service_ID, Vehicle_ID, Mechanic_ID, Service_Date, Problem, Total_Cost, Status, Mileage_At_Service, Duration FROM service_record WHERE Service_ID=%s", (service_id,), fetch=True)
        if not svc:
            messagebox.showwarning("Not found", f"Service {service_id} not found.")
            return
        svc = svc[0]
        parts = db_query("SELECT sp.Part_ID, p.Part_Name, sp.Quantity_Used, sp.Unit_Price, sp.Total_Part_Cost FROM service_parts sp JOIN spare_parts p ON sp.Part_ID=p.Part_ID WHERE sp.Service_ID=%s", (service_id,), fetch=True)
        pdf = FPDF()
        pdf.add_page()

        # shop header
        pdf.set_font("Arial", size=16, style='B')
        pdf.cell(0, 8, "Prime Auto Care Service Center", ln=1, align="C")
        pdf.set_font("Arial", size=12)
        pdf.cell(0, 6, "Bangalore, Karnataka", ln=1, align="C")
        pdf.ln(6)

        pdf.set_font("Arial", size=11)
        pdf.cell(0, 6, f"Service ID: {svc[0]}    Vehicle ID: {svc[1]}    Mechanic ID: {svc[2]}", ln=1)
        pdf.cell(0, 6, f"Service Date: {svc[3]}    Status: {svc[6]}", ln=1)
        pdf.cell(0, 6, f"Problem: {svc[4]}", ln=1)

        pdf.ln(6)
        pdf.set_font("Arial", size=12, style='B')
        pdf.cell(80, 8, "Part Name", border=1)
        pdf.cell(30, 8, "Qty", border=1)
        pdf.cell(40, 8, "Unit Price", border=1)
        pdf.cell(40, 8, "Total", border=1, ln=1)

        pdf.set_font("Arial", size=11)
        total_parts = 0
        for p in parts:
            pdf.cell(80, 8, str(p[1]), border=1)
            pdf.cell(30, 8, str(p[2]), border=1)
            pdf.cell(40, 8, f"{p[3]:.2f}", border=1)
            pdf.cell(40, 8, f"{p[4]:.2f}", border=1, ln=1)
            total_parts += p[4]

        pdf.ln(6)
        pdf.set_font("Arial", size=12, style='B')
        pdf.cell(0, 8, f"Total Parts: {total_parts:.2f}", ln=1)
        pdf.cell(0, 8, f"Service Total Cost: {svc[5]:.2f}", ln=1)

        filename = f"service_bill_{service_id}.pdf"
        pdf.output(filename)

        # auto open PDF
        try:
            os.startfile(filename)
        except:
            pass

        messagebox.showinfo("PDF Saved", f"Bill generated and opened: {filename}")

    except Exception as e:
        messagebox.showerror("PDF Error", str(e))

# ---------------- GUI LAYOUT -----------------
main_frame = ttk.Frame(root, padding=10)
main_frame.pack(fill="both", expand=True)

header = ttk.Label(main_frame, text="Vehicle Service Management System", font=("Helvetica", 18, "bold"))
header.pack(pady=(4,8))

tabs = ttk.Notebook(main_frame)
tabs.pack(expand=1, fill="both")

# -------------------- CUSTOMERS TAB --------------------
cust_tab = ttk.Frame(tabs)
tabs.add(cust_tab, text="Customers")

cust_cols = ("Customer_ID", "Name", "Address", "Phone_No")
cust_tree = ttk.Treeview(cust_tab, columns=cust_cols, show="headings", selectmode="browse")
for c in cust_cols:
    cust_tree.heading(c, text=c)
    cust_tree.column(c, width=220, anchor="w")
cust_tree.pack(fill="both", expand=True, padx=8, pady=6)

search_frame = ttk.Frame(cust_tab)
search_frame.pack(fill="x", padx=8, pady=4)
ttk.Label(search_frame, text="Search Customer:").pack(side="left", padx=6)
cust_search = ttk.Entry(search_frame, width=30)
cust_search.pack(side="left", padx=4)

def load_customers(q=None):
    try:
        if q:
            rows = db_query("SELECT Customer_ID, Name, Address, Phone_No FROM Customer WHERE Name LIKE %s", (f"%{q}%",), fetch=True)
        else:
            rows = db_query("SELECT Customer_ID, Name, Address, Phone_No FROM Customer", fetch=True)
        for i in cust_tree.get_children():
            cust_tree.delete(i)
        for r in rows:
            cust_tree.insert("", "end", values=r)
    except Exception as e:
        messagebox.showerror("DB ERROR", str(e))

def do_search_customer():
    load_customers(cust_search.get().strip())

def add_customer_popup():
    w = ttk.Toplevel(root)
    w.title("Add Customer")
    w.geometry("380x300")
    w.transient(root)
    ttk.Label(w, text="Name").pack(pady=4)
    name = ttk.Entry(w); name.pack(fill="x", padx=10)
    ttk.Label(w, text="Address").pack(pady=4)
    addr = ttk.Entry(w); addr.pack(fill="x", padx=10)
    ttk.Label(w, text="Phone").pack(pady=4)
    ph = ttk.Entry(w); ph.pack(fill="x", padx=10)

    def save():
        try:
            cid = get_next_id("Customer", "Customer_ID")
            db_query("INSERT INTO Customer (Customer_ID, Name, Address, Phone_No) VALUES (%s,%s,%s,%s)",
                     (cid, name.get().strip(), addr.get().strip(), ph.get().strip()))
            messagebox.showinfo("Success", "Customer added.")
            w.destroy(); load_customers()
        except Exception as e:
            messagebox.showerror("DB ERROR", str(e))

    btn_fr = ttk.Frame(w)
    btn_fr.pack(pady=10)
    ttk.Button(btn_fr, text="Save", command=save).pack(side="left", padx=6)
    ttk.Button(btn_fr, text="Cancel", command=w.destroy).pack(side="left", padx=6)

def edit_customer_popup():
    sel = cust_tree.selection()
    if not sel:
        messagebox.showwarning("Select", "Select a customer to edit")
        return
    vals = cust_tree.item(sel[0])['values']
    w = ttk.Toplevel(root); w.title("Edit Customer"); w.geometry("380x300"); w.transient(root)
    ttk.Label(w, text="Name").pack(pady=4); name = ttk.Entry(w); name.insert(0, vals[1]); name.pack(fill="x", padx=10)
    ttk.Label(w, text="Address").pack(pady=4); addr = ttk.Entry(w); addr.insert(0, vals[2]); addr.pack(fill="x", padx=10)
    ttk.Label(w, text="Phone").pack(pady=4); ph = ttk.Entry(w); ph.insert(0, vals[3]); ph.pack(fill="x", padx=10)
    def save():
        try:
            db_query("UPDATE Customer SET Name=%s, Address=%s, Phone_No=%s WHERE Customer_ID=%s",
                     (name.get().strip(), addr.get().strip(), ph.get().strip(), vals[0]))
            messagebox.showinfo("Success", "Customer updated."); w.destroy(); load_customers()
        except Exception as e:
            messagebox.showerror("DB ERROR", str(e))
    btn_fr = ttk.Frame(w); btn_fr.pack(pady=10)
    ttk.Button(btn_fr, text="Save", command=save).pack(side="left", padx=6)
    ttk.Button(btn_fr, text="Cancel", command=w.destroy).pack(side="left", padx=6)

def delete_customer():
    sel = cust_tree.selection()
    if not sel:
        messagebox.showwarning("Select", "Select a customer to delete")
        return
    vals = cust_tree.item(sel[0])['values']
    if messagebox.askyesno("Confirm", f"Delete customer {vals[1]} ({vals[0]})?"):
        try:
            db_query("DELETE FROM Customer WHERE Customer_ID=%s", (vals[0],))
            load_customers()
        except Exception as e:
            messagebox.showerror("DB ERROR", str(e))

cust_btns = ttk.Frame(cust_tab)
cust_btns.pack(fill="x", padx=8, pady=6)
ttk.Button(cust_btns, text="Load Customers", command=lambda: load_customers(None)).pack(side="left", padx=6)
ttk.Button(cust_btns, text="Search", command=do_search_customer).pack(side="left", padx=6)
ttk.Button(cust_btns, text="Add Customer", command=add_customer_popup).pack(side="left", padx=6)
ttk.Button(cust_btns, text="Edit Selected", command=edit_customer_popup).pack(side="left", padx=6)
ttk.Button(cust_btns, text="Delete Selected", command=delete_customer).pack(side="left", padx=6)

# -------------------- VEHICLES TAB --------------------
veh_tab = ttk.Frame(tabs)
tabs.add(veh_tab, text="Vehicles")

veh_cols = ("Vehicle_ID", "Reg_No", "Color", "Mileage", "Customer_ID")
veh_tree = ttk.Treeview(veh_tab, columns=veh_cols, show="headings", selectmode="browse")
for c in veh_cols:
    veh_tree.heading(c, text=c)
    veh_tree.column(c, width=180, anchor="w")
veh_tree.pack(fill="both", expand=True, padx=8, pady=6)

v_search_frame = ttk.Frame(veh_tab)
v_search_frame.pack(fill="x", padx=8, pady=4)
ttk.Label(v_search_frame, text="Search Reg No:").pack(side="left", padx=6)
veh_search = ttk.Entry(v_search_frame, width=30); veh_search.pack(side="left", padx=4)

def load_vehicles(q=None):
    try:
        if q:
            rows = db_query("SELECT Vehicle_ID, Reg_No, Color, Mileage, Customer_ID FROM Vehicle WHERE Reg_No LIKE %s", (f"%{q}%",), fetch=True)
        else:
            rows = db_query("SELECT Vehicle_ID, Reg_No, Color, Mileage, Customer_ID FROM Vehicle", fetch=True)
        for i in veh_tree.get_children():
            veh_tree.delete(i)
        for r in rows:
            veh_tree.insert("", "end", values=r)
    except Exception as e:
        messagebox.showerror("DB ERROR", str(e))

def add_vehicle():
    w = ttk.Toplevel(root); w.title("Add Vehicle"); w.geometry("420x320"); w.transient(root)
    ttk.Label(w, text="Reg No").pack(pady=4); reg = ttk.Entry(w); reg.pack(fill="x", padx=8)
    ttk.Label(w, text="Color").pack(pady=4); color = ttk.Entry(w); color.pack(fill="x", padx=8)
    ttk.Label(w, text="Mileage").pack(pady=4); mil = ttk.Entry(w); mil.pack(fill="x", padx=8)
    ttk.Label(w, text="Customer ID").pack(pady=4); cid = ttk.Entry(w); cid.pack(fill="x", padx=8)
    def save():
        try:
            vid = get_next_id("Vehicle", "Vehicle_ID")
            db_query("INSERT INTO Vehicle (Vehicle_ID, Reg_No, Color, Mileage, Customer_ID) VALUES (%s,%s,%s,%s,%s)",
                     (vid, reg.get().strip(), color.get().strip(), safe_int(mil.get()), safe_int(cid.get())))
            messagebox.showinfo("Success", "Vehicle added"); w.destroy(); load_vehicles()
        except Exception as e:
            messagebox.showerror("DB ERROR", str(e))
    btn_fr = ttk.Frame(w); btn_fr.pack(pady=8)
    ttk.Button(btn_fr, text="Save", command=save).pack(side="left", padx=6)
    ttk.Button(btn_fr, text="Cancel", command=w.destroy).pack(side="left", padx=6)

def edit_vehicle():
    sel = veh_tree.selection()
    if not sel:
        messagebox.showwarning("Select", "Select a vehicle to edit")
        return
    vals = veh_tree.item(sel[0])['values']
    w = ttk.Toplevel(root); w.title("Edit Vehicle"); w.geometry("420x340"); w.transient(root)
    ttk.Label(w, text="Reg No").pack(pady=4); reg = ttk.Entry(w); reg.insert(0, vals[1]); reg.pack(fill="x", padx=8)
    ttk.Label(w, text="Color").pack(pady=4); color = ttk.Entry(w); color.insert(0, vals[2]); color.pack(fill="x", padx=8)
    ttk.Label(w, text="Mileage").pack(pady=4); mil = ttk.Entry(w); mil.insert(0, vals[3]); mil.pack(fill="x", padx=8)
    ttk.Label(w, text="Customer ID").pack(pady=4); cid = ttk.Entry(w); cid.insert(0, vals[4]); cid.pack(fill="x", padx=8)
    def save():
        try:
            db_query("UPDATE Vehicle SET Reg_No=%s, Color=%s, Mileage=%s, Customer_ID=%s WHERE Vehicle_ID=%s",
                     (reg.get().strip(), color.get().strip(), safe_int(mil.get()), safe_int(cid.get()), vals[0]))
            messagebox.showinfo("Success", "Vehicle updated"); w.destroy(); load_vehicles()
        except Exception as e:
            messagebox.showerror("DB ERROR", str(e))
    btn_fr = ttk.Frame(w); btn_fr.pack(pady=8)
    ttk.Button(btn_fr, text="Save", command=save).pack(side="left", padx=6)
    ttk.Button(btn_fr, text="Cancel", command=w.destroy).pack(side="left", padx=6)

def delete_vehicle():
    sel = veh_tree.selection()
    if not sel:
        messagebox.showwarning("Select", "Select a vehicle to delete")
        return
    vals = veh_tree.item(sel[0])['values']
    if messagebox.askyesno("Confirm", f"Delete vehicle {vals[1]} ({vals[0]})?"):
        try:
            db_query("DELETE FROM Vehicle WHERE Vehicle_ID=%s", (vals[0],))
            load_vehicles()
        except Exception as e:
            messagebox.showerror("DB ERROR", str(e))

veh_btns = ttk.Frame(veh_tab)
veh_btns.pack(fill="x", padx=8, pady=6)
ttk.Button(veh_btns, text="Load Vehicles", command=lambda: load_vehicles(None)).pack(side="left", padx=6)
ttk.Button(veh_btns, text="Search", command=lambda: load_vehicles(veh_search.get().strip())).pack(side="left", padx=6)
ttk.Button(veh_btns, text="Add Vehicle", command=add_vehicle).pack(side="left", padx=6)
ttk.Button(veh_btns, text="Edit Selected", command=edit_vehicle).pack(side="left", padx=6)
ttk.Button(veh_btns, text="Delete Selected", command=delete_vehicle).pack(side="left", padx=6)

# -------------------- MECHANICS TAB --------------------
mech_tab = ttk.Frame(tabs)
tabs.add(mech_tab, text="Mechanics")

mech_cols = ("Mechanic_ID", "Name", "Hire_Date", "Salary", "Phone_Number")
mech_tree = ttk.Treeview(mech_tab, columns=mech_cols, show="headings", selectmode="browse")
for c in mech_cols:
    mech_tree.heading(c, text=c)
    mech_tree.column(c, width=180, anchor="w")
mech_tree.pack(fill="both", expand=True, padx=8, pady=6)

def load_mechanics():
    try:
        rows = db_query("SELECT Mechanic_ID, Name, Hire_Date, Salary, Phone_Number FROM Mechanic", fetch=True)
        for i in mech_tree.get_children():
            mech_tree.delete(i)
        for r in rows:
            mech_tree.insert("", "end", values=r)
    except Exception as e:
        messagebox.showerror("DB ERROR", str(e))

def add_mechanic():
    w = ttk.Toplevel(root); w.title("Add Mechanic"); w.geometry("450x350"); w.transient(root)
    ttk.Label(w, text="Name").pack(pady=4); nm = ttk.Entry(w); nm.pack(fill="x", padx=10)
    ttk.Label(w, text="Hire Date (YYYY-MM-DD)").pack(pady=4); hd = ttk.Entry(w); hd.insert(0, str(date.today())); hd.pack(fill="x", padx=10)
    ttk.Label(w, text="Salary").pack(pady=4); sal = ttk.Entry(w); sal.pack(fill="x", padx=10)
    ttk.Label(w, text="Phone").pack(pady=4); ph = ttk.Entry(w); ph.pack(fill="x", padx=10)

    def save():
        try:
            mid = get_next_id("Mechanic", "Mechanic_ID")
            db_query("INSERT INTO Mechanic (Mechanic_ID, Name, Hire_Date, Salary, Phone_Number) VALUES (%s,%s,%s,%s,%s)",
                     (mid, nm.get().strip(), hd.get().strip(), float(sal.get()), ph.get().strip()))
            messagebox.showinfo("Success","Mechanic added"); w.destroy(); load_mechanics()
        except Exception as e:
            messagebox.showerror("DB ERROR", str(e))

    fr = ttk.Frame(w); fr.pack(pady=8)
    ttk.Button(fr, text="Save", command=save).pack(side="left", padx=6)
    ttk.Button(fr, text="Cancel", command=w.destroy).pack(side="left", padx=6)

def edit_mechanic():
    sel = mech_tree.selection()
    if not sel:
        messagebox.showwarning("Select","Select a mechanic to edit")
        return
    vals = mech_tree.item(sel[0])['values']
    w = ttk.Toplevel(root); w.title("Edit Mechanic"); w.geometry("450x350"); w.transient(root)
    ttk.Label(w, text="Name").pack(pady=4); nm = ttk.Entry(w); nm.insert(0, vals[1]); nm.pack(fill="x", padx=10)
    ttk.Label(w, text="Hire Date").pack(pady=4); hd = ttk.Entry(w); hd.insert(0, vals[2]); hd.pack(fill="x", padx=10)
    ttk.Label(w, text="Salary").pack(pady=4); sal = ttk.Entry(w); sal.insert(0, vals[3]); sal.pack(fill="x", padx=10)
    ttk.Label(w, text="Phone").pack(pady=4); ph = ttk.Entry(w); ph.insert(0, vals[4]); ph.pack(fill="x", padx=10)

    def save():
        try:
            db_query("UPDATE Mechanic SET Name=%s, Hire_Date=%s, Salary=%s, Phone_Number=%s WHERE Mechanic_ID=%s",
                     (nm.get().strip(), hd.get().strip(), float(sal.get()), ph.get().strip(), vals[0]))
            messagebox.showinfo("Success","Mechanic updated"); w.destroy(); load_mechanics()
        except Exception as e:
            messagebox.showerror("DB ERROR", str(e))

    fr = ttk.Frame(w); fr.pack(pady=8)
    ttk.Button(fr, text="Save", command=save).pack(side="left", padx=6)
    ttk.Button(fr, text="Cancel", command=w.destroy).pack(side="left", padx=6)

def delete_mechanic():
    sel = mech_tree.selection()
    if not sel:
        messagebox.showwarning("Select","Select a mechanic to delete"); return
    vals = mech_tree.item(sel[0])['values']
    if messagebox.askyesno("Confirm", f"Delete mechanic {vals[1]} ({vals[0]})?"):
        try:
            db_query("DELETE FROM Mechanic WHERE Mechanic_ID=%s", (vals[0],))
            load_mechanics()
        except Exception as e:
            messagebox.showerror("DB ERROR", str(e))

mech_btns = ttk.Frame(mech_tab)
mech_btns.pack(fill="x", padx=8, pady=6)
ttk.Button(mech_btns, text="Load Mechanics", command=load_mechanics).pack(side="left", padx=6)
ttk.Button(mech_btns, text="Add Mechanic", command=add_mechanic).pack(side="left", padx=6)
ttk.Button(mech_btns, text="Edit Selected", command=edit_mechanic).pack(side="left", padx=6)
ttk.Button(mech_btns, text="Delete Selected", command=delete_mechanic).pack(side="left", padx=6)

# -------------------- SPARE PARTS TAB --------------------
sp_tab = ttk.Frame(tabs)
tabs.add(sp_tab, text="Spare Parts")

sp_cols = ("Part_ID", "Part_Name", "Manufacturer", "Unit_Price", "Quantity_In_Stock")
sp_tree = ttk.Treeview(sp_tab, columns=sp_cols, show="headings", selectmode="browse")
for c in sp_cols:
    sp_tree.heading(c, text=c)
    sp_tree.column(c, width=180, anchor="w")
sp_tree.pack(fill="both", expand=True, padx=8, pady=6)

def load_spares():
    try:
        rows = db_query("SELECT Part_ID, Part_Name, Manufacturer, Unit_Price, Quantity_In_Stock FROM Spare_Parts", fetch=True)
        for i in sp_tree.get_children():
            sp_tree.delete(i)
        for r in rows:
            sp_tree.insert("", "end", values=r)
    except Exception as e:
        messagebox.showerror("DB ERROR", str(e))

def add_spare():
    w = ttk.Toplevel(root); w.title("Add Spare"); w.geometry("450x350"); w.transient(root)
    ttk.Label(w, text="Part Name").pack(pady=4); nm = ttk.Entry(w); nm.pack(fill="x", padx=10)
    ttk.Label(w, text="Manufacturer").pack(pady=4); manuf = ttk.Entry(w); manuf.pack(fill="x", padx=10)
    ttk.Label(w, text="Unit Price").pack(pady=4); up = ttk.Entry(w); up.pack(fill="x", padx=10)
    ttk.Label(w, text="Quantity In Stock").pack(pady=4); qty = ttk.Entry(w); qty.pack(fill="x", padx=10)

    def save():
        try:
            pid = get_next_id("Spare_Parts", "Part_ID")
            db_query("INSERT INTO Spare_Parts (Part_ID, Part_Name, Manufacturer, Unit_Price, Quantity_In_Stock) VALUES (%s,%s,%s,%s,%s)",
                     (pid, nm.get().strip(), manuf.get().strip(), float(up.get()), safe_int(qty.get())))
            messagebox.showinfo("Success","Spare added"); w.destroy(); load_spares()
        except Exception as e:
            messagebox.showerror("DB ERROR", str(e))

    fr = ttk.Frame(w); fr.pack(pady=8)
    ttk.Button(fr, text="Save", command=save).pack(side="left", padx=6)
    ttk.Button(fr, text="Cancel", command=w.destroy).pack(side="left", padx=6)

def update_stock():
    sel = sp_tree.selection()
    if not sel:
        messagebox.showwarning("Select", "Select a spare to update")
        return
    vals = sp_tree.item(sel[0])['values']
    newq = simpledialog.askinteger("New Quantity", f"Current: {vals[4]}\nEnter new quantity:")
    if newq is None: return
    try:
        db_query("UPDATE Spare_Parts SET Quantity_In_Stock=%s WHERE Part_ID=%s", (newq, vals[0]))
        load_spares()
    except Exception as e:
        messagebox.showerror("DB ERROR", str(e))

def delete_spare():
    sel = sp_tree.selection()
    if not sel:
        messagebox.showwarning("Select", "Select a spare to delete")
        return
    vals = sp_tree.item(sel[0])['values']
    if messagebox.askyesno("Confirm", f"Delete spare {vals[1]} ({vals[0]})?"):
        try:
            db_query("DELETE FROM Spare_Parts WHERE Part_ID=%s", (vals[0],))
            load_spares()
        except Exception as e:
            messagebox.showerror("DB ERROR", str(e))

sp_btns = ttk.Frame(sp_tab)
sp_btns.pack(fill="x", padx=8, pady=6)
ttk.Button(sp_btns, text="Load Spares", command=load_spares).pack(side="left", padx=6)
ttk.Button(sp_btns, text="Add Spare", command=add_spare).pack(side="left", padx=6)
ttk.Button(sp_btns, text="Update Stock", command=update_stock).pack(side="left", padx=6)
ttk.Button(sp_btns, text="Delete Selected", command=delete_spare).pack(side="left", padx=6)

# -------------------- SERVICE RECORDS TAB (with parts) --------------------
svc_tab = ttk.Frame(tabs)
tabs.add(svc_tab, text="Service Records")

svc_cols = ("Service_ID","Vehicle_ID","Mechanic_ID","Service_Date","Problem","Total_Cost","Status","Mileage_At_Service","Duration")
svc_tree = ttk.Treeview(svc_tab, columns=svc_cols, show="headings", selectmode="browse")
for c in svc_cols:
    svc_tree.heading(c, text=c)
    svc_tree.column(c, width=150, anchor="w")
svc_tree.pack(fill="both", expand=True, padx=8, pady=6)

def load_services():
    try:
        rows = db_query("SELECT Service_ID,Vehicle_ID,Mechanic_ID,Service_Date,Problem,Total_Cost,Status,Mileage_At_Service,Duration FROM Service_Record", fetch=True)
        for i in svc_tree.get_children():
            svc_tree.delete(i)
        for r in rows:
            svc_tree.insert("", "end", values=r)
    except Exception as e:
        messagebox.showerror("DB ERROR", str(e))

def delete_service():
    sel = svc_tree.selection()
    if not sel:
        messagebox.showwarning("Select","Select a service record")
        return
    vals = svc_tree.item(sel[0])['values']
    if messagebox.askyesno("Confirm",f"Delete Service {vals[0]}?"):
        try:
            db_query("DELETE FROM Service_Record WHERE Service_ID=%s",(vals[0],))
            load_services()
        except Exception as e:
            messagebox.showerror("DB ERROR", str(e))

# --- Add Service with parts selection
def add_service_with_parts():
    w = ttk.Toplevel(root)
    w.title("Add Service (with Parts)")
    w.geometry("700x600")
    w.transient(root)

    def make_entry(lbl, default=""):
        ttk.Label(w, text=lbl).pack(pady=2)
        e = ttk.Entry(w)
        e.insert(0, default)
        e.pack(fill="x", padx=10)
        return e

    veh = make_entry("Vehicle ID")
    mech = make_entry("Mechanic ID")
    dt = make_entry("Service Date (YYYY-MM-DD)", str(date.today()))
    prob = make_entry("Problem")
    stat = make_entry("Status", "In Progress")
    mil = make_entry("Mileage At Service")
    dur = make_entry("Duration (hours)")

    parts_selected = []  # list of [Part_ID, Part_Name, qty, unit_price]

    # parts listbox in main add window
    parts_frame = ttk.LabelFrame(w, text="Selected Parts (Name | Qty | Unit Price)")
    parts_frame.pack(fill="both", expand=False, padx=10, pady=8)
    parts_listbox = tk.Listbox(parts_frame, height=8)
    parts_listbox.pack(fill="both", expand=True, padx=6, pady=6)

    def refresh_parts_list():
        parts_listbox.delete(0, tk.END)
        for p in parts_selected:
            parts_listbox.insert(tk.END, f"{p[1]} | {p[2]} | {p[3]:.2f}")

    def remove_selected_part():
        sel = parts_listbox.curselection()
        if not sel:
            return
        idx = sel[0]
        parts_selected.pop(idx)
        refresh_parts_list()

    ttk.Button(parts_frame, text="Remove Selected Part", command=remove_selected_part).pack(pady=4)

    def choose_parts():
        pwin = ttk.Toplevel(w)
        pwin.title("Select Parts")
        pwin.geometry("760x420")
        pwin.transient(w)

        tv = ttk.Treeview(pwin, columns=("Part_ID","Name","Unit_Price","QtyInStock"), show="headings", selectmode="extended")
        tv.heading("Part_ID", text="Part_ID"); tv.heading("Name", text="Part_Name")
        tv.heading("Unit_Price", text="Unit_Price"); tv.heading("QtyInStock", text="In Stock")
        tv.column("Part_ID", width=80); tv.column("Name", width=320); tv.column("Unit_Price", width=120); tv.column("QtyInStock", width=100)
        tv.pack(fill="both", expand=True, padx=6, pady=6)

        try:
            rows = db_query("SELECT Part_ID, Part_Name, Unit_Price, Quantity_In_Stock FROM Spare_Parts", fetch=True)
            for r in rows:
                tv.insert("", "end", values=r)
        except Exception as e:
            messagebox.showerror("DB ERROR", str(e))
            pwin.destroy()
            return

        qty_frame = ttk.Frame(pwin)
        qty_frame.pack(pady=6)
        ttk.Label(qty_frame, text="Quantity to use for selected part(s):").pack(side="left", padx=6)
        qty_e = ttk.Entry(qty_frame, width=8); qty_e.pack(side="left", padx=6)

        def add_selected():
            sel = tv.selection()
            if not sel:
                messagebox.showwarning("Select", "Select one or more parts from the list")
                return
            q = safe_int(qty_e.get(), None)
            if q is None or q <= 0:
                messagebox.showwarning("Quantity", "Enter a valid integer quantity > 0")
                return
            for s in sel:
                row = tv.item(s)['values']  # (Part_ID, Part_Name, Unit_Price, InStock)
                pid, pname, unitp, instock = row[0], row[1], float(row[2]), int(row[3])
                if q > instock:
                    if not messagebox.askyesno("Low stock", f"Requested {q} for {pname} but only {instock} in stock. Proceed?"):
                        return
                parts_selected.append([pid, pname, q, unitp])
            refresh_parts_list()
            pwin.destroy()

        ttk.Button(qty_frame, text="Add Selected with Qty", command=add_selected).pack(side="left", padx=6)
        ttk.Button(qty_frame, text="Cancel", command=pwin.destroy).pack(side="left", padx=6)

    def save_service_and_parts():
        try:
            sid = get_next_id("Service_Record", "Service_ID")
            vid = safe_int(veh.get())
            mid = safe_int(mech.get())
            sdate = dt.get().strip()
            problem_text = prob.get().strip()
            status_text = stat.get().strip()
            mileage_val = safe_int(mil.get())
            duration_val = safe_int(dur.get())

            db_query("""INSERT INTO Service_Record(Service_ID, Vehicle_ID, Mechanic_ID, Service_Date, Problem, Total_Cost, Status, Mileage_At_Service, Duration)
                        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                     (sid, vid, mid, sdate, problem_text, 0.0, status_text, mileage_val, duration_val))

            for p in parts_selected:
                db_query("INSERT INTO Service_Parts (Service_ID, Part_ID, Quantity_Used, Unit_Price) VALUES (%s,%s,%s,%s)",
                         (sid, p[0], p[2], p[3]))

            messagebox.showinfo("Success", f"Service {sid} added with {len(parts_selected)} part(s).")
            w.destroy()
            load_services()
            load_spares()
        except Exception as e:
            messagebox.showerror("DB ERROR", str(e))

    control_fr = ttk.Frame(w)
    control_fr.pack(pady=8)
    ttk.Button(control_fr, text="Choose Parts", command=choose_parts).pack(side="left", padx=6)
    ttk.Button(control_fr, text="Save Service + Parts", command=save_service_and_parts).pack(side="left", padx=6)
    ttk.Button(control_fr, text="Cancel", command=w.destroy).pack(side="left", padx=6)

def view_parts_of_service():
    sel = svc_tree.selection()
    if not sel:
        messagebox.showwarning("Select", "Select a service row first")
        return
    svc_id = svc_tree.item(sel[0])['values'][0]
    try:
        parts = db_query("SELECT sp.Part_ID, p.Part_Name, sp.Quantity_Used, sp.Unit_Price, sp.Total_Part_Cost FROM Service_Parts sp JOIN Spare_Parts p ON sp.Part_ID=p.Part_ID WHERE sp.Service_ID=%s", (svc_id,), fetch=True)
        w = ttk.Toplevel(root); w.title(f"Parts for Service {svc_id}"); w.geometry("520x320"); w.transient(root)
        tv = ttk.Treeview(w, columns=("Part_ID","Part_Name","Qty","Unit_Price","Total"), show="headings")
        tv.heading("Part_ID", text="Part_ID"); tv.heading("Part_Name", text="Name"); tv.heading("Qty", text="Qty"); tv.heading("Unit_Price", text="Unit Price"); tv.heading("Total", text="Total")
        tv.pack(fill="both", expand=True, padx=6, pady=6)
        for p in parts:
            tv.insert("", "end", values=p)
    except Exception as e:
        messagebox.showerror("DB ERROR", str(e))

svc_btns = ttk.Frame(svc_tab)
svc_btns.pack(fill="x", padx=8, pady=6)
ttk.Button(svc_btns, text="Load Services", command=load_services).pack(side="left", padx=6)
ttk.Button(svc_btns, text="Add Service (with parts)", command=add_service_with_parts).pack(side="left", padx=6)
ttk.Button(svc_btns, text="View Parts for Selected", command=view_parts_of_service).pack(side="left", padx=6)
ttk.Button(svc_btns, text="Delete Selected", command=delete_service).pack(side="left", padx=6)
ttk.Button(svc_btns, text="Generate PDF Bill", command=lambda: (lambda sel=svc_tree.selection(): save_pdf_for_service(svc_tree.item(sel[0])['values'][0]) if sel else messagebox.showwarning("Select","Select service"))()).pack(side="left", padx=6)

# -------------------- Bottom controls --------------------
bottom_frame = ttk.Frame(main_frame)
bottom_frame.pack(fill="x", padx=10, pady=6)
ttk.Button(bottom_frame, text="Refresh All", command=lambda: (load_customers(), load_vehicles(), load_mechanics(), load_spares(), load_services())).pack(side="left", padx=8)
ttk.Button(bottom_frame, text="Open SQL File", command=lambda: filedialog.askopenfilename()).pack(side="left", padx=8)
ttk.Button(bottom_frame, text="Exit", command=root.destroy).pack(side="right", padx=8)

# ------------------ Preload (safe) ---------------------
try:
    load_customers(); load_vehicles(); load_mechanics(); load_spares(); load_services()
except Exception:
    # ignore at startup; user can press Load buttons
    pass

# ------------------ Simple Login Window ------------------
def show_login_modal():
    L = ttk.Toplevel(root)
    L.title("Login"); L.geometry("360x180"); L.transient(root); L.grab_set()
    ttk.Label(L, text="Username").pack(pady=6); ue = ttk.Entry(L); ue.pack(fill="x", padx=20)
    ttk.Label(L, text="Password").pack(pady=6); pe = ttk.Entry(L, show="*"); pe.pack(fill="x", padx=20)
    def attempt():
        u = ue.get().strip(); p = pe.get().strip()
        if u == "admin" and p == "admin":
            L.destroy()
        else:
            messagebox.showerror("Login failed", "Use username: admin and password: admin")
    ttk.Button(L, text="Login", command=attempt).pack(pady=12)
    root.wait_window(L)

# show login first
show_login_modal()

# start
root.mainloop()
