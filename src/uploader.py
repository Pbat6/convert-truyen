import requests
import src.config as config


class TangThuvienClient:
    """
    Client để tương tác và upload chương lên Tang Thư Viện.
    """

    def __init__(self):
        """
        Khởi tạo session và thiết lập các giá trị mặc định.
        """
        if not config.TTV_API_URL or not config.TTV_TOKEN or not config.TTV_COOKIES:
            raise ValueError("Cấu hình TTV (API, Token, Cookies) bị thiếu. Vui lòng kiểm tra file .env")

        self.api_url = config.TTV_API_URL
        self.token = config.TTV_TOKEN

        # Khởi tạo một session để giữ cookies và headers
        self.session = requests.Session()

        # Cập nhật cookies và headers từ config
        self.session.cookies.update(config.TTV_COOKIES)
        self.session.headers.update({
            "Origin": "https://tangthuvien.net",
            "Referer": f"https://tangthuvien.net/dang-chuong/story/{config.TTV_STORY_ID}",  # Referer động
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        })

    def upload_chapter(self, story_id: str, chapter_number: int, title: str, content: str) -> bool:
        """
        Upload một chương mới lên Tang Thư Viện.

        Args:
            story_id (str): ID của truyện.
            chapter_number (int): Số thứ tự của chương.
            title (str): Tiêu đề chương (đã dịch).
            content (str): Nội dung chương (đã dịch).

        Returns:
            bool: True nếu thành công, False nếu thất bại.
        """

        # Xây dựng payload (data)
        data = {
            "_token": self.token,
            "story_id": story_id,
            "chap_stt[1]": str(chapter_number),
            "chap_number[1]": str(chapter_number),
            "vol[1]": "1",  # quyển
            "vol_name[1]": "", # tên quyển
            "chap_name[1]": title,
            "introduce[1]": content,
            "adv[1]": ""
        }

        print(f"Đang tiến hành upload chương {chapter_number}: {title}...")

        try:
            response = self.session.post(self.api_url, data=data)

            # Kiểm tra lỗi HTTP (ví dụ: 403 Forbidden, 500 Server Error)
            response.raise_for_status()

            # (Tùy chọn) Bạn có thể kiểm tra thêm nội dung response.text
            # để chắc chắn TTV trả về "thành công" chứ không phải trang lỗi
            # Ví dụ: if "lỗi" in response.text.lower():
            #    print("Lỗi từ phía TTV: " + response.text[:200])
            #    return False

            return True

        except requests.exceptions.HTTPError as http_err:
            print(f"Lỗi HTTP khi upload: {http_err}")
            print(f"Response Body: {http_err.response.text[:500]}...")  # In 500 ký tự đầu của lỗi
        except requests.exceptions.RequestException as e:
            print(f"Lỗi nghiêm trọng khi gọi API upload: {e}")

        return False