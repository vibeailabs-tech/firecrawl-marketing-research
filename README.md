# Firecrawl Marketing Research Skill

Skill cho AI coding agent (Devin, Claude Code và các agent hỗ trợ chuẩn `SKILL.md`) để **research marketing bằng [Firecrawl](https://firecrawl.dev)**: lấy dữ liệu từ website đối thủ, kết quả tìm kiếm, review, tin tức... rồi tự phân tích và xuất **báo cáo Markdown tiếng Việt kèm file CSV**.

Bạn chỉ cần chat bằng ngôn ngữ tự nhiên, ví dụ:

> So sánh bảng giá của Haravan, Sapo và KiotViet

Agent sẽ tự tìm trang giá, trích xuất từng gói, lập bảng so sánh, chỉ ra khoảng trống định vị và đề xuất hành động.

---

## Mục lục

- [Tính năng](#tính-năng)
- [Yêu cầu](#yêu-cầu)
- [Cài đặt](#cài-đặt)
- [Thiết lập API key](#thiết-lập-api-key)
- [Cách dùng](#cách-dùng)
- [Dùng script trực tiếp (CLI)](#dùng-script-trực-tiếp-cli)
- [Schema có sẵn](#schema-có-sẵn)
- [Kết quả đầu ra](#kết-quả-đầu-ra)
- [Cấu trúc repo](#cấu-trúc-repo)
- [Credit và chi phí](#credit-và-chi-phí)
- [Giới hạn và đạo đức](#giới-hạn-và-đạo-đức)
- [Xử lý sự cố](#xử-lý-sự-cố)

---

## Tính năng

Skill có 6 playbook (quy trình research dựng sẵn):

| # | Playbook | Ví dụ yêu cầu |
|---|---|---|
| 1 | **Nghiên cứu đối thủ**: giá, gói, tính năng, thông điệp, CTA, social proof | "Phân tích trang chủ và bảng giá của 3 đối thủ này" |
| 2 | **Theo dõi thay đổi**: đổi giá, sản phẩm mới, đổi messaging | "Đối thủ X tháng này có thay đổi gì không?" |
| 3 | **Content & SEO**: content gap, top bài theo từ khóa, cấu trúc site | "Tìm content gap cho từ khóa 'phần mềm quản lý bán hàng'" |
| 4 | **Insight khách hàng**: pain point, voice of customer, persona | "Tổng hợp review về sản phẩm Y, khách hay phàn nàn gì?" |
| 5 | **Thị trường & xu hướng**: tin tức, số liệu, báo cáo ngành | "Tin tức ngành thương mại điện tử VN tháng này" |
| 6 | **Lead B2B / KOL / agency**: danh sách công ty kèm thông tin công khai | "Lập danh sách 20 agency marketing ở TP.HCM" |

Ngoài ra:
- **Luôn kiểm tra API key trước khi chạy.** Nếu thiếu hoặc sai key, agent dừng lại và hỏi bạn.
- Script chỉ dùng thư viện chuẩn của Python, **không cần `pip install`**.
- Trích xuất dữ liệu có cấu trúc từ nhiều URL ra **CSV** (UTF-8 BOM, mở bằng Excel không lỗi font tiếng Việt).
- Hỗ trợ xem trang theo quốc gia (`--country VN`), lọc tin theo thời gian, lọc domain.
- Tự thử lại khi bị giới hạn tốc độ (429) hoặc lỗi server tạm thời.
- Báo cáo có nguồn cho mọi số liệu. Không tìm thấy thì ghi "không tìm thấy", không bịa.

## Yêu cầu

- **Python 3.8+** (macOS và hầu hết Linux đã có sẵn `python3`).
- **Firecrawl API key**: đăng ký tại [firecrawl.dev](https://www.firecrawl.dev), lấy key ở [trang API keys](https://www.firecrawl.dev/app/api-keys). Key có dạng `fc-...`. Tài khoản miễn phí có sẵn credit dùng thử.
- Một AI agent hỗ trợ skill, ví dụ **Devin** (Desktop/CLI) hoặc **Claude Code**.

## Cài đặt

### Cách 1: Cài cho một project (khuyên dùng)

Chạy trong thư mục project của bạn:

```bash
git clone https://github.com/vibeailabs-tech/firecrawl-marketing-research.git /tmp/firecrawl-marketing-research
mkdir -p .devin/skills
cp -r /tmp/firecrawl-marketing-research/.devin/skills/firecrawl-marketing-research .devin/skills/
```

Hoặc clone cả repo này và mở nó làm workspace. Skill đã nằm sẵn ở `.devin/skills/`.

### Cách 2: Cài global (dùng ở mọi project)

```bash
# Devin
mkdir -p ~/.config/devin/skills
cp -r /tmp/firecrawl-marketing-research/.devin/skills/firecrawl-marketing-research ~/.config/devin/skills/

# Claude Code
mkdir -p ~/.claude/skills
cp -r /tmp/firecrawl-marketing-research/.devin/skills/firecrawl-marketing-research ~/.claude/skills/
```

Khi cài global, file `.env` chứa key sẽ được lưu ở thư mục bạn đang làm việc (xem [Thiết lập API key](#thiết-lập-api-key)). Bạn cũng có thể đặt biến môi trường `FIRECRAWL_API_KEY` trong `~/.zshrc` để dùng ở mọi nơi.

### Kiểm tra skill đã được nhận

Mở agent trong project và hỏi *"bạn có skill firecrawl-marketing-research không?"*. Trong Devin, skill sẽ xuất hiện trong danh sách skill khả dụng.

## Thiết lập API key

Lần đầu dùng, agent chạy `check-key` và sẽ hỏi bạn key nếu chưa có. Có 3 cách đưa key vào:

**a) Tự nhập trong terminal (an toàn nhất, key không hiện trong chat):**

```bash
python3 .devin/skills/firecrawl-marketing-research/scripts/firecrawl.py set-key
# Nhap Firecrawl API key (fc-...):   <- key được nhập ở chế độ ẩn
```

**b) Dán key vào chat:** agent sẽ lưu giúp bằng `set-key --key fc-...`.

**c) Biến môi trường:**

```bash
export FIRECRAWL_API_KEY=fc-xxxxxxxx
```

`set-key` sẽ:
1. Ghi `FIRECRAWL_API_KEY=...` vào file `.env` ở thư mục gốc project (thư mục cha của `.devin/`). Nếu skill cài global thì ghi vào thư mục hiện tại. Dùng `--env-file` để chọn đường dẫn khác.
2. Đặt quyền file là `600` (chỉ bạn đọc được).
3. Thêm `.env` vào `.gitignore`.
4. Gọi API kiểm tra key và in số credit còn lại.

Thứ tự script tìm key: biến môi trường `FIRECRAWL_API_KEY` → `./.env` → `.env` ở gốc project → `.env` trong thư mục skill.

> **Không bao giờ commit file `.env`.** Repo này đã có sẵn `.env` trong `.gitignore`.

## Cách dùng

Chỉ cần chat với agent. Một số prompt mẫu:

```text
So sánh bảng giá và tính năng của Haravan, Sapo, KiotViet. Xuất CSV.
Phân tích thông điệp trang chủ của 5 đối thủ này: a.com, b.com, c.com, d.com, e.com
Site doithu.com có những mục nội dung nào? Họ đang đầu tư blog về chủ đề gì?
Tìm top 10 bài cho từ khóa "cách chạy quảng cáo TikTok" ở VN và đề xuất dàn ý bài viết tốt hơn
Tổng hợp review của app X trên các trang review, nhóm pain point theo chủ đề
Tin tức về ngành fintech Việt Nam trong 1 tháng qua, có số liệu gì đáng chú ý?
Lập danh sách công ty SaaS ở Việt Nam kèm website, mô tả, sản phẩm
```

Quy trình agent sẽ làm:

1. **Kiểm tra API key.** Thiếu thì hỏi bạn.
2. **Làm rõ yêu cầu** nếu thiếu thông tin: đối thủ nào, thị trường nào, mục đích gì.
3. **Chọn playbook** và thu thập dữ liệu bằng script. Agent sẽ hỏi trước khi chạy job lớn (crawl hơn ~50 trang hoặc extract hơn ~30 URL).
4. **Viết báo cáo** `research/<chủ-đề>-<ngày>/report.md`, gồm: Tóm tắt nhanh, Phát hiện chính, Cơ hội & đề xuất hành động, Dữ liệu đính kèm, Nguồn & hạn chế.

## Dùng script trực tiếp (CLI)

Bạn có thể dùng script mà không cần agent:

```bash
FC="python3 .devin/skills/firecrawl-marketing-research/scripts/firecrawl.py"
$FC -h              # xem tất cả lệnh
$FC <lệnh> -h       # xem tùy chọn của từng lệnh
```

| Lệnh | Mô tả |
|---|---|
| `set-key` | Lưu API key vào `.env` (`--key`, `--env-file`, `--no-check`) |
| `check-key` | Kiểm tra key, in số credit còn lại |
| `search` | Tìm kiếm web/tin tức, có thể scrape luôn từng kết quả |
| `map` | Liệt kê URL của site, đếm số trang theo từng mục |
| `scrape` | Lấy 1 trang: markdown, summary, links, hoặc JSON theo prompt/schema |
| `extract` | Trích xuất dữ liệu có cấu trúc từ nhiều URL ra CSV + JSON |
| `crawl` | Crawl nhiều trang của site, mỗi trang lưu thành 1 file markdown |

### Ví dụ

```bash
# Tìm trang giá của đối thủ
$FC map https://doithu.com --search pricing --show 10

# Trích xuất bảng giá nhiều đối thủ vào 1 CSV, mỗi gói 1 dòng
$FC extract https://a.com/pricing https://b.com/pricing --schema pricing --rows-key plans

# Định vị và messaging từ trang chủ
$FC extract https://a.com https://b.com --schema positioning

# Trích xuất từ danh sách URL trong file (mỗi dòng 1 URL, dòng bắt đầu bằng # được bỏ qua)
$FC extract --urls-file urls.txt --schema company --workers 3

# Trích xuất tự do bằng prompt
$FC scrape https://a.com/about --prompt "Liệt kê các khách hàng tiêu biểu và số liệu ấn tượng"

# Top 10 kết quả cho từ khóa ở Việt Nam, kèm nội dung từng bài
$FC search "phần mềm quản lý bán hàng" --country VN --limit 10 --scrape

# Tin tức 1 tháng gần nhất
$FC search "VinFast" --sources news --tbs qdr:m --limit 15

# Crawl blog, tối đa 30 trang
$FC crawl https://doithu.com/blog --limit 30 --include "blog/.*"
```

### Tùy chọn hay dùng

| Tùy chọn | Áp dụng cho | Ý nghĩa |
|---|---|---|
| `--schema` | scrape, extract | Tên schema có sẵn (`pricing`...), đường dẫn file JSON schema, hoặc chuỗi JSON |
| `--prompt` | scrape, extract | Mô tả bằng lời dữ liệu cần trích xuất |
| `--rows-key` | extract | Tách một mảng (vd `plans`, `reviews`) thành nhiều dòng CSV |
| `--formats` | scrape | `markdown,summary,links,html,json` |
| `--country`, `--lang` | scrape, extract | Xem trang theo quốc gia/ngôn ngữ, vd `--country VN --lang vi-VN` |
| `--wait` | scrape, extract | Chờ thêm N ms cho trang nặng JavaScript |
| `--full-page` | scrape, extract | Lấy cả header/footer/menu (mặc định chỉ lấy nội dung chính) |
| `--max-age 0` | scrape, extract | Luôn lấy dữ liệu mới, không dùng cache |
| `--sources` | search | `web`, `news`, `images` (có thể kết hợp: `web,news`) |
| `--tbs` | search | `qdr:d` / `qdr:w` / `qdr:m` / `qdr:y` hoặc `cdr:1,cd_min:MM/DD/YYYY,cd_max:MM/DD/YYYY` |
| `--include-domains`, `--exclude-domains` | search | Lọc domain, phân tách bằng dấu phẩy |
| `--include`, `--exclude`, `--max-depth` | crawl | Lọc path bằng regex, giới hạn độ sâu |
| `--out-dir` | tất cả | Thư mục lưu kết quả |

Mã thoát (exit code): `0` thành công, `1` lỗi API hoặc mạng, `2` thiếu hoặc sai API key.

Muốn dùng Firecrawl tự host thì đặt `FIRECRAWL_API_URL=http://localhost:3002`.

## Schema có sẵn

Nằm trong `assets/schemas/`, gọi bằng tên với `--schema <tên>`:

| Schema | Dùng cho | Trường chính |
|---|---|---|
| `pricing` | Trang bảng giá | `plans[]`: tên gói, giá, chu kỳ, đối tượng, tính năng, giới hạn, CTA |
| `positioning` | Trang chủ / landing page | headline, value proposition, đối tượng, CTA, social proof, tone of voice |
| `company` | Trang giới thiệu công ty | tên, mô tả, ngành, sản phẩm, khách hàng mục tiêu, trang liên hệ |
| `reviews` | Trang review | `reviews[]`: rating, ngày, phân khúc, thích, không thích, trích dẫn |
| `article` | Bài blog / SEO | tiêu đề, dàn ý heading, search intent, chủ đề, định dạng, góc tiếp cận |

Muốn thêm schema mới: tạo file JSON Schema trong `assets/schemas/` rồi gọi bằng tên file.

## Kết quả đầu ra

Mặc định kết quả lưu ở `./research/<thời-gian>-<lệnh>-<slug>/`:

```text
research/
├── 20261030-140501-extract-3-urls/
│   ├── extract.csv          # dữ liệu dạng bảng, mở bằng Excel/Google Sheets
│   └── extract.json         # dữ liệu gốc + lỗi (nếu có)
├── 20261030-141210-search-phan-mem-quan-ly-ban-hang/
│   ├── search.csv           # rank, nguồn, tiêu đề, URL, mô tả
│   ├── search.json
│   └── 01-example-com-....md  # nội dung từng bài (khi dùng --scrape)
└── so-sanh-gia-doi-thu-2026-10-30/
    └── report.md            # báo cáo cuối do agent viết
```

Thư mục `research/` đã có trong `.gitignore`.

## Cấu trúc repo

```text
.
├── README.md
├── .gitignore
└── .devin/skills/firecrawl-marketing-research/
    ├── SKILL.md                  # hướng dẫn cho agent: quy trình, mẫu báo cáo, nguyên tắc
    ├── scripts/
    │   └── firecrawl.py          # CLI gọi Firecrawl API v2 (chỉ dùng thư viện chuẩn)
    ├── references/
    │   └── playbooks.md          # 6 quy trình research chi tiết
    └── assets/schemas/           # JSON Schema dựng sẵn
        ├── pricing.json
        ├── positioning.json
        ├── company.json
        ├── reviews.json
        └── article.json
```

## Credit và chi phí

- Mỗi trang scrape/crawl tốn credit Firecrawl. Trích xuất JSON (`extract`, `scrape --prompt/--schema`) tốn nhiều hơn scrape markdown thường. Xem bảng giá mới nhất tại [firecrawl.dev/pricing](https://www.firecrawl.dev/pricing).
- `crawl` mặc định chỉ lấy **20 trang**. Tăng bằng `--limit` khi cần.
- Nên dùng `map --search` để nhắm đúng trang thay vì crawl cả site.
- Agent sẽ hỏi trước khi chạy job lớn. Chạy `check-key` để xem số credit còn lại.

## Giới hạn và đạo đức

- Chỉ lấy **dữ liệu công khai**. Không scrape trang cần đăng nhập, không vượt paywall hay CAPTCHA. Firecrawl mặc định tuân theo `robots.txt`.
- **Không thu thập dữ liệu cá nhân** (tên, email, số điện thoại của cá nhân hay người review). Với lead B2B, chỉ lấy thông tin doanh nghiệp công khai như email chung `info@`, `sales@` hoặc trang liên hệ.
- Facebook, LinkedIn, Instagram, TikTok chặn scrape rất chặt, nên dữ liệu từ đó thường không lấy được.
- Tôn trọng điều khoản sử dụng của từng website.

## Xử lý sự cố

| Thông báo | Nguyên nhân | Cách xử lý |
|---|---|---|
| `NO_API_KEY` | Chưa có key | Chạy `set-key` hoặc đặt `FIRECRAWL_API_KEY` |
| `INVALID_API_KEY` | Key sai, bị thu hồi, hoặc không bắt đầu bằng `fc-` | Tạo key mới ở dashboard Firecrawl rồi chạy lại `set-key` |
| `PAYMENT_REQUIRED` | Hết credit | Nạp thêm hoặc nâng gói Firecrawl |
| `HTTP 408 SCRAPE_TIMEOUT` | Trang tải quá lâu | Thử lại với `--wait 3000` |
| `HTTP 500 SCRAPE_ALL_ENGINES_FAILED` | Site chặn hoặc lỗi | Thử `--full-page`, hoặc bỏ qua URL đó |
| Kết quả rỗng hoặc thiếu giá | Nội dung render bằng JavaScript hoặc nằm trong tab ẩn | Thử `--wait`, hoặc `scrape` lấy markdown rồi đọc thủ công |
| `Het thoi gian cho` (crawl) | Crawl lâu hơn `--wait-max` | Tăng `--wait-max` hoặc giảm `--limit` |

---

Xây dựng bằng [Firecrawl API v2](https://docs.firecrawl.dev). Skill được tạo với sự hỗ trợ của [Devin](https://devin.ai).
