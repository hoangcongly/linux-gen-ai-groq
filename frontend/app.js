/* 
=============================================================================
  LINUX COMMAND GENERATOR - CORE APP LOGIC (app.js)
  - Firebase v10 Authentication (Email/Password + Google Popup)
  - API Integration (FastAPI)
  - Robust Error Handling & UI State Management
=============================================================================
*/

import { initializeApp } from "https://www.gstatic.com/firebasejs/10.9.0/firebase-app.js";
import {
    getAuth,
    signInWithEmailAndPassword,
    createUserWithEmailAndPassword,
    signInWithPopup,
    GoogleAuthProvider,
    signOut,
    onAuthStateChanged,
    updateProfile
} from "https://www.gstatic.com/firebasejs/10.9.0/firebase-auth.js";

// ==========================================
// 1. CẤU HÌNH FIREBASE VÀ API
// ==========================================
const firebaseConfig = {
    apiKey: "AIzaSyD8A0tDkusFSzUZ3PeQvCr2HNB5iALR4cE",
    authDomain: "lab02-44919.firebaseapp.com",
    projectId: "lab02-44919",
    storageBucket: "lab02-44919.firebasestorage.app",
    messagingSenderId: "1058430630604",
    appId: "1:1058430630604:web:fe545c54cd01701f1d2069",
    measurementId: "G-C1C3Z04EN2"
};

const API_BASE_URL = "http://localhost:8000";

let app, auth, googleProvider;

// Guard against unconfigured Firebase
if (firebaseConfig.apiKey !== "YOUR_API_KEY") {
    app = initializeApp(firebaseConfig);
    auth = getAuth(app);
    googleProvider = new GoogleAuthProvider();
}

// ==========================================
// 2. DOM ELEMENTS MAPPING
// ==========================================

// Màn hình (Screens)
const authScreen = document.getElementById('auth-screen');
const mainScreen = document.getElementById('main-screen');

// Component Guest Mode (Forms)
const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const btnGoRegister = document.getElementById('toggle-to-register');
const btnGoLogin = document.getElementById('toggle-to-login-form');

const btnLoginSubmit = document.getElementById('btn-login-submit');
const txtLogin = document.getElementById('txt-login');
const spinLogin = document.getElementById('spin-login');

const btnRegisterSubmit = document.getElementById('btn-register-submit');
const txtRegister = document.getElementById('txt-register');
const spinRegister = document.getElementById('spin-register');

const btnGoogleLogin = document.getElementById('btn-google-login');

// Component Authenticated Mode (Dashboard)
const userName = document.getElementById('user-name');
const userAvatar = document.getElementById('user-avatar');
const btnLogout = document.getElementById('btn-logout');

const promptInput = document.getElementById('prompt-input');
const btnGenerate = document.getElementById('btn-generate');
const txtGenerate = document.getElementById('txt-generate');
const spinGenerate = document.getElementById('spin-generate');

const resultContainer = document.getElementById('result-container');
const terminalWelcome = document.getElementById('terminal-welcome');
const terminalContent = document.getElementById('terminal-content');
const resultPrompt = document.getElementById('result-prompt');
const resultCommand = document.getElementById('result-command');
const btnCopy = document.getElementById('btn-copy');
const iconCopy = document.getElementById('icon-copy');
const iconCheck = document.getElementById('icon-check');

const historyList = document.getElementById('history-list');
const historyEmpty = document.getElementById('history-empty');
const historyLoading = document.getElementById('history-loading');

// ==========================================
// 3. UTILITIES & FIREBASE ERROR TRANSLATOR
// ==========================================

/**
 * Dịch chuẩn xác các mã lỗi phổ biến của Firebase Auth sang tiếng Việt thân thiện.
 */
function translateAuthError(code) {
    switch (code) {
        case 'auth/invalid-credential':
        case 'auth/user-not-found':
        case 'auth/wrong-password':
            return 'Email hoặc mật khẩu không chính xác.';
        case 'auth/email-already-in-use':
            return 'Email này đã tồn tại. Vui lòng đăng nhập.';
        case 'auth/weak-password':
            return 'Mật khẩu quá yếu (cần tối thiểu 6 ký tự).';
        case 'auth/invalid-email':
            return 'Định dạng email không hợp lệ.';
        case 'auth/too-many-requests':
            return 'Bạn thử sai quá nhiều lần. Cần chờ vài phút.';
        case 'auth/network-request-failed':
            return 'Lỗi mạng kết nối. Vui lòng kiểm tra Wifi/4G.';
        case 'auth/popup-closed-by-user':
            return 'Bạn đã hủy quá trình đăng nhập Google.';
        default:
            return `Lỗi hệ thống (${code}). Vui lòng thử lại.`;
    }
}

/**
 * Hiển thị Toast (Đẹp, tự động mất)
 * @param {string} message 
 * @param {'success'|'error'} type 
 */
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    const isSuccess = type === 'success';
    
    toast.className = `toast-enter flex items-center gap-3 px-4 py-3 rounded-xl shadow-2xl border backdrop-blur-md ${
        isSuccess ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-red-500/10 border-red-500/30'
    }`;
    
    // SVG icon tuỳ loại
    const iconSVG = isSuccess 
        ? `<svg class="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7"/></svg>`
        : `<svg class="w-5 h-5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>`;
    
    toast.innerHTML = `
        ${iconSVG}
        <span class="text-sm font-semibold ${isSuccess ? 'text-emerald-300' : 'text-red-300'}">${message}</span>
    `;

    container.appendChild(toast);

    // Kích hoạt biến mất mượt mà sau 3 giây
    setTimeout(() => {
        toast.classList.replace('toast-enter', 'toast-exit');
        toast.addEventListener('animationend', () => toast.remove());
    }, 3000);
}

/**
 * Quản lý khóa (disable) nút bấm & hiển thị spinner khi call API
 */
function setButtonState(button, textEl, spinEl, isLoading, defaultText) {
    if (isLoading) {
        button.disabled = true;
        textEl.textContent = 'Đang xử lý...';
        spinEl.classList.remove('hidden');
    } else {
        button.disabled = false;
        textEl.textContent = defaultText;
        spinEl.classList.add('hidden');
    }
}

// ==========================================
// 4. AUTHENTICATION EVENTS & STATE LOGIC
// ==========================================

if (!auth) {
    showToast('Lỗi: Firebase không được cấu hình', 'error');
}

// 4.1 Chuyển đổi giữa 2 dạng Form
btnGoRegister.addEventListener('click', () => {
    loginForm.classList.add('hidden');
    registerForm.classList.remove('hidden');
});
btnGoLogin.addEventListener('click', () => {
    registerForm.classList.add('hidden');
    loginForm.classList.remove('hidden');
});

// 4.2 Auth Mode: Đăng nhập Bằng Email/Pass
loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('login-email').value.trim();
    const pass = document.getElementById('login-password').value;

    setButtonState(btnLoginSubmit, txtLogin, spinLogin, true, 'Đăng nhập');
    try {
        await signInWithEmailAndPassword(auth, email, pass);
    } catch (error) {
        showToast(translateAuthError(error.code), 'error');
    } finally {
        setButtonState(btnLoginSubmit, txtLogin, spinLogin, false, 'Đăng nhập');
    }
});

// 4.3 Auth Mode: Đăng ký Bằng Email/Pass
registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('register-name').value.trim();
    const email = document.getElementById('register-email').value.trim();
    const pass = document.getElementById('register-password').value;

    setButtonState(btnRegisterSubmit, txtRegister, spinRegister, true, 'Tạo tài khoản');
    try {
        // Create User
        const userCredential = await createUserWithEmailAndPassword(auth, email, pass);
        // Lưu Tên hiển thị vào Profile
        await updateProfile(userCredential.user, { displayName: name });
        showToast('Tạo tài khoản thành công! Tự động đăng nhập.', 'success');
        
        // Refresh token to ensure custom claims/auth works perfectly with backend
        await userCredential.user.getIdToken(true); 
    } catch (error) {
        showToast(translateAuthError(error.code), 'error');
    } finally {
        setButtonState(btnRegisterSubmit, txtRegister, spinRegister, false, 'Tạo tài khoản');
    }
});

// 4.4 Auth Mode: Đăng nhập Google Popup
btnGoogleLogin.addEventListener('click', async () => {
    try {
        await signInWithPopup(auth, googleProvider);
    } catch (error) {
        // Chỉ hiện lỗi nếu người dùng không thuộc loại tắt Popup chủ động
        if (error.code !== 'auth/popup-closed-by-user') {
            showToast(translateAuthError(error.code), 'error');
        }
    }
});

// 4.5 Đăng xuất
btnLogout.addEventListener('click', async () => {
    try {
        await signOut(auth);
        showToast('Đã đăng xuất an toàn.', 'success');
    } catch (error) {
        showToast('Lỗi khi đăng xuất.', 'error');
    }
});

// 4.6 Global State Handler (Lắng nghe để thay Layout)
if (auth) {
    onAuthStateChanged(auth, async (user) => {
        if (user) {
            /** ---------------- USER LOGGED IN ---------------- **/
            const idToken = await user.getIdToken();
            
            // Background sync (tránh blocking UI)
            syncAuthWithBackend(idToken); 

            // Cập nhật Profile Info trên Sidebar
            userName.textContent = user.displayName || user.email.split('@')[0];
            // Render avatar mặc định siêu đẹp nếu hông có ảnh
            userAvatar.src = user.photoURL || `https://ui-avatars.com/api/?name=${encodeURIComponent(userName.textContent)}&background=10b981&color=fff&bold=true`;

            // Transition UI (Slide/Fade Smoothly)
            authScreen.classList.add('hidden');
            mainScreen.classList.remove('hidden');
            setTimeout(() => {
                mainScreen.classList.remove('opacity-0');
            }, 50);

            // Tải danh sách lịch sử lệnh
            fetchHistory();
        } else {
            /** ---------------- USER LOGGED OUT ---------------- **/
            authScreen.classList.remove('hidden');
            mainScreen.classList.add('hidden', 'opacity-0');

            // Xóa rác, tránh lọt data nhạy cảm của người trước
            resetTerminalBox();
            historyList.innerHTML = '';
        }
    });
}

// Hàm bổ trợ gọi `/auth/login` (nếu Backend bạn có triển khai Endpoint này độc lập)
async function syncAuthWithBackend(idToken) {
    try {
        await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id_token: idToken })
        });
    } catch (e) {
        // Fail silent: Thường do lỗi CORS, hoặc server chậm, không cần hiển thị cho UX
    }
}

// Bác sĩ đảm bảo token của Firebase không bao giờ hết hạn.
async function getFreshToken() {
    if (auth && auth.currentUser) {
        return await auth.currentUser.getIdToken(true); // Buộc refresh
    }
    return null;
}


// ==========================================
// 5. API LOGIC: GENERATOR & HISTORY
// ==========================================

// Sự kiện
btnGenerate.addEventListener('click', emitCommandGeneration);
promptInput.addEventListener('keydown', (e) => {
    // Phím tắt Ctrl+Enter hoặc Cmd+Enter
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        if (!btnGenerate.disabled) emitCommandGeneration();
    }
});

// Core Function Gọi API Sinh Lệnh
async function emitCommandGeneration() {
    const promptText = promptInput.value.trim();
    if (!promptText) {
        showToast('Vui lòng nhập mô tả lệnh cần sinh!', 'error');
        return;
    }

    const token = await getFreshToken();
    if (!token) {
        showToast('Session hết hạn. Đang tải lại...', 'error');
        window.location.reload();
        return;
    }

    // Lock Button - Set Loading
    setButtonState(btnGenerate, txtGenerate, spinGenerate, true, 'Tạo lệnh');
    
    // Cập nhật giao diện MacOS Terminal giả
    resultContainer.classList.remove('opacity-50');
    terminalWelcome.classList.add('hidden');
    terminalContent.classList.remove('hidden');
    
    resultPrompt.textContent = promptText;
    resultCommand.classList.add('text-emerald-400');
    resultCommand.classList.remove('text-red-400', 'font-normal');
    resultCommand.textContent = 'Trí tuệ nhân tạo đang phân tích...';

    // Call Tới Backend
    try {
        const response = await fetch(`${API_BASE_URL}/commands`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}` 
            },
            body: JSON.stringify({ prompt: promptText })
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || "Sinh lệnh thất bại từ hệ thống.");
        }

        // Tích kê kết quả
        resultCommand.textContent = data.command;
        showToast('Lệnh đã được tạo cấu trúc!', 'success');
        
        // Background update History menu
        fetchHistory();

    } catch (error) {
        // Trường hợp API sập hoặc rate limit
        resultCommand.classList.remove('text-emerald-400');
        resultCommand.classList.add('text-red-400'); // Terminal báo lỗi màu đỏ code
        resultCommand.textContent = 'Execution Error: ' + error.message;
        
        showToast(error.message, 'error');
    } finally {
        // Unlock button cho lần sau
        setButtonState(btnGenerate, txtGenerate, spinGenerate, false, 'Tạo lệnh');
    }
}

// Load List API Command History
async function fetchHistory() {
    const token = await getFreshToken();
    if (!token) return;

    // Loading states
    historyLoading.classList.remove('hidden');
    historyEmpty.classList.add('hidden');
    historyList.innerHTML = '';

    try {
        const response = await fetch(`${API_BASE_URL}/commands`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) throw new Error("Load lịch sử gián đoạn");
        const items = await response.json();

        // Render Empty state
        if (items.length === 0) {
            historyEmpty.classList.remove('hidden');
            return;
        }

        // Render HTML
        items.forEach(item => {
            const li = document.createElement('li');
            li.className = "history-item bg-[#1e293b]/50 rounded-xl p-3.5 cursor-pointer group"; // Tailwind class mượt mà
            
            li.innerHTML = `
                <div class="text-slate-300 text-xs font-semibold mb-2 truncate group-hover:text-emerald-300 transition-colors" title="${item.prompt}">${item.prompt}</div>
                <code class="block text-emerald-400/80 text-[11px] bg-black/40 px-2.5 py-1.5 rounded truncate font-mono shadow-inner border border-white/5">${item.command}</code>
            `;

            // Behavior khi View lại lệnh ở góc sidebar
            li.addEventListener('click', () => {
                resultContainer.classList.remove('opacity-50');
                terminalWelcome.classList.add('hidden');
                terminalContent.classList.remove('hidden');
                
                resultCommand.classList.add('text-emerald-400');
                resultCommand.classList.remove('text-red-400');
                
                resultPrompt.textContent = item.prompt;
                resultCommand.textContent = item.command;
                promptInput.value = item.prompt; // Fill input
                
                showToast('Đã phục hồi lịch sử', 'success');
            });
            historyList.appendChild(li);
        });
        
    } catch (error) {
        historyEmpty.classList.remove('hidden');
        historyEmpty.textContent = "Lỗi kết nối Server";
        console.error(error);
    } finally {
        historyLoading.classList.add('hidden');
    }
}

// Clear Terminal View cho Logout logic
function resetTerminalBox() {
    resultContainer.classList.add('opacity-50');
    terminalWelcome.classList.remove('hidden');
    terminalContent.classList.add('hidden');
    resultCommand.textContent = '';
    resultPrompt.textContent = '';
    promptInput.value = '';
}

// Function copy MacOS Fake
btnCopy.addEventListener('click', () => {
    let copyText = resultCommand.textContent.trim();
    // Chặn chống copy linh tinh
    if (!copyText || copyText.startsWith('Trí tuệ nhân') || copyText.startsWith('Execution')) return;
    
    // Gỡ biểu tượng Typing Indicator khi copy text thuần túy
    copyText = copyText.replace(/▋$/, '').trim(); 

    navigator.clipboard.writeText(copyText).then(() => {
        // Toggle icon SVG check hiệu ứng mắt tinh tế
        iconCopy.classList.add('hidden');
        iconCheck.classList.remove('hidden');
        
        showToast('Sao chép lệnh thành công', 'success');

        // Phục hồi Icon sau 2 giây
        setTimeout(() => {
            iconCheck.classList.add('hidden');
            iconCopy.classList.remove('hidden');
        }, 2000);
    });
});
