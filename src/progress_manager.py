import os
import json
from pathlib import Path

class ProgressManager:
    """
    Quản lý việc đọc/ghi file progress.json CỤ THỂ cho từng bộ truyện.
    """

    def __init__(self, state_file: str):
        """
        Khởi tạo ProgressManager với một đường dẫn file state cụ thể.

        Args:
            state_file (str): Đường dẫn đầy đủ đến file progress.json
                              (ví dụ: /.../progress/book_123/progress.json)
        """
        self.state_file = state_file
        print(f"ProgressManager được khởi tạo. Sẽ sử dụng file: {self.state_file}")
        self.progress_data = self._load_progress()

    def _load_progress(self) -> dict:
        """
        Tải file JSON chứa tiến độ.
        """
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"Đã tải tiến độ từ {self.state_file}")
                return data
        except FileNotFoundError:
            print(f"Không tìm thấy file tiến độ {self.state_file}. Sẽ tạo file mới.")
            return {}
        except json.JSONDecodeError:
            print(f"LỖI: File tiến độ {self.state_file} bị hỏng. Sẽ tạo file mới.")
            return {}
        except Exception as e:
            print(f"Lỗi không xác định khi tải {self.state_file}: {e}")
            return {}

    def _save_progress(self):
        """
        Lưu dữ liệu tiến độ hiện tại vào file JSON.
        """
        try:
            # Đảm bảo thư mục cha tồn tại (quan trọng khi chạy lần đầu)
            os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"LỖI NGHIÊM TRỌNG: Không thể lưu tiến độ vào {self.state_file}: {e}")

    def get_last_processed_url(self, book_id: str) -> str | None:
        """
        Lấy URL của chương cuối cùng đã xử lý cho book_id.
        """
        return self.progress_data.get(book_id, {}).get('last_processed_url')

    def update_progress(self, book_id: str, chapter_info: dict, book_url: str):
        """
        Cập nhật tiến độ cho book_id với thông tin chương mới nhất.
        """
        if book_id not in self.progress_data:
            self.progress_data[book_id] = {}

        self.progress_data[book_id]['last_processed_url'] = chapter_info['url']
        self.progress_data[book_id]['last_processed_title'] = chapter_info['title']
        self.progress_data[book_id]['book_url'] = book_url
        self.progress_data[book_id]['last_updated'] = os.path.getmtime(self.state_file) if os.path.exists(self.state_file) else 0

        self._save_progress()