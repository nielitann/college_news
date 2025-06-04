const express = require('express');
const bodyParser = require('body-parser');

const app = express();
const PORT = 3000;

// Простой объект для хранения пользователей
const users = {
    admin: 'password123'  // Логин: admin, Пароль: password123
};

app.use(bodyParser.json());
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static('public')); // Для статических файлов

app.post('/login', (req, res) => {
    const { username, password } = req.body;

    // Проверка логина и пароля
    if (users[username] && users[username] === password) {
        return res.json({ success: true });
    }
    return res.json({ success: false });
});

app.listen(PORT, () => {
    console.log(`Сервер запущен на http://localhost:${PORT}`);
});
