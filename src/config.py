import os
from pathlib import Path
from dotenv import load_dotenv

# Tải các biến môi trường từ file .env
load_dotenv()

# Lấy đường dẫn thư mục gốc của dự án (ví dụ: .../hybrid_translator/)
BASE_DIR = Path(__file__).resolve().parent.parent
# Đường dẫn đến thư mục 'data'
DATA_DIR = BASE_DIR / "data"

# Chọn model (Flash rẻ và nhanh, phù hợp cho dịch thuật)
GEMINI_MODEL_NAME = "gemini-2.0-flash" #

TTV_API_URL = os.environ.get("TTV_API_URL")
TTV_STORY_ID = os.environ.get("TTV_STORY_ID")
TTV_TOKEN = os.environ.get("TTV_TOKEN")

# Xây dựng dict cookies từ các biến môi trường
TTV_COOKIES = {
    "remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d": os.environ.get("TTV_COOKIE_REMEMBER"),
    "XSRF-TOKEN": os.environ.get("TTV_COOKIE_XSRF"),
    "laravel_session": os.environ.get("TTV_COOKIE_SESSION"),
}

# Kiểm tra xem các biến quan trọng đã được set chưa
if not all([TTV_API_URL, TTV_STORY_ID, TTV_TOKEN,
            TTV_COOKIES["remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d"],
            TTV_COOKIES["XSRF-TOKEN"],
            TTV_COOKIES["laravel_session"]]):
    print("Cảnh báo: Một hoặc nhiều biến môi trường TTV (API, Story ID, Token, Cookies) chưa được Sét trong file .env")

# Các file này sẽ được gộp lại. File ở trên sẽ "ghi đè" file ở dưới nếu trùng key.
# => Names.txt được ưu tiên cao nhất.
TERM_DICTIONARY_FILES = [
    DATA_DIR / "Names.txt",              # Ưu tiên 1: Tên riêng
    DATA_DIR / "Pronouns.txt",           # Ưu tiên 2: Đại từ
    DATA_DIR / "VietPhrase.txt",         # Ưu tiên 3: Cụm từ thông dụng
    DATA_DIR / "LacViet.txt",            # Ưu tiên 4: Từ điển Lạc Việt
    DATA_DIR / "ChinesePhienAmWords.txt" # Ưu tiên 5: Phiên âm
]

# Các cụm từ trong file này sẽ bị xóa khỏi văn bản thô TRƯỚC KHI dịch
# IGNORED_PHRASES_FILES = [
#     DATA_DIR / "IgnoredChinesePhrases.txt"
# ]

# File này cần logic xử lý đặc biệt (thường là Regex)
# Chúng ta định nghĩa sẵn, nhưng chưa implement logic tải (xem giải thích bên dưới)
RULE_DICTIONARY_FILES = [
    DATA_DIR / "LuatNhan.txt"
]