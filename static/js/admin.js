// Смена темы
document.getElementById('theme-toggle').addEventListener('click', () => {
    document.body.classList.toggle('dark-theme');
    document.body.classList.toggle('light-theme');
    const theme = document.body.classList.contains('dark-theme') ? 'dark' : 'light';
    localStorage.setItem('theme', theme);
});

// Загрузка изображений
document.getElementById('image-upload').addEventListener('change', function(e) {
    Array.from(e.target.files).forEach(file => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const img = document.createElement('img');
            img.src = e.target.result;
            document.getElementById('image-gallery').appendChild(img);
        };
        reader.readAsDataURL(file);
    });
});

// Сохранение черновика
function saveDraft() {
    const draft = {
        content: document.getElementById('news-content').value,
        hashtags: document.getElementById('hashtags').value,
        images: Array.from(document.querySelectorAll('#image-gallery img')).map(img => img.src),
        videos: Array.from(document.querySelectorAll('#video-gallery video')).map(video => video.src)
    };
    localStorage.setItem('draft', JSON.stringify(draft));
    alert('Черновик сохранён!');
}

// Очистка формы
function clearForm() {
    document.getElementById('news-content').value = '';
    document.getElementById('hashtags').value = '';
    document.getElementById('image-gallery').innerHTML = '';
    document.getElementById('video-gallery').innerHTML = '';
}