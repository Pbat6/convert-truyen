import sys
from src.dictionary_manager import DictionaryManager
from src.translator import Translator


def run_translation(input_path: str, output_path: str):
    """
    Hàm chính điều phối toàn bộ quá trình.
    """
    print("--- Bắt đầu khởi tạo Tool Convert Hybrid ---")

    # 1. Khởi tạo Dictionary Manager (Chỉ 1 lần)
    try:
        dict_manager = DictionaryManager()
    except Exception as e:
        print(f"Lỗi nghiêm trọng khi tải từ điển: {e}")
        return

    # 2. Khởi tạo Translator (Chỉ 1 lần)
    try:
        translator = Translator(dictionary_manager=dict_manager)
    except ValueError as e:
        print(e)  # Lỗi thiếu API key
        return

    print("--- Tool đã sẵn sàng! ---")

    # 3. Đọc file input (chương truyện cần dịch)
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            chinese_text = f.read()
        if not chinese_text:
            print(f"Lỗi: File input '{input_path}' bị rỗng.")
            return
        print(f"Đã đọc xong file: {input_path}")
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file input '{input_path}'.")
        return
    except Exception as e:
        print(f"Lỗi khi đọc file input: {e}")
        return

    # 4. Thực hiện dịch
    vietnamese_text = translator.translate_chapter(chinese_text)

    # 5. Ghi ra file output
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(vietnamese_text)
        print("\n--- DỊCH THÀNH CÔNG! ---")
        print(f"Bản dịch đã được lưu vào: {output_path}")
    except Exception as e:
        print(f"Lỗi khi ghi file output: {e}")


if __name__ == "__main__":
    # Đây là cách chạy tool từ command line
    # Ví dụ: python main.py input.txt output.txt

    if len(sys.argv) != 3:
        print("Cách sử dụng: python main.py <ten_file_input> <ten_file_output>")
        # Chạy ví dụ nếu không có tham số
        print("Đang chạy ví dụ mặc định: input_demo.txt -> output_demo.txt")
        # Tạo file demo
        demo_text = "七叶真人冷哼一声，说道：“你这个小小的弟子，竟敢如此无礼！”"
        with open("input_demo.txt", "w", encoding="utf-8") as f:
            f.write(demo_text)

        run_translation("input_demo.txt", "output_demo.txt")
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
        run_translation(input_file, output_file)