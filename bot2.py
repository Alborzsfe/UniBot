import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes


DB_NAME = 'bot.db'
CHAT_ID = '-************' 

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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute('SELECT id, Name FROM Fields ORDER BY "Order"')
    fields = cur.fetchall()
    conn.close()

    if not fields:
        await update.message.reply_text("No fields available.")
        return

    keyboard = [[InlineKeyboardButton(name, callback_data=f'field_{id}')] for id, name in fields]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Choose a field:', reply_markup=reply_markup)

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
            await query.edit_message_text("No courses available for this field.")
            conn.close()
            return

        keyboard = [[InlineKeyboardButton(name, callback_data=f'course_{cid}_{field_id}')] for cid, name in courses]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text('Choose a course:', reply_markup=reply_markup)

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
            await query.edit_message_text("No universities available for this course.")
            conn.close()
            return

        keyboard = [[InlineKeyboardButton(name, callback_data=f'uni_{uid}_{course_id}')] for uid, name in universities]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text('Choose a university:', reply_markup=reply_markup)

    elif data.startswith('uni_'):
        parts = data.split('_')
        uni_id = int(parts[1])
        course_id = int(parts[2])

        cur.execute('''
            SELECT Filename, MIN(Desc) as Desc
            FROM Files 
            WHERE course_id = ? AND university_id = ? 
            GROUP BY Filename
            ORDER BY MIN("Order")
        ''', (course_id, uni_id))
        files = cur.fetchall()

        if not files:
            await query.edit_message_text("No files found for this course and university.")
            conn.close()
            return

        
        for filename, desc in files:
            message_id = int(filename)
            await context.bot.forward_message(
                chat_id=query.message.chat_id,
                from_chat_id=CHAT_ID,
                message_id=message_id
            )
            
            cur.execute('''
                UPDATE Files 
                SET DownloadCount = DownloadCount + 1 
                WHERE Filename = ? AND course_id = ? AND university_id = ?
            ''', (filename, course_id, uni_id))
            conn.commit()

  
        user = update.effective_user
        username = user.username or "Unknown"
        user_id = str(user.id)
        cur.execute("INSERT INTO Logs (Username, UserID) VALUES (?, ?)", (username, user_id))
        conn.commit()

        await query.edit_message_text("Files have been sent.")

    conn.close()

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    await update.message.reply_text(f"Chat ID: {chat_id}")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.reply_to_message:
        message_id = update.message.reply_to_message.message_id
        await update.message.reply_text(f"Message ID: {message_id}")
    else:
        await update.message.reply_text("Please reply to a message to get its ID.")


if __name__ == '__main__':
    create_db()
    TOKEN = '7519604639:AAE0FzLZXrIIMK153Ao79sWbuYbr4HO8SMQ'  # Replace with your actual bot token
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler('getchatid', get_chat_id))
    application.add_handler(CommandHandler('getid', get_id))
    application.run_polling()
