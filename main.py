from flask import Flask, render_template, current_app, request, flash, redirect, url_for
import psycopg2
from psycopg2.extras import DictCursor
import os

app = Flask(__name__)
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'  # Замість цього введіть свій унікальний секретний ключ

# Функція для підключення до бази даних PostgreSQL
def get_db():
    """Establishes a connection to the database."""
    try:
        conn = psycopg2.connect(
            dbname="dbone",
            user="postgres",
            password="14062005",
            host="localhost",
            port="5432"
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None  # Or raise a specific exception

#------------------------------------CMD------------------------------------

# INIT
@app.cli.command("init")
def init_db():
    """Clear existing data and create new tables."""
    conn = get_db()
    if not conn:
        return  # Handle connection error gracefully

    cur = conn.cursor()
    with current_app.open_resource("schema.sql") as file:
        alltext = file.read().decode('utf-8')
        cur.execute(alltext)
    conn.commit()
    print("Initialized the database and cleared tables.")

# POPULATE
@app.cli.command('populate')
def populate_db():
    conn = get_db()
    cur = conn.cursor()
    with current_app.open_resource("populate.sql") as file:  # open the file
        alltext = file.read().decode('utf-8')  # read all the text
        cur.execute(alltext)  # execute all the SQL in the file
    conn.commit()
    print("Populated database with sample data.")

#------------------------------------HTML------------------------------------

# BROWSE
@app.route("/browse")
def browse():
    conn = get_db()
    cursor = conn.cursor(cursor_factory=DictCursor)  # Використовуємо DictCursor тут
    cursor.execute('select id, date, title, content from entries order by date')
    rowlist = cursor.fetchall()
    return render_template('browse.html', entries=rowlist)

# Маршрут для відображення сторінки видалення запису
@app.route("/delete/<int:entry_id>", methods=["GET"])
def delete_entry(entry_id):
    conn = get_db()
    if conn is None:
        flash("Failed to connect to the database.", "error")
        return redirect(url_for("browse"))

    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        cursor.execute('SELECT id, date, title, content FROM entries WHERE id = %s', (entry_id,))
        entry = cursor.fetchone()
        if entry:
            return render_template('delete.html', entry=entry)
        else:
            flash("Entry not found.", "error")
            return redirect(url_for("browse"))
    except psycopg2.Error as e:
        flash(f"Error fetching entry: {e}", "error")
        return redirect(url_for("browse"))
    finally:
        cursor.close()
        conn.close()

# Маршрут для обробки видалення запису
@app.route("/delete_entry", methods=["POST"])
def delete_entry_post():
    conn = get_db()
    if conn is None:
        flash("Failed to connect to the database.", "error")
        return redirect(url_for("browse"))

    entry_id = request.form.get('entry_id')
    cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM entries WHERE id = %s', (entry_id,))
        conn.commit()
        flash("Entry deleted successfully.", "success")
        # Redirect to dev_edit.html/<entry_id> after deletion
        return redirect(url_for("dev_edit", entry_id=entry_id))
    except psycopg2.Error as e:
        flash(f"Error deleting entry: {e}", "error")
        return redirect(url_for("browse"))
    finally:
        cursor.close()
        conn.close()

# Маршрут для відображення сторінки редагування запису
@app.route("/edit/<int:entry_id>", methods=["GET"])
def edit_entry(entry_id):
    conn = get_db()
    if conn is None:
        flash("Failed to connect to the database.", "error")
        return redirect(url_for("browse"))

    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        cursor.execute('SELECT id, date, title, content FROM entries WHERE id = %s', (entry_id,))
        entry = cursor.fetchone()
        if entry:
            return render_template('edit.html', entry=entry)
        else:
            flash("Entry not found.", "error")
            return redirect(url_for("browse"))
    except psycopg2.Error as e:
        flash(f"Error fetching entry: {e}", "error")
        return redirect(url_for("browse"))
    finally:
        cursor.close()
        conn.close()

# Маршрут для обробки додавання нового запису
@app.route("/add_entry", methods=["POST"])
def add_entry():
    conn = get_db()
    if conn is None:
        flash("Failed to connect to the database.", "error")
        return redirect(url_for("write_entry"))

    title = request.form.get('title')
    content = request.form.get('content')

    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO entries (title, content) VALUES (%s, %s)', (title, content))
        conn.commit()
        flash("Entry added successfully.", "success")
        return redirect(url_for("browse"))
    except psycopg2.Error as e:
        flash(f"Error adding entry: {e}", "error")
        return redirect(url_for("write_entry"))
    finally:
        cursor.close()
        conn.close()

# Маршрут для обробки редагування запису
@app.route("/update_entry", methods=["POST"])
def update_entry():
    conn = get_db()
    if conn is None:
        flash("Failed to connect to the database.", "error")
        return redirect(url_for("browse"))

    entry_id = request.form.get('entry_id')
    title = request.form.get('title')
    content = request.form.get('content')

    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE entries SET title = %s, content = %s WHERE id = %s', (title, content, entry_id))
        conn.commit()
        flash("Entry updated successfully.", "success")
        return redirect(url_for("browse"))
    except psycopg2.Error as e:
        flash(f"Error updating entry: {e}", "error")
        return redirect(url_for("browse"))
    finally:
        cursor.close()
        conn.close()

# Маршрут для відображення сторінки створення нового запису
@app.route("/write")
def write_entry():
    return render_template('write.html')

# Маршрут для відображення домашньої сторінки
@app.route("/")
def home():
    return render_template('home.html')

# Маршрут для відображення сторінки автентифікації в режимі розробника
@app.route("/developer_mode")
def developer_mode():
    return render_template('dev_auth.html')

# Маршрут для обробки автентифікації в режимі розробника
@app.route("/dev_authenticate", methods=["POST"])
def dev_authenticate():
    password = request.form.get('password')

    if password in ["shevchuk", "kuzmich"]:
        return redirect(url_for('dev_edit'))
    else:
        flash("Incorrect password.", "error")
        return redirect(url_for('developer_mode'))

# Маршрут для відображення сторінки редагування у режимі розробника
@app.route("/dev_edit")
def dev_edit():
    conn = get_db()
    if conn is None:
        flash("Failed to connect to the database.", "error")
        return redirect(url_for("browse"))

    cursor = conn.cursor(cursor_factory=DictCursor)
    try:
        cursor.execute('SELECT id, date, title, content FROM entries ORDER BY date')
        entries = cursor.fetchall()
        return render_template('dev_edit.html', entries=entries)
    except psycopg2.Error as e:
        flash(f"Error fetching entries: {e}", "error")
        return redirect(url_for("browse"))
    finally:
        cursor.close()
        conn.close()

# Маршрут для відображення сторінки додавання нового запису у режимі розробника
@app.route("/dev_write")
def dev_write_entry():
    return render_template('write.html')

if __name__ == '__main__':
    app.run()
