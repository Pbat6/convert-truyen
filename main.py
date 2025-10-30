# main.py

import sys
import os
import re
from src.dictionary_manager import DictionaryManager
from src.translator import Translator
from src.scraper import Scraper
from src.progress_manager import ProgressManager


def initialize_services():
    """
    Khởi tạo tất cả các dịch vụ cần thiết (Từ điển, Translator, Scraper, Progress).
    """
    print("--- Bắt đầu khởi tạo Tool Convert Hybrid ---")
    try:
        dict_manager = DictionaryManager()
        translator = Translator(dictionary_manager=dict_manager)
        scraper = Scraper()
        progress_manager = ProgressManager()

        return translator, scraper, progress_manager
    except Exception as e:
        print(f"Lỗi nghiêm trọng khi khởi tạo dịch vụ: {e}")
        return None, None, None


def get_book_id_from_url(url: str) -> str:
    """
    Tạo một ID duy nhất cho truyện từ URL.
    Ví dụ: 'https://uukanshu.cc/book/421/' -> 'book_421'
    """
    match = re.search(r'/book/(\d+)', url)
    if match:
        return f"book_{match.group(1)}"
    return re.sub(r'[^a-zA-Z0-9]', '_', url.split('//')[-1])


def run_full_translation_process(
        book_url: str,
        base_output_dir: str,
        chapter_limit: int | None = None
):
    """
    Hàm chính điều phối toàn bộ quá trình.

    Args:
        book_url (str): URL trang mục lục của truyện.
        base_output_dir (str): Thư mục gốc để lưu tất cả truyện.
        chapter_limit (int | None): Số chương tối đa cần dịch.
                                    Nếu là None, dịch tất cả chương mới.
    """
    translator, scraper, progress_manager = initialize_services()
    if not translator or not scraper or not progress_manager:
        print("Không thể khởi động. Thoát.")
        return

    # 1. Xác định ID và thư mục output riêng cho truyện này
    book_id = get_book_id_from_url(book_url)
    book_output_dir = os.path.join(base_output_dir, book_id)
    os.makedirs(book_output_dir, exist_ok=True)

    print(f"--- Tool đã sẵn sàng! ---")
    print(f"Đang xử lý truyện: {book_id} (URL: {book_url})")
    print(f"Sẽ lưu các chương đã dịch vào: {book_output_dir}")

    # 2. Lấy danh sách *tất cả* chương
    all_chapters = scraper.get_chapter_links(book_url)
    if not all_chapters:
        print("Không có chương nào để dịch. Thoát.")
        return

    # 3. Lấy "bookmark" và lọc ra các chương cần dịch
    last_processed_url = progress_manager.get_last_processed_url(book_id)
    chapters_to_process = []

    if last_processed_url is None:
        # Đây là truyện mới, dịch tất cả
        print("Phát hiện truyện mới. Bắt đầu dịch từ chương đầu tiên.")
        chapters_to_process = all_chapters
    else:
        # Đây là truyện đã dịch, tìm chương cuối cùng
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

    # 4. (LOGIC MỚI) Áp dụng giới hạn số chương (NẾU CÓ)
    if chapter_limit is not None and chapter_limit > 0:
        total_available = len(chapters_to_process)
        if total_available == 0:
            print("Không có chương mới nào để áp dụng giới hạn.")
            return

        # Cắt danh sách chỉ lấy số lượng chương theo `chapter_limit`
        chapters_to_process = chapters_to_process[:chapter_limit]

        print(
            f"Đã áp dụng giới hạn: Chỉ xử lý {len(chapters_to_process)} chương (trong tổng số {total_available} chương mới).")
    elif chapter_limit is not None:
        print("Giới hạn chương không hợp lệ (<= 0). Sẽ không dịch chương nào.")
        return

    # 5. Lặp qua, cào, dịch và lưu (CHỈ các chương đã lọc và giới hạn)
    total_batch = len(chapters_to_process)
    if total_batch == 0:
        print("Không có chương nào trong batch này để xử lý.")
        return

    print(f"Bắt đầu dịch batch gồm {total_batch} chương...")
    for i, chapter_info in enumerate(chapters_to_process, 1):
        title = chapter_info['title']
        url = chapter_info['url']

        print(f"\n--- Bắt đầu chương {i}/{total_batch}: {title} ---")

        # 6. Cào nội dung
        print(f"Đang cào nội dung từ: {url}")
        chinese_text = scraper.get_chapter_content(url)

        if not chinese_text or not chinese_text.strip():
            print(f"Bỏ qua chương này do không cào được nội dung hoặc nội dung rỗng.")
            continue

        # 7. Thực hiện dịch
        print("Đã có nội dung. Bắt đầu dịch...")
        vietnamese_text = translator.translate_chapter(chinese_text)
        print("Dịch xong.")

        # 8. Ghi ra file output
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_')).rstrip()
        try:
            chapter_index = all_chapters.index(chapter_info) + 1
            output_filename = f"{chapter_index:04d} - {safe_title}.txt"
        except ValueError:
            output_filename = f"{safe_title}.txt"

        output_path = os.path.join(book_output_dir, output_filename)

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(vietnamese_text)
            print(f"Đã lưu thành công vào: {output_path}")

            # 9. Cập nhật "bookmark"
            progress_manager.update_progress(book_id, chapter_info, book_url)
            print(f"Đã cập nhật tiến độ: Đã xong chương '{title}'")

        except Exception as e:
            print(f"Lỗi khi ghi file output {output_path}: {e}")

    print(f"\n--- HOÀN TẤT BATCH {total_batch} CHƯƠNG CHO TRUYỆN {book_id} ---")


if __name__ == "__main__":
    # --- Khu vực cấu hình ---
    BOOK_MAIN_URL = 'https://uukanshu.cc/book/25398/'

    BASE_OUTPUT_DIRECTORY = "/home/thepham/Desktop/disk/convert/dich"

    # === THAM SỐ TÙY CHỈNH MỚI ===
    # Đặt là 10 để dịch 10 chương.
    # Đặt là 5 để dịch 5 chương.
    # Đặt là None để dịch TẤT CẢ chương mới tìm thấy.
    CHAPTER_LIMIT = 1
    # ===============================

    run_full_translation_process(
        BOOK_MAIN_URL,
        BASE_OUTPUT_DIRECTORY,
        chapter_limit=CHAPTER_LIMIT
    )