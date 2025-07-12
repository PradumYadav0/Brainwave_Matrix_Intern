import sqlite3
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk, filedialog
from tkinter import scrolledtext
import hashlib
from datetime import datetime
import csv
import os

# Database setup
def init_db():
    conn = sqlite3.connect('inventory.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT,
            role TEXT DEFAULT 'staff' CHECK(role IN ('admin', 'staff', 'pending')),
            approved INTEGER DEFAULT 0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            quantity INTEGER NOT NULL CHECK(quantity >= 0 AND quantity <= 10000),
            price REAL NOT NULL CHECK(price >= 0 AND price <= 100000),
            category TEXT NOT NULL,
            low_threshold INTEGER DEFAULT 10 CHECK(low_threshold >= 0 AND low_threshold <= 100),
            supplier_id INTEGER,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            type TEXT,
            quantity INTEGER,
            date TEXT,
            user TEXT,
            new_price REAL,
            FOREIGN KEY (product_id) REFERENCES products(id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT NOT NULL,
            date TEXT,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'resolved'))
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT,
            details TEXT,
            user TEXT,
            timestamp TEXT
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_id ON transactions(product_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_username ON users(username)')
    cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',))
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO users (username, password_hash, role, approved) VALUES (?, ?, ?, ?)', 
                      ('admin', hashlib.sha256('password123'.encode()).hexdigest(), 'admin', 1))
    conn.commit()
    conn.close()

class InventorySystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Inventory Management System")
        self.current_user = None
        self.theme = "light"
        self.style = ttk.Style()
        self.init_ui()
        self.configure_styles()  # Initialize styles
        init_db()
        self.create_login_screen()

    def init_ui(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def configure_styles(self):
        # Light theme
        self.style.configure('Light.TFrame', background='#F0F8FF')
        self.style.configure('Light.TLabel', background='#F0F8FF', foreground='black')
        self.style.configure('Light.TButton', background='#E0E0E0', foreground='black')
        self.style.configure('Light.TEntry', fieldbackground='#FFFFFF', foreground='black')
        self.style.configure('Light.Treeview', background='#FFFFFF', foreground='black', fieldbackground='#E0E0E0')
        self.style.configure('Horizontal.TProgressbar', background='#E0E0E0', troughcolor='#F0F8FF', foreground='blue')  # Configure default Progressbar style for light theme
        self.style.map('Light.TButton', background=[('active', '#D0D0D0')])

        # Dark theme
        self.style.configure('Dark.TFrame', background='#333333')
        self.style.configure('Dark.TLabel', background='#333333', foreground='white')
        self.style.configure('Dark.TButton', background='#444444', foreground='white')
        self.style.configure('Dark.TEntry', fieldbackground='#555555', foreground='white')
        self.style.configure('Dark.Treeview', background='#444444', foreground='white', fieldbackground='#333333')
        self.style.configure('Horizontal.TProgressbar', background='#444444', troughcolor='#333333', foreground='cyan')  # Configure default Progressbar style for dark theme
        self.style.map('Dark.TButton', background=[('active', '#555555')])

        # Apply initial theme
        self.apply_theme()

    def apply_theme(self):
        self.root.configure(bg=self.style.lookup(f"{self.theme.capitalize()}.TFrame", 'background'))
        for widget in self.root.winfo_children():
            if isinstance(widget, ttk.Frame):
                widget.configure(style=f"{self.theme.capitalize()}.TFrame")
            elif isinstance(widget, ttk.Label):
                widget.configure(style=f"{self.theme.capitalize()}.TLabel")
            elif isinstance(widget, ttk.Button):
                widget.configure(style=f"{self.theme.capitalize()}.TButton")
            elif isinstance(widget, ttk.Entry):
                widget.configure(style=f"{self.theme.capitalize()}.TEntry")
            elif isinstance(widget, ttk.Treeview):
                widget.configure(style=f"{self.theme.capitalize()}.Treeview")

    def create_login_screen(self):
        self.clear_screen()
        frame = ttk.Frame(self.root, padding="10", style=f"{self.theme.capitalize()}.TFrame")
        frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        ttk.Label(frame, text="Login", font=("Arial", 16, "bold"), style=f"{self.theme.capitalize()}.TLabel").grid(row=0, column=0, columnspan=2, pady=10)
        ttk.Label(frame, text="Username:", style=f"{self.theme.capitalize()}.TLabel").grid(row=1, column=0, padx=5, pady=5)
        self.username_entry = ttk.Entry(frame, style=f"{self.theme.capitalize()}.TEntry")
        self.username_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(frame, text="Password:", style=f"{self.theme.capitalize()}.TLabel").grid(row=2, column=0, padx=5, pady=5)
        self.password_entry = ttk.Entry(frame, show="*", style=f"{self.theme.capitalize()}.TEntry")
        self.password_entry.grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Login", command=self.login, style=f"{self.theme.capitalize()}.TButton").grid(row=3, column=0, columnspan=2, pady=5)
        ttk.Button(frame, text="Register", command=self.create_register_screen, style=f"{self.theme.capitalize()}.TButton").grid(row=4, column=0, columnspan=2, pady=5)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash, role, approved FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()
        conn.close()
        if result and hashlib.sha256(password.encode()).hexdigest() == result[0] and result[2]:
            self.current_user = {"username": username, "role": result[1]}
            self.create_main_screen()
        else:
            messagebox.showerror("Error", "Invalid username, password, or unapproved account")

    def create_register_screen(self):
        self.clear_screen()
        frame = ttk.Frame(self.root, padding="10", style=f"{self.theme.capitalize()}.TFrame")
        frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        ttk.Label(frame, text="Register", font=("Arial", 16, "bold"), style=f"{self.theme.capitalize()}.TLabel").grid(row=0, column=0, columnspan=2, pady=10)
        ttk.Label(frame, text="Username:", style=f"{self.theme.capitalize()}.TLabel").grid(row=1, column=0, padx=5, pady=5)
        username_entry = ttk.Entry(frame, style=f"{self.theme.capitalize()}.TEntry")
        username_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(frame, text="Password:", style=f"{self.theme.capitalize()}.TLabel").grid(row=2, column=0, padx=5, pady=5)
        password_entry = ttk.Entry(frame, show="*", style=f"{self.theme.capitalize()}.TEntry")
        password_entry.grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Submit", command=lambda: self.process_register(username_entry.get(), password_entry.get()), style=f"{self.theme.capitalize()}.TButton").grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(frame, text="Back", command=self.create_login_screen, style=f"{self.theme.capitalize()}.TButton").grid(row=4, column=0, columnspan=2, pady=5)

    def process_register(self, username, password):
        if not username or not password:
            messagebox.showerror("Error", "Username and password are required")
            return
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)', 
                          (username, hashlib.sha256(password.encode()).hexdigest(), 'pending'))
            conn.commit()
            messagebox.showinfo("Success", "Registration submitted. Awaiting admin approval.")
        except sqlite3.IntegrityError:
            conn.rollback()
            messagebox.showerror("Error", "Username already exists")
        finally:
            conn.close()
        self.create_login_screen()

    def create_main_screen(self):
        self.clear_screen()
        frame = ttk.Frame(self.root, padding="10", style=f"{self.theme.capitalize()}.TFrame")
        frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        ttk.Label(frame, text="Dashboard", font=("Arial", 18, "bold"), style=f"{self.theme.capitalize()}.TLabel").grid(row=0, column=0, columnspan=3, pady=10)
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM products')
        total_products = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM products WHERE quantity < low_threshold')
        low_stock_count = cursor.fetchone()[0]
        conn.close()
        ttk.Label(frame, text=f"Total Products: {total_products}", style=f"{self.theme.capitalize()}.TLabel").grid(row=1, column=0, padx=5, pady=5)
        ttk.Label(frame, text=f"Low Stock Items: {low_stock_count}", style=f"{self.theme.capitalize()}.TLabel").grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Add Product", command=self.add_product, style=f"{self.theme.capitalize()}.TButton").grid(row=2, column=0, pady=5)
        ttk.Button(frame, text="Edit Product", command=self.edit_product, style=f"{self.theme.capitalize()}.TButton").grid(row=2, column=1, pady=5)
        if self.current_user["role"] == "admin":
            ttk.Button(frame, text="Delete Product", command=self.delete_product, style=f"{self.theme.capitalize()}.TButton").grid(row=3, column=0, pady=5)
            ttk.Button(frame, text="Approve Users", command=self.approve_users, style=f"{self.theme.capitalize()}.TButton").grid(row=3, column=1, pady=5)
            ttk.Button(frame, text="Manage Suppliers", command=self.manage_suppliers, style=f"{self.theme.capitalize()}.TButton").grid(row=3, column=2, pady=5)
        ttk.Button(frame, text="View Inventory", command=self.view_inventory, style=f"{self.theme.capitalize()}.TButton").grid(row=4, column=0, pady=5)
        ttk.Button(frame, text="Low Stock Alert", command=self.low_stock_alert, style=f"{self.theme.capitalize()}.TButton").grid(row=4, column=1, pady=5)
        ttk.Button(frame, text="Sales Summary", command=self.sales_summary, style=f"{self.theme.capitalize()}.TButton").grid(row=5, column=0, pady=5)
        ttk.Button(frame, text="Sell Product", command=self.sell_product, style=f"{self.theme.capitalize()}.TButton").grid(row=5, column=1, pady=5)
        ttk.Button(frame, text="Import CSV", command=self.import_csv, style=f"{self.theme.capitalize()}.TButton").grid(row=6, column=0, pady=5)
        ttk.Button(frame, text="Export Inventory", command=lambda: self.export_data("inventory"), style=f"{self.theme.capitalize()}.TButton").grid(row=6, column=1, pady=5)
        ttk.Button(frame, text="Export Sales", command=lambda: self.export_data("sales"), style=f"{self.theme.capitalize()}.TButton").grid(row=7, column=0, pady=5)
        ttk.Button(frame, text="Backup DB", command=self.backup_db, style=f"{self.theme.capitalize()}.TButton").grid(row=7, column=1, pady=5)
        ttk.Button(frame, text="View Notifications", command=self.view_notifications, style=f"{self.theme.capitalize()}.TButton").grid(row=8, column=0, pady=5)
        ttk.Button(frame, text="Logout", command=lambda: self.confirm_action("logout", self.logout), style=f"{self.theme.capitalize()}.TButton").grid(row=9, column=0, columnspan=2, pady=10)

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def confirm_action(self, action, callback):
        if messagebox.askyesno("Confirm", f"Are you sure you want to {action}?"):
            callback()

    def logout(self):
        self.current_user = None
        self.create_login_screen()

    def validate_input(self, name, quantity, price, category, threshold=None, supplier_id=None):
        if not name or not category:
            return False, "Name and category are required."
        try:
            quantity = int(quantity)
            price = float(price)
            if threshold is not None:
                threshold = int(threshold)
                if threshold < 0 or threshold > 100:
                    return False, "Threshold must be between 0 and 100."
            if quantity < 0 or quantity > 10000 or price < 0 or price > 100000:
                return False, "Quantity (0-10000) and price (0-100000) out of range."
            if supplier_id is not None:
                conn = sqlite3.connect('inventory.db')
                cursor = conn.cursor()
                cursor.execute('SELECT COUNT(*) FROM suppliers WHERE id = ?', (supplier_id,))
                if cursor.fetchone()[0] == 0:
                    conn.close()
                    return False, "Invalid supplier ID."
                conn.close()
            return True, ""
        except ValueError:
            return False, "Quantity, price, and threshold must be numbers."

    def add_product(self):
        self.clear_screen()
        frame = ttk.Frame(self.root, padding="10", style=f"{self.theme.capitalize()}.TFrame")
        frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        ttk.Label(frame, text="Add Product", font=("Arial", 14, "bold"), style=f"{self.theme.capitalize()}.TLabel").grid(row=0, column=0, columnspan=2, pady=10)
        ttk.Label(frame, text="Name:", style=f"{self.theme.capitalize()}.TLabel").grid(row=1, column=0, padx=5, pady=5)
        name_entry = ttk.Entry(frame, style=f"{self.theme.capitalize()}.TEntry")
        name_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(frame, text="Quantity:", style=f"{self.theme.capitalize()}.TLabel").grid(row=2, column=0, padx=5, pady=5)
        quantity_entry = ttk.Entry(frame, style=f"{self.theme.capitalize()}.TEntry")
        quantity_entry.grid(row=2, column=1, padx=5, pady=5)
        ttk.Label(frame, text="Price (₹):", style=f"{self.theme.capitalize()}.TLabel").grid(row=3, column=0, padx=5, pady=5)
        price_entry = ttk.Entry(frame, style=f"{self.theme.capitalize()}.TEntry")
        price_entry.grid(row=3, column=1, padx=5, pady=5)
        ttk.Label(frame, text="Category:", style=f"{self.theme.capitalize()}.TLabel").grid(row=4, column=0, padx=5, pady=5)
        category_entry = ttk.Entry(frame, style=f"{self.theme.capitalize()}.TEntry")
        category_entry.grid(row=4, column=1, padx=5, pady=5)
        ttk.Label(frame, text="Supplier ID (optional):", style=f"{self.theme.capitalize()}.TLabel").grid(row=5, column=0, padx=5, pady=5)
        supplier_entry = ttk.Entry(frame, style=f"{self.theme.capitalize()}.TEntry")
        supplier_entry.grid(row=5, column=1, padx=5, pady=5)
        if self.current_user["role"] == "admin":
            ttk.Label(frame, text="Low Threshold:", style=f"{self.theme.capitalize()}.TLabel").grid(row=6, column=0, padx=5, pady=5)
            threshold_entry = ttk.Entry(frame, style=f"{self.theme.capitalize()}.TEntry")
            threshold_entry.grid(row=6, column=1, padx=5, pady=5)
        else:
            threshold_entry = None
        ttk.Button(frame, text="Submit", command=lambda: self.process_add_product(name_entry.get(), quantity_entry.get(), price_entry.get(), category_entry.get(), supplier_entry.get() if supplier_entry.get() else None, threshold_entry.get() if threshold_entry else None), style=f"{self.theme.capitalize()}.TButton").grid(row=7, column=0, columnspan=2, pady=10)
        ttk.Button(frame, text="Back", command=self.create_main_screen, style=f"{self.theme.capitalize()}.TButton").grid(row=8, column=0, columnspan=2, pady=5)

    def process_add_product(self, name, quantity, price, category, supplier_id, threshold):
        is_valid, message = self.validate_input(name, quantity, price, category, threshold, supplier_id)
        if is_valid:
            conn = sqlite3.connect('inventory.db')
            cursor = conn.cursor()
            try:
                cursor.execute('BEGIN TRANSACTION')
                cursor.execute('INSERT INTO products (name, quantity, price, category, low_threshold, supplier_id) VALUES (?, ?, ?, ?, ?, ?)', 
                              (name, int(quantity), float(price), category, int(threshold) if threshold else 10, int(supplier_id) if supplier_id else None))
                product_id = cursor.lastrowid
                cursor.execute('INSERT INTO transactions (product_id, type, quantity, date, user, new_price) VALUES (?, ?, ?, ?, ?, ?)', 
                              (product_id, "Add", int(quantity), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.current_user["username"], float(price)))
                self.log_action(conn, cursor, "Added", f"Product: {name}, ID: {product_id}")
                conn.commit()
                self.check_low_stock(product_id)
                messagebox.showinfo("Success", "Product added successfully")
            except sqlite3.IntegrityError:
                conn.rollback()
                messagebox.showerror("Error", "Product name must be unique or invalid supplier ID")
            finally:
                conn.close()
            self.create_main_screen()
        else:
            messagebox.showerror("Error", message)

    def log_action(self, conn, cursor, action, details):
        cursor.execute('INSERT INTO audit_logs (action, details, user, timestamp) VALUES (?, ?, ?, ?)', 
                      (action, details, self.current_user["username"], datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        # No commit here, as it’s handled by the calling method

    def edit_product(self):
        self.clear_screen()
        frame = ttk.Frame(self.root, padding="10", style=f"{self.theme.capitalize()}.TFrame")
        frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        ttk.Label(frame, text="Edit Product", font=("Arial", 14, "bold"), style=f"{self.theme.capitalize()}.TLabel").grid(row=0, column=0, columnspan=2, pady=10)
        ttk.Label(frame, text="Product ID:", style=f"{self.theme.capitalize()}.TLabel").grid(row=1, column=0, padx=5, pady=5)
        id_entry = ttk.Entry(frame, style=f"{self.theme.capitalize()}.TEntry")
        id_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Load", command=lambda: self.load_product_for_edit(id_entry.get(), frame), style=f"{self.theme.capitalize()}.TButton").grid(row=2, column=0, columnspan=2, pady=5)
        ttk.Button(frame, text="Back", command=self.create_main_screen, style=f"{self.theme.capitalize()}.TButton").grid(row=3, column=0, columnspan=2, pady=5)

    def load_product_for_edit(self, product_id, frame):
        try:
            product_id = int(product_id)
            conn = sqlite3.connect('inventory.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, quantity, price, category, low_threshold, supplier_id FROM products WHERE id = ?', (product_id,))
            product = cursor.fetchone()
            conn.close()
            if product:
                for widget in frame.winfo_children():
                    widget.destroy()
                ttk.Label(frame, text="Edit Product", font=("Arial", 14, "bold"), style=f"{self.theme.capitalize()}.TLabel").grid(row=0, column=0, columnspan=2, pady=10)
                ttk.Label(frame, text=f"ID: {product[0]}", style=f"{self.theme.capitalize()}.TLabel").grid(row=1, column=0, columnspan=2, pady=5)
                ttk.Label(frame, text="Name:", style=f"{self.theme.capitalize()}.TLabel").grid(row=2, column=0, padx=5, pady=5)
                name_entry = ttk.Entry(frame, style=f"{self.theme.capitalize()}.TEntry")
                name_entry.insert(0, product[1])
                name_entry.grid(row=2, column=1, padx=5, pady=5)
                ttk.Label(frame, text="Quantity:", style=f"{self.theme.capitalize()}.TLabel").grid(row=3, column=0, padx=5, pady=5)
                quantity_entry = ttk.Entry(frame, style=f"{self.theme.capitalize()}.TEntry")
                quantity_entry.insert(0, str(product[2]))
                quantity_entry.grid(row=3, column=1, padx=5, pady=5)
                ttk.Label(frame, text="Price (₹):", style=f"{self.theme.capitalize()}.TLabel").grid(row=4, column=0, padx=5, pady=5)
                price_entry = ttk.Entry(frame, style=f"{self.theme.capitalize()}.TEntry")
                price_entry.insert(0, str(product[3]))
                price_entry.grid(row=4, column=1, padx=5, pady=5)
                ttk.Label(frame, text="Category:", style=f"{self.theme.capitalize()}.TLabel").grid(row=5, column=0, padx=5, pady=5)
                category_entry = ttk.Entry(frame, style=f"{self.theme.capitalize()}.TEntry")
                category_entry.insert(0, product[4])
                category_entry.grid(row=5, column=1, padx=5, pady=5)
                ttk.Label(frame, text="Supplier ID (optional):", style=f"{self.theme.capitalize()}.TLabel").grid(row=6, column=0, padx=5, pady=5)
                supplier_entry = ttk.Entry(frame, style=f"{self.theme.capitalize()}.TEntry")
                supplier_entry.insert(0, str(product[6]) if product[6] else "")
                supplier_entry.grid(row=6, column=1, padx=5, pady=5)
                if self.current_user["role"] == "admin":
                    ttk.Label(frame, text="Low Threshold:", style=f"{self.theme.capitalize()}.TLabel").grid(row=7, column=0, padx=5, pady=5)
                    threshold_entry = ttk.Entry(frame, style=f"{self.theme.capitalize()}.TEntry")
                    threshold_entry.insert(0, str(product[5]))
                    threshold_entry.grid(row=7, column=1, padx=5, pady=5)
                else:
                    threshold_entry = None
                ttk.Button(frame, text="Update", command=lambda: self.process_edit_product(product_id, name_entry.get(), quantity_entry.get(), price_entry.get(), category_entry.get(), supplier_entry.get() if supplier_entry.get() else None, threshold_entry.get() if threshold_entry else None), style=f"{self.theme.capitalize()}.TButton").grid(row=8, column=0, columnspan=2, pady=10)
                ttk.Button(frame, text="Back", command=self.create_main_screen, style=f"{self.theme.capitalize()}.TButton").grid(row=9, column=0, columnspan=2, pady=5)
            else:
                messagebox.showerror("Error", "Product not found")
        except ValueError:
            messagebox.showerror("Error", "Invalid Product ID")

    def process_edit_product(self, product_id, name, quantity, price, category, supplier_id, threshold):
        is_valid, message = self.validate_input(name, quantity, price, category, threshold, supplier_id)
        if is_valid:
            conn = sqlite3.connect('inventory.db')
            cursor = conn.cursor()
            try:
                cursor.execute('BEGIN TRANSACTION')
                cursor.execute('SELECT price FROM products WHERE id = ?', (product_id,))
                old_price = cursor.fetchone()[0]
                new_quantity = int(quantity)
                cursor.execute('SELECT quantity FROM products WHERE id = ?', (product_id,))
                old_quantity = cursor.fetchone()[0]
                diff = new_quantity - old_quantity
                cursor.execute('UPDATE products SET name = ?, quantity = ?, price = ?, category = ?, low_threshold = ?, supplier_id = ? WHERE id = ?', 
                              (name, new_quantity, float(price), category, int(threshold) if threshold else 10, int(supplier_id) if supplier_id else None, product_id))
                if diff != 0 or float(price) != old_price:
                    cursor.execute('INSERT INTO transactions (product_id, type, quantity, date, user, new_price) VALUES (?, ?, ?, ?, ?, ?)', 
                                  (product_id, "Adjust" if diff > 0 else "Reduce", abs(diff), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.current_user["username"], float(price) if float(price) != old_price else None))
                self.log_action(conn, cursor, "Edited", f"Product: {name}, ID: {product_id}")
                conn.commit()
                self.check_low_stock(product_id)
                messagebox.showinfo("Success", "Product updated successfully")
            except sqlite3.IntegrityError:
                conn.rollback()
                messagebox.showerror("Error", "Product name must be unique or invalid supplier ID")
            finally:
                conn.close()
            self.create_main_screen()
        else:
            messagebox.showerror("Error", message)

    def delete_product(self):
        self.clear_screen()
        frame = ttk.Frame(self.root, padding="10", style=f"{self.theme.capitalize()}.TFrame")
        frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        ttk.Label(frame, text="Delete Product", font=("Arial", 14, "bold"), style=f"{self.theme.capitalize()}.TLabel").grid(row=0, column=0, columnspan=2, pady=10)
        ttk.Label(frame, text="Product ID:", style=f"{self.theme.capitalize()}.TLabel").grid(row=1, column=0, padx=5, pady=5)
        id_entry = ttk.Entry(frame, style=f"{self.theme.capitalize()}.TEntry")
        id_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Delete", command=lambda: self.confirm_action("delete", lambda: self.process_delete_product(id_entry.get())), style=f"{self.theme.capitalize()}.TButton").grid(row=2, column=0, columnspan=2, pady=5)
        ttk.Button(frame, text="Back", command=self.create_main_screen, style=f"{self.theme.capitalize()}.TButton").grid(row=3, column=0, columnspan=2, pady=5)

    def process_delete_product(self, product_id):
        try:
            product_id = int(product_id)
            conn = sqlite3.connect('inventory.db')
            cursor = conn.cursor()
            cursor.execute('SELECT name, quantity FROM products WHERE id = ?', (product_id,))
            product = cursor.fetchone()
            if product:
                cursor.execute('BEGIN TRANSACTION')
                cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
                cursor.execute('INSERT INTO transactions (product_id, type, quantity, date, user) VALUES (?, ?, ?, ?, ?)', 
                              (product_id, "Delete", product[1], datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.current_user["username"]))
                self.log_action(conn, cursor, "Deleted", f"Product: {product[0]}, ID: {product_id}")
                conn.commit()
                messagebox.showinfo("Success", "Product deleted successfully")
            else:
                messagebox.showerror("Error", "Product not found")
            conn.close()
            self.create_main_screen()
        except ValueError:
            messagebox.showerror("Error", "Invalid Product ID")

    def view_inventory(self):
        self.clear_screen()
        frame = ttk.Frame(self.root, padding="10", style=f"{self.theme.capitalize()}.TFrame")
        frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        # Progress bar with correct style
        progress = ttk.Progressbar(frame, mode="indeterminate", style='Horizontal.TProgressbar')
        progress.grid(row=0, column=0, columnspan=2, pady=5)
        progress.start()
        self.root.update()
        # Search bar
        search_frame = ttk.Frame(frame, style=f"{self.theme.capitalize()}.TFrame")
        search_frame.grid(row=1, column=0, pady=5, columnspan=2)
        ttk.Label(search_frame, text="Search:", style=f"{self.theme.capitalize()}.TLabel").grid(row=0, column=0, padx=5)
        search_entry = ttk.Entry(search_frame, style=f"{self.theme.capitalize()}.TEntry")
        search_entry.grid(row=0, column=1, padx=5)
        ttk.Button(search_frame, text="Filter", command=lambda: self.filter_inventory(tree, search_entry.get()), style=f"{self.theme.capitalize()}.TButton").grid(row=0, column=2, padx=5)
        # Treeview
        tree = ttk.Treeview(frame, columns=("ID", "Name", "Quantity", "Price", "Category", "Threshold", "Supplier"), show="headings", style=f"{self.theme.capitalize()}.Treeview")
        tree.heading("ID", text="ID")
        tree.heading("Name", text="Name")
        tree.heading("Quantity", text="Quantity")
        tree.heading("Price", text="Price (₹)")
        tree.heading("Category", text="Category")
        tree.heading("Threshold", text="Threshold")
        tree.heading("Supplier", text="Supplier Name")
        tree.column("ID", width=50)
        tree.column("Name", width=150)
        tree.column("Quantity", width=80)
        tree.column("Price", width=80)
        tree.column("Category", width=100)
        tree.column("Threshold", width=80)
        tree.column("Supplier", width=150)
        tree.bind("<Double-1>", lambda event: self.on_tree_double_click(event, tree))
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute('SELECT p.id, p.name, p.quantity, p.price, p.category, p.low_threshold, s.name FROM products p LEFT JOIN suppliers s ON p.supplier_id = s.id')
        products = cursor.fetchall()
        conn.close()
        for product in products:
            tree.insert("", "end", values=(product[0], product[1], product[2], f"{product[3]:.2f}", product[4], product[5], product[6] or "N/A"))
        tree.grid(row=2, column=0, columnspan=2, sticky=(tk.N, tk.S, tk.E, tk.W))
        ttk.Button(frame, text="Back", command=self.create_main_screen, style=f"{self.theme.capitalize()}.TButton").grid(row=3, column=0, columnspan=2, pady=10)
        progress.stop()
        progress.destroy()

    def filter_inventory(self, tree, search_term):
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute('SELECT p.id, p.name, p.quantity, p.price, p.category, p.low_threshold, s.name FROM products p LEFT JOIN suppliers s ON p.supplier_id = s.id WHERE p.name LIKE ? OR p.id LIKE ?', 
                      (f'%{search_term}%', f'%{search_term}%'))
        products = cursor.fetchall()
        conn.close()
        for item in tree.get_children():
            tree.delete(item)
        for product in products:
            tree.insert("", "end", values=(product[0], product[1], product[2], f"{product[3]:.2f}", product[4], product[5], product[6] or "N/A"))

    def on_tree_double_click(self, event, tree):
        item = tree.selection()[0]
        product_id = tree.item(item, "values")[0]
        self.load_product_for_edit(product_id, ttk.Frame(self.root, padding="10", style=f"{self.theme.capitalize()}.TFrame"))

    def low_stock_alert(self):
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, quantity, low_threshold FROM products WHERE quantity < low_threshold')
        low_stock = cursor.fetchall()
        conn.close()
        if low_stock:
            message = "Low Stock Alert:\n" + "\n".join([f"ID: {item[0]}, Name: {item[1]}, Qty: {item[2]}, Threshold: {item[3]}" for item in low_stock])
            self.add_notification(f"Low stock detected: {message}")
            messagebox.showinfo("Low Stock Alert", message)
        else:
            messagebox.showinfo("Low Stock Alert", "No low stock items")

    def sales_summary(self):
        self.clear_screen()
        frame = ttk.Frame(self.root, padding="10", style=f"{self.theme.capitalize()}.TFrame")
        frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        ttk.Label(frame, text="Sales Summary", font=("Arial", 14, "bold"), style=f"{self.theme.capitalize()}.TLabel").grid(row=0, column=0, columnspan=2, pady=10)
        ttk.Label(frame, text="Start Date (YYYY-MM-DD):", style=f"{self.theme.capitalize()}.TLabel").grid(row=1, column=0, padx=5, pady=5)
        start_date = ttk.Entry(frame, style=f"{self.theme.capitalize()}.TEntry")
        start_date.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(frame, text="End Date (YYYY-MM-DD):", style=f"{self.theme.capitalize()}.TLabel").grid(row=2, column=0, padx=5, pady=5)
        end_date = ttk.Entry(frame, style=f"{self.theme.capitalize()}.TEntry")
        end_date.grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Generate", command=lambda: self.generate_sales_summary(start_date.get(), end_date.get()), style=f"{self.theme.capitalize()}.TButton").grid(row=3, column=0, columnspan=2, pady=5)
        ttk.Button(frame, text="Back", command=self.create_main_screen, style=f"{self.theme.capitalize()}.TButton").grid(row=4, column=0, columnspan=2, pady=5)

    def generate_sales_summary(self, start_date, end_date):
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        query = 'SELECT p.name, SUM(t.quantity) as total_sold, SUM(t.quantity * p.price) as total_revenue FROM products p LEFT JOIN transactions t ON p.id = t.product_id WHERE t.type = "Withdrawal"'
        params = []
        if start_date and end_date:
            query += ' AND t.date BETWEEN ? AND ?'
            params.extend([start_date, end_date])
        query += ' GROUP BY p.name'
        cursor.execute(query, params)
        summary = cursor.fetchall()
        conn.close()
        if summary:
            message = "Sales Summary:\n" + "\n".join([f"Product: {item[0]}, Total Sold: {item[1] or 0}, Revenue: ₹{item[2]:.2f}" for item in summary])
            messagebox.showinfo("Sales Summary", message)
        else:
            messagebox.showinfo("Sales Summary", "No sales data available")

    def sell_product(self):
        self.clear_screen()
        frame = ttk.Frame(self.root, padding="10", style=f"{self.theme.capitalize()}.TFrame")
        frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        ttk.Label(frame, text="Sell Product", font=("Arial", 14, "bold"), style=f"{self.theme.capitalize()}.TLabel").grid(row=0, column=0, columnspan=2, pady=10)
        ttk.Label(frame, text="Product ID:", style=f"{self.theme.capitalize()}.TLabel").grid(row=1, column=0, padx=5, pady=5)
        id_entry = ttk.Entry(frame, style=f"{self.theme.capitalize()}.TEntry")
        id_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Label(frame, text="Quantity to Sell:", style=f"{self.theme.capitalize()}.TLabel").grid(row=2, column=0, padx=5, pady=5)
        qty_entry = ttk.Entry(frame, style=f"{self.theme.capitalize()}.TEntry")
        qty_entry.grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Sell", command=lambda: self.process_sell_product(id_entry.get(), qty_entry.get()), style=f"{self.theme.capitalize()}.TButton").grid(row=3, column=0, columnspan=2, pady=10)
        ttk.Button(frame, text="Back", command=self.create_main_screen, style=f"{self.theme.capitalize()}.TButton").grid(row=4, column=0, columnspan=2, pady=5)

    def process_sell_product(self, product_id, quantity):
        try:
            product_id = int(product_id)
            quantity = int(quantity)
            if quantity <= 0:
                messagebox.showerror("Error", "Quantity must be positive")
                return
            conn = sqlite3.connect('inventory.db')
            cursor = conn.cursor()
            cursor.execute('BEGIN TRANSACTION')
            cursor.execute('SELECT quantity, price FROM products WHERE id = ?', (product_id,))
            result = cursor.fetchone()
            if not result:
                messagebox.showerror("Error", "Product not found")
                conn.rollback()
                conn.close()
                return
            current_quantity, price = result
            if current_quantity < quantity:
                messagebox.showerror("Error", "Insufficient stock")
                conn.rollback()
                conn.close()
                return
            new_quantity = current_quantity - quantity
            cursor.execute('UPDATE products SET quantity = ? WHERE id = ?', (new_quantity, product_id))
            cursor.execute('INSERT INTO transactions (product_id, type, quantity, date, user, new_price) VALUES (?, ?, ?, ?, ?, ?)', 
                          (product_id, "Withdrawal", quantity, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.current_user["username"], price))
            self.log_action(conn, cursor, "Sold", f"Product ID: {product_id}, Quantity: {quantity}")
            conn.commit()
            self.check_low_stock(product_id)
            messagebox.showinfo("Success", f"Sold {quantity} units of product ID {product_id}")
        except ValueError:
            messagebox.showerror("Error", "Invalid Product ID or Quantity")
        finally:
            conn.close()
        self.create_main_screen()

    def import_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return
        with open(file_path, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            conn = sqlite3.connect('inventory.db')
            cursor = conn.cursor()
            for row in reader:
                is_valid, message = self.validate_input(row['name'], row['quantity'], row['price'], row['category'], row.get('low_threshold'), row.get('supplier_id'))
                if is_valid:
                    try:
                        cursor.execute('BEGIN TRANSACTION')
                        cursor.execute('INSERT INTO products (name, quantity, price, category, low_threshold, supplier_id) VALUES (?, ?, ?, ?, ?, ?)', 
                                      (row['name'], int(row['quantity']), float(row['price']), row['category'], int(row['low_threshold']) if row.get('low_threshold') else 10, int(row['supplier_id']) if row.get('supplier_id') else None))
                        product_id = cursor.lastrowid
                        cursor.execute('INSERT INTO transactions (product_id, type, quantity, date, user, new_price) VALUES (?, ?, ?, ?, ?, ?)', 
                                      (product_id, "Add", int(row['quantity']), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.current_user["username"], float(row['price'])))
                        self.log_action(conn, cursor, "Imported", f"Product: {row['name']}, ID: {product_id}")
                        conn.commit()
                    except sqlite3.IntegrityError:
                        conn.rollback()
                        continue
            conn.close()
        messagebox.showinfo("Success", "CSV imported successfully")
        self.create_main_screen()

    def export_data(self, type):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        if type == "inventory":
            cursor.execute('SELECT p.id, p.name, p.quantity, p.price, p.category, p.low_threshold, s.name FROM products p LEFT JOIN suppliers s ON p.supplier_id = s.id')
            data = cursor.fetchall()
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["ID", "Name", "Quantity", "Price", "Category", "Threshold", "Supplier"])
                for row in data:
                    writer.writerow([row[0], row[1], row[2], f"{row[3]:.2f}", row[4], row[5], row[6] or "N/A"])
        elif type == "sales":
            cursor.execute('SELECT p.name, t.quantity, t.date, t.new_price FROM transactions t JOIN products p ON t.product_id = p.id WHERE t.type = "Withdrawal"')
            data = cursor.fetchall()
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Product", "Quantity Sold", "Date", "Price"])
                for row in data:
                    writer.writerow([row[0], row[1], row[2], f"{row[3]:.2f}" if row[3] else "N/A"])
        conn.close()
        messagebox.showinfo("Success", f"{type.capitalize()} data exported to {file_path}")

    def backup_db(self):
        backup_path = filedialog.asksaveasfilename(defaultextension=".db", filetypes=[("Database files", "*.db")])
        if not backup_path:
            return
        conn = sqlite3.connect('inventory.db')
        conn.backup(sqlite3.connect(backup_path))
        conn.close()
        messagebox.showinfo("Success", f"Database backed up to {backup_path}")

    def approve_users(self):
        self.clear_screen()
        frame = ttk.Frame(self.root, padding="10", style=f"{self.theme.capitalize()}.TFrame")
        frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        ttk.Label(frame, text="Approve Users", font=("Arial", 14, "bold"), style=f"{self.theme.capitalize()}.TLabel").grid(row=0, column=0, pady=10)
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM users WHERE role = "pending" AND approved = 0')
        pending_users = cursor.fetchall()
        conn.close()
        for i, user in enumerate(pending_users, start=1):
            ttk.Label(frame, text=user[0], style=f"{self.theme.capitalize()}.TLabel").grid(row=i, column=0, padx=5, pady=5)
            ttk.Button(frame, text="Approve", command=lambda u=user[0]: self.approve_user(u), style=f"{self.theme.capitalize()}.TButton").grid(row=i, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Back", command=self.create_main_screen, style=f"{self.theme.capitalize()}.TButton").grid(row=len(pending_users) + 1, column=0, columnspan=2, pady=5)

    def approve_user(self, username):
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET approved = 1, role = "staff" WHERE username = ?', (username,))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", f"User {username} approved")
        self.approve_users()

    def manage_suppliers(self):
        self.clear_screen()
        frame = ttk.Frame(self.root, padding="10", style=f"{self.theme.capitalize()}.TFrame")
        frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        ttk.Label(frame, text="Manage Suppliers", font=("Arial", 14, "bold"), style=f"{self.theme.capitalize()}.TLabel").grid(row=0, column=0, columnspan=2, pady=10)

        # Display existing suppliers
        tree = ttk.Treeview(frame, columns=("ID", "Name", "Contact"), show="headings", style=f"{self.theme.capitalize()}.Treeview")
        tree.heading("ID", text="ID")
        tree.heading("Name", text="Name")
        tree.heading("Contact", text="Contact")
        tree.column("ID", width=50)
        tree.column("Name", width=150)
        tree.column("Contact", width=150)
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, contact FROM suppliers')
        suppliers = cursor.fetchall()
        conn.close()
        for supplier in suppliers:
            tree.insert("", "end", values=supplier)
        tree.grid(row=1, column=0, columnspan=2, pady=5)

        # Add new supplier form
        ttk.Label(frame, text="New Supplier Name:", style=f"{self.theme.capitalize()}.TLabel").grid(row=2, column=0, padx=5, pady=5)
        name_entry = ttk.Entry(frame, style=f"{self.theme.capitalize()}.TEntry")
        name_entry.grid(row=2, column=1, padx=5, pady=5)
        ttk.Label(frame, text="Contact:", style=f"{self.theme.capitalize()}.TLabel").grid(row=3, column=0, padx=5, pady=5)
        contact_entry = ttk.Entry(frame, style=f"{self.theme.capitalize()}.TEntry")
        contact_entry.grid(row=3, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Add Supplier", command=lambda: self.process_add_supplier(name_entry.get(), contact_entry.get()), style=f"{self.theme.capitalize()}.TButton").grid(row=4, column=0, columnspan=2, pady=5)
        ttk.Button(frame, text="Back", command=self.create_main_screen, style=f"{self.theme.capitalize()}.TButton").grid(row=5, column=0, columnspan=2, pady=5)

    def process_add_supplier(self, name, contact):
        if not name:
            messagebox.showerror("Error", "Supplier name is required")
            return
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO suppliers (name, contact) VALUES (?, ?)', (name, contact))
            conn.commit()
            messagebox.showinfo("Success", f"Supplier '{name}' added with ID {cursor.lastrowid}")
            self.manage_suppliers()  # Refresh the screen
        except sqlite3.IntegrityError:
            conn.rollback()
            messagebox.showerror("Error", "Supplier name must be unique")
        finally:
            conn.close()

    def view_notifications(self):
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, message, date, status FROM notifications')
        notifications = cursor.fetchall()
        conn.close()
        self.clear_screen()
        frame = ttk.Frame(self.root, padding="10", style=f"{self.theme.capitalize()}.TFrame")
        frame.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        ttk.Label(frame, text="Notifications", font=("Arial", 14, "bold"), style=f"{self.theme.capitalize()}.TLabel").grid(row=0, column=0, pady=10)
        text = scrolledtext.ScrolledText(frame, width=50, height=10, bg=self.style.lookup(f"{self.theme.capitalize()}.TEntry", 'fieldbackground'), fg=self.style.lookup(f"{self.theme.capitalize()}.TEntry", 'foreground'))
        text.grid(row=1, column=0, pady=5)
        for notif in notifications:
            text.insert(tk.END, f"ID: {notif[0]}, Msg: {notif[1]}, Date: {notif[2]}, Status: {notif[3]}\n")
        if self.current_user["role"] == "admin":
            ttk.Button(frame, text="Mark All Resolved", command=self.mark_all_resolved, style=f"{self.theme.capitalize()}.TButton").grid(row=2, column=0, pady=5)
        ttk.Button(frame, text="Back", command=self.create_main_screen, style=f"{self.theme.capitalize()}.TButton").grid(row=3, column=0, pady=5)

    def mark_all_resolved(self):
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute('UPDATE notifications SET status = ? WHERE status = ?', ('resolved', 'pending'))
        conn.commit()
        conn.close()
        messagebox.showinfo("Success", "All notifications marked as resolved")
        self.create_main_screen()

    def add_notification(self, message):
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO notifications (message, date) VALUES (?, ?)', 
                      (message, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()

    def check_low_stock(self, product_id):
        conn = sqlite3.connect('inventory.db')
        cursor = conn.cursor()
        cursor.execute('SELECT quantity, low_threshold FROM products WHERE id = ?', (product_id,))
        result = cursor.fetchone()
        if result and result[0] < result[1]:
            self.add_notification(f"Low stock for product ID {product_id}: Quantity {result[0]} below threshold {result[1]}")
        conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = InventorySystem(root)
    root.mainloop()