from auth import Auth

def main():
    auth = Auth()
    username = input("Введите логин: ")
    password = input("Введите пароль: ")
    
    if auth.create_user(username, password, is_admin=True):
        print("Администратор создан!")
    else:
        print("Ошибка при создании администратора!")

if __name__ == "__main__":
    main()