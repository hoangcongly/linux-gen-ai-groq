import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies import get_current_user

# ─────────────────────────────────────────────────────────────────────────────
# SETUP: TestClient & Dependency Mocking
# ─────────────────────────────────────────────────────────────────────────────

client = TestClient(app)

def mock_get_current_user():
    """
    Mock dependency: Giả lập một người dùng đã đăng nhập hợp lệ.
    Cho phép đi qua các route bảo mật mà không cần truyền Authorization header.
    """
    return {
        "uid": "test_user_123", 
        "email": "test@example.com",
        "name": "Test User",
        "picture": "https://example.com/avatar.png"
    }

# Ghi đè dependency của ứng dụng bằng hàm mock ở trên
app.dependency_overrides[get_current_user] = mock_get_current_user


# ─────────────────────────────────────────────────────────────────────────────
# TEST CASES
# ─────────────────────────────────────────────────────────────────────────────

def test_root_and_health():
    """Kiểm tra các endpoint tiện ích không yêu cầu xác thực."""
    
    # 1. Test Root
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "message" in res_root.json()

    # 2. Test Health
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json()["status"] == "ok"


@patch("app.routers.auth.verify_token")
@patch("app.routers.auth.extract_user_info")
def test_auth_login(mock_extract, mock_verify):
    """
    Test quá trình đăng nhập. 
    Mock các hàm verify từ Firebase để không gọi network thực.
    """
    # Setup mock returns
    mock_verify.return_value = {"uid": "test_user_123", "email": "test@example.com"}
    mock_extract.return_value = {
        "uid": "test_user_123", 
        "email": "test@example.com", 
        "name": "Test User", 
        "picture": ""
    }

    payload = {"id_token": "fake_firebase_token_from_client"}
    response = client.post("/auth/login", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["uid"] == "test_user_123"
    assert data["email"] == "test@example.com"


@patch("app.services.command_svc.generate_linux_command")
def test_generate_command(mock_generate):
    """
    Test tạo lệnh. 
    Sử dụng patch để OpenAI API luôn trả về chuỗi tĩnh 'ls -la'.
    """
    # Setup mock return cho OpenAI
    mock_generate.return_value = "ls -la"

    payload = {"prompt": "Liệt kê tất cả file ẩn trong thư mục"}
    
    # Vì đã đè get_current_user, ta không cần gửi Bearer token
    response = client.post("/commands/", json=payload)

    assert response.status_code == 201
    data = response.json()
    
    # Kiểm tra dữ liệu được lưu và trả về chính xác
    assert data["command"] == "ls -la"
    assert data["prompt"] == "Liệt kê tất cả file ẩn trong thư mục"
    assert data["uid"] == "test_user_123"  # Bằng với uid trong mock_get_current_user
    assert "id" in data
    assert "created_at" in data


def test_get_command_history():
    """
    Test lấy danh sách lịch sử lệnh của người dùng đang đăng nhập.
    (Do bài test create_command chạy trước, DB có thể đã có ít nhất 1 record)
    """
    response = client.get("/commands/")
    assert response.status_code == 200
    
    data = response.json()
    
    # Kết quả phải là một mảng (list)
    assert isinstance(data, list)
    
    # Kiểm tra cấu trúc của phần tử nếu mảng không rỗng
    if len(data) > 0:
        item = data[0]
        assert "id" in item
        assert "prompt" in item
        assert "command" in item
        assert "created_at" in item
        # Đảm bảo schema danh sách không lộ uid
        assert "uid" not in item


@patch("app.services.command_svc.generate_linux_command")
def test_get_command_detail(mock_generate):
    """
    Test lấy chi tiết của một lệnh cụ thể.
    """
    # 1. Tạo trước 1 lệnh để lấy Firestore ID
    mock_generate.return_value = "pwd"
    create_res = client.post("/commands/", json={"prompt": "In đường dẫn thư mục hiện tại"})
    assert create_res.status_code == 201
    command_id = create_res.json()["id"]

    # 2. Gọi GET detail bằng chính ID vừa tạo
    detail_res = client.get(f"/commands/{command_id}")
    
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    
    assert detail_data["id"] == command_id
    assert detail_data["command"] == "pwd"
    assert detail_data["uid"] == "test_user_123"
