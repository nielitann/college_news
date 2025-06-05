import psycopg2
import json
import os
from dotenv import load_dotenv

load_dotenv()

class Database:
    def __init__(self):
        database_url = os.environ.get('DATABASE_URL')
        # Fixed indentation: moved inside __init__
        if not database_url:
            raise RuntimeError("DATABASE_URL environment variable not set")
        
        try:
            self.conn = psycopg2.connect(
                database_url,
                sslmode='require',
                connect_timeout=5,
                options="-c search_path=public"
            )
            self.create_tables()
        except psycopg2.OperationalError as e:
            print(f"Database connection failed: {e}")
            raise  # Remove unreachable create_tables() after raise
    
    def create_tables(self):
        try:
            with self.conn.cursor() as cur:
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
        except Exception as e:
            print(f"Ошибка создания таблиц: {e}")
            self.conn.rollback()
    
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
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()
