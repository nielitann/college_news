import psycopg2
import json
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    return psycopg2.connect(os.environ['DATABASE_URL'])

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            host="localhost",
            database="college_news",
            user="postgres",
            password="QztxViMj"
        )
        self._init_db()
        
    def _init_db(self):
        """Создает таблицы при инициализации"""
        with self.conn.cursor() as cur:
            # Создаем таблицу новостей
            cur.execute("""
                CREATE TABLE IF NOT EXISTS news (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    hashtags VARCHAR(255),
                    category VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_featured BOOLEAN DEFAULT FALSE,
                    is_popular BOOLEAN DEFAULT FALSE,
                    media_urls JSONB DEFAULT '[]'::jsonb
                )
            """)
            
            # Создаем таблицу мероприятий
            cur.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    description TEXT NOT NULL,
                    date DATE NOT NULL,
                    location VARCHAR(255) NOT NULL
                )
            """)
            self.conn.commit()

    def add_news(self, title, content, hashtags=None, category='general', 
                 is_featured=False, is_popular=False, media_urls=None):
        """Добавляет новость в базу данных"""
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO news 
                    (title, content, hashtags, category, is_featured, is_popular, media_urls)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (title, content, hashtags, category, is_featured, is_popular, json.dumps(media_urls or []))
                )
                self.conn.commit()
                return True
        except Exception as e:
            print(f"Ошибка добавления новости: {e}")
            self.conn.rollback()
            return False

    def get_featured_news(self):
        with self.conn.cursor() as cur:
            cur.execute("SELECT id, title, content, hashtags, category, created_at, media_urls FROM news WHERE is_featured = TRUE ORDER BY created_at DESC LIMIT 1")
            return cur.fetchall()
            
    def get_popular_news(self):
        with self.conn.cursor() as cur:
            cur.execute("SELECT id, title, content, hashtags, category, created_at, media_urls FROM news WHERE is_popular = TRUE ORDER BY created_at DESC LIMIT 3")
            return cur.fetchall()

    def get_news(self, page=1, per_page=5):
        offset = (page - 1) * per_page
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT id, title, content, hashtags, created_at, media_urls 
                    FROM news 
                    ORDER BY created_at DESC 
                    LIMIT %s OFFSET %s
                """, (per_page, offset))
                return cur.fetchall()
        except Exception as e:
            print(f"Ошибка получения новостей: {e}")
            return []

    def get_all_news(self):
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT id, title, content, hashtags, category, created_at, 
                           is_featured, is_popular, media_urls 
                    FROM news 
                    ORDER BY created_at DESC
                """)
                return cur.fetchall()
        except Exception as e:
            print(f"Ошибка получения новостей: {e}")
            return []

    def delete_news(self, news_id):
        try:
            with self.conn.cursor() as cur:
                cur.execute("DELETE FROM news WHERE id = %s", (news_id,))
                self.conn.commit()
                return True
        except Exception as e:
            self.conn.rollback()
            print(f"Ошибка удаления: {e}")
            return False

    def get_news_by_id(self, news_id):
        try:
            with self.conn.cursor() as cur:
                cur.execute("""
                    SELECT id, title, content, hashtags, category, created_at,
                           is_featured, is_popular, media_urls
                    FROM news WHERE id = %s
                """, (news_id,))
                return cur.fetchone()
        except Exception as e:
            print(f"Ошибка получения новости: {e}")
            return None

    def __del__(self):
        self.conn.close()