import sys
import os  # Dùng để tạo thư mục và ghép đường dẫn file
from src.dictionary_manager import DictionaryManager
from src.translator import Translator
from src.scraper import Scraper  # <-- Import lớp Scraper mới


def initialize_services():
    """
    Khởi tạo tất cả các dịch vụ cần thiết (Từ điển, Translator, Scraper).
    Trả về (translator, scraper) hoặc (None, None) nếu lỗi.
    """
    print("--- Bắt đầu khởi tạo Tool Convert Hybrid ---")
    try:
        # 1. Khởi tạo Dictionary Manager (Chỉ 1 lần)
        dict_manager = DictionaryManager()
        # 2. Khởi tạo Translator (Chỉ 1 lần)
        translator = Translator(dictionary_manager=dict_manager)
        # 3. Khởi tạo Scraper (Chỉ 1 lần)
        scraper = Scraper()

        return translator, scraper
    except Exception as e:
        print(f"Lỗi nghiêm trọng khi khởi tạo dịch vụ: {e}")
        return None, None


def run_full_translation_process(book_url: str, output_dir: str):
    """
    Hàm chính điều phối toàn bộ quá trình:
    1. Cào (Scrape) danh sách chương.
    2. Dịch (Translate) từng chương.
    3. Lưu (Save) từng chương.
    """
    translator, scraper = initialize_services()
    if not translator or not scraper:
        print("Không thể khởi động. Thoát.")
        return

    # Đảm bảo thư mục output tồn tại
    os.makedirs(output_dir, exist_ok=True)
    print(f"--- Tool đã sẵn sàng! ---")
    print(f"Sẽ lưu các chương đã dịch vào: {output_dir}")

    # 1. Lấy danh sách chương
    chapter_list = scraper.get_chapter_links(book_url)

    if not chapter_list:
        print("Không có chương nào để dịch. Thoát.")
        return

    # 2. Lặp qua, cào, dịch và lưu
    total_chapters = len(chapter_list)
    for i, chapter_info in enumerate(chapter_list, 1):
        title = chapter_info['title']
        url = chapter_info['url']

        print(f"\n--- Bắt đầu chương {i}/{total_chapters}: {title} ---")

        # 3. Cào nội dung
        # Đây là phần thay thế cho logic đọc file của bạn
        print(f"Đang cào nội dung từ: {url}")
        chinese_text = scraper.get_chapter_content(url)

        if not chinese_text or not chinese_text.strip():
            print(f"Bỏ qua chương này do không cào được nội dung hoặc nội dung rỗng.")
            continue

        # 4. Thực hiện dịch
        # Bây giờ chúng ta truyền thẳng biến `chinese_text` vào
        print("Đã có nội dung. Bắt đầu dịch...")
        vietnamese_text = translator.translate_chapter(chinese_text)
        print("Dịch xong.")

        # 5. Ghi ra file output
        # Tạo tên file an toàn (loại bỏ ký tự đặc biệt)
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_')).rstrip()
        output_filename = f"{i:04d} - {safe_title}.txt"
        output_path = os.path.join(output_dir, output_filename)

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(vietnamese_text)
            print(f"Đã lưu thành công vào: {output_path}")
        except Exception as e:
            print(f"Lỗi khi ghi file output {output_path}: {e}")

    print("\n--- HOÀN TẤT TOÀN BỘ QUÁ TRÌNH ---")


if __name__ == "__main__":
    BOOK_MAIN_URL = 'https://uukanshu.cc/book/421/'
    OUTPUT_DIRECTORY = "output_truyen_dich"  # Tên thư mục lưu bản dịch

    run_full_translation_process(BOOK_MAIN_URL, OUTPUT_DIRECTORY)