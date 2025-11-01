import re
import time
import google.generativeai as genai
from .config import GEMINI_MODEL_NAME
from .dictionary_manager import DictionaryManager


class Translator:
    """
    Lớp này xử lý việc xây dựng prompt và gọi Gemini API.
    """

    def __init__(self, dictionary_manager: DictionaryManager, api_key: str):
        if not api_key:
            raise ValueError("GOOGLE_API_KEY không được cung cấp. Vui lòng kiểm tra file books_to_run.json")

        # Dùng api_key được truyền vào
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(GEMINI_MODEL_NAME)

        self.dictionary_manager = dictionary_manager
        print("Đang tải từ điển từ DictionaryManager...")
        # Tải 1 lần duy nhất để tái sử dụng
        self.full_term_map = self.dictionary_manager.get_term_map()

        # Sắp xếp các key từ dài đến ngắn.
        self.sorted_term_keys = sorted(self.full_term_map.keys(), key=len, reverse=True)
        print("Trình dịch AI (Gemini) đã sẵn sàng (đã nạp từ điển).")

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



        # Tìm các thuật ngữ liên quan DỰA TRÊN văn bản
        context_glossary = self._find_contextual_glossary(text_to_translate)

        # Xây dựng prompt với văn bản
        prompt = self._build_prompt(text_to_translate, context_glossary)

        primary_model_name = GEMINI_MODEL_NAME  # "gemini-2.5-flash"
        fallback_model_name = "gemini-2.0-flash"  # Model dự phòng theo yêu cầu

        def format_response(translated_text: str) -> str:
            """Hàm tiện ích nội bộ để format text trả về."""
            paragraphs = re.split(r'\n+', translated_text.strip())
            non_empty_paragraphs = [p for p in paragraphs if p.strip()]
            return '\n\n'.join(non_empty_paragraphs)

        # 4. Gọi API
        print(f"Đang gửi yêu cầu đến Gemini API (Model: {primary_model_name})... (Lần 1)")
        try:
            response = self.model.generate_content(prompt)
            return format_response(response.text)

        except Exception as e:
            error_message = str(e)
            print(f"Lỗi lần 1 (Model: {primary_model_name}): {error_message}")

            # --- XỬ LÝ LỖI ---

            # TRƯỜNG HỢP 1: Lỗi 500 -> Chuyển sang model dự phòng
            if "500" in error_message:
                print(f"Gặp lỗi 500. Chuyển sang model '{fallback_model_name}' và thử lại (Lần 2)...")
                try:
                    # Khởi tạo model dự phòng
                    fallback_model = genai.GenerativeModel(fallback_model_name)
                    response = fallback_model.generate_content(prompt)
                    return format_response(response.text)

                except Exception as e2:
                    print(f"Lỗi lần 2 (Model: {fallback_model_name}): {e2}")
                    # Thất bại cả 2 lần -> Báo lỗi
                    raise Exception(f"Lỗi Gemini API (thất bại sau khi thử lại với model dự phòng): {e2}")

            # TRƯỜNG HỢP 2: Lỗi khác -> Sleep 3s và thử lại với CÙNG model
            else:
                print(f"Gặp lỗi khác. Chờ 3 giây và thử lại với CÙNG model (Lần 2)...")
                try:
                    time.sleep(3)
                    # Thử lại với model chính (self.model)
                    response = self.model.generate_content(prompt)
                    return format_response(response.text)

                except Exception as e3:
                    print(f"Lỗi lần 2 (Model: {primary_model_name} sau khi sleep): {e3}")
                    # Thất bại cả 2 lần -> Báo lỗi
                    raise Exception(f"Lỗi Gemini API (thất bại sau khi thử lại): {e3}")