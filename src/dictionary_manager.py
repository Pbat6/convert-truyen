from .config import VIETPHRASE_FILE, NAMES_FILE


class DictionaryManager:
    """
    Lớp này quản lý việc tải và tra cứu các từ điển.
    Nó chỉ tải 1 lần khi khởi tạo.
    """

    def __init__(self):
        print("Bắt đầu nạp từ điển vào bộ nhớ...")
        self.combined_glossary = {}
        self.sorted_keys = []
        self._load_dictionaries()
        print(f"Đã nạp thành công {len(self.combined_glossary)} thuật ngữ.")

    def _load_key_value_file(self, file_path):
        """Hàm nội bộ để đọc file .txt (dạng key=value)"""
        glossary = {}
        content = None

        # Thử đọc file với các encoding phổ biến
        try:
            # 1. Thử UTF-8 (chuẩn)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError as e:
            # 2. Nếu UTF-8 lỗi (ví dụ: '0xff'), thử UTF-16
            # Lỗi '0xff' ở vị trí 0 thường là BOM của UTF-16
            print(f"Cảnh báo: Đọc {file_path} bằng UTF-8 thất bại. Thử lại bằng UTF-16...")
            try:
                # 'utf-16' sẽ tự động phát hiện BOM (LE hoặc BE)
                with open(file_path, 'r', encoding='utf-16') as f:
                    content = f.read()
                print(f"Đã đọc thành công {file_path} bằng UTF-16.")
            except Exception as e_utf16:
                print(f"Lỗi: Không thể đọc file {file_path} bằng cả UTF-8 và UTF-16: {e_utf16}")
                return glossary  # Trả về dict rỗng
        except FileNotFoundError:
            print(f"CẢNH BÁO: Không tìm thấy file từ điển: {file_path}")
            return glossary
        except Exception as e:
            print(f"Lỗi không xác định khi đọc file {file_path}: {e}")
            return glossary

        if content is None:
            return glossary  # Trường hợp FileNotFoundError

        # Xử lý nội dung đã đọc (tách ra khỏi khối try...except đọc file)
        try:
            for line in content.splitlines():
                if '=' not in line:
                    continue

                parts = line.strip().split('=', 1)
                if len(parts) == 2 and parts[0]:
                    glossary[parts[0]] = parts[1]
        except Exception as e:
            print(f"Lỗi khi xử lý nội dung (đã đọc) của file {file_path}: {e}")

        return glossary

    def _load_dictionaries(self):
        """Tải và gộp các từ điển chính (VietPhrase và Names)"""
        vietphrase = self._load_key_value_file(VIETPHRASE_FILE)
        names = self._load_key_value_file(NAMES_FILE)

        # Gộp 2 từ điển, ưu tiên file Names (ghi đè lên VietPhrase nếu trùng)
        self.combined_glossary = {**vietphrase, **names}

        # Tối ưu hóa: Sắp xếp các key từ dài nhất đến ngắn nhất
        # Việc này ĐẢM BẢO "Lý Bạch" được khớp trước "Lý"
        self.sorted_keys = sorted(self.combined_glossary.keys(), key=len, reverse=True)

    def find_contextual_terms(self, text: str) -> dict:
        """
        Quét văn bản đầu vào và trích xuất các thuật ngữ
        có trong từ điển.
        """
        context_glossary = {}
        # Tạo bản sao để tránh thay đổi text gốc (nếu cần)
        temp_text = text

        for key in self.sorted_keys:
            if key in temp_text:
                # Nếu tìm thấy, thêm vào glossary và xóa khỏi temp_text
                # để tránh các cụm từ con bị khớp nhầm
                context_glossary[key] = self.combined_glossary[key]
                temp_text = temp_text.replace(key, "")

        return context_glossary