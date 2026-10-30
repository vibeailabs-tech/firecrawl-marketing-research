# Playbooks research marketing

Mỗi playbook gồm: mục tiêu, lệnh gợi ý, cách phân tích, và phần riêng cần có trong báo cáo.
Trong các lệnh dưới đây, `FC` = `python3 <skill-dir>/scripts/firecrawl.py`.

## Mục lục
1. Nghiên cứu đối thủ (giá, định vị, messaging)
2. Theo dõi thay đổi của đối thủ
3. Content & SEO (content gap, cấu trúc site)
4. Insight khách hàng (review, diễn đàn)
5. Thị trường & xu hướng (tin tức, báo cáo)
6. Danh sách công ty / lead B2B, KOL, agency

---

## 1. Nghiên cứu đối thủ

**Mục tiêu:** so sánh giá, gói, tính năng, thông điệp, CTA, social proof.

1. Nếu chỉ có tên đối thủ, tìm domain trước:
   `FC search "<tên đối thủ> official site" --limit 3`
2. Tìm trang giá và trang chính của mỗi đối thủ:
   `FC map https://doithu.com --search pricing --show 10`
   (thử thêm `--search gia`, `bang-gia`, `plans` với site tiếng Việt)
3. Trích xuất bảng giá của tất cả đối thủ vào một CSV:
   `FC extract https://a.com/pricing https://b.com/pricing --schema pricing --rows-key plans`
4. Trích xuất định vị và messaging từ trang chủ:
   `FC extract https://a.com https://b.com --schema positioning`

**Phân tích:**
- Mức giá theo phân khúc, gói rẻ nhất / phổ biến nhất, cách tính tiền (theo user, theo usage...).
- Tính năng nào ai cũng có (table stakes), tính năng nào là khác biệt.
- Hero headline nói về điều gì: giá, tốc độ, dễ dùng, AI, hay uy tín? Đối thủ nào đang chiếm thông điệp nào.
- Khoảng trống định vị mà khách hàng của người dùng có thể chiếm.

**Báo cáo thêm:** bảng so sánh giá (Markdown), bảng "thông điệp chính theo đối thủ", mục "Khoảng trống định vị".

## 2. Theo dõi thay đổi của đối thủ

**Mục tiêu:** phát hiện đổi giá, ra sản phẩm mới, đổi messaging.

- Chạy lại lệnh `extract` với cùng schema và `--out-dir research/monitor/<doi-thu>/<YYYY-MM-DD>`, rồi so sánh với lần trước (đọc 2 file `extract.json` và liệt kê khác biệt).
- Thêm `--max-age 0` để chắc chắn lấy dữ liệu mới, không lấy cache.
- Tin tức gần đây: `FC search "<tên đối thủ>" --sources news --tbs qdr:m --limit 10`
- Nếu người dùng muốn chạy tự động định kỳ, gợi ý cron/n8n/Make gọi script này; không tự cài cron khi chưa được đồng ý.

**Báo cáo thêm:** bảng "Thay đổi kể từ lần trước" (trước → sau, ngày phát hiện).

## 3. Content & SEO

**Cấu trúc nội dung của một site:**
`FC map https://doithu.com --limit 5000` → xem phân bố theo section (/blog, /docs, /use-cases...). Có thể chạy thêm `--search blog` để xem chủ đề bài viết qua slug URL.

**Content gap theo từ khóa:**
1. `FC search "<từ khóa>" --limit 10 --country VN --scrape`
   (bỏ `--country` nếu thị trường không phải VN; dùng `--location` cho thành phố cụ thể)
2. Trích xuất dàn ý của các bài top:
   `FC extract <url1> <url2> ... --schema article`
3. Đọc file markdown nếu cần chi tiết hơn (chỉ đọc phần cần thiết, file có thể dài).

**Phân tích:** độ dài trung bình, search intent chiếm ưu thế, các heading lặp lại (chủ đề bắt buộc phải có), chủ đề ít bài đề cập (cơ hội), định dạng nội dung (bảng, template, FAQ, video).

**Báo cáo thêm:** bảng top kết quả (vị trí, tiêu đề, độ dài, góc tiếp cận), "Chủ đề bắt buộc", "Content gap / cơ hội", và dàn ý đề xuất cho bài viết mới.

## 4. Insight khách hàng

**Nguồn tốt:** trang review công khai (G2, Capterra, Trustpilot, App Store/Google Play web pages), Reddit, Tinhte, Voz, các group/diễn đàn công khai, phần Q&A, bình luận trên blog.

1. Tìm nguồn: `FC search "<sản phẩm> review" --limit 10`, `FC search "<sản phẩm> site:reddit.com" --limit 10`, `FC search "<vấn đề khách hàng gặp> site:tinhte.vn"`.
2. Trích xuất review: `FC extract <url-review-1> <url-review-2> --schema reviews --rows-key reviews`
3. Với thread diễn đàn, `scrape` lấy markdown rồi tự đọc và tổng hợp.

**Phân tích:** nhóm pain point theo chủ đề và tần suất, lý do chọn / lý do rời bỏ, ngôn ngữ nguyên văn khách hay dùng (voice of customer), phân khúc khách hàng nào phàn nàn điều gì.

**Báo cáo thêm:** bảng "Pain point — tần suất — trích dẫn nguyên văn", danh sách cụm từ khách hàng dùng (dùng được cho ad copy), gợi ý góc quảng cáo / persona.

**Quyền riêng tư:** không lưu hay báo cáo tên người, email, số điện thoại của người review. Chỉ giữ nội dung và phân khúc (vai trò, quy mô công ty) nếu có.

## 5. Thị trường & xu hướng

- Tin tức: `FC search "<chủ đề>" --sources news --tbs qdr:m --limit 15`
- Báo cáo ngành dạng PDF: `FC search "<chủ đề> report 2026 filetype:pdf" --limit 10`, rồi `scrape` từng PDF (Firecrawl tự chuyển PDF sang markdown).
- Bài phân tích chuyên sâu: `FC search "<chủ đề> market size Vietnam" --scrape --limit 8`

**Phân tích:** số liệu chính (luôn kèm nguồn và năm), các xu hướng lặp lại giữa nhiều nguồn, tín hiệu mới (sự kiện, sản phẩm, quy định), tác động tới người dùng.

**Báo cáo thêm:** bảng "Số liệu chính — giá trị — nguồn — năm", "Xu hướng nổi bật", "Tín hiệu cần theo dõi".

## 6. Danh sách công ty / lead B2B, KOL, agency

1. Tìm danh sách: `FC search "top <ngành> companies in Vietnam" --limit 10 --scrape` hoặc từ trang danh bạ / bài "top 10".
2. Lấy domain các công ty từ kết quả, rồi trích xuất thông tin:
   `FC extract --urls-file research/.../domains.txt --schema company`
3. KOL/agency: tìm bằng search + site cụ thể, rồi trích xuất từ trang giới thiệu công khai của họ.

**Giới hạn:** chỉ lấy thông tin doanh nghiệp công khai (email chung như info@/sales@, trang liên hệ). Không thu thập email hay số điện thoại cá nhân, và không scrape trang cần đăng nhập. LinkedIn/Facebook chặn scrape rất chặt nên dữ liệu thường không có; nói rõ với người dùng thay vì cố lách.

**Báo cáo thêm:** CSV lead (tên, website, ngành, mô tả, sản phẩm, trang liên hệ) và nhận xét mức độ phù hợp với ICP của người dùng nếu họ đã mô tả ICP.
