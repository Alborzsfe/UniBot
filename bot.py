import os
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes


DB_NAME = 'bot.db'
FILES_FOLDER = 'StoredFiles'

def create_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

 
    cur.execute('''
    CREATE TABLE IF NOT EXISTS Fields (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT,
        Desc TEXT,
        "Order" INTEGER
    )
    ''')

 
    cur.execute('''
    CREATE TABLE IF NOT EXISTS Courses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT,
        Desc TEXT,
        "Order" INTEGER
    )
    ''')

 
    cur.execute('''
    CREATE TABLE IF NOT EXISTS Universities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT,
        Desc TEXT,
        "Order" INTEGER
    )
    ''')

    
    cur.execute('''
    CREATE TABLE IF NOT EXISTS Files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Name TEXT,
        Filename TEXT,
        DownloadCount INTEGER DEFAULT 0,
        "Order" INTEGER,
        Desc TEXT,
        course_id INTEGER,
        university_id INTEGER,
        FOREIGN KEY (course_id) REFERENCES Courses(id),
        FOREIGN KEY (university_id) REFERENCES Universities(id)
    )
    ''')

 
    cur.execute('''
    CREATE TABLE IF NOT EXISTS Logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        Username TEXT,
        UserID TEXT,
        DateTime DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

   
    cur.execute('''
    CREATE TABLE IF NOT EXISTS FieldCourses (
        field_id INTEGER,
        course_id INTEGER,
        PRIMARY KEY (field_id, course_id),
        FOREIGN KEY (field_id) REFERENCES Fields(id),
        FOREIGN KEY (course_id) REFERENCES Courses(id)
    )
    ''')

    
    cur.execute('''
    CREATE TABLE IF NOT EXISTS UniversityCourses (
        university_id INTEGER,
        course_id INTEGER,
        PRIMARY KEY (university_id, course_id),
        FOREIGN KEY (university_id) REFERENCES Universities(id),
        FOREIGN KEY (course_id) REFERENCES Courses(id)
    )
    ''')

    conn.commit()
    conn.close()


if not os.path.exists(FILES_FOLDER):
    os.makedirs(FILES_FOLDER)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id, Name FROM Fields ORDER BY "Order"')
    fields = cur.fetchall()
    conn.close()

    if not fields:
        await update.message.reply_text("هیچ رشته ای تعریف نشده است.")
        return

    keyboard = [[InlineKeyboardButton(name, callback_data=f'field_{id}')] for id, name in fields]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('رشته خود را انتخاب نمایید:', reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    if data.startswith('field_'):
        field_id = int(data.split('_')[1])
        cur.execute('''
            SELECT c.id, c.Name 
            FROM Courses c
            JOIN FieldCourses fc ON c.id = fc.course_id
            WHERE fc.field_id = ?
            ORDER BY c."Order"
        ''', (field_id,))
        courses = cur.fetchall()

        if not courses:
            await query.edit_message_text("هیچ درسی با این رشته وجود ندارد.")
            conn.close()
            return

        keyboard = [[InlineKeyboardButton(name, callback_data=f'course_{cid}_{field_id}')] for cid, name in courses]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text('یک درس را انتخاب نمایید:', reply_markup=reply_markup)

    elif data.startswith('course_'):
        parts = data.split('_')
        course_id = int(parts[1])
       

        cur.execute('''
            SELECT u.id, u.Name 
            FROM Universities u
            JOIN UniversityCourses uc ON u.id = uc.university_id
            WHERE uc.course_id = ?
            ORDER BY u."Order"
        ''', (course_id,))
        universities = cur.fetchall()

        if not universities:
            await query.edit_message_text("هیچ دانشگاهی برای این درس وجود ندارد.")
            conn.close()
            return

        keyboard = [[InlineKeyboardButton(name, callback_data=f'uni_{uid}_{course_id}')] for uid, name in universities]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text('یک دانشگاه را انتخاب نمایید:', reply_markup=reply_markup)

    elif data.startswith('uni_'):
        parts = data.split('_')
        uni_id = int(parts[1])
        course_id = int(parts[2])

        cur.execute('''
            SELECT id, Name, Filename, Desc, DownloadCount 
            FROM Files 
            WHERE course_id = ? AND university_id = ? 
            ORDER BY "Order"
        ''', (course_id, uni_id))
        files = cur.fetchall()

        if not files:
            await query.edit_message_text("هیچ فایلی برای این درس و این دانشگاه یافت نشد.")
            conn.close()
            return

        
        for file_id, name, filename, desc, download_count in files:
            file_path = os.path.join(FILES_FOLDER, filename)
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    await query.message.reply_document(document=f, filename=filename, caption=desc)
                
                cur.execute('UPDATE Files SET DownloadCount = DownloadCount + 1 WHERE id = ?', (file_id,))
                conn.commit()
            else:
                await query.message.reply_text(f"File '{filename}' not found in storage.")

    
        user = update.effective_user
        username = user.username or "Unknown"
        user_id = str(user.id)
        cur.execute("INSERT INTO Logs (Username, UserID) VALUES (?, ?)", (username, user_id))
        conn.commit()

        await query.edit_message_text("فایل ها خدمت شما دوست عزیز :)")

    conn.close()


if __name__ == '__main__':
    create_db()
    TOKEN = '****************'  
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling()
    
