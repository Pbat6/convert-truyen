import requests

url = "https://tangthuvien.net:443/post-chuong"

cookies = {
    "remember_web_59ba36addc2b2f9401580f014c7f58ea4e30989d": "eyJpdiI6ImNvVWh6c2FEdlRTdjBvVHpDTzBmalE9PSIsInZhbHVlIjoiaW50eVZ2QjJUSWhuWVRGSDc5TUhsRStMbk0xcG5CM2ZjZHVFeHd4UzUzSmVqUjBVdU16SlJmZGlTYVhwcllMS3ZFNXZCQ1cwMmJ4MFR6d2g5S2FIWFJPMlFvNGFrWXB6N0xMXC9sRGRtMnhZPSIsIm1hYyI6Ijg3NjQ2NjdkNzUzZGRiMDZmZDM4MzQ2MDA1ZGI4ZjQxNjY3ZWQ5ODM4NWY1NmFhZDdmOTFmZGQ2NjU2ZGQwN2EifQ%3D%3D",
    "_gid": "GA1.2.385369368.1761763779",
    "XSRF-TOKEN": "eyJpdiI6IjdBUUp1R3NYNUhLam5BelNnWEwyNHc9PSIsInZhbHVlIjoiVjFYRURHanJTaFVuWkorWjBBQmtvaDkrbFZuMkJ1TWFaK3pXUGZpWEJPM0VndUcxd200TlwvaUx3Nlo4bW5LMkN0QUJoSk1RamdEUm9mMmRzQ1ZjU0N3PT0iLCJtYWMiOiIxYjcxYzA4ZDNiZmMxODVmNjNhMTQ1MTgwYjM5ODVkNDc0OWZhOTc2NDAxNjI4NGVjZTljMzk3NTkzNmFkY2FmIn0%3D",
    "laravel_session": "eyJpdiI6IlwvdDY1Q3IxTHNpUE1rblR6cXNhYmx3PT0iLCJ2YWx1ZSI6InJSanBGcVwvUDlOV05XVjZ1NUhlNFJBVXBJdW4yZmh0QmxLMlFuU1ZtWXpudmhSV05OMG1UTU9qblB4UkQ4NjJORzlQRGRscHpzNE00OHdEaWxcL3YyNHc9PSIsIm1hYyI6IjJkMjUzZDg1YjI5MzFmYWY3YTI2MjlkYTg4NTk0ODY2YTVmMTk5M2NiMWQ4NTMwZjQyNzk3MjdhMzZmYzI2MTkifQ%3D%3D",
    "_ga_13FFK38L2F": "GS2.1.s1761839476$o6$g1$t1761839999$j15$l0$h0",
    "_ga": "GA1.2.1197411439.1761763679"
}

headers = {
    "Origin": "https://tangthuvien.net",
    "Referer": "https://tangthuvien.net/dang-chuong/story/39072",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
}
data = {
"_token": "h0fR2dFqipGVHdPp78R8AKYhiTow0LYwyvowNRCA",
    "story_id": "39072",
    "chap_stt[1]": "3",
    "chap_number[1]": "3",
    "vol[1]": "1",
    "vol_name[1]": "",
    "chap_name[1]": "Tấm tất đen của Lục sư tỷ",
    "introduce[1]": "\"Cót két ——\" một tiếng, cửa căn nhà cũ bị đẩy ra.\n\n"
                    "Ngoài cửa, một nữ tử tuyệt mỹ, cùng Vân Phong bốn mắt nhìn nhau.\n",
    "adv[1]": ""
}
requests.post(url, headers=headers, cookies=cookies, data=data)