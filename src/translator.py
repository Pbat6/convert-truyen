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
        self.dictionary_manager = dictionary_manager
        print("Trình dịch AI (Gemini) đã sẵn sàng.")

    def _build_prompt(self, text_chunk: str, glossary: dict) -> str:
        """Hàm nội bộ để xây dựng prompt hoàn chỉnh"""

        if not glossary:
            glossary_prompt_part = "Hãy dịch một cách tự nhiên và mượt mà nhất."
        else:
            # Format các thuật ngữ
            items = [f'- "{k}" phải được dịch là "{v}"' for k, v in glossary.items()]
            glossary_prompt_part = (
                    "YÊU CẦU CỐT LÕI: Bạn PHẢI tuân thủ nghiêm ngặt bảng chú giải (glossary) sau đây "
                    "cho các tên riêng và thuật ngữ. KHÔNG được dịch tự do các từ này:\n" +
                    "\n".join(items)
            )

        return f"""
        Nhiệm vụ: Dịch đoạn văn truyện tiếng Trung sau đây sang tiếng Việt.
        Phong cách: Văn phong mượt mà, tự nhiên, trôi chảy, đúng ngữ cảnh truyện (kiếm hiệp, tiên hiệp, đô thị...).

        {glossary_prompt_part}

        Đoạn văn tiếng Trung cần dịch:
        ---
        {text_chunk}
        ---

        Bản dịch tiếng Việt (Chỉ trả về phần văn bản đã dịch, không thêm lời chào hay giải thích):
        """

    def translate_chapter(self, text_to_translate: str) -> str:
        """
        Hàm chính để dịch một đoạn văn bản (ví dụ: 1 chương truyện).
        """
        print("Đang phân tích thuật ngữ trong văn bản...")
        # 1. Tìm các thuật ngữ liên quan
        context_glossary = self.dictionary_manager.find_contextual_terms(text_to_translate)
        print(f"Đã tìm thấy {len(context_glossary)} thuật ngữ liên quan.")

        # 2. Xây dựng prompt
        prompt = self._build_prompt(text_to_translate, context_glossary)

        # 3. Gọi API
        print("Đang gửi yêu cầu đến Gemini API...")
        try:
            response = self.model.generate_content(prompt)
            translated_text = response.text.strip()

            # --- BEST PRACTICE START ---
            # Đây là logic mới để chuẩn hóa output:

            # 1. Tách văn bản thành các đoạn dựa trên MỘT HOẶC NHIỀU ký tự newline
            #    Điều này xử lý cả trường hợp model trả về '\n' và '\n\n'
            paragraphs = re.split(r'\n+', translated_text)

            # 2. Lọc ra các đoạn rỗng (nếu có)
            non_empty_paragraphs = [p for p in paragraphs if p.strip()]

            # 3. Nối các đoạn lại với nhau, đảm bảo mỗi đoạn cách nhau 2 dấu newline
            formatted_text = '\n\n'.join(non_empty_paragraphs)

            return formatted_text
            # --- BEST PRACTICE END ---

        except Exception as e:
            print(f"Lỗi khi gọi API: {e}")
            return f"Lỗi Dịch Thuật: {e}"