# run_all.py
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

# Import các dịch vụ để khởi tạo
from src.dictionary_manager import DictionaryManager
from src.scraper import Scraper
from src.uploader import TangThuvienClient
# Import hàm main
from main import run_full_translation_process

# --- CẤU HÌNH SONG SONG ---
MAX_WORKERS = 3
# --------------------------

base_dir = os.path.dirname(os.path.abspath(__file__))
base_output_directory = os.path.join(base_dir, "progress")

# === THAY ĐỔI: Các biến global cho DỊCH VỤ STATELESS ===
# Chúng sẽ được khởi tạo là None
g_dict_manager = None
g_scraper = None
g_uploader = None


# === THAY ĐỔI: Hàm init_worker mới (sẽ được gọi "lười biếng") ===
def init_worker_lazy():
    """
    Hàm này được gọi BÊN TRONG worker_task,
    đảm bảo nó chỉ chạy khi worker THỰC SỰ nhận việc lần đầu tiên.
    """
    global g_dict_manager, g_scraper, g_uploader

    # Kiểm tra một lần nữa (mặc dù đã kiểm tra bên ngoài)
    if g_dict_manager is None:
        print(f"[WORKER {os.getpid()}] Lần chạy đầu tiên. Đang khởi tạo dịch vụ stateless (Tải từ điển...)...")

        # Đây chính là logic của hàm initialize_services_stateless() cũ
        g_dict_manager = DictionaryManager()
        g_scraper = Scraper()
        g_uploader = TangThuvienClient()

        print(f"[WORKER {os.getpid()}] Đã sẵn sàng.")


def load_book_configs():
    """Đọc file config truyện (Giữ nguyên)"""
    config_file_path = os.path.join(base_dir, 'books_to_run.json')
    try:
        with open(config_file_path, 'r', encoding='utf-8') as f:
            books = json.load(f)
        return books
    except FileNotFoundError:
        print(f"LỖI: Không tìm thấy file 'books_to_run.json'.")
        return []
    except json.JSONDecodeError:
        print(f"LỖI: File 'books_to_run.json' bị lỗi cú pháp JSON.")
        return []


def worker_task(book_config):
    """
    Hàm này được mỗi tiến trình (worker) gọi cho MỖI TRUYỆN.
    """
    global g_dict_manager, g_scraper, g_uploader

    # === THAY ĐỔI: Logic "Khởi tạo Lười biếng" ===
    # Kiểm tra xem worker này đã được khởi tạo chưa
    if g_dict_manager is None:
        init_worker_lazy()
    # === KẾT THÚC THAY ĐỔI ===

    story_id = book_config.get('ttv_story_id', 'UNKNOWN')
    print(f"[WORKER {os.getpid()}] Bắt đầu xử lý truyện: {story_id}")
    start_time = time.time()

    try:
        # Truyền các dịch vụ (bây giờ đã chắc chắn được khởi tạo)
        run_full_translation_process(
            # Dịch vụ stateless (từ global)
            dict_manager=g_dict_manager,
            scraper=g_scraper,
            uploader=g_uploader,

            # Config của truyện (từ book_config)
            book_url=book_config['book_url'],
            base_output_dir=base_output_directory,
            ttv_story_id=book_config['ttv_story_id'],
            chapter_limit=book_config.get('chapter_limit', None),
            google_api_key=book_config['google_api_key']
        )

        end_time = time.time()
        return f"Hoàn tất {story_id} trong {end_time - start_time:.2f} giây."

    except KeyError as e:
        return f"LỖI {story_id}: Cấu hình thiếu key bắt buộc: {e}"
    except Exception as e:
        return f"LỖI NGHIÊM TRỌNG {story_id}: {e}"


def run_parallel():
    """
    Đọc file config và thực thi song song
    """
    print(f"--- BẮT ĐẦU CHẠY SONG SONG (Tối đa: {MAX_WORKERS} luồng) ---")

    books = load_book_configs()
    if not books:
        print("Không có truyện nào để chạy. Dừng.")
        return

    print(f"Tìm thấy {len(books)} truyện. Bắt đầu đưa vào hàng đợi...")

    # === THAY ĐỔI: XÓA `initializer=init_worker` ===
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:

        futures = {executor.submit(worker_task, config): config for config in books}

        for future in as_completed(futures):
            book_id = futures[future].get('ttv_story_id', 'UNKNOWN')
            try:
                result = future.result()
                print(f"[MAIN] Kết quả job {book_id}: {result}")
            except Exception as e:
                print(f"[MAIN] Job {book_id} phát sinh lỗi nghiêm trọng: {e}")

    print("--- HOÀN TẤT TẤT CẢ TRUYỆN ---")


if __name__ == "__main__":
    run_parallel()