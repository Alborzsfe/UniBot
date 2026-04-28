import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Database Manager")
        self.geometry("800x600")
        self.conn = None
        self.cur = None
        self.db_path = None

        open_button = tk.Button(self, text="Open Database", command=self.open_db)
        open_button.pack(pady=20)

    def open_db(self):
        file = filedialog.askopenfilename(filetypes=[("SQLite DB files", "*.db")])
        if file:
            self.db_path = file
            self.conn = sqlite3.connect(self.db_path)
            self.cur = self.conn.cursor()
            self.build_interface()

    def build_interface(self):
        for widget in self.winfo_children():
            widget.destroy()

        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True)

        fields_columns = ["id", "Name", "Desc", "Order"]
        self.create_tab(notebook, "Fields", fields_columns, "Fields")

        courses_columns = ["id", "Name", "Desc", "Order"]
        self.create_tab(notebook, "Courses", courses_columns, "Courses")

        unis_columns = ["id", "Name", "Desc", "Order"]
        self.create_tab(notebook, "Universities", unis_columns, "Universities")

        files_columns = ["Filename", "Name", "Desc", "Order", "TotalDownloads", "Courses", "Universities"]
        self.create_tab(notebook, "Files", files_columns, "Files")

        logs_columns = ["id", "Username", "UserID", "DateTime"]
        self.create_tab(notebook, "Logs", logs_columns, "Logs")

        self.create_association_tab(notebook, "FieldCourses", "field_id", "Fields", "course_id", "Courses")

        self.create_association_tab(notebook, "UniversityCourses", "university_id", "Universities", "course_id", "Courses")

    def quote_col(self, col):
        return f'"{col}"' if col.lower() == 'order' else col

    def load_data(self, tree, table, columns):
        tree.delete(*tree.get_children())
        if table == "Files":
            self.cur.execute('''
                SELECT Filename, MIN(Name) as Name, MIN(Desc) as Desc, MIN("Order") as "Order", 
                SUM(DownloadCount) as TotalDownloads, GROUP_CONCAT(DISTINCT course_id || '') as Courses, 
                GROUP_CONCAT(DISTINCT university_id || '') as Universities 
                FROM Files GROUP BY Filename ORDER BY "Order"
            ''')
            for row in self.cur.fetchall():
                tree.insert('', 'end', values=row)
        else:
            cols_str = ','.join(self.quote_col(c) for c in columns)
            order_by = ' ORDER BY "Order"' if "Order" in columns else ''
            self.cur.execute(f"SELECT {cols_str} FROM {table}{order_by}")
            for row in self.cur.fetchall():
                tree.insert('', 'end', values=row)

    def create_tab(self, notebook, tab_name, columns, table):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=tab_name)

        tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col)
        tree.pack(fill='both', expand=True)
        self.load_data(tree, table, columns)

        button_frame = tk.Frame(frame)
        button_frame.pack(pady=10)

        add_btn = tk.Button(button_frame, text="Add", command=lambda: self.add_record(table, columns, tree))
        add_btn.pack(side='left', padx=5)

        edit_btn = tk.Button(button_frame, text="Edit", command=lambda: self.edit_record(table, columns, tree))
        edit_btn.pack(side='left', padx=5)

        del_btn = tk.Button(button_frame, text="Delete", command=lambda: self.delete_record(table, tree))
        del_btn.pack(side='left', padx=5)

        if table == "Logs":
            add_btn.config(state='disabled')

        if table == "Files":
            add_btn.config(command=lambda: self.add_file_record(tree, columns, table))

    def add_record(self, table, columns, tree):
        dialog = tk.Toplevel(self)
        dialog.title("Add Record")

        entries = {}
        for col in columns[1:]:
            tk.Label(dialog, text=col).pack()
            entry = tk.Entry(dialog)
            entry.pack()
            entries[col] = entry

        def save():
            values = [entries[col].get() for col in columns[1:]]
            cols_str = ','.join(self.quote_col(c) for c in columns[1:])
            placeholders = ','.join('?' * len(values))
            self.cur.execute(f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders})", values)
            self.conn.commit()
            self.load_data(tree, table, columns)
            dialog.destroy()

        tk.Button(dialog, text="Save", command=save).pack(pady=10)

    def add_file_record(self, tree, columns, table):
        dialog = tk.Toplevel(self)
        dialog.title("Add File")

        # Entries for common fields
        tk.Label(dialog, text="Name").pack()
        name_entry = tk.Entry(dialog)
        name_entry.pack()

        tk.Label(dialog, text="Message ID (Filename)").pack()
        filename_entry = tk.Entry(dialog)
        filename_entry.pack()

        tk.Label(dialog, text="Desc").pack()
        desc_entry = tk.Entry(dialog)
        desc_entry.pack()

        tk.Label(dialog, text="Order").pack()
        order_entry = tk.Entry(dialog)
        order_entry.pack()

        # Courses checkboxes
        tk.Label(dialog, text="Select Courses").pack()
        course_frame = tk.Frame(dialog)
        course_frame.pack()
        self.cur.execute('SELECT id, Name FROM Courses ORDER BY "Order"')
        courses = self.cur.fetchall()
        course_vars = []
        for cid, cname in courses:
            var = tk.IntVar()
            check = tk.Checkbutton(course_frame, text=cname, variable=var)
            check.pack(anchor='w')
            course_vars.append((cid, var))

        # Universities checkboxes
        tk.Label(dialog, text="Select Universities").pack()
        uni_frame = tk.Frame(dialog)
        uni_frame.pack()
        self.cur.execute('SELECT id, Name FROM Universities ORDER BY "Order"')
        universities = self.cur.fetchall()
        uni_vars = []
        for uid, uname in universities:
            var = tk.IntVar()
            check = tk.Checkbutton(uni_frame, text=uname, variable=var)
            check.pack(anchor='w')
            uni_vars.append((uid, var))

        def save():
            name = name_entry.get()
            filename = filename_entry.get()
            desc = desc_entry.get()
            order = order_entry.get()
            if not name or not filename or not order:
                messagebox.showerror("Error", "Please fill all fields")
                return
            selected_courses = [cid for cid, var in course_vars if var.get() == 1]
            selected_unis = [uid for uid, var in uni_vars if var.get() == 1]
            if not selected_courses or not selected_unis:
                messagebox.showerror("Error", "Select at least one course and one university")
                return
            for cid in selected_courses:
                for uid in selected_unis:
                    self.cur.execute('INSERT INTO Files (Name, Filename, DownloadCount, "Order", Desc, course_id, university_id) VALUES (?, ?, 0, ?, ?, ?, ?)',
                                     (name, filename, order, desc, cid, uid))
            self.conn.commit()
            self.load_data(tree, table, columns)
            dialog.destroy()

        tk.Button(dialog, text="Save", command=save).pack(pady=10)

    def edit_record(self, table, columns, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Error", "No record selected")
            return
        values = tree.item(selected[0])['values']

        if table == "Files":
            self.edit_file_record(tree, columns, table, values)
            return

        dialog = tk.Toplevel(self)
        dialog.title("Edit Record")

        id_val = values[0]
        entries = {}
        for i, col in enumerate(columns[1:], start=1):
            tk.Label(dialog, text=col).pack()
            entry = tk.Entry(dialog)
            entry.insert(0, values[i])
            entry.pack()
            entries[col] = entry

        def save():
            new_values = [entries[col].get() for col in columns[1:]]
            set_str = ','.join(f"{self.quote_col(c)} = ?" for c in columns[1:])
            self.cur.execute(f"UPDATE {table} SET {set_str} WHERE id = ?", (*new_values, id_val))
            self.conn.commit()
            self.load_data(tree, table, columns)
            dialog.destroy()

        tk.Button(dialog, text="Save", command=save).pack(pady=10)

    def edit_file_record(self, tree, columns, table, values):
        dialog = tk.Toplevel(self)
        dialog.title("Edit File")

        old_filename = values[0]

        tk.Label(dialog, text="Name").pack()
        name_entry = tk.Entry(dialog)
        name_entry.insert(0, values[1])
        name_entry.pack()

        tk.Label(dialog, text="Message ID (Filename)").pack()
        filename_entry = tk.Entry(dialog)
        filename_entry.insert(0, old_filename)
        filename_entry.pack()

        tk.Label(dialog, text="Desc").pack()
        desc_entry = tk.Entry(dialog)
        desc_entry.insert(0, values[2])
        desc_entry.pack()

        tk.Label(dialog, text="Order").pack()
        order_entry = tk.Entry(dialog)
        order_entry.insert(0, values[3])
        order_entry.pack()

        # Courses checkboxes
        tk.Label(dialog, text="Select Courses").pack()
        course_frame = tk.Frame(dialog)
        course_frame.pack()
        self.cur.execute('SELECT id, Name FROM Courses ORDER BY "Order"')
        courses = self.cur.fetchall()
        course_vars = []
        current_courses = set(values[5].split(',') if values[5] else [])
        for cid, cname in courses:
            var = tk.IntVar(value=1 if str(cid) in current_courses else 0)
            check = tk.Checkbutton(course_frame, text=cname, variable=var)
            check.pack(anchor='w')
            course_vars.append((cid, var))

        # Universities checkboxes
        tk.Label(dialog, text="Select Universities").pack()
        uni_frame = tk.Frame(dialog)
        uni_frame.pack()
        self.cur.execute('SELECT id, Name FROM Universities ORDER BY "Order"')
        universities = self.cur.fetchall()
        uni_vars = []
        current_unis = set(values[6].split(',') if values[6] else [])
        for uid, uname in universities:
            var = tk.IntVar(value=1 if str(uid) in current_unis else 0)
            check = tk.Checkbutton(uni_frame, text=uname, variable=var)
            check.pack(anchor='w')
            uni_vars.append((uid, var))

        def save():
            name = name_entry.get()
            filename = filename_entry.get()
            desc = desc_entry.get()
            order = order_entry.get()
            if not name or not filename or not order:
                messagebox.showerror("Error", "Please fill all fields")
                return
            selected_courses = [cid for cid, var in course_vars if var.get() == 1]
            selected_unis = [uid for uid, var in uni_vars if var.get() == 1]
            desired_pairs = set((c, u) for c in selected_courses for u in selected_unis)

            current_filename = old_filename

            if filename != old_filename:
                # Update filename in DB
                self.cur.execute('UPDATE Files SET Filename = ? WHERE Filename = ?', (filename, old_filename))
                current_filename = filename

            # Update common fields
            self.cur.execute('UPDATE Files SET Name = ?, Desc = ?, "Order" = ? WHERE Filename = ?',
                             (name, desc, order, current_filename))

            # Get current pairs
            self.cur.execute('SELECT course_id, university_id FROM Files WHERE Filename = ?', (current_filename,))
            current_pairs = set(tuple(row) for row in self.cur.fetchall())

            # Delete unwanted pairs
            for pair in current_pairs - desired_pairs:
                c, u = pair
                self.cur.execute('DELETE FROM Files WHERE Filename = ? AND course_id = ? AND university_id = ?',
                                 (current_filename, c, u))

            # Insert new pairs
            for pair in desired_pairs - current_pairs:
                c, u = pair
                self.cur.execute('INSERT INTO Files (Name, Filename, DownloadCount, "Order", Desc, course_id, university_id) VALUES (?, ?, 0, ?, ?, ?, ?)',
                                 (name, current_filename, order, desc, c, u))

            self.conn.commit()

            # Check if no records left
            self.cur.execute('SELECT COUNT(*) FROM Files WHERE Filename = ?', (current_filename,))
            if self.cur.fetchone()[0] == 0:
                pass  # No physical file to remove

            self.load_data(tree, table, columns)
            dialog.destroy()

        tk.Button(dialog, text="Save", command=save).pack(pady=10)

    def delete_record(self, table, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Error", "No record selected")
            return
        values = tree.item(selected[0])['values']
        if table == "Files":
            filename = values[0]
            self.cur.execute(f"DELETE FROM {table} WHERE Filename = ?", (filename,))
        else:
            id_val = values[0]
            self.cur.execute(f"DELETE FROM {table} WHERE id = ?", (id_val,))
        self.conn.commit()
        self.load_data(tree, table, tree["columns"])

    def load_association_data(self, tree, tab_name, left_id, left_table, right_id, right_table):
        tree.delete(*tree.get_children())
        query = f"""
        SELECT fc.{left_id}, l.Name, fc.{right_id}, r.Name
        FROM {tab_name} fc
        JOIN {left_table} l ON fc.{left_id} = l.id
        JOIN {right_table} r ON fc.{right_id} = r.id
        """
        self.cur.execute(query)
        for row in self.cur.fetchall():
            tree.insert('', 'end', values=row)

    def create_association_tab(self, notebook, tab_name, left_id, left_table, right_id, right_table):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text=tab_name)

        columns = [left_id, left_table + '_name', right_id, right_table + '_name']
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        tree.heading(left_id, text=left_id)
        tree.heading(left_table + '_name', text=left_table + ' Name')
        tree.heading(right_id, text=right_id)
        tree.heading(right_table + '_name', text=right_table + ' Name')
        tree.pack(fill='both', expand=True)
        self.load_association_data(tree, tab_name, left_id, left_table, right_id, right_table)

        button_frame = tk.Frame(frame)
        button_frame.pack(pady=10)

        add_btn = tk.Button(button_frame, text="Add", command=lambda: self.add_association(tab_name, left_id, left_table, right_id, right_table, tree))
        add_btn.pack(side='left', padx=5)

        del_btn = tk.Button(button_frame, text="Delete", command=lambda: self.delete_association(tab_name, left_id, right_id, tree))
        del_btn.pack(side='left', padx=5)

    def add_association(self, tab_name, left_id, left_table, right_id, right_table, tree):
        dialog = tk.Toplevel(self)
        dialog.title("Add Association")

        self.cur.execute(f'SELECT id, Name FROM {left_table} ORDER BY "Order"')
        lefts = self.cur.fetchall()
        left_names = [f"{lid} - {lname}" for lid, lname in lefts]

        tk.Label(dialog, text=left_table).pack()
        left_combo = ttk.Combobox(dialog, values=left_names)
        left_combo.pack()

        self.cur.execute(f'SELECT id, Name FROM {right_table} ORDER BY "Order"')
        rights = self.cur.fetchall()
        right_names = [f"{rid} - {rname}" for rid, rname in rights]

        tk.Label(dialog, text=right_table).pack()
        right_combo = ttk.Combobox(dialog, values=right_names)
        right_combo.pack()

        def save():
            left_text = left_combo.get()
            if not left_text:
                messagebox.showerror("Error", "Select " + left_table)
                return
            l_id = int(left_text.split(' - ')[0])

            right_text = right_combo.get()
            if not right_text:
                messagebox.showerror("Error", "Select " + right_table)
                return
            r_id = int(right_text.split(' - ')[0])

            try:
                self.cur.execute(f"INSERT INTO {tab_name} ({left_id}, {right_id}) VALUES (?, ?)", (l_id, r_id))
                self.conn.commit()
                self.load_association_data(tree, tab_name, left_id, left_table, right_id, right_table)
                dialog.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Association already exists")

        tk.Button(dialog, text="Save", command=save).pack(pady=10)

    def delete_association(self, tab_name, left_id, right_id, tree):
        selected = tree.selection()
        if not selected:
            messagebox.showerror("Error", "No record selected")
            return
        values = tree.item(selected[0])['values']
        l_val = values[0]
        r_val = values[2]
        self.cur.execute(f"DELETE FROM {tab_name} WHERE {left_id} = ? AND {right_id} = ?", (l_val, r_val))
        self.conn.commit()
        self.load_association_data(tree, tab_name, left_id, tree["columns"][1].split('_')[0], right_id, tree["columns"][3].split('_')[0])

if __name__ == "__main__":
    app = App()
    app.mainloop()