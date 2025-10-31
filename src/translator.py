import re
import google.generativeai as genai
from .config import GOOGLE_API_KEY, GEMINI_MODEL_NAME
from .dictionary_manager import DictionaryManager


class Translator:
    """
    Lớp này xử lý việc xây dựng prompt và gọi Gemini API.
    """

    def __init__(self, dictionary_manager: DictionaryManager):
        if not GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY không được tìm thấy. Vui lòng kiểm tra file .env")

        genai.configure(api_key=GOOGLE_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL_NAME)

        # --- THAY ĐỔI: Lấy và lưu trữ các từ điển ngay khi khởi tạo ---
        self.dictionary_manager = dictionary_manager
        print("Đang tải từ điển từ DictionaryManager...")
        # Tải 1 lần duy nhất để tái sử dụng
        self.full_term_map = self.dictionary_manager.get_term_map()
        self.ignored_phrases = self.dictionary_manager.get_ignored_phrases()
        # Sắp xếp các key từ dài đến ngắn. Đây là bước CỰC KỲ QUAN TRỌNG
        # để ưu tiên khớp "Trương Tam Phong" trước "Trương Tam".
        self.sorted_term_keys = sorted(self.full_term_map.keys(), key=len, reverse=True)
        print("Trình dịch AI (Gemini) đã sẵn sàng (đã nạp từ điển).")
        # --- KẾT THÚC THAY ĐỔI ---

    def _build_prompt(self, text_chunk: str, glossary: dict) -> str:
        """Hàm nội bộ để xây dựng prompt hoàn chỉnh"""

        if not glossary:
            glossary_prompt_part = "Hãy dịch một cách tự nhiên và mượt mà nhất."
        else:
            # Format các thuật ngữ
            items = [f'- "{k}" phải được dịch là "{v}"' for k, v in glossary.items()]
            glossary_prompt_part = (
                    "YÊU CẦU CỐT LÕI (GLOSSARY): Bạn PHẢI tuân thủ nghiêm ngặt bảng chú giải (glossary) sau đây "
                    "cho các tên riêng và thuật ngữ. KHÔNG được dịch tự do các từ này:\n" +
                    "\n".join(items)
            )

        return f"""
        Nhiệm vụ: Dịch đoạn văn truyện tiếng Trung sau đây sang tiếng Việt.

        --- QUY TẮC PHONG CÁCH & ĐỊNH DẠNG ---
        1.  Phong cách: Văn phong mượt mà, trôi chảy, phù hợp ngữ cảnh (kiếm hiệp, tiên hiệp, đô thị...).
        2.  ƯU TIÊN HÁN VIỆT: Đối với tên riêng, địa danh, tước vị (ví dụ: 'Lục sư tỷ', 'Vân Lam Tông'), PHẢI ưu tiên dùng từ Hán Việt thay vì dịch nghĩa thuần Việt (KHÔNG dịch 'sáu sư tỷ', 'Mây Lam Tông') trừ khi glossary (bảng chú giải) yêu cầu khác.
        3.  HỘI THOẠI: Nội dung trong cặp dấu「」là lời thoại, BẮT BUỘC thay thế cặp dấu「」thành dấu ngoặc kép "".
        4.  TIÊU ĐỀ: Tiêu đề (nếu có ở dòng đầu) phải được dịch và giữ ở dòng đầu tiên.

        {glossary_prompt_part}

        Đoạn văn tiếng Trung cần dịch:
        ---
        {text_chunk}
        ---

        Bản dịch tiếng Việt (Chỉ trả về phần văn bản đã dịch, không thêm lời chào hay giải thích):
        """

    def _preprocess_text(self, text: str) -> str:
        """
        Tiền xử lý văn bản: Xóa các cụm từ rác (ignored).
        """
        print(f"Đang làm sạch văn bản, xoá {len(self.ignored_phrases)} cụm từ rác...")
        for phrase in self.ignored_phrases:
            text = text.replace(phrase, '')
        return text

    def _find_contextual_glossary(self, text: str) -> dict:
        """
        Tái tạo lại logic "find_contextual_terms".
        Tìm các thuật ngữ trong 'full_term_map' có xuất hiện trong văn bản.
        """
        print("Đang phân tích thuật ngữ theo ngữ cảnh...")
        context_glossary = {}

        # Chúng ta dùng self.sorted_term_keys đã được sắp xếp lúc khởi tạo
        # để đảm bảo ưu tiên khớp cụm từ dài trước
        for key in self.sorted_term_keys:
            if key in text:
                context_glossary[key] = self.full_term_map[key]

        print(f"Đã tìm thấy {len(context_glossary)} thuật ngữ liên quan.")
        return context_glossary

    def translate_chapter(self, text_to_translate: str) -> str:
        """
        Hàm chính để dịch một đoạn văn bản (ví dụ: 1 chương truyện).
        """

        # 1. (MỚI) Tiền xử lý, xoá rác
        cleaned_text = self._preprocess_text(text_to_translate)

        # 2. (MỚI) Tìm các thuật ngữ liên quan DỰA TRÊN văn bản đã làm sạch
        context_glossary = self._find_contextual_glossary(cleaned_text)

        # 3. (SỬA ĐỔI) Xây dựng prompt với văn bản đã làm sạch
        prompt = self._build_prompt(cleaned_text, context_glossary)

        # 4. Gọi API
        print("Đang gửi yêu cầu đến Gemini API...")
        try:
            response = self.model.generate_content(prompt)
            translated_text = response.text.strip()

            # (Giữ nguyên logic format)
            # 1. Tách văn bản thành các đoạn dựa trên MỘT HOẶC NHIỀU ký tự newline
            paragraphs = re.split(r'\n+', translated_text)

            # 2. Lọc ra các đoạn rỗng (nếu có)
            non_empty_paragraphs = [p for p in paragraphs if p.strip()]

            # 3. Nối các đoạn lại với nhau, đảm bảo mỗi đoạn cách nhau 2 dấu newline
            formatted_text = '\n\n'.join(non_empty_paragraphs)

            return formatted_text

        except Exception as e:
            print(f"Lỗi khi gọi API: {e}")
            raise Exception(f"Lỗi Gemini API: {e}")