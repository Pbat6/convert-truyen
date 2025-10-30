# src/progress_manager.py
import json
import os
from datetime import datetime


class ProgressManager:
    """
    Quản lý trạng thái dịch của các bộ truyện.
    Sử dụng file 'progress.json' để lưu "bookmark".
    """

    def __init__(self, state_file='progress.json'):
        self.state_file = state_file
        self.progress_data = self._load_progress()
        print(f"Quản lý tiến độ đã sẵn sàng. (Sử dụng file: {self.state_file})")

    def _load_progress(self) -> dict:
        """Tải file JSON. Trả về dict rỗng nếu file không tồn tại."""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Cảnh báo: File {self.state_file} bị lỗi. Sẽ tạo file mới.")
                return {}
        return {}

    def _save_progress(self):
        """Lưu dữ liệu hiện tại vào file JSON."""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress_data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Lỗi nghiêm trọng khi lưu tiến độ: {e}")

    def get_last_processed_url(self, book_id: str) -> str | None:
        """
        Lấy URL của chương cuối cùng đã được xử lý cho một book_id.
        """
        if book_id in self.progress_data:
            return self.progress_data[book_id].get('last_processed_url')
        return None

    def update_progress(self, book_id: str, chapter_info: dict, main_book_url: str):
        """
        Cập nhật "bookmark" cho một book_id sau khi dịch xong 1 chương.
        """
        if book_id not in self.progress_data:
            self.progress_data[book_id] = {}

        # Cập nhật thông tin
        self.progress_data[book_id]['main_url'] = main_book_url
        self.progress_data[book_id]['last_processed_url'] = chapter_info['url']
        self.progress_data[book_id]['last_processed_title'] = chapter_info['title']
        self.progress_data[book_id]['last_processed_timestamp'] = datetime.now().isoformat()

        # Lưu thay đổi ngay lập tức
        self._save_progress()