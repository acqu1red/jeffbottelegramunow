// Initialize Telegram Web App
const tg = window.Telegram.WebApp;

// Expand to full height
tg.expand();

// Main color setup
tg.MainButton.textColor = '#FFFFFF';
tg.MainButton.color = '#000000';

function updateStats(data) {
    if (!data) return;
    document.getElementById('stats-users').textContent = data.users || '--';
    document.getElementById('stats-subs').textContent = data.active_subs || '--';
    document.getElementById('stats-stars').textContent = data.revenue || '--';
    document.getElementById('stats-today').textContent = data.today || '--';
}

// Request data from bot on load
function requestDataRefresh() {
    // Send data to bot to trigger a refresh (in a real scenario, this might be an API call)
    // For now, we simulate or use sendData if the bot opened this with a keyboard request
    // Since this is a Mini App opened from a Menu Button or Inline Button, 
    // we should use cloudStorage in a real production app or an API.
    // For this prototype, we'll visually simulate 'loading'.
    
    document.getElementById('stats-users').textContent = '...';
    setTimeout(() => {
        // Mock data for display purposes until backend is linked
        updateStats({
            users: '1,240',
            active_subs: '85',
            revenue: '25,000',
            today: '+12%'
        });
    }, 800);
}

function openBroadcast() {
    document.getElementById('overlay').classList.add('active');
    document.getElementById('broadcast-modal').classList.add('active');
}

function closeBroadcast() {
    document.getElementById('overlay').classList.remove('active');
    document.getElementById('broadcast-modal').classList.remove('active');
}

function sendBroadcast() {
    const text = document.getElementById('broadcast-text').value;
    if (!text) {
        tg.HapticFeedback.notificationOccurred('error');
        return;
    }
    
    tg.MainButton.text = "Confirm Broadcast";
    tg.MainButton.show();
    
    tg.MainButton.onClick(() => {
        // Send data back to bot
        const data = JSON.stringify({
            action: 'broadcast',
            text: text,
            admin_id: tg.initDataUnsafe?.user?.id
        });
        
        tg.sendData(data);
        tg.close();
    });
}

// Initial mock load
// requestDataRefresh();

// Parse stats from URL parameters
function loadStatsFromUrl() {
    const params = new URLSearchParams(window.location.search);
    
    // Default to '--' if not present
    const users = params.get('users') || '--';
    const subs = params.get('subs') || '--';
    const revenue = params.get('revenue') || '--';
    const today = params.get('today') || '--';

    updateStats({
        users: users,
        active_subs: subs,
        revenue: revenue,
        today: today
    });
}

// Load stats immediately
loadStatsFromUrl();
