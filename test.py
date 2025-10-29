import cloudscraper
from bs4 import BeautifulSoup

# 1. Vẫn là cloudscraper để "qua ải" Cloudflare
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',  # Giả mạo y hệt Chrome
        'platform': 'windows',
        'desktop': True
    }
)
main_page_url = 'https://uukanshu.cc/book/421/'

try:
    # Thêm header giả mạo cho chắc ăn
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    main_page_html = scraper.get(main_page_url, headers=headers).text

except Exception as e:
    print(f"Bị Cloudflare chặn rồi (hoặc lỗi mạng): {e}")
    exit()

# 2. Tạo 'soup' từ HTML bạn vừa lấy được
soup = BeautifulSoup(main_page_html, 'html.parser')

chapter_links = soup.select("div#list-chapterAll dd a")

if not chapter_links:
    print("Không tìm thấy link chương nào! Cấu trúc HTML có thể đã thay đổi.")
    print("----- DEBUG HTML -----")
    print(main_page_html)  # In ra HTML để xem nó có phải trang lỗi không
    print("----------------------")
    exit()

# 4. Lặp qua các link đã tìm thấy và in ra
all_chapter_data = []
for link in chapter_links:
    chapter_title = link.text  # Lấy tiêu đề: "第一章 體液掃碼"
    chapter_path = link.get('href')  # Lấy link: "/book/419/265517.html"

    # Một số link quảng cáo vớ vẩn có thể không có href
    if not chapter_path:
        continue

    # Ghép lại thành URL đầy đủ
    full_chapter_url = 'https://uukanshu.cc' + chapter_path

    # print(f"Đã tìm thấy: {chapter_title}  ->  {full_chapter_url}")
    all_chapter_data.append({
        'title': chapter_title,
        'url': full_chapter_url
    })

# print(f"\nTổng cộng tìm thấy: {len(all_chapter_data)} chương.")

# 5. Giờ bạn có thể bắt đầu cào nội dung từng chương
# (Chỉ cào 3 chương đầu làm ví dụ)
# (Code lấy all_chapter_data ở trên giữ nguyên...)

for chapter in all_chapter_data:
    try:
        # 1. Dùng lại scraper để cào HTML của trang chương
        chapter_content_html = scraper.get(chapter['url'], headers=headers).text

        # 2. Tạo một "soup" mới CHỈ cho trang chương này
        chapter_soup = BeautifulSoup(chapter_content_html, 'html.parser')

        # 3. Dùng selector "chí mạng" bạn vừa tìm thấy
        #    (Dùng select_one vì ta biết chỉ có 1 cái div này)
        content_div = chapter_soup.select_one("div.readcotent.bbb.font-normal")

        if content_div:
            #    - separator="\n" để giữ lại các lần xuống dòng (giữa các thẻ <p>)
            #    - strip=True để dọn dẹp khoảng trắng thừa ở đầu/cuối
            story_text = content_div.get_text(separator="\n", strip=True)

            # 5. Dọn dẹp quảng cáo (nếu có)
            #    Trang này hay chèn text quảng cáo vào, ta lọc nó ra
            cleaned_lines = []
            for line in story_text.split('\n'):
                # Lọc bỏ các dòng quảng cáo đặc trưng
                if "uukanshu.cc" in line or "uu看書" in line or "UU看书" in line:
                    continue
                # Lọc bỏ các dòng trống
                if line.strip():
                    cleaned_lines.append(line)

            final_text = "\n".join(cleaned_lines)

            print(f"   [Cào thành công! Trích đoạn 300 ký tự đầu:]")
            print(f"   {final_text[:300]}...")
        else:
            print(
                f"   [LỖI] Không tìm thấy 'div.readcotent' trong chương này. Trang có thể bị lỗi hoặc cấu trúc đã đổi.")
    except Exception as e:
        print(f"   [LỖI NGHIÊM TRỌNG] Lỗi khi cào chương {chapter['title']}: {e}")