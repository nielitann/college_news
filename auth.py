import bcrypt
from config import DB_CONFIG
import psycopg2

class Auth:
    def __init__(self):
        self.conn = None  # Явная инициализация соединения
        self.init_db()    # Попытка инициализации БД

    def init_db(self):
        """Инициализация таблиц и тестового администратора"""
        try:
            # Подключение к базе данных
            self.conn = psycopg2.connect(**DB_CONFIG, client_encoding='utf-8')
            with self.conn.cursor() as cur:
                # Создание таблицы users, если её нет
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(50) UNIQUE NOT NULL,
                        password VARCHAR(100) NOT NULL,
                        is_admin BOOLEAN DEFAULT FALSE
                    )
                """)
                
                # Добавление тестового администратора, если его нет
                cur.execute("SELECT * FROM users WHERE username = 'admin'")
                if not cur.fetchone():
                    hashed_pw = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8')
                    cur.execute("""
                        INSERT INTO users (username, password, is_admin)
                        VALUES (%s, %s, TRUE)
                    """, ('admin', hashed_pw))
                
                self.conn.commit()
            print("✅ База данных инициализирована!")
            
        except Exception as e:
            print(f"❌ Ошибка инициализации БД: {e}")
            if self.conn:
                self.conn.rollback()

    def authenticate(self, username, password):
        """Аутентификация пользователя"""
        if not self.conn:
            print("⚠️ Нет подключения к базе данных!")
            return None

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "SELECT password, is_admin FROM users WHERE username = %s",
                    (username,)
                )
                result = cursor.fetchone()

                if result and bcrypt.checkpw(password.encode("utf-8"), result[0].encode("utf-8")):
                    return {"is_admin": result[1]}
                return None
        except psycopg2.Error as e:
            print(f"❌ Ошибка базы данных: {e}")
            return None

    def create_user(self, username, password, is_admin=False):
        """Создание пользователя"""
        if not self.conn:
            print("Нет подключения к базе данных!")
            return False

        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (username, password, is_admin) VALUES (%s, %s, %s)",
                    (username, hashed_password, is_admin)
                )
                self.conn.commit()
                return True
        except psycopg2.Error as e:
            print(f"Ошибка SQL: {e}")
            self.conn.rollback()
            return False

    def create_admin(self, current_user_id, new_username, new_password):
        """Создание нового администратора"""
        if not self.conn:
            print("Нет подключения к базе данных!")
            return False

        try:
            with self.conn.cursor() as cur:
                cur.execute("SELECT is_admin FROM users WHERE id = %s", (current_user_id,))
                result = cur.fetchone()
                
                if not result or not result[0]:
                    raise PermissionError("Требуются права администратора")

                hashed_pw = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                cur.execute(
                    "INSERT INTO users (username, password, is_admin) VALUES (%s, %s, TRUE)",
                    (new_username, hashed_pw)
                )
                self.conn.commit()
                return True
        except PermissionError as e:
            print(e)
            return False
        except psycopg2.Error as e:
            print(f"Ошибка SQL: {e}")
            self.conn.rollback()
            return False

    def close_connection(self):
            """Закрытие подключения к базе данных"""
            if self.conn:
                self.conn.close()
                print("🔌 Подключение к базе данных закрыто.")
    def create_user(self, username, password, is_admin=False):
        if not self.conn:
            print("Нет подключения к базе данных!")
            return False

        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        try:
            with self.conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (username, password, is_admin) VALUES (%s, %s, %s)",
                    (username, hashed_password, is_admin)
                )
                self.conn.commit()
                return True
        except psycopg2.Error as e:
            print(f"Ошибка SQL: {e}")
            self.conn.rollback()
            return False