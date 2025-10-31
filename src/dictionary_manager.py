import src.config as config
import time
from pathlib import Path


class DictionaryManager:
    """
    Lớp này quản lý việc tải và tra cứu các từ điển.
    Nó chỉ tải 1 lần khi khởi tạo.
    """

    def __init__(self):
        """
        Khởi tạo và tự động tải tất cả các từ điển được định nghĩa trong config.
        """
        print("--- Bắt đầu tải các từ điển ---")

        self.term_map = {}
        # Tải theo thứ tự ngược lại (reversed)
        # để file ưu tiên cao (ở đầu list) ghi đè lên các file ưu tiên thấp (ở cuối list).
        for file_path in reversed(config.TERM_DICTIONARY_FILES):
            if not file_path.exists():
                print(f"Cảnh báo: Không tìm thấy file từ điển: {file_path}")
                continue

            start_time = time.time()
            count = self._load_term_dictionary(file_path)
            elapsed = time.time() - start_time
            print(f"  - Đã tải {count} terms từ {file_path.name} (mất {elapsed:.2f}s)")

        print(f"==> Tổng số 'Term' (Key=Value) đã tải: {len(self.term_map)}")

        # 2. Tải Từ điển Ignored
        self.ignored_phrases = set()
        for file_path in config.IGNORED_PHRASES_FILES:
            if not file_path.exists():
                print(f"Cảnh báo: Không tìm thấy file từ điển: {file_path}")
                continue

            start_time = time.time()
            count = self._load_ignored_phrases(file_path)
            elapsed = time.time() - start_time
            print(f"  - Đã tải {count} cụm từ 'Ignored' từ {file_path.name} (mất {elapsed:.2f}s)")

        print(f"==> Tổng số 'Ignored Phrases' đã tải: {len(self.ignored_phrases)}")

        # 3. Tải Từ điển Rules (LuatNhan.txt)
        # File này cần logic xử lý riêng (regex) nên chúng ta sẽ chưa implement
        # Khi nào cần, bạn có thể thêm hàm _load_rule_dictionary
        print("Lưu ý: LuatNhan.txt (Rule Dictionary) đã được nhận diện nhưng chưa implement logic tải.")
        print("--- Tải từ điển hoàn tất ---")

    def _load_term_dictionary(self, file_path: Path) -> int:
        """
        Tải file từ điển (định dạng 'Key=Value\n') vào self.term_map.
        Ghi đè (overwrite) các key đã tồn tại (đây là lý do chúng ta tải ngược).
        """
        count = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Bỏ qua dòng trống hoặc dòng comment (thường bắt đầu bằng #)
                    if not line or line.startswith('#'):
                        continue

                    # Tách Key=Value
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        key, value = parts[0].strip(), parts[1].strip()
                        # Đảm bảo key không rỗng và value không rỗng
                        if key and value:
                            self.term_map[key] = value
                            count += 1
                    # Bỏ qua các dòng không đúng định dạng (ví dụ: file LacViet có dòng ✚[...])
                    elif file_path.name == "LacViet.txt" and line.startswith('✚'):
                        # Logic đặc thù nếu cần xử lý LacViet, tạm thời bỏ qua
                        pass

        except Exception as e:
            print(f"Lỗi khi đọc file {file_path.name}: {e}")
        return count

    def _load_ignored_phrases(self, file_path: Path) -> int:
        """
        Tải file từ điển ignored (mỗi dòng là một cụm từ) vào self.ignored_phrases.
        """
        count = 0
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    phrase = line.strip()
                    if phrase and not phrase.startswith('#'):
                        self.ignored_phrases.add(phrase)
                        count += 1
        except Exception as e:
            print(f"Lỗi khi đọc file {file_path.name}: {e}")
        return count

    # --- Các hàm Getter ---

    def get_term_map(self):
        """
        Trả về MỘT từ điển duy nhất đã gộp tất cả các file.
        """
        return self.term_map

    def get_ignored_phrases(self):
        """
        Trả về MỘT set duy nhất chứa tất cả các cụm từ cần bỏ qua.
        """
        return self.ignored_phrases