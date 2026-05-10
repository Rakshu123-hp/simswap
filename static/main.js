let currentToken = localStorage.getItem('token');
let currentUsername = localStorage.getItem('username');

const loginOverlay = document.getElementById('loginOverlay');
const appContent = document.getElementById('appContent');
const userInfo = document.getElementById('userInfo');
const logoutBtn = document.getElementById('logoutBtn');
const authMessage = document.getElementById('authMessage');

function updateUIState() {
    if (currentToken) {
        loginOverlay.style.display = 'none';
        appContent.style.display = 'block';
        userInfo.textContent = `Analyst ID: ${currentUsername.toUpperCase()}`;
        loadDashboardData();
    } else {
        loginOverlay.style.display = 'flex';
        appContent.style.display = 'none';
    }
}

async function handleLogin() {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    if (!username || !password) {
        authMessage.textContent = 'Please enter credentials.';
        return;
    }
    
    // First try login. If it fails, try to register it (for easy demo purposes silently)
    try {
        let response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });

        if (response.status === 401) {
            // Might not exist, auto-register
            await fetch('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            // Try login again
            response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
        }
        
        const data = await response.json();
        
        if (response.ok) {
            currentToken = data.token;
            currentUsername = username;
            localStorage.setItem('token', currentToken);
            localStorage.setItem('username', currentUsername);
            authMessage.textContent = '';
            updateUIState();
        } else {
            authMessage.textContent = 'Authentication failed.';
        }
    } catch (err) {
        authMessage.textContent = 'An error occurred connecting to the server.';
    }
}

document.getElementById('loginBtn').addEventListener('click', handleLogin);
logoutBtn.addEventListener('click', () => {
    currentToken = null;
    currentUsername = null;
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    updateUIState();
});

async function loadDashboardData() {
    if (!currentToken) return;
    try {
        const response = await fetch('/api/dashboard/data');
        const data = await response.json();
        
        // Metrics
        document.getElementById('totalTx').textContent = data.transactions.length;
        document.getElementById('activeThreats').textContent = data.sim_swaps.filter(s => s.decision !== 'ALLOW').length;
        document.getElementById('blockedFraud').textContent = data.transactions.filter(t => t.decision === 'BLOCK').length;

        // Alerts
        const alertsTable = document.querySelector('#alertsTable tbody');
        alertsTable.innerHTML = '';
        data.alerts.forEach(a => {
            const date = new Date(a.time).toLocaleString();
            alertsTable.innerHTML += `
                <tr>
                    <td>${date}</td>
                    <td><strong>${a.user_id}</strong></td>
                    <td><span class="badge ${a.event_type === 'SIM_SWAP' ? 'BLOCK' : 'STEP_UP'}">${a.event_type}</span></td>
                    <td>${a.message}</td>
                </tr>
            `;
        });

        // Transactions
        const txTable = document.querySelector('#txTable tbody');
        txTable.innerHTML = '';
        data.transactions.forEach(t => {
            const date = new Date(t.time).toLocaleString();
            txTable.innerHTML += `
                <tr>
                    <td>${date}</td>
                    <td>${t.user_id}</td>
                    <td>$${t.amount.toFixed(2)}</td>
                    <td><span class="badge ${t.decision}">${t.decision}</span></td>
                    <td>${t.risk_score}</td>
                </tr>
            `;
        });

        // SIM Swaps
        const simSwapTable = document.querySelector('#simSwapTable tbody');
        simSwapTable.innerHTML = '';
        data.sim_swaps.forEach(s => {
            const date = new Date(s.time).toLocaleString();
            simSwapTable.innerHTML += `
                <tr>
                    <td>${date}</td>
                    <td>${s.user_id}</td>
                    <td><span class="badge ${s.decision}">${s.decision}</span></td>
                    <td>${s.risk_score}</td>
                </tr>
            `;
        });
        
    } catch (error) {
        console.error("Failed to load dashboard data:", error);
    }
}

// Load initially
updateUIState();
// Poll every 5 seconds for a snappy live feel
setInterval(loadDashboardData, 5000);

// OTP Modal Logic
const otpModal = document.getElementById('otpModal');
const openOtpModalBtn = document.getElementById('openOtpModalBtn');
const closeOtpModalBtn = document.getElementById('closeOtpModalBtn');
const verifyOtpBtn = document.getElementById('verifyOtpBtn');
const otpMessage = document.getElementById('otpMessage');

openOtpModalBtn.addEventListener('click', () => {
    otpModal.style.display = 'flex';
    otpMessage.textContent = '';
});

closeOtpModalBtn.addEventListener('click', () => {
    otpModal.style.display = 'none';
});

verifyOtpBtn.addEventListener('click', async () => {
    const customerId = document.getElementById('otpCustomerId').value;
    const otpCode = document.getElementById('otpCode').value;
    
    if (!customerId || !otpCode) {
        otpMessage.style.color = '#dc3545'; // red
        otpMessage.textContent = 'Please enter both ID and OTP.';
        return;
    }
    
    verifyOtpBtn.disabled = true;
    verifyOtpBtn.textContent = 'VERIFYING...';
    
    try {
        const response = await fetch('/api/customer/verify-otp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                customer_id: customerId,
                otp_code: otpCode
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            otpMessage.style.color = '#28a745'; // green
            otpMessage.textContent = '✅ OTP Verified! Transaction Unblocked.';
            document.getElementById('otpCode').value = '';
            // Force quick refresh
            loadDashboardData();
            setTimeout(() => {
                otpModal.style.display = 'none';
            }, 2000);
        } else {
            otpMessage.style.color = '#dc3545'; // red
            otpMessage.textContent = '❌ Error: ' + (data.error || 'Invalid OTP');
        }
    } catch (err) {
        otpMessage.style.color = '#dc3545';
        otpMessage.textContent = 'Connection Error.';
    } finally {
        verifyOtpBtn.disabled = false;
        verifyOtpBtn.textContent = 'SUBMIT OTP';
    }
});
