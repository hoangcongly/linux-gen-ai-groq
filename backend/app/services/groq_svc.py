"""
services/groq_svc.py
----------------------
Integrates with Groq to convert natural language into Linux commands.
"""

from openai import AsyncOpenAI, RateLimitError, AuthenticationError, APIConnectionError
from fastapi import HTTPException, status
from app.core.config import get_settings

_SYSTEM_PROMPT = """Bạn là một công cụ chuyển đổi ngôn ngữ tự nhiên sang lệnh Linux/Ubuntu.

QUY TẮC TUYỆT ĐỐI — VI PHẠM BẤT KỲ QUY TẮC NÀO LÀ SAI:
1. Chỉ trả về DUY NHẤT câu lệnh Linux/Ubuntu hợp lệ.
2. TUYỆT ĐỐI KHÔNG dùng markdown. Không dùng ```bash, ```, hay bất kỳ ký hiệu nào khác.
3. TUYỆT ĐỐI KHÔNG giải thích. Không ghi "Lệnh này...", "Để thực hiện...", hay bất kỳ câu văn nào.
4. TUYỆT ĐỐI KHÔNG chào hỏi, không mở đầu, không kết thúc bằng chữ.
5. Nếu yêu cầu mơ hồ hoặc không thể chuyển thành một lệnh Linux duy nhất, hãy trả về lệnh gần đúng nhất và hợp lý nhất.
6. Output chỉ là chuỗi ký tự của lệnh shell. Không có gì khác.

VÍ DỤ:
- Input : "Hiển thị dung lượng ổ đĩa còn trống"
  Output: df -h
- Input : "Liệt kê tất cả file trong thư mục hiện tại bao gồm file ẩn"
  Output: ls -la
- Input : "Tìm tất cả file .log lớn hơn 100MB"
  Output: find / -name "*.log" -size +100M
"""

async def generate_linux_command(user_prompt: str) -> str:
    settings = get_settings()
    
    if not settings.GROQ_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GROQ_API_KEY chưa được cấu hình. Vui lòng kiểm tra lại file .env."
        )

    try:
        client = AsyncOpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url=settings.GROQ_BASE_URL or "https://api.groq.com/openai/v1"
        )
        response = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": f"Yêu cầu: {user_prompt.strip()}"}
            ]
        )
        
        raw_text = response.choices[0].message.content
        if not raw_text:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="AI không thể tạo lệnh Linux từ yêu cầu này. Vui lòng mô tả rõ hơn."
            )

        return _strip_markdown_fences(raw_text)

    except RateLimitError as exc:
        print(f"[groq_svc] Groq API Limit: {exc}")
        # Lệnh dự phòng khi hệ thống quá tải (fallback logic)
        return "ls -la"
    except AuthenticationError as exc:
        print(f"[groq_svc] AuthenticationError: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Lỗi xác thực GROQ_API_KEY. Vui lòng kiểm tra lại API Key."
        )
    except APIConnectionError as exc:
        print(f"[groq_svc] APIConnectionError: {exc}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Lỗi kết nối đến máy chủ Groq. Vui lòng thử lại."
        )
    except HTTPException:
        raise
    except Exception as exc:
        print(f"[groq_svc] Unexpected error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Lỗi nội bộ khi gọi Groq API. Vui lòng thử lại."
        )

def _strip_markdown_fences(text: str) -> str:
    lines = text.strip().splitlines()

    if lines and lines[0].startswith("```"):
        lines = lines[1:]

    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]

    result = "\n".join(lines).strip()
    if result.startswith("`") and result.endswith("`"):
        result = result[1:-1].strip()

    return result
