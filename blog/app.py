import sqlite3
from flask import Flask, render_template, request, url_for, flash, redirect
from werkzeug.exceptions import abort

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



app = Flask(__name__)
#app.config('SECRET_KEY') = 'secret key'


@app.route('/')
def index():
    connec = get_db_connection()
    posts = connec.execute('SELECT * FROM posts').fetchall()
    connec.close()
    return render_template('index.html', posts=posts)

@app.route('/<int:post_id>') 
def post(post_id):
    post = get_post(post_id)
    return render_template('post.html', post=post)

@app.route('/create', methods=('GET', 'POST')) #/create - url adress. GET POST - forms
def create():
    if request.method == 'POST':
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
    return render_template('create.html')

@app.route('/<int:id>/edit', methods=('GET', 'POST')) # відпрацьовується роут по id
def edit(id):
    post = get_post(id)

    if request.method == 'POST':
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

    return render_template('edit.html', post=post)

@app.route('/<int:id>/delete', methods=['POST'])
def delete(id):
    post = get_post(id)
    conn = get_db_connection()
    conn.execute('DELETE FROM posts WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('"{}" was successfully deleted from posts'.format(post['title']))
    return redirect(url_for('index')) # повертаємося на індекс html



if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.run(debug=True, port=5000)
