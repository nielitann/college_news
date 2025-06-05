from flask import Flask, request, jsonify, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import datetime
import os
import uuid
from dotenv import load_dotenv
from database import Database
from auth import Auth

load_dotenv()

# 1. Создаем экземпляр Flask ДО использования
app = Flask(__name__)

# 2. Инициализируем зависимости ПОСЛЕ создания app
db = Database()
auth = Auth()

# 3. Теперь можно настраивать приложение
app.secret_key = os.environ.get('SECRET_KEY', 'fallback-key')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def check_admin_session():
    return request.cookies.get('admin_session') == 'authenticated'

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    return response

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.get_json()
    user = auth.authenticate(data['username'], data['password'])
    
    if user and user['is_admin']:
        response = jsonify({'success': True, 'redirect': '/admin'})
        response.set_cookie('admin_session', 'authenticated')
        return response
    
    return jsonify({'success': False}), 401

@app.route('/access_denied')
def access_denied():
    return render_template('access_denied.html')

@app.route('/admin')
def admin_panel():
    if not check_admin_session():
        return redirect(url_for('access_denied'))
    return render_template('admin.html')

@app.route('/logout')
def logout():
    response = redirect(url_for('login'))
    response.delete_cookie('admin_session')
    return response

@app.route('/api/add_admin', methods=['POST'])
def add_admin():
    try:
        data = request.get_json()
        username = data['username']
        password = data['password']

        with auth.conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            if cur.fetchone():
                return jsonify({"message": "Логин уже существует"}), 400

        success = auth.create_user(username, password, is_admin=True)
        return jsonify({"status": "success" if success else "error"})
        
    except Exception as e:
        return jsonify({"message": str(e)}), 500

@app.route('/api/get_admins')
def get_admins():
    try:
        with auth.conn.cursor() as cur:
            cur.execute("SELECT username, password FROM users WHERE is_admin = TRUE")
            admins = [{'username': row[0], 'password': row[1]} for row in cur.fetchall()]
            return jsonify(admins)
    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify([])

@app.route('/api/delete_admin', methods=['POST'])
def delete_admin():
    if not check_admin_session():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    username = data['username']
    
    try:
        with auth.conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE username = %s AND is_admin = TRUE", (username,))
            auth.conn.commit()
            return jsonify({"status": "success"})
    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({"status": "error"}), 500
    
@app.route('/api/publish_news', methods=['POST'])
def publish_news():
    if not check_admin_session():
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        title = request.form.get('title')
        content = request.form.get('content')
        hashtags = request.form.get('hashtags', '')
        category = request.form.get('category', 'general')
        is_featured = request.form.get('is_featured') == 'true'
        is_popular = request.form.get('is_popular') == 'true'

        if not title or not content:
            return jsonify({'error': 'Заполните заголовок и содержание'}), 400

        # Обработка медиафайлов
        media_urls = []
        if 'media' in request.files:
            files = request.files.getlist('media')
            for file in files:
                if file.filename != '':
                    # Генерируем уникальное имя файла
                    filename = str(uuid.uuid4()) + os.path.splitext(file.filename)[1]
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(file_path)
                    media_urls.append(filename)

        # Сохранение в БД
        if db.add_news(title, content, hashtags, category, is_featured, is_popular, media_urls):
            return jsonify({'status': 'success'}), 200
        return jsonify({'error': 'Ошибка базы данных'}), 500

    except Exception as e:
        print(f"Ошибка: {str(e)}")
        return jsonify({'error': 'Internal Server Error'}), 500

@app.route('/api/get_all_news', methods=['GET'])
def get_all_news():
    try:
        category = request.args.get('category')
        search = request.args.get('search', '')
        
        base_query = """
            SELECT id, title, content, hashtags, category, created_at, 
                   is_featured, is_popular, media_urls 
            FROM news
        """
        
        conditions = []
        params = []
        
        if search:
            conditions.append("(title ILIKE %s OR content ILIKE %s)")
            params.extend([f'%{search}%', f'%{search}%'])
        
        if category and category != 'all':
            conditions.append("category = %s")
            params.append(category)
        
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        
        base_query += " ORDER BY created_at DESC"
        
        with db.conn.cursor() as cur:
            cur.execute(base_query, params)
            news = []
            for row in cur.fetchall():
                created_at = row[5]
                if isinstance(created_at, datetime.datetime):
                    formatted_date = created_at.strftime('%d.%m.%Y')
                else:
                    try:
                        parsed_date = datetime.datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                        formatted_date = parsed_date.strftime('%d.%m.%Y')
                    except (ValueError, TypeError):
                        formatted_date = created_at
                
                news.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'hashtags': row[3],
                    'category': row[4],
                    'created_at': formatted_date,
                    'is_featured': row[6],
                    'is_popular': row[7],
                    'media_urls': row[8] or []
                })
            return jsonify(news), 200
    except Exception as e:
        print(f"Ошибка: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete_news/<int:news_id>', methods=['DELETE'])
def delete_news(news_id):
    if not check_admin_session():
        return jsonify({'error': 'Unauthorized'}), 401
    if db.delete_news(news_id):
        return jsonify({'status': 'success'})
    return jsonify({'error': 'Ошибка удаления'}), 500

@app.route('/api/get_categories', methods=['GET'])
def get_categories():
    return jsonify([
        'general', 'academic', 'student_life',
        'sport', 'culture', 'research', 'announcements'
    ]), 200

@app.route('/api/add_event', methods=['POST'])
def add_event():
    if not check_admin_session():
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    date = data.get('date')
    location = data.get('location')
    
    if not all([title, description, date, location]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        with db.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO events (title, description, date, location) VALUES (%s, %s, %s, %s)",
                (title, description, date, location)
            )
            db.conn.commit()
            return jsonify({'status': 'success'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_events', methods=['GET'])
def get_events():
    try:
        with db.conn.cursor() as cur:
            cur.execute("SELECT * FROM events ORDER BY date ASC")
            events = [{
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'date': row[3],
                'location': row[4]
            } for row in cur.fetchall()]
            return jsonify(events), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_featured_news', methods=['GET'])
def get_featured_news():
    try:
        with db.conn.cursor() as cur:
            cur.execute("""
                SELECT id, title, content, hashtags, category, created_at, 
                       media_urls 
                FROM news 
                WHERE is_featured = TRUE 
                ORDER BY created_at DESC
            """)
            news = []
            for row in cur.fetchall():
                created_at = row[5]
                if isinstance(created_at, datetime.datetime):
                    formatted_date = created_at.strftime('%d.%m.%Y')
                else:
                    try:
                        parsed_date = datetime.datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                        formatted_date = parsed_date.strftime('%d.%m.%Y')
                    except (ValueError, TypeError):
                        formatted_date = created_at
                
                news.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'hashtags': row[3],
                    'category': row[4],
                    'created_at': formatted_date,
                    'media_urls': row[6] or []
                })
            return jsonify(news), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_popular_news', methods=['GET'])
def get_popular_news():
    try:
        with db.conn.cursor() as cur:
            cur.execute("""
                SELECT id, title, content, hashtags, category, created_at, 
                       media_urls 
                FROM news 
                WHERE is_popular = TRUE 
                ORDER BY created_at DESC
            """)
            news = []
            for row in cur.fetchall():
                created_at = row[5]
                if isinstance(created_at, datetime.datetime):
                    formatted_date = created_at.strftime('%d.%m.%Y')
                else:
                    try:
                        parsed_date = datetime.datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                        formatted_date = parsed_date.strftime('%d.%m.%Y')
                    except (ValueError, TypeError):
                        formatted_date = created_at
                
                news.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'hashtags': row[3],
                    'category': row[4],
                    'created_at': formatted_date,
                    'media_urls': row[6] or []
                })
            return jsonify(news), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get_news_by_id/<int:news_id>', methods=['GET'])
def get_news_by_id(news_id):
    try:
        with db.conn.cursor() as cur:
            cur.execute("""
                SELECT id, title, content, hashtags, category, created_at, 
                       is_featured, is_popular, media_urls 
                FROM news 
                WHERE id = %s
            """, (news_id,))
            row = cur.fetchone()
            if row:
                created_at = row[5]
                if isinstance(created_at, datetime.datetime):
                    formatted_date = created_at.strftime('%d.%m.%Y')
                else:
                    try:
                        parsed_date = datetime.datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')
                        formatted_date = parsed_date.strftime('%d.%m.%Y')
                    except (ValueError, TypeError):
                        formatted_date = created_at
                
                news_item = {
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'hashtags': row[3],
                    'category': row[4],
                    'created_at': formatted_date,
                    'is_featured': row[6],
                    'is_popular': row[7],
                    'media_urls': row[8] or []
                }
                return jsonify(news_item), 200
            return jsonify({'error': 'News not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)
