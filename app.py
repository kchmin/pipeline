from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'bulletin-board-secret-key'
DATABASE = 'board.db'


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                done INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS faqs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()


@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    with get_db() as conn:
        total = conn.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
        posts = conn.execute(
            'SELECT * FROM posts ORDER BY created_at DESC LIMIT ? OFFSET ?',
            (per_page, offset)
        ).fetchall()
    total_pages = (total + per_page - 1) // per_page
    return render_template('index.html', posts=posts, page=page,
                           total_pages=total_pages, total=total)


@app.route('/post/<int:post_id>')
def view_post(post_id):
    with get_db() as conn:
        post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    if post is None:
        flash('게시글을 찾을 수 없습니다.', 'error')
        return redirect(url_for('index'))
    return render_template('view.html', post=post)


@app.route('/post/new', methods=['GET', 'POST'])
def create_post():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        content = request.form.get('content', '').strip()
        if not title or not author or not content:
            flash('모든 필드를 입력해주세요.', 'error')
            return render_template('form.html', action='create', post=request.form)
        with get_db() as conn:
            conn.execute(
                'INSERT INTO posts (title, author, content) VALUES (?, ?, ?)',
                (title, author, content)
            )
            conn.commit()
        flash('게시글이 등록되었습니다.', 'success')
        return redirect(url_for('index'))
    return render_template('form.html', action='create', post={})


@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
def edit_post(post_id):
    with get_db() as conn:
        post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    if post is None:
        flash('게시글을 찾을 수 없습니다.', 'error')
        return redirect(url_for('index'))
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        content = request.form.get('content', '').strip()
        if not title or not author or not content:
            flash('모든 필드를 입력해주세요.', 'error')
            return render_template('form.html', action='edit', post=request.form, post_id=post_id)
        with get_db() as conn:
            conn.execute(
                'UPDATE posts SET title=?, author=?, content=?, updated_at=CURRENT_TIMESTAMP WHERE id=?',
                (title, author, content, post_id)
            )
            conn.commit()
        flash('게시글이 수정되었습니다.', 'success')
        return redirect(url_for('view_post', post_id=post_id))
    return render_template('form.html', action='edit', post=post, post_id=post_id)


@app.route('/post/<int:post_id>/delete', methods=['POST'])
def delete_post(post_id):
    with get_db() as conn:
        conn.execute('DELETE FROM posts WHERE id = ?', (post_id,))
        conn.commit()
    flash('게시글이 삭제되었습니다.', 'success')
    return redirect(url_for('index'))


@app.route('/todos')
def todos():
    with get_db() as conn:
        items = conn.execute(
            'SELECT * FROM todos ORDER BY created_at DESC'
        ).fetchall()
    return render_template('todos.html', todos=items)


@app.route('/todos/add', methods=['POST'])
def add_todo():
    content = request.form.get('content', '').strip()
    if not content:
        flash('할 일을 입력해주세요.', 'error')
        return redirect(url_for('todos'))
    with get_db() as conn:
        conn.execute('INSERT INTO todos (content) VALUES (?)', (content,))
        conn.commit()
    flash('할 일이 추가되었습니다.', 'success')
    return redirect(url_for('todos'))


@app.route('/todos/<int:todo_id>/toggle', methods=['POST'])
def toggle_todo(todo_id):
    with get_db() as conn:
        todo = conn.execute('SELECT done FROM todos WHERE id = ?', (todo_id,)).fetchone()
        if todo is None:
            flash('항목을 찾을 수 없습니다.', 'error')
            return redirect(url_for('todos'))
        conn.execute(
            'UPDATE todos SET done = ? WHERE id = ?',
            (0 if todo['done'] else 1, todo_id)
        )
        conn.commit()
    return redirect(url_for('todos'))


@app.route('/todos/<int:todo_id>/delete', methods=['POST'])
def delete_todo(todo_id):
    with get_db() as conn:
        conn.execute('DELETE FROM todos WHERE id = ?', (todo_id,))
        conn.commit()
    flash('할 일이 삭제되었습니다.', 'success')
    return redirect(url_for('todos'))


@app.route('/faqs')
def faqs():
    with get_db() as conn:
        items = conn.execute('SELECT * FROM faqs ORDER BY created_at DESC').fetchall()
    return render_template('faqs.html', faqs=items)


@app.route('/faqs/add', methods=['POST'])
def add_faq():
    question = request.form.get('question', '').strip()
    answer = request.form.get('answer', '').strip()
    if not question or not answer:
        flash('질문과 답변을 모두 입력해주세요.', 'error')
        return redirect(url_for('faqs'))
    with get_db() as conn:
        conn.execute('INSERT INTO faqs (question, answer) VALUES (?, ?)', (question, answer))
        conn.commit()
    flash('FAQ가 등록되었습니다.', 'success')
    return redirect(url_for('faqs'))


@app.route('/faqs/<int:faq_id>/edit', methods=['POST'])
def edit_faq(faq_id):
    question = request.form.get('question', '').strip()
    answer = request.form.get('answer', '').strip()
    if not question or not answer:
        flash('질문과 답변을 모두 입력해주세요.', 'error')
        return redirect(url_for('faqs'))
    with get_db() as conn:
        conn.execute(
            'UPDATE faqs SET question=?, answer=?, updated_at=CURRENT_TIMESTAMP WHERE id=?',
            (question, answer, faq_id)
        )
        conn.commit()
    flash('FAQ가 수정되었습니다.', 'success')
    return redirect(url_for('faqs'))


@app.route('/faqs/<int:faq_id>/delete', methods=['POST'])
def delete_faq(faq_id):
    with get_db() as conn:
        conn.execute('DELETE FROM faqs WHERE id = ?', (faq_id,))
        conn.commit()
    flash('FAQ가 삭제되었습니다.', 'success')
    return redirect(url_for('faqs'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
