# main.py

import sys
import os
import re
from src.dictionary_manager import DictionaryManager
from src.translator import Translator
from src.scraper import Scraper
from src.progress_manager import ProgressManager
from src.uploader import TangThuvienClient
import src.config as config

def initialize_services_stateless():
    """
    Khởi tạo các dịch vụ "stateless" (không phụ thuộc vào từng bộ truyện).
    ProgressManager (stateful) sẽ được khởi tạo sau.
    """
    print("--- Bắt đầu khởi tạo các dịch vụ Stateless (Dict, Translator, Scraper, Uploader) ---")
    try:
        dict_manager = DictionaryManager()
        translator = Translator(dictionary_manager=dict_manager)
        scraper = Scraper()
        uploader = TangThuvienClient()

        return translator, scraper, uploader
    except Exception as e:
        print(f"Lỗi nghiêm trọng khi khởi tạo dịch vụ: {e}")
        return None, None, None

def run_full_translation_process(
        book_url: str,
        base_output_dir: str,  # Giữ lại để lưu progress.json
        ttv_story_id: str,  # <--- THAY ĐỔI: ID truyện trên TTV
        chapter_limit: int | None = None
):
    """
    Hàm chính điều phối toàn bộ quá trình.

    Args:
        book_url (str): URL trang mục lục của truyện.
        base_output_dir (str): Thư mục gốc để lưu file progress.
        ttv_story_id (str): ID của truyện trên Tang Thư Viện để upload.
        chapter_limit (int | None): Số chương tối đa cần dịch/upload.
    """
    translator, scraper, uploader = initialize_services_stateless()
    if not all([translator, scraper, uploader]):
        print("Không thể khởi động. Thoát.")
        return

    # Xác định ID và thư mục output riêng cho truyện này
    book_id = "book_" + config.TTV_STORY_ID
    book_output_dir = os.path.join(base_output_dir, book_id)
    os.makedirs(book_output_dir, exist_ok=True)

    # Đường dẫn file progress riêng cho truyện này
    progress_file_path = os.path.join(book_output_dir, 'progress.json')
    # Khởi tạo ProgressManager với đường dẫn cụ thể
    progress_manager = ProgressManager(state_file=progress_file_path)

    print(f"--- Tool đã sẵn sàng! ---")
    print(f"Đang xử lý truyện: {book_id} (URL: {book_url})")
    print(f"Sẽ upload chương lên TTV Story ID: {ttv_story_id}")
    print(f"Sẽ lưu tiến độ vào: {progress_file_path}")

    # 2. Lấy danh sách *tất cả* chương
    all_chapters = scraper.get_chapter_links(book_url)
    if not all_chapters:
        print("Không có chương nào để dịch. Thoát.")
        return

    # 3. Lấy "bookmark" và lọc ra các chương cần dịch
    # (Giữ nguyên logic này)
    last_processed_url = progress_manager.get_last_processed_url(book_id)
    chapters_to_process = []

    if last_processed_url is None:
        print("Phát hiện truyện mới. Bắt đầu dịch từ chương đầu tiên.")
        chapters_to_process = all_chapters
    else:
        print(f"Đang tìm chương cuối cùng đã dịch: {last_processed_url}")
        found_last = False
        for chapter in all_chapters:
            if found_last:
                chapters_to_process.append(chapter)
            elif chapter['url'] == last_processed_url:
                found_last = True

        if not found_last:
            print("Cảnh báo: Không tìm thấy URL đã lưu. Sẽ dịch lại từ đầu.")
            chapters_to_process = all_chapters
        elif not chapters_to_process:
            print("Không có chương mới. Bạn đã dịch đến chương mới nhất.")
            return
        else:
            print(f"Tìm thấy {len(chapters_to_process)} chương mới.")

    # Áp dụng giới hạn số chương (NẾU CÓ)
    if chapter_limit is not None and chapter_limit > 0:
        total_available = len(chapters_to_process)
        if total_available == 0:
            print("Không có chương mới nào để áp dụng giới hạn.")
            return
        chapters_to_process = chapters_to_process[:chapter_limit]
        print(
            f"Đã áp dụng giới hạn: Chỉ xử lý {len(chapters_to_process)} chương (trong tổng số {total_available} chương mới).")
    elif chapter_limit is not None:
        print("Giới hạn chương không hợp lệ (<= 0). Sẽ không dịch chương nào.")
        return

    # 5. Lặp qua, cào, dịch và UPLOAD
    total_batch = len(chapters_to_process)
    if total_batch == 0:
        print("Không có chương nào trong batch này để xử lý.")
        return

    print(f"Bắt đầu dịch và upload batch gồm {total_batch} chương...")
    try:
        for i, chapter_info in enumerate(chapters_to_process, 1):
            title = chapter_info['title']
            url = chapter_info['url']

            print(f"\n--- Bắt đầu chương {i}/{total_batch}: {title} ---")

            # 6. Cào nội dung
            print(f"Đang cào nội dung từ: {url}")
            chinese_text = scraper.get_chapter_content(url)

            if not chinese_text or not chinese_text.strip():
                print(f"LỖI: Không cào được nội dung hoặc nội dung rỗng. Dừng xử lý batch này.")
                break

            text_to_translate = f"{title}\n\n{chinese_text}"

            # 7. Thực hiện dịch
            print("Đã có nội dung. Bắt đầu dịch...")
            full_translated_output = translator.translate_chapter(text_to_translate)
            print("Dịch xong.")

            # 8. Tách tiêu đề và nội dung đã dịch
            # (Giữ nguyên logic này)
            translated_title = title
            vietnamese_text = full_translated_output
            try:
                parts = full_translated_output.split('\n\n', 1)
                raw_translated_title = parts[0].strip()
                pattern_to_remove = r'^(Chương|C|Q|Quyển)\s*\d+\s*[:\-–—\s]*\s*'
                cleaned_title = re.sub(pattern_to_remove, '', raw_translated_title, flags=re.IGNORECASE).strip()

                if not cleaned_title:
                    translated_title = "Vô Đề"  # Hoặc giữ raw_translated_title
                else:
                    translated_title = cleaned_title

                if len(parts) > 1:
                    vietnamese_text = parts[1].strip()
                else:
                    vietnamese_text = ""

                print(f"Đã tách tiêu đề dịch: {translated_title}")

            except Exception as e:
                print(f"Cảnh báo: Lỗi khi tách tiêu đề ({e}). Sẽ dùng tiêu đề gốc và toàn bộ nội dung.")

            # Lấy số thứ tự chương (chap_stt)
            try:
                # Lấy index tuyệt đối của chương trong toàn bộ danh sách
                chapter_index = all_chapters.index(chapter_info) + 1
            except ValueError:
                print(f"LỖI: Không tìm thấy chapter_info trong all_chapters. Dùng index tạm thời {i}.")
                # Đây là một giải pháp dự phòng không lý tưởng,
                # vì 'i' là index trong batch, không phải index của toàn truyện
                # Nếu logic ở bước 3 đúng, lỗi này không nên xảy ra.
                # Tạm thời bỏ qua chương này nếu logic index lỗi
                print("Bỏ qua chương này do lỗi logic index.")
                continue

            # Thêm tiêu đề vào đầu nội dung (nhiều truyện trên TTV làm vậy)
            # BẠN CÓ THỂ TÙY CHỈNH DÒNG NÀY
            # final_content_to_upload = f"{translated_title}\n\n{vietnamese_text}"

            # Thực hiện upload
            success = uploader.upload_chapter(
                story_id=ttv_story_id,
                chapter_number=chapter_index,
                title=translated_title,
                content=vietnamese_text  # Sử dụng `vietnamese_text` nếu không muốn lặp lại tiêu đề
            )

            # 10. Cập nhật "bookmark" CHỈ KHI upload thành công
            if success:
                print(f"Đã upload thành công chương {chapter_index} lên TTV.")
                progress_manager.update_progress(book_id, chapter_info, book_url)
                print(f"Đã cập nhật tiến độ: Đã xong chương '{title}'")
            else:
                # Nếu upload lỗi, dừng ngay batch này để kiểm tra (tránh spam, lỗi cookies, etc.)
                print(f"LỖI: Upload thất bại cho chương {chapter_index}. Dừng batch.")
                break
    except Exception as e:
        print(f"\n--- LỖI NGHIÊM TRỌNG ---")
        print(f"Đã xảy ra lỗi trong quá trình dịch hoặc xử lý: {e}")
        print("Đã dừng batch. Tiến độ CHƯA được cập nhật cho chương này.")
        print("Vui lòng kiểm tra lỗi (ví dụ: API key Gemini, mạng) và chạy lại tool.")
    finally:
        # Thông báo này sẽ LUÔN LUÔN chạy, dù lỗi hay thành công
        print(f"\n--- KẾT THÚC BATCH CHO TRUYỆN {book_id} ---")

    print(f"\n--- HOÀN TẤT BATCH CHO TRUYỆN {book_id} ---")

if __name__ == "__main__":
    BOOK_MAIN_URL = 'https://uukanshu.cc/book/25398/'

    # Đường dẫn này VẪN CẦN THIẾT để lưu file progress.json
    BASE_OUTPUT_DIRECTORY = "/home/thepham/Desktop/disk/convert/progress"

    # Lấy ID truyện từ config (đã đọc từ .env)
    TTV_STORY_ID_TO_UPLOAD = config.TTV_STORY_ID

    CHAPTER_LIMIT = 1  # Đặt là None để dịch/upload tất cả chương mới

    if not TTV_STORY_ID_TO_UPLOAD:
        print("LỖI: TTV_STORY_ID chưa được Set trong file .env. Vui lòng kiểm tra lại.")
    else:
        run_full_translation_process(
            BOOK_MAIN_URL,
            BASE_OUTPUT_DIRECTORY,
            TTV_STORY_ID_TO_UPLOAD,
            chapter_limit=CHAPTER_LIMIT
        )