# 🐧 Linux Command Generator

> Ứng dụng web cho phép người dùng nhập yêu cầu bằng **tiếng Việt** và nhận lại câu lệnh Linux tương ứng, được tạo ra bởi **Groq (Llama 3)**. Tích hợp **Firebase Authentication** (đăng nhập Google) và **Firestore** để lưu lịch sử lệnh.

### Thông tin nộp bài
- **Môn học:** Tư duy tính toán (Bài thực hành số 2)
- **Họ và tên sinh viên:** Hoàng Công Lý
- **MSSV:** 24120378
- **Video Demo:** https://drive.google.com/file/d/12j6pv5gpvZakfqnPMW_PX9hYe5agVNIe/view?usp=sharing

---

## 📁 Kiến trúc dự án

```
project_root/              ← BASE_DIR (thư mục này)
├── .env                   ← Secrets — KHÔNG commit lên Git
├── .env.example           ← Template — copy và đổi tên thành .env
├── .gitattributes         ← Chuẩn hóa line endings (LF) cho mọi OS
├── .gitignore
├── requirements.txt
├── firebase-credentials.json  ← Tải từ Firebase Console — KHÔNG commit
│
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
│
└── backend/
    └── app/
        ├── main.py
        ├── dependencies.py
        ├── core/
        │   ├── config.py      ← Đọc .env, resolve path cross-platform
        │   └── firebase.py    ← Khởi tạo Firebase Admin SDK
        ├── routers/
        │   ├── auth.py
        │   └── commands.py
        ├── schemas/
        │   └── command.py
        └── services/
            ├── auth_svc.py
            ├── command_svc.py
            └── groq_svc.py
```

---

## ⚙️ Yêu cầu hệ thống

| Công cụ | Phiên bản tối thiểu |
|---|---|
| Python | 3.11+ |
| pip | 23+ |
| Git | Bất kỳ |

---

## 🚀 Cài đặt môi trường & Thư viện

Để chạy được dự án, bạn cần thiết lập môi trường lập trình Python và cài đặt các thư viện phụ thuộc. Việc này đảm bảo ứng dụng có đủ các gói cần thiết để tương tác với Firebase, Groq AI và cung cấp API.

### Bước 1 — Clone & vào thư mục dự án

Mở Terminal (trên Linux/macOS) hoặc Command Prompt / PowerShell (trên Windows) và chạy:

```bash
git clone <repo-url>
cd <tên-thư-mục>
```

### Bước 2 — Tạo môi trường ảo (Virtual Environment)

**Tại sao cần môi trường ảo?**
Môi trường ảo giúp cô lập các thư viện của dự án này với các dự án Python khác trên máy của bạn, tránh tình trạng xung đột phiên bản thư viện.

<details>
<summary>🪟 <strong>Windows (PowerShell / Command Prompt)</strong></summary>

```powershell
# Tạo môi trường ảo có tên là "venv"
python -m venv venv

# Kích hoạt môi trường ảo
# Nếu dùng PowerShell:
venv\Scripts\activate
# Nếu dùng Command Prompt (CMD):
venv\Scripts\activate.bat
```
*(Lưu ý: Nếu PowerShell báo lỗi execution policies, chạy lệnh này với quyền Admin trước: `Set-ExecutionPolicy Unrestricted -Force`)*
</details>

<details>
<summary>🐧 <strong>Linux / macOS (Bash / Zsh)</strong></summary>

```bash
# Đảm bảo bạn đã cài đặt gói venv (trên Ubuntu: sudo apt install python3-venv)
python3 -m venv venv

# Kích hoạt môi trường ảo
source venv/bin/activate
```
</details>

> 💡 **Dấu hiệu thành công:** Khi môi trường ảo được kích hoạt, bạn sẽ thấy tiền tố `(venv)` xuất hiện ở đầu dòng lệnh trong terminal.

### Bước 3 — Cài đặt thư viện phụ thuộc

Sau khi đã kích hoạt môi trường ảo `(venv)`, bạn cần cài đặt các thư viện được liệt kê trong file `requirements.txt`.

```bash
# (Tùy chọn nhưng khuyến khích) Cập nhật công cụ pip lên phiên bản mới nhất
pip install --upgrade pip

# Cài đặt tất cả thư viện trong requirements.txt
pip install -r requirements.txt
```

**Cách kiểm tra thư viện đã được cài đặt thành công:**
Chạy lệnh `pip list`. Bạn sẽ thấy danh sách các gói như `fastapi`, `uvicorn`, `firebase-admin`, `openai`, `python-dotenv`,... đã được cài.

> **Lưu ý:** Tất cả gói trong `requirements.txt` đều có **pre-built binary wheel** trên PyPI cho Windows x64 và Linux x64/arm64. Không cần cài Visual C++ hay build tools. Nếu gặp lỗi, hãy thử `pip install --only-binary=:all: -r requirements.txt`.

### Bước 4 — Cấu hình file `.env`

File `.env` chứa các biến môi trường nhạy cảm (như API Key) và thiết lập cục bộ. **Không bao giờ đưa file `.env` lên Github.**

Sao chép file mẫu và điền giá trị thực của bạn:

<details>
<summary>🪟 <strong>Windows (PowerShell)</strong></summary>

```powershell
Copy-Item .env.example .env
notepad .env
```
</details>

<details>
<summary>🐧 <strong>Linux / macOS (Bash)</strong></summary>

```bash
cp .env.example .env
nano .env   # hoặc code .env nếu dùng VS Code
```
</details>

Mở file `.env` vừa tạo và cập nhật nội dung:
```dotenv
# Thay 'your_actual_groq_api_key' bằng API key thật lấy từ https://console.groq.com
GROQ_API_KEY=your_actual_groq_api_key

# Giữ nguyên dòng này nếu file credentials nằm ở thư mục gốc
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
```

### Bước 5 — Đặt file Firebase credentials

Ứng dụng cần quyền quản trị Firebase (Admin SDK) để xác thực người dùng và ghi dữ liệu lên Firestore.

1. Truy cập **Firebase Console**.
2. Đi tới `Project Settings` (Cài đặt dự án) → `Service Accounts` (Tài khoản dịch vụ).
3. Bấm vào nút `Generate new private key` (Tạo khóa riêng tư mới).
4. Sẽ có một file `.json` được tải về máy của bạn.
5. **Đổi tên** file đó thành `firebase-credentials.json` và **đặt vào thư mục gốc của dự án** (cùng vị trí với file `requirements.txt`).

---

## ▶️ Chạy Backend (FastAPI Server)

Backend của dự án được viết bằng framework **FastAPI** và chạy bằng web server **Uvicorn**.

**Đảm bảo bạn đang ở thư mục gốc của dự án và môi trường ảo `(venv)` đang được kích hoạt.**

<details>
<summary>🪟 <strong>Windows / 🐧 Linux / macOS</strong></summary>

```bash
# 1. Di chuyển vào thư mục backend
cd backend

# 2. Khởi chạy server Uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
</details>

**Giải thích các tham số:**
- `app.main:app`: Trỏ tới biến `app` (FastAPI instance) bên trong file `backend/app/main.py`.
- `--reload`: Tự động khởi động lại server mỗi khi bạn sửa code (rất hữu ích khi dev).
- `--host 0.0.0.0`: Lắng nghe yêu cầu từ mọi địa chỉ IP (cho phép máy khác trong mạng LAN truy cập).
- `--port 8000`: Chạy server ở cổng 8000.

**Kiểm tra Backend:**
- Truy cập trình duyệt: **[http://localhost:8000](http://localhost:8000)** -> Trả về JSON trạng thái.
- **Tài liệu API (Swagger UI):** Truy cập **[http://localhost:8000/docs](http://localhost:8000/docs)** để xem và test trực tiếp các API mà không cần dùng Postman.

> 🛑 **Dừng server:** Nhấn tổ hợp phím `Ctrl + C` trên terminal đang chạy Uvicorn.

---

## 🌐 Chạy Frontend (Giao diện web)

Frontend bao gồm HTML, CSS và JS thuần túy nằm trong thư mục `frontend/`. Tuy nhiên, vì lý do bảo mật của Firebase Authentication và trình duyệt (lỗi CORS), **bạn KHÔNG THỂ mở file `index.html` trực tiếp bằng cách click đúp chuột (`file:///...`).**

Bạn bắt buộc phải phục vụ (serve) thư mục frontend thông qua một **HTTP Server cục bộ**. Dưới đây là 3 cách dễ nhất:

### Cách 1: Sử dụng VS Code Live Server (Khuyến khích)
1. Mở dự án bằng Visual Studio Code.
2. Cài đặt tiện ích mở rộng (extension) **[Live Server](https://marketplace.visualstudio.com/items?itemName=ritwickdey.LiveServer)** của Ritwick Dey.
3. Mở file `frontend/index.html`.
4. Click chuột phải vào màn hình code, chọn **"Open with Live Server"** (Hoặc bấm nút "Go Live" ở thanh trạng thái dưới cùng góc phải).
5. Trình duyệt sẽ tự động mở trang web ở địa chỉ `http://127.0.0.1:5500`.

### Cách 2: Sử dụng Python HTTP Server (Đã có sẵn, không cần cài thêm)
Vì bạn đã cài Python, bạn có thể dùng chính Python để tạo server tĩnh siêu nhanh:

1. Mở một Terminal mới (giữ Terminal chạy Backend hoạt động).
2. Di chuyển vào thư mục frontend:
   ```bash
   cd frontend
   ```
3. Chạy lệnh:
   ```bash
   python -m http.server 3000
   ```
4. Mở trình duyệt và truy cập: **http://localhost:3000**

### Cách 3: Sử dụng Node.js (Nếu máy bạn có cài Node)
1. Mở Terminal và di chuyển vào thư mục frontend: `cd frontend`
2. Chạy lệnh `npx serve` hoặc `npx http-server`.
3. Trình duyệt sẽ mở theo link được in ra trên terminal.

> ⚠️ **Lưu ý quan trọng:** Đảm bảo Backend Uvicorn (cổng 8000) đang chạy song song khi bạn tương tác với trang web Frontend! Mở 2 cửa sổ terminal khác nhau để chạy chúng cùng lúc.

---

## 📡 API Endpoints

| Method | Endpoint | Mô tả | Auth |
|--------|----------|-------|------|
| `GET` | `/` | Root message | ❌ |
| `GET` | `/health` | Health check | ❌ |
| `POST` | `/auth/login` | Xác thực Firebase ID Token | ❌ |
| `GET` | `/auth/me` | Lấy thông tin user hiện tại | ✅ |
| `POST` | `/commands` | Sinh lệnh Linux từ tiếng Việt & lưu Firestore | ✅ |
| `GET` | `/commands` | Lấy lịch sử lệnh của user | ✅ |
| `GET` | `/commands/{id}` | Lấy chi tiết một lệnh | ✅ |

> ✅ = Yêu cầu header `Authorization: Bearer <firebase_id_token>`

---

## 🔧 Xử lý sự cố thường gặp

### `UnicodeDecodeError` khi đọc `.env`

Đảm bảo file `.env` được lưu với encoding **UTF-8** (không phải UTF-16 hay ANSI):
- Windows Notepad: `File → Save As → Encoding: UTF-8`
- VS Code: góc dưới phải → click `UTF-16` → chọn `Save with Encoding → UTF-8`

### `FileNotFoundError: firebase-credentials.json`

Kiểm tra file đặt đúng vị trí: phải ở thư mục gốc dự án (cùng cấp với `requirements.txt`), **không phải** trong `backend/`.

### `grpcio` hoặc `pydantic-core` lỗi install trên Windows

```powershell
pip install --upgrade pip
pip install --only-binary=:all: -r requirements.txt
```

---

## 🛠 Công nghệ sử dụng

| Layer | Technology |
|---|---|
| Frontend | HTML5 · Tailwind CSS · JavaScript (Vanilla) |
| Backend | Python 3.11+ · FastAPI · Uvicorn |
| Auth | Firebase Authentication (Google OAuth) |
| Database | Cloud Firestore |
| AI | Groq API (`llama-3.1-8b-instant`) |
| Cross-platform | `pathlib` · `python-dotenv` · `.gitattributes` |
