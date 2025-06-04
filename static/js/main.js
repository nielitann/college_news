let page = 1;
let loading = false;

window.addEventListener('scroll', () => {
    if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 100) {
        loadMoreNews();
    }
});

async function loadMoreNews() {
    if (loading) return;
    loading = true;
    
    const response = await fetch(`/api/news?page=${page}`);
    const news = await response.json();
    
    news.forEach(item => {
        const card = document.createElement('div');
        card.className = 'news-card';
        card.innerHTML = `
            <h3>${item.title}</h3>
            ${item.image ? `<img src="/static/uploads/${item.image}" alt="${item.title}"> `: ''}
            <p>${item.content}</p>
            <small>${new Date(item.created_at).toLocaleDateString()}</small>
        `;
        document.getElementById('news-container').appendChild(card);
    });
    
    page++;
    loading = false;
}


loadMoreNews() ;
async function checkAuth() {
    try {
        const response = await fetch('/api/check-auth');
        const data = await response.json();
        
        if (data.isAdmin) {
            document.getElementById('login-link').style.display = 'none';
            document.getElementById('admin-link').style.display = 'block';
        }
    } catch (error) {
        console.error('Ошибка проверки авторизации:', error);
    }
}
checkAuth();