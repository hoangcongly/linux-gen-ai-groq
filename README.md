# 🐧 Linux Command Generator

> Ứng dụng web cho phép người dùng nhập yêu cầu bằng **tiếng Việt** và nhận lại câu lệnh Linux tương ứng, được tạo ra bởi **Groq (Llama 3)**. Tích hợp **Firebase Authentication** (đăng nhập Google) và **Firestore** để lưu lịch sử lệnh.

### Thông tin nộp bài
- **Môn học:** Tư duy tính toán (Bài thực hành số 2)
- **Họ và tên sinh viên:** Hoàng Công Lý
- **MSSV:** 24120378
- **Video Demo:** 

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

## 🚀 Cài đặt môi trường

### Bước 1 — Clone & vào thư mục dự án

```bash
git clone <repo-url>
cd <tên-thư-mục>
```

### Bước 2 — Tạo môi trường ảo (Virtual Environment)

<details>
<summary>🪟 <strong>Windows (PowerShell)</strong></summary>

```powershell
python -m venv venv
venv\Scripts\activate
```

</details>

<details>
<summary>🐧 <strong>Linux / macOS (Bash)</strong></summary>

```bash
python3 -m venv venv
source venv/bin/activate
```

</details>

### Bước 3 — Cài đặt thư viện

```bash
pip install -r requirements.txt
```

> **Lưu ý:** Tất cả gói trong `requirements.txt` đều có **pre-built binary wheel** trên PyPI cho Windows x64 và Linux x64/arm64. Không cần cài Visual C++ hay build tools.

### Bước 4 — Cấu hình file `.env`

Sao chép template và điền giá trị thực:

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
nano .env   # hoặc code .env
```

</details>

Nội dung `.env` cần điền:

```dotenv
GROQ_API_KEY=your_actual_groq_api_key
FIREBASE_CREDENTIALS_PATH=firebase-credentials.json
```

> **Cross-platform note:** `FIREBASE_CREDENTIALS_PATH` chỉ cần là **tên file** (không cần đường dẫn đầy đủ). Code sẽ tự resolve tuyệt đối từ thư mục gốc dự án, hoạt động giống nhau trên Windows và Linux.

### Bước 5 — Đặt file Firebase credentials

Tải file `firebase-credentials.json` từ **Firebase Console**:
> `Project Settings` → `Service Accounts` → `Generate new private key`

Đặt file vào **thư mục gốc dự án** (cạnh `requirements.txt`).

---

## ▶️ Chạy Backend

<details>
<summary>🪟 <strong>Windows (PowerShell)</strong></summary>

```powershell
# Kích hoạt venv nếu chưa kích hoạt
venv\Scripts\activate

# Di chuyển vào thư mục backend và chạy server
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

</details>

<details>
<summary>🐧 <strong>Linux / macOS (Bash)</strong></summary>

```bash
# Kích hoạt venv nếu chưa kích hoạt
source venv/bin/activate

# Di chuyển vào thư mục backend và chạy server
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

</details>

Server sẽ khởi động tại: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

---

## 🌐 Chạy Frontend

Mở `frontend/index.html` bằng một trong các cách sau:

- **VS Code**: Cài extension [Live Server](https://marketplace.visualstudio.com/items?itemName=ritwickdey.LiveServer), click chuột phải → *Open with Live Server*
- **Trực tiếp**: Mở file `frontend/index.html` trong trình duyệt (có thể gặp CORS nếu không qua server)

> ⚠️ Firebase Authentication yêu cầu file chạy qua HTTP server(Live Server hoặc bất kỳ static server nào), không phải `file://` protocol.

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
