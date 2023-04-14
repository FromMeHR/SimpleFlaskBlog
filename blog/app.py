import sqlite3
from flask import Flask, render_template, request, url_for, flash, redirect, session
from werkzeug.exceptions import abort
# НОВЕ 2
import bcrypt
from bcrypt import hashpw, checkpw, gensalt

def get_db_connection():
    connec = sqlite3.connect('database.db')
    connec.row_factory = sqlite3.Row
    return connec

def get_post(post_id):
    connec = get_db_connection()
    post = connec.execute('SELECT * FROM posts WHERE id = ?',
                          (post_id,)).fetchone()
    connec.close()
    if post is None:
        abort(404)
    return post

# НОВЕ
def get_users():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users').fetchall()
    conn.close()
    return users

app = Flask(__name__)
#app.config('SECRET_KEY') = 'secret key'


@app.route('/')
def index():
    connec = get_db_connection()
    posts = connec.execute('SELECT * FROM posts').fetchall()
    connec.close()
    # return render_template('index.html', posts=posts)
    # якщо користувач залогінений
    if 'user_id' in session:
        user_id = session['user_id']
        return render_template('index.html', posts=posts, user_id=user_id, is_logged_in=True)
    else:
        return render_template('index.html', posts=posts, is_logged_in=False)

@app.route('/<int:post_id>') 
def post(post_id):
    if 'user_id' not in session:
        flash('You must be logged in to look a post.')
        return redirect(url_for('index'))
    post = get_post(post_id)
    if 'user_id' in session:
        is_logged_in = True
    else:
        is_logged_in = False
    return render_template('post.html', post=post, is_logged_in=is_logged_in)

@app.route('/create', methods=('GET', 'POST')) #/create - url adress. GET POST - forms
def create():
    if 'user_id' not in session:
            flash('You must be logged in to create a post.')
            return redirect(url_for('index'))
    if request.method == 'POST':
        user_id = session['user_id']
        title = request.form['title']
        content = request.form['content']
        if not title:
            flash('Title is required!')
        else:
            connec = get_db_connection()
            connec.execute('INSERT INTO posts (title, content) VALUES (?,?)',
                           (title, content))
            connec.commit()
            connec.close()
            return redirect(url_for('index'))
    if 'user_id' in session:
        is_logged_in = True
    else:
        is_logged_in = False
    return render_template('create.html', is_logged_in=is_logged_in)

@app.route('/<int:id>/edit', methods=('GET', 'POST')) # відпрацьовується роут по id
def edit(id):
    if 'user_id' not in session:
            flash('You must be logged in to edit a post.')
            return redirect(url_for('index'))
    post = get_post(id)
    if request.method == 'POST':
        user_id = session['user_id']
        title = request.form['title'] # запити якщо метод GET
        content = request.form['content']
        if not title:
            flash('Title is required!')
        else:
            conn = get_db_connection()  # створюється коннект до бази даних (записуємо)
            conn.execute('UPDATE posts SET title = ?, content = ?'
                         'WHERE id = ?',
                         (title, content, id)) # де збігається id встановлюємо title connect (до цих полів)# використовуэмо SQL запит на оновлення інформації в таблиці Post


            conn.commit()
            conn.close()
            return redirect(url_for('index')) # повертаємося на головну сторінку
    if 'user_id' in session:
        is_logged_in = True
    else:
        is_logged_in = False
    return render_template('edit.html', post=post, is_logged_in=is_logged_in)

@app.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    post = get_post(id)
    conn = get_db_connection()
    conn.execute('DELETE FROM posts WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('"{}" was successfully deleted from posts'.format(post['title']))
    return redirect(url_for('index')) # повертаємося на індекс html

# НОВЕ
@app.route('/add_user', methods=('GET', 'POST'))
def add_user():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        if not first_name:
            flash('First Name is required!')
        elif not last_name:
            flash('Last Name is required!')
        else:
            conn = get_db_connection()
            conn.execute('INSERT INTO users (first_name, last_name) VALUES (?,?)',
                         (first_name, last_name))
            conn.commit()
            conn.close()
            flash('User added successfully!')
            return redirect(url_for('users'))
    if 'user_id' in session:
        is_logged_in = True
    else:
        is_logged_in = False
    return render_template('add_user.html', is_logged_in=is_logged_in)

# НОВЕ
@app.route('/delete_user/<int:user_id>', methods=('GET', 'POST'))
def delete_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    if request.method == 'POST':
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        flash(f'User {user["first_name"]} {user["last_name"]} has been deleted successfully!')
        return redirect(url_for('users'))
    if 'user_id' in session:
        is_logged_in = True
    else:
        is_logged_in = False
    return render_template('delete_user.html', user=user, is_logged_in=is_logged_in)

# НОВЕ
@app.route('/users')
def users():
    users = get_users()
    if 'user_id' in session:
        is_logged_in = True
    else:
        is_logged_in = False
    return render_template('users.html', users=users, is_logged_in=is_logged_in)

# НОВЕ 2
@app.route('/login')
def show_login_form(): # рендеринг сторінки входу на сайт
    if 'user_id' in session:
        is_logged_in = True
    else:
        is_logged_in = False
    return render_template('login.html', is_logged_in=is_logged_in)

# НОВЕ 2
@app.route('/login', methods=['POST'])
def login():
    first_name = request.form['first_name'] # Отримання введених даних
    password = request.form['password']
    conn = get_db_connection() # пошук користувача в базі даних
    user = conn.execute('SELECT * FROM users WHERE first_name = ?', (first_name,)).fetchone()
    conn.close()
    if user and check_password(password, user['password']): # якщо пароль вірний створюємо сесію 
        session['user_id'] = user['id']
        session['first_name'] = user['first_name']
        flash('You were successfully logged in')
        return redirect(url_for('index'))
    else:
        error = 'Invalid username or password'  # якщо пароль невірний повідомляємо про помилку
        return render_template('login.html', error=error)

def check_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password) # перевірка хеша пароля з бази даних

# НОВЕ 2
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out successfully!')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(debug=True, port=5000)
