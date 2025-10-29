import os
from pathlib import Path
from dotenv import load_dotenv

# Tải các biến môi trường từ file .env
load_dotenv()

# --- Đường dẫn ---
# Lấy đường dẫn thư mục gốc của dự án (ví dụ: .../hybrid_translator/)
BASE_DIR = Path(__file__).resolve().parent.parent
# Đường dẫn đến thư mục 'data'
DATA_DIR = BASE_DIR / "data"

# --- Cấu hình API ---
# Lấy API Key từ biến môi trường
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
# Chọn model (Flash rẻ và nhanh, phù hợp cho dịch thuật)
GEMINI_MODEL_NAME = "gemini-2.5-flash"

# --- Cấu hình Từ điển ---
# Chúng ta tập trung vào 2 file này cho việc convert hybrid
VIETPHRASE_FILE = DATA_DIR / "VietPhrase.txt"
NAMES_FILE = DATA_DIR / "Names.txt"