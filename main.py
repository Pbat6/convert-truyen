# main.py
import sys
import os
import re
import argparse
import json  # Thêm import json

# Import các dịch vụ
from src.dictionary_manager import DictionaryManager
from src.translator import Translator
from src.scraper import Scraper
from src.progress_manager import ProgressManager
from src.uploader import TangThuvienClient

def run_full_translation_process(
        dict_manager: DictionaryManager,
        scraper: Scraper,
        uploader: TangThuvienClient,
        book_url: str,
        base_output_dir: str,
        ttv_story_id: str,
        chapter_limit: int | None,
        google_api_key: str
):
    """
    Hàm chính điều phối toàn bộ quá trình.
    (Giữ nguyên logic của hàm này, không thay đổi)
    """

    try:
        translator = Translator(dictionary_manager=dict_manager, api_key=google_api_key)
    except Exception as e:
        print(f"Lỗi khi khởi tạo Translator (kiểm tra API key?): {e}")
        return

    book_id = "book_" + ttv_story_id
    book_output_dir = os.path.join(base_output_dir, book_id)
    os.makedirs(book_output_dir, exist_ok=True)

    progress_file_path = os.path.join(book_output_dir, 'progress.json')
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
    # (Giữ nguyên logic)
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
    # (Giữ nguyên logic)
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
    # (Giữ nguyên toàn bộ logic vòng lặp, try/except/finally)
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
            # (Giữ nguyên logic)
            translated_title = title
            vietnamese_text = full_translated_output
            try:
                parts = full_translated_output.split('\n\n', 1)
                raw_translated_title = parts[0].strip()
                pattern_to_remove = r'^(Chương|C|Q|Quyển)\s*\d+\s*[:\-–—\s]*\s*'
                cleaned_title = re.sub(pattern_to_remove, '', raw_translated_title, flags=re.IGNORECASE).strip()

                if not cleaned_title:
                    translated_title = "Vô Đề"
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
            # (Giữ nguyên logic)
            try:
                chapter_index = all_chapters.index(chapter_info) + 1
            except ValueError:
                print(f"LỖI: Không tìm thấy chapter_info trong all_chapters. Bỏ qua.")
                continue

            # Thực hiện upload
            success = uploader.upload_chapter(
                story_id=ttv_story_id,
                chapter_number=chapter_index,
                title=translated_title,
                content=vietnamese_text
            )

            # 10. Cập nhật "bookmark"
            if success:
                print(f"Đã upload thành công chương {chapter_index} lên TTV.")
                progress_manager.update_progress(book_id, chapter_info, book_url)
                print(f"Đã cập nhật tiến độ: Đã xong chương '{title}'")
            else:
                print(f"LỖI: Upload thất bại cho chương {chapter_index}. Dừng batch.")
                break
    except Exception as e:
        print(f"\n--- LỖI NGHIÊM TRỌNG ---")
        print(f"Đã xảy ra lỗi trong quá trình dịch hoặc xử lý: {e}")
        print("Đã dừng batch. Tiến độ CHƯA được cập nhật cho chương này.")
    finally:
        print(f"\n--- KẾT THÚC BATCH CHO TRUYỆN {book_id} ---")

    print(f"\n--- HOÀN TẤT BATCH CHO TRUYỆN {book_id} ---")


# === THAY ĐỔI MỚI: Thêm khối main để chạy độc lập ===
def get_book_config_by_id(story_id: str):
    """
    Đọc file books_to_run.json và tìm config cho story_id cụ thể.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    config_file_path = os.path.join(base_dir, 'books_to_run.json')
    try:
        with open(config_file_path, 'r', encoding='utf-8') as f:
            books = json.load(f)

        for book_config in books:
            if book_config.get('ttv_story_id') == story_id:
                return book_config, base_dir

        return None, base_dir
    except Exception as e:
        print(f"Lỗi khi đọc file config: {e}")
        return None, base_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chạy quy trình dịch cho một truyện cụ thể.")
    parser.add_argument("story_id", type=str, help="ttv_story_id của truyện cần chạy (lấy từ books_to_run.json)")
    args = parser.parse_args()

    print(f"[MAIN] Bắt đầu chạy cho story_id: {args.story_id}")

    # 1. Tải config cho truyện này
    book_config, base_dir = get_book_config_by_id(args.story_id)
    if not book_config:
        print(f"LỖI: Không tìm thấy config cho ttv_story_id '{args.story_id}' trong 'books_to_run.json'")
        sys.exit(1)

    # 2. Khởi tạo các dịch vụ stateless (giống logic trong run_all.py)
    # Vì mỗi process là độc lập, chúng cần tự khởi tạo.
    print(f"[MAIN] Đang khởi tạo dịch vụ (Tải từ điển...)...")
    try:
        g_dict_manager = DictionaryManager()
        g_scraper = Scraper()
        g_uploader = TangThuvienClient()
        print(f"[MAIN] Dịch vụ đã sẵn sàng.")
    except Exception as e:
        print(f"LỖI NGHIÊM TRỌNG khi khởi tạo dịch vụ: {e}")
        sys.exit(1)

    base_output_directory = os.path.join(base_dir, "progress")

    # 3. Gọi hàm xử lý chính
    try:
        run_full_translation_process(
            # Dịch vụ stateless
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
    except KeyError as e:
        print(f"LỖI: Cấu hình cho {args.story_id} thiếu key bắt buộc: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"LỖI NGHIÊM TRỌNG không xác định: {e}")
        sys.exit(1)