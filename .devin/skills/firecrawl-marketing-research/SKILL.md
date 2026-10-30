---
name: firecrawl-marketing-research
description: Research marketing bằng Firecrawl, gồm scrape, crawl, map, search và trích xuất dữ liệu có cấu trúc từ web để phân tích đối thủ (bảng giá, gói, tính năng, messaging, CTA), theo dõi đối thủ thay đổi, content/SEO (content gap, top bài theo từ khóa, cấu trúc site), insight khách hàng từ review và diễn đàn, xu hướng thị trường và tin tức, danh sách công ty/lead B2B, KOL, agency. Xuất báo cáo Markdown tiếng Việt kèm CSV. Dùng skill này bất cứ khi nào người dùng muốn nghiên cứu đối thủ, so sánh giá, phân tích website, tìm content gap, tổng hợp review, nghiên cứu thị trường, tìm lead, hoặc nhắc tới Firecrawl, scrape hay crawl dữ liệu web cho marketing, kể cả khi họ không nói chữ "Firecrawl". Also triggers on English requests like "competitor analysis", "pricing comparison", "scrape competitor sites", "market research", "content gap", "voice of customer".
---

# Firecrawl Marketing Research

Skill này dùng Firecrawl API để lấy dữ liệu web sạch (markdown/JSON), sau đó bạn tự phân tích và viết báo cáo marketing bằng tiếng Việt. Mọi lệnh gọi API đều đi qua script `scripts/firecrawl.py` (Python 3, chỉ dùng thư viện chuẩn, không cần cài gì).

Trong tài liệu này, `FC` = `python3 <skill-dir>/scripts/firecrawl.py`, với `<skill-dir>` là thư mục chứa file SKILL.md này. Chạy lệnh từ thư mục gốc của workspace để kết quả lưu vào `./research/`.

## Bước 0: API key (luôn làm trước tiên)

Mọi lệnh đều cần Firecrawl API key, nên hãy kiểm tra key trước khi làm bất cứ việc gì khác:

```bash
FC check-key
```

- In ra `KEY_OK ...`: key đã sẵn sàng. Báo ngắn số credit còn lại rồi làm tiếp.
- Exit code 2 với `NO_API_KEY` hoặc `INVALID_API_KEY`: **dừng lại và hỏi người dùng API key**. Đừng tự đoán, đừng tìm key ở chỗ khác trên máy. Hướng dẫn người dùng:
  1. Lấy key tại https://www.firecrawl.dev/app/api-keys (đăng ký miễn phí có sẵn credit dùng thử). Key có dạng `fc-...`.
  2. Cách an toàn nhất là người dùng tự chạy lệnh này trong terminal của họ. Lệnh sẽ hỏi key ở chế độ ẩn, nên key không xuất hiện trong cuộc trò chuyện:
     ```bash
     python3 <skill-dir>/scripts/firecrawl.py set-key
     ```
  3. Nếu người dùng dán key thẳng vào chat, lưu giúp họ bằng:
     ```bash
     FC set-key --key fc-xxxxxxxx
     ```

`set-key` ghi `FIRECRAWL_API_KEY` vào file `.env` ở thư mục gốc workspace (thư mục cha của `.devin/`), đặt quyền 600, thêm `.env` vào `.gitignore`, rồi tự kiểm tra key. Script tìm key theo thứ tự: biến môi trường → `./.env` → `.env` ở gốc workspace → `.env` trong thư mục skill.

Không bao giờ in lại toàn bộ key trong câu trả lời, không ghi key vào báo cáo hay file nào khác ngoài `.env`, và không commit `.env`.

## Bước 1: Làm rõ yêu cầu (ngắn gọn)

Nếu yêu cầu đã đủ rõ thì làm luôn. Nếu thiếu thông tin quan trọng, hỏi gộp một lần các ý cần thiết:
- Đối tượng research: tên/website đối thủ, từ khóa, sản phẩm, ngành.
- Thị trường: Việt Nam hay quốc tế (ảnh hưởng `--country VN`, `--location`, ngôn ngữ từ khóa).
- Mục đích: định giá, viết content, chạy quảng cáo, tìm lead... Mục đích quyết định phần "Đề xuất hành động" của báo cáo.

## Bước 2: Chọn playbook và thu thập dữ liệu

Đọc `references/playbooks.md` để lấy quy trình chi tiết cho từng loại research:

| Người dùng muốn | Playbook |
|---|---|
| So sánh giá, gói, tính năng, messaging của đối thủ | 1. Nghiên cứu đối thủ |
| Theo dõi đối thủ đổi giá / ra sản phẩm mới | 2. Theo dõi thay đổi |
| Content gap, top bài theo từ khóa, cấu trúc site | 3. Content & SEO |
| Pain point, review, voice of customer, persona | 4. Insight khách hàng |
| Tin tức, xu hướng, số liệu thị trường | 5. Thị trường & xu hướng |
| Danh sách công ty, lead B2B, KOL, agency | 6. Lead / đối tác |

### Các lệnh của script

| Lệnh | Dùng khi | Ví dụ |
|---|---|---|
| `search` | Tìm nguồn theo từ khóa/tin tức, có thể scrape luôn | `FC search "phần mềm CRM" --country VN --limit 10 --scrape` |
| `map` | Liệt kê URL của site, tìm trang pricing/blog | `FC map https://a.com --search pricing` |
| `scrape` | Lấy 1 trang (markdown, summary, JSON) | `FC scrape https://a.com --formats markdown,summary` |
| `extract` | Trích xuất dữ liệu có cấu trúc từ nhiều URL ra CSV | `FC extract URL1 URL2 --schema pricing --rows-key plans` |
| `crawl` | Lấy nhiều trang của một site (mặc định 20 trang) | `FC crawl https://a.com/blog --limit 30 --include "blog/.*"` |

Chạy `FC <lệnh> -h` để xem đầy đủ tùy chọn. Một số tùy chọn hay dùng:
- `--schema`: tên schema có sẵn trong `assets/schemas/` (`pricing`, `positioning`, `company`, `reviews`, `article`), đường dẫn file JSON schema, hoặc chuỗi JSON. Nếu không có schema phù hợp, dùng `--prompt "..."` để mô tả dữ liệu cần lấy, hoặc tự viết schema mới cho trường hợp đó.
- `--rows-key`: tách một mảng (vd `plans`, `reviews`) thành nhiều dòng CSV, mỗi dòng kèm `source_url`.
- `--country VN --lang vi-VN`: xem trang như người dùng ở Việt Nam (giá theo VND, nội dung bản địa).
- `--tbs qdr:w|qdr:m|qdr:y`: giới hạn search theo thời gian. `--sources news` để lấy tin tức.
- `--out-dir`: tự đặt thư mục kết quả. Mặc định là `./research/<thời-gian>-<lệnh>-<slug>/`.

### Cách làm việc với kết quả

- Script lưu dữ liệu đầy đủ vào file (`.md`, `.json`, `.csv`) và chỉ in bản tóm tắt ra màn hình. Cách này giữ context gọn: chỉ mở file markdown khi thực sự cần đọc chi tiết, và với file dài thì đọc theo đoạn.
- Ưu tiên `extract` với schema khi cần so sánh nhiều đối tượng, vì dữ liệu cùng cấu trúc sẽ dễ lập bảng. Dùng `scrape`/`crawl` lấy markdown khi cần đọc hiểu nội dung tự do (bài blog, thread diễn đàn).
- Có URL lỗi thì thử lại một lần với `--wait 3000` (trang nặng JS) hoặc `--full-page`. Nếu vẫn lỗi, ghi vào phần hạn chế của báo cáo rồi đi tiếp, đừng dừng cả quá trình.
- Mỗi trang scrape đều tốn credit, trích xuất JSON còn tốn hơn. Trước khi crawl hơn khoảng 50 trang hoặc extract hơn khoảng 30 URL, nói cho người dùng biết quy mô và hỏi xác nhận. Ưu tiên `map --search` để nhắm đúng trang thay vì crawl cả site.

## Bước 3: Viết báo cáo

Lưu báo cáo vào `research/<slug-chủ-đề>-<YYYY-MM-DD>/report.md`, để cạnh các file CSV đã tạo (copy hoặc ghi rõ đường dẫn). Trong chat, gửi bản tóm tắt ngắn và đường dẫn file.

Viết bằng tiếng Việt, theo cấu trúc sau. Các mục có thể điều chỉnh theo playbook (playbook ghi rõ phần riêng cần thêm):

```markdown
# [Tên research]
_Ngày thực hiện: YYYY-MM-DD · Phạm vi: ... · Nguồn: N trang_

## Tóm tắt nhanh
3–5 gạch đầu dòng: phát hiện quan trọng nhất, mỗi ý một câu, có số liệu nếu có.

## Phát hiện chính
Các mục theo playbook, mỗi nhận định kèm bằng chứng (số liệu, trích dẫn) và link nguồn.
Dùng bảng Markdown khi so sánh từ 2 đối tượng trở lên.

## Cơ hội & đề xuất hành động
Việc cụ thể người dùng có thể làm (định giá, thông điệp, chủ đề content, góc quảng cáo...),
sắp theo mức độ ưu tiên.

## Dữ liệu đính kèm
- `extract.csv`: mô tả ngắn
- ...

## Nguồn & hạn chế
Danh sách URL đã dùng. Trang nào lỗi hoặc bị chặn, dữ liệu nào có thể đã cũ hoặc không đầy đủ.
```

Nguyên tắc viết:
- Mỗi số liệu (giá, thị phần, rating) phải có nguồn từ dữ liệu đã scrape. Không có dữ liệu thì ghi "không tìm thấy", đừng điền từ trí nhớ. Người dùng sẽ ra quyết định kinh doanh dựa trên báo cáo, nên một con số bịa ra còn hại hơn một ô trống.
- Phân biệt rõ dữ kiện (trang web ghi gì) với nhận định của bạn (điều đó có nghĩa là gì).
- Giữ nguyên giá và đơn vị như trang web hiển thị. Nếu quy đổi tiền tệ, ghi rõ tỷ giá dùng để quy đổi.
- Trích dẫn nguyên văn của khách hàng thì giữ đúng ngôn ngữ gốc. Có thể thêm bản dịch nếu cần.

## Giới hạn và đạo đức

- Chỉ lấy dữ liệu công khai. Không scrape trang cần đăng nhập, không cố vượt paywall hay CAPTCHA, và tôn trọng robots.txt (Firecrawl mặc định đã tuân theo robots.txt).
- Không thu thập dữ liệu cá nhân như tên, email, số điện thoại của cá nhân hay người review. Với lead B2B, chỉ lấy thông tin doanh nghiệp công khai.
- Facebook, LinkedIn, Instagram, TikTok chặn scrape rất chặt. Nếu người dùng cần dữ liệu từ đó, nói rõ giới hạn và gợi ý nguồn thay thế (website chính thức, báo chí, trang review).
