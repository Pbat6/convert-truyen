import cloudscraper
from bs4 import BeautifulSoup


class Scraper:

    def __init__(self):
        """Khởi tạo scraper và headers một lần duy nhất."""
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
        }
        print("Module Scraper đã sẵn sàng.")

    def get_chapter_links(self, main_page_url: str) -> list[dict]:
        """
        Lấy danh sách link và tiêu đề các chương từ trang chính.
        Trả về list của các dictionary, ví dụ: [{'title': '...', 'url': '...'}]
        """
        print(f"Đang lấy danh sách chương từ: {main_page_url}")
        try:
            main_page_html = self.scraper.get(main_page_url, headers=self.headers).text
        except Exception as e:
            print(f"Lỗi khi lấy trang chính (Cloudflare/Mạng): {e}")
            return []  # Trả về list rỗng nếu lỗi

        soup = BeautifulSoup(main_page_html, 'html.parser')
        chapter_links = soup.select("div#list-chapterAll dd a")

        if not chapter_links:
            print("Không tìm thấy link chương nào! Cấu trúc HTML có thể đã thay đổi.")
            return []

        all_chapter_data = []
        for link in chapter_links:
            chapter_title = link.text
            chapter_path = link.get('href')

            if not chapter_path:
                continue  # Bỏ qua các link quảng cáo không có href

            full_chapter_url = 'https://uukanshu.cc' + chapter_path
            all_chapter_data.append({
                'title': chapter_title,
                'url': full_chapter_url
            })

        print(f"Tìm thấy tổng cộng: {len(all_chapter_data)} chương.")
        return all_chapter_data

    def get_chapter_content(self, chapter_url: str) -> str | None:
        """
        Cào, trích xuất và dọn dẹp nội dung của MỘT chương.
        Trả về nội dung chương (str) hoặc None nếu lỗi.
        """
        try:
            # 1. Dùng lại scraper để cào HTML của trang chương
            chapter_content_html = self.scraper.get(chapter_url, headers=self.headers).text

            # 2. Tạo "soup" mới cho trang chương
            chapter_soup = BeautifulSoup(chapter_content_html, 'html.parser')

            # 3. Dùng selector
            content_div = chapter_soup.select_one("div.readcotent.bbb.font-normal")

            if content_div:
                # 4. Lấy text và dọn dẹp
                story_text = content_div.get_text(separator="\n", strip=True)

                cleaned_lines = []
                for line in story_text.split('\n'):
                    # Lọc bỏ các dòng quảng cáo đặc trưng
                    if "uukanshu.cc" in line or "uu看書" in line or "UU看书" in line:
                        continue
                    # Lọc bỏ các dòng trống
                    if line.strip():
                        cleaned_lines.append(line)

                final_text = "\n".join(cleaned_lines)
                return final_text  # Trả về text đã dọn dẹp
            else:
                print(f"   [LỖI] Không tìm thấy 'div.readcotent' tại: {chapter_url}")
                return None
        except Exception as e:
            print(f"   [LỖI NGHIÊM TRỌNG] Lỗi khi cào chương {chapter_url}: {e}")
            return None