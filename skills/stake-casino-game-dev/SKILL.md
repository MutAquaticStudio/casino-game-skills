---
name: "stake-casino-game-dev"
description: "Agent dẫn dắt làm game slot Stake Engine từng bước (concept, math, style frame, mascot, vertical slice, đủ tính năng, polish, audit, nộp), mỗi bước có cổng QA bằng chứng. Use for any Stake Engine slot task: làm game slot mới, chấm cổng QA, Math SDK, RGS, PixiJS 8, Bet UI, win celebration, social mode, replay, mascot, submission."
---

# Agent làm game slot Stake Engine

Agent này dẫn một game slot từ ý tưởng đến lúc nộp Stake Engine, đi qua **9 bước**. Mỗi bước kết thúc bằng một **cổng QA**: chưa qua cổng thì không sang bước sau.

Viết bằng tiếng Việt. Giữ tiếng Anh cho tên kỹ thuật, tên event của book, lệnh, đường dẫn và thuật ngữ Stake. Trả lời người dùng bằng ngôn ngữ của họ.

**Kiểm tra quy tắc Stake:** 2026-11-15, đối chiếu với repo `StakeEngine/docs` (commit `fefadc7`, ngày 2026-03-17): trang approval (checklist, math, frontend, RGS, disclaimer, game tile, quality), `reference/social-mode`, `dimensions`, `currencies`, `languages`, mã lỗi API. Chưa mở bản web đang chạy. Giới hạn dung lượng (4 GiB sau giải nén, 1 MiB mỗi round, 400 MiB mỗi file zip) **không có trong repo docs**; chúng đến từ lần nộp Inkblade Ronin, nên gọi là "kinh nghiệm", không phải quy tắc chính thức. Khi một quy tắc quyết định kết quả và có mạng, mở lại docs trước khi kết luận.

## 0. Cách dùng

- Người dùng nói **đang ở bước nào** ("đang ở bước 3") hoặc **"làm game mới"**. Với game mới, bắt đầu ở bước 1. Với game đang làm dở, hỏi file handoff (Phụ lục I), đọc nó, rồi chạy lại cổng của bước hiện tại trước khi làm tiếp.
- Mỗi bước có cùng khung: **Mục tiêu · Việc cần làm · Sản phẩm · Cổng QA**.
- Phụ lục A–J nằm cuối file. Phần nào cần chi tiết, đọc phụ lục tương ứng khi tới bước đó, không đọc hết một lượt.

### Quy tắc chung (áp dụng ở mọi bước)

1. **Luôn đưa bằng chứng.** Một tiêu chí chỉ "đạt" khi có ảnh chụp, kết quả lệnh, link demo hoặc file đính kèm. Lời nói "đã kiểm" không phải bằng chứng.
2. **Mặc định "chưa đạt".** Báo cáo cổng bắt đầu với mọi dòng là chưa đạt, chỉ đổi khi có bằng chứng. Nếu tự chấm mà đạt hết ngay lần đầu, kiểm lại bằng chứng một lượt nữa (điểm hoàn hảo ở lần đầu thường là dấu hiệu chấm lỏng).
3. **Commit và push sau mỗi thay đổi có ý nghĩa.** Phiên cloud có thể bị khởi động lại; việc chưa push là việc có thể mất.
4. **Giữ handoff** (Phụ lục I): mỗi cổng xong thì cập nhật quyết định, cách chạy, việc còn mở.
5. **Lỗi thuộc bước nào thì quay về bước đó**, chạy lại cổng của bước đó, rồi chạy lại các cổng sau nó. Không vá vòng quanh ở bước sau.
6. **Chỉ 3 cổng cần chủ dự án duyệt:** bước 1 (concept), bước 3 (style frame), bước 9 (demo cuối). Các cổng còn lại agent tự chấm có bằng chứng và gửi chủ dự án một **báo cáo gộp** sau bước 5, bước 7 và bước 8. Báo cáo gộp không chặn tiến độ, nhưng chủ dự án có thể phủ quyết bất kỳ mục nào.
7. **Việc cần người** (thiết bị thật, RGS thật, người bản ngữ, giấy phép, mua dịch vụ trả phí) thì ghi rõ là cần người, không tự đánh dấu đạt.
8. Trước khi chọn dịch vụ AI nào cho việc gì, kiểm tra gói và hạn mức của nó (Inkblade mất hai vòng hỏi đáp vì gói miễn phí chặn model video).

---

## 1. Mô hình Stake Engine và lỗi chặn duyệt

Game Stake **tính trước và không giữ trạng thái**. Dev mô phỏng mọi vòng ở ngoài, rồi tải lên các file tĩnh cho từng bet mode: **lookup table** (CSV không header: `sim_id,weight,payoutMultiplier`) và **book** (JSONL nén zstd, dòng i = `{"id": i, "payoutMultiplier": p, "events": [...]}`), liệt kê trong `index.json`. Khi gọi `/wallet/play`, RGS chọn một sim theo trọng số và trả events của nó. **Frontend chỉ là lớp hoạt hình**: vẽ đúng điều book nói, hiện số tiền RGS trả về, không bao giờ tự tính hay đổi tiền thắng.

- Hệ số nhân có độ chia 2 chữ số thập phân: số nguyên ×100 (150 = 1.5x). Tiền là số nguyên 6 chữ số thập phân (1 đơn vị = 1.000.000).
- RTP do trọng số LUT quyết định: `RTP = Σ w·p / (100 · cost · Σ w)`.
- Sau khi được duyệt chỉ được sửa nhỏ phần hình, **không đổi math, mode hay cơ chế**. Vì vậy mọi quyết định gameplay phải chốt trước khi nộp.
- **Cấm:** jackpot, gamble/double-up, cashout sớm, mọi trạng thái mang sang vòng sau. Mỗi lượt cược độc lập. Nếu người dùng đòi, giải thích một hai câu và đề xuất lựa chọn hợp lệ (mode mua bonus, hệ số nhân trong một vòng, feature mode).
- Chấm điểm: ba reviewer ẩn danh, thang 0 đến 3 (bước 0.33). Trung bình dưới 1.0 là **không được duyệt**; còn lại làm tròn thành 1, 2 hoặc 3 sao (3 sao: Featured, Burst Games, Stake Exclusives).

### Lỗi chặn duyệt (mỗi mục cần bằng chứng ở cổng liên quan)

| # | Lỗi chặn | Cổng kiểm |
|---|---|---|
| 1 | Game không gốc, đụng IP, tên chứa "Megaways"/"Xways", dùng thương hiệu Stake/Kick, dùng asset mẫu của Web SDK, nội dung phản cảm, nhân vật trẻ con | 1, 3, 8 |
| 2 | Có jackpot, gamble, hay trạng thái qua vòng | 1, 2 |
| 3 | Math ngoài ngưỡng (bảng dưới) hoặc book/LUT không khớp | 2 |
| 4 | Không `authenticate` được khi mở game, hoặc nút cược không gửi được `play` | 5, 8 |
| 5 | Thiếu luật chơi: bảng trả thưởng, RTP và max win từng mode, giá và mô tả từng mode, điều kiện kích hoạt và retrigger, disclaimer | 6 |
| 6 | Không dùng đủ bet level từ `authenticate`; tải lại trang giữa lúc quay làm mất mức cược; bỏ qua `rgs_url` | 5, 8 |
| 7 | Đổi sang mode giá trên 2x mà không có bước xác nhận; autoplay bắt đầu bằng một cú nhấp; không tắt được âm thanh; phím cách không là nút cược | 6 |
| 8 | Số thắng hiển thị khác payout của RGS (kiểm 10 ván thắng mỗi mode) | 5, 8 |
| 9 | Build gọi ra ngoài (CDN, Google Fonts, analytics), có lỗi console, ghi log thông tin game | 5, 9 |
| 10 | Một trong 7 viewport hỏng, hoặc mini-player làm méo bàn chơi | 6, 8 |
| 11 | Replay thiếu hoặc sai (thiếu các tham số, không ẩn nút cược, không hiện chi phí thật) | 6 |
| 12 | Social mode (stake.us): còn từ cấm (chữ hoặc ảnh), thiếu GC/SC hoặc còn dấu `$` | 6, 8 |

### Ngưỡng math (docs `approval/math-requirements` và checklist)

| Chỉ số | Ngưỡng |
|---|---|
| RTP mỗi mode | 90.0 đến 98.0% |
| Chênh RTP giữa các mode | ≤ 0.5% (base 97% thì các mode khác 96.5 đến 97.5%) |
| Max win | Khớp luật chơi và đạt được. Docs viết "thường hay hơn 1 trên 10.000.000"; checklist viết "1 trên 20.000.000 hoặc hay hơn". Dùng ngưỡng chặt hơn (1/10.000.000) làm mục tiêu. |
| Số ván mô phỏng (slot) | 100.000 đến 1.000.000 mỗi mode |
| Tỉ lệ thắng khác 0 | Tối thiểu hay hơn 1 trên 20; base thường 1 trên 3 đến 8 |
| Phần thua | Không áp đảo (90.000 thua trên 100.000 có thể bị loại) |
| Kết quả đơn lẻ | Không có sim nào chiếm trội nếu hình ảnh gợi sự đa dạng |
| Độ biến động base | Độ lệch chuẩn nằm trong chuẩn ngành |
| Hàng trọng số 0 | Không áp đảo; báo số payout có trọng số khác 0 |
| Dải thắng | Không có khoảng trống giữa thắng nhỏ và max win |
| Giá mode | Ghi đúng trong luật chơi |

### Quy tắc phía frontend cần nhớ ở mọi bước

- Build **tĩnh**, không gọi ra ngoài (không CDN, font nhúng sẵn, đường dẫn tương đối, Vite `base: './'`).
- Tiếng Anh bắt buộc. `lang` không hỗ trợ không được làm hỏng chữ. Tiền tệ: USD 2 số lẻ, JPY 0, XGC và XSC hiện "10.00 GC" và "10.00 SC" (không có `$`).
- 7 viewport: Desktop 1200×675, Laptop 1024×576, Popout L 800×450, **Popout S 400×225**, Mobile L 425×812, M 375×667, S 320×568.
- Phím cách = nút cược (bỏ qua key repeat và ô nhập). Không làm "giữ phím để quay liên tục".
- Số thắng nhiều bước thì bộ đếm tăng từng bước tới tổng. Turbo vẫn phải đọc được số thắng.

---

## 2. Bước 1. Concept

**Mục tiêu:** chốt game là gì và mode ladder, vì không thêm mode hay đổi cơ chế được sau khi duyệt.

**Việc cần làm**
1. Thiết kế chiều sâu theo Phụ lục H: một cơ chế lõi có bản sắc, tiến trình trong vòng (meter có stage), mode ladder đầy đủ, nhịp cảm xúc một phiên, kiểm tra thiết kế có trách nhiệm. Không dừng ở "quay, thắng, hết".
2. Chốt lưới, theme, RTP mục tiêu, wincap, độ biến động, và sàng lọc theo bảng lỗi chặn mục 1.
3. Liệt kê **mọi event của book** (tên, dữ liệu mang theo, handler dự kiến).
4. Chốt các quyết định sớm: ai làm animation (animator, làm bằng tay), Bet UI (mặc định bộ chung của studio), dịch vụ tạo ảnh (Figma `generate_image`) còn hạn mức.
5. Với yêu cầu "làm cho tôi một game slot", hỏi nhanh vài câu trước khi code. Nếu người dùng chỉ muốn prototype hình ảnh, nói rõ prototype dùng book giả và chưa sẵn sàng nộp.

**Sản phẩm:** trang concept (Phụ lục H), bảng sàng lọc, danh sách event.

### Cổng QA 1: Concept (chủ dự án duyệt)

| Tiêu chí (đo được) | Bằng chứng |
|---|---|
| Game tả được trong **một câu ≤ 25 từ**, có cơ chế lõi | Câu mô tả trong trang concept |
| Mode ladder chốt đủ: id, giá, wincap, RTP mục tiêu cho từng mode; có dòng "không thêm mode sau khi duyệt" | Bảng mode |
| Mọi meter chỉ sống trong một vòng (có/không) | Mục stateless trong concept |
| Mỗi cơ chế có tên event book; mỗi event có handler dự kiến (0 event mồ côi) | Danh sách event |
| Sàng lọc: 0 IP, 0 thương hiệu Stake/Kick, 0 nhân vật trẻ con; tên game đã tìm trùng và không trùng | Bảng sàng lọc + kết quả tìm |
| Kiểm tra trách nhiệm, 3 mục có/không: không ăn mừng khi người chơi lỗ so với tiền cược; không ép mua bonus; không "suýt thắng" giả | Mục trách nhiệm |
| Đã chốt: animator làm animation bằng tay; Bet UI mặc định bộ chung; hạn mức dịch vụ ảnh đã kiểm | Mục quyết định |

**Mặc định: chưa đạt.** **Người duyệt:** chủ dự án (ký bằng văn bản trong handoff).
**Quay lại bước 1** khi: bước sau cần đổi cơ chế, thêm mode, hoặc đổi wincap. Chạy lại cổng 1, rồi bước 2 và các bước sau nó.

---

## 3. Bước 2. Math

**Mục tiêu:** có book và LUT cuối cùng đạt ngưỡng, kèm bằng chứng đo lại. Math chốt trước art lớn.

**Việc cần làm**
1. Cài Math SDK (`github.com/StakeEngine/math-sdk`, MIT): `make setup`, copy `games/template/` hoặc game mẫu gần nhất (`0_0_lines`, `0_0_ways`, `0_0_scatter` pay-anywhere + tumble, `0_0_cluster`, `0_0_expwilds`, `0_0_lines_feature_match`, `fifty_fifty`).
2. Viết `game_config.py` (symbol, bảng trả thưởng, reel, bet mode), `gamestate.py` (`run_spin`, `run_freespin`), các file calculations/events/override.
3. Chạy theo vòng: 100 ván không nén, không tối ưu → xem events → 1e4 ván có tối ưu → bản cuối 100k+ mỗi mode, có nén.
4. Tối ưu trọng số, **tự đo lại RTP** từ bảng LUT cuối, không tin số optimizer in ra.
5. Viết script replay book cho mọi cơ chế riêng (ví dụ meter) và so từng event. Mục tiêu 0 lệch.
6. Chọn event ID replay cho mỗi mode (từ `forces/force_<mode>.json`): thắng thường, thắng lớn, wincap, thua, kích hoạt bonus.
7. Đo dung lượng ngay sau lần chạy đầy đủ đầu tiên.

**Ghi chú chạy math (đều đã gây mất việc ở Inkblade)**
- **Giới hạn dung lượng (kinh nghiệm):** mỗi mode dưới 4 GiB sau giải nén, mỗi round tối đa 1 MiB. Book vượt giới hạn bị từ chối khi tải lên. Cách xử: nén JSON gọn (bỏ khoảng trắng, nội dung không đổi) hoặc **giảm số ván của riêng mode đó** (Inkblade: Awakened Duel 100.000 ván là 6,5 GB, 50.000 ván còn 3,24 GB). Mỗi file zip giao đi ≤ 400 MiB, chia nhiều zip nếu cần.
- **Bẫy optimizer:** nó ưu tiên đọc book `.json` đọc được nếu có. Lần chạy `quick` để lại các file đó trong `library/books` và `library/publish_files`; phải dời đi trước khi chạy bản đầy đủ, nếu không trọng số tính trên vài nghìn ván và ghi đè bảng trọng số.
- Sau khi đổi quy tắc cơ chế: chạy lại math, kiểm lại script replay, cập nhật luật chơi mọi ngôn ngữ.
- Book dùng cho demo phải **lấy mẫu từ math thật**, không viết tay. Nhờ vậy mọi hành vi lạ nhìn thấy ở demo là hành vi của math, không phải lỗi hiển thị.
- Tầng thắng ở frontend tính theo chi phí thật của mode, nên math nên chứa `winLevel` theo thang chuẩn (Phụ lục D); không chỉnh ngưỡng ở frontend.

**Sản phẩm:** `library/publish_files` (`index.json`, books nén, LUT), bảng chỉ số, PAR sheet, script replay, danh sách event ID.

### Cổng QA 2: Math (agent tự kiểm)

| Tiêu chí | Bằng chứng |
|---|---|
| `scripts/validate_math.py <publish_files>` PASS 100% (hoặc bản rút gọn tương đương) | Output lệnh |
| RTP mỗi mode trong 90 đến 98%; chênh giữa các mode ≤ 0.5% | RTP tự đo lại từ LUT, mỗi mode một dòng |
| Tỉ lệ thắng khác 0 của base hay hơn 1/20 (mục tiêu 1/3 đến 1/8) | Bảng chỉ số |
| Max win khớp luật và hay hơn 1/10.000.000 | Bảng chỉ số |
| Số ván ≥ 100.000 mỗi mode, hoặc ghi lý do giảm | `run.py` và dung lượng |
| Book mỗi mode < 4 GiB giải nén, mỗi round ≤ 1 MiB, mỗi zip ≤ 400 MiB | Số đo `du` hoặc output lệnh |
| Không còn file lần chạy `quick` trong `library/` khi tối ưu (có/không) | Danh sách thư mục |
| Script replay cơ chế riêng: 0 lệch | Output lệnh |
| Mỗi event trong concept có mặt trong book (có/không) | Bảng đối chiếu |
| Tần suất feature đã đo và ghi vào concept | Số đo trong handoff |
| Có event ID replay đủ 5 loại cho mỗi mode | Danh sách |
| Dải thắng không có khoảng trống (PAR sheet) | Ảnh hoặc bảng PAR |

**Mặc định: chưa đạt.** **Người duyệt:** agent tự kiểm; chủ dự án xem gộp.
**Quay lại bước 1** nếu cần đổi cơ chế hay mode. **Quay lại bước 2** mỗi khi sau đó có bất kỳ đổi nào chạm math (kể cả đổi một trọng số): chạy lại toàn bộ cổng 2.

---

## 4. Bước 3. Style frame

**Mục tiêu:** chốt phong cách hình ảnh trên **một màn hình mẫu** trước khi làm art hàng loạt.

**Việc cần làm**
1. Tạo một màn hình mẫu gồm nền, bàn chơi, ít nhất 3 symbol (cao, thấp và wild hoặc scatter) và HUD mặc định (Phụ lục C), cùng bảng màu có mã hex.
2. **Tạo ảnh bằng Figma `generate_image`.** Công cụ này **không nhận ảnh tham chiếu**, nên mọi prompt phải lặp lại đủ mô tả nhân vật, trang phục và bảng màu, nếu không màu và chi tiết sẽ lệch từ ảnh này sang ảnh khác (Inkblade: đồ đen thành xanh tím than, giáp to hơn). Lưu toàn bộ prompt và seed vào repo.
3. Tạo mọi art trên **nền magenta phẳng (#FF00FF)** rồi tách nền bằng script chạy lại được (ngưỡng + halo 2 px, khử màu viền). Sửa một script là có lại toàn bộ asset.
4. Dùng `casino-symbol-art` nếu cần công cụ kiểm silhouette, thu nhỏ và thang xám (tùy chọn).
5. Chụp ở 1200×675, 400×225 và 425×812.

**Sản phẩm:** ảnh màn hình mẫu ở 3 kích thước, bảng màu, prompt và script tách nền.

### Cổng QA 3: Style frame (chủ dự án duyệt)

| Tiêu chí | Bằng chứng |
|---|---|
| Màn hình mẫu chụp đủ 3 kích thước (1200×675, 400×225, 425×812) | 3 ảnh chụp |
| ≥ 3 symbol; phân biệt được ở 400×225 bằng hình dạng (thu nhỏ và thang xám), không chỉ bằng màu | Ảnh thu nhỏ + thang xám |
| Bàn chơi là thứ nổi nhất: ảnh làm mờ vẫn thấy bàn trước tiên (có/không) | Ảnh làm mờ |
| Phân biệt được dưới mô phỏng mù màu (deuteranopia, protanopia) | 2 ảnh mô phỏng |
| Chữ tương phản ≥ 4.5:1; nhãn không nhỏ hơn ~12 px | Số đo hoặc ảnh có chú thích |
| Bảng màu có mã hex; đoạn mô tả phong cách được khóa | File bảng màu + đoạn mô tả |
| Art gốc, không IP; toàn bộ prompt đã lưu; script tách nền chạy lại ra cùng kết quả | Prompt, script, 2 lần chạy |
| HUD là bộ chung của studio (hoặc có quyết định bằng văn bản của chủ dự án để theo theme) | Ảnh chụp, ghi chú quyết định |

**Mặc định: chưa đạt.** **Người duyệt:** chủ dự án.
**Quay lại bước 3** khi phong cách đổi sau này: làm lại style frame và duyệt lại, không vá từng asset.

---

## 5. Bước 4. Mascot concept (pose)

**Mục tiêu:** có **một pose gốc** đủ trung tính để animator rig và làm nhiều kiểu animation khác nhau bằng tay. Phạm vi của skill chỉ gồm phần tạo ảnh; animator làm rig và animation (Phụ lục F).

Bỏ qua bước này nếu game không có mascot, và ghi "không mascot" vào handoff.

**Việc cần làm**
1. Tạo mô tả khóa cho nhân vật: vóc dáng, trang phục, vật cầm, bảng màu (một đoạn văn bản dùng lại nguyên văn trong mọi prompt).
2. **Gen thử 5 pose** (tạo bằng prompt có đoạn mô tả khóa, nền magenta). Mỗi pose phải là **tư thế gốc dùng được cho nhiều kiểu animation**, không phải khoảnh khắc giữa một hành động: tay tách thân, chân tách nhau, vật cầm xa thân, thân hơi nghiêng 3/4, toàn thân không cắt biên.
3. Chấm từng pose bằng bảng khả năng animation (Cổng QA 4): với mỗi animation trong 11 animation (Phụ lục F), pose có cho phép làm được không (✓/✗) và vì sao. Chọn pose có nhiều ✓ nhất.
4. Chốt: animator và định dạng giao (Spine hoặc chuỗi PNG 30 fps; kiểm giấy phép runtime Spine trước khi đưa vào game), và ai trả giấy phép.
5. Sửa giải phẫu ở bước này (ngón tay, bàn tay). Từ đây mọi thứ đo theo pose đã chọn (tỉ lệ, góc nhìn, màu).

**Sản phẩm:** 5 pose, bảng chấm khả năng animation, pose đã chọn, mô tả khóa, quyết định về animator.

### Cổng QA 4: Mascot concept (agent tự kiểm, chủ dự án xem gộp)

| Tiêu chí | Bằng chứng |
|---|---|
| Có đủ **5 pose** để so sánh | 5 ảnh trong một bảng |
| Pose chọn: toàn thân, góc 3/4, không cắt biên, nền magenta, tay và chân tách thân, vật cầm xa thân, silhouette đọc được (mỗi mục có/không) | Ảnh pose + checklist 6 dòng |
| **Khả năng animation:** trong 11 animation, pose đạt ≥ 10 ✓ và không có ✗ ở `idle`, `win_big`, `win_huge` | Bảng 11 dòng (animation, ✓/✗, lý do) |
| Đúng 5 ngón mỗi tay; mặt, giáp và vật cầm không dị dạng (kiểm bằng mắt, có phóng to) | Ảnh phóng to bàn tay |
| Có danh sách bộ phận dự kiến (số lượng theo nhóm) và danh sách phần bị che cần vẽ đủ | Bảng bộ phận |
| Có mô tả khóa nhân vật và bảng màu để lặp lại trong mọi prompt | Đoạn văn bản |
| Đã chốt animator, định dạng giao và người chịu trách nhiệm giấy phép Spine | Mục quyết định |

**Mặc định: chưa đạt.** **Người duyệt:** agent tự kiểm; pose đã chọn vào báo cáo gộp đầu tiên (sau bước 5), kèm câu "nói ngay nếu muốn đổi pose". Đổi pose sau khi gen bộ phận là làm lại bước 4 và phần gen bộ phận ở bước 6.
**Quay lại bước 3** nếu pose không hợp phong cách đã duyệt.

---

## 6. Bước 5. Vertical slice

**Mục tiêu:** một vòng chơi trọn vẹn từ book thật, chạy trong demo web, để chốt cảm giác chơi trước khi làm đủ tính năng.

**Việc cần làm**
1. Dựng frontend theo Phụ lục A (RGS client, round controller, book event player) và Phụ lục B (Pixi 8). Kiến trúc: **RGS client → round controller → book event player → handler từng event → renderer**; cùng một đường chạy cho chơi thật, khôi phục vòng và replay.
2. Làm một vòng hoàn chỉnh: quay, thắng, tumble (nếu có), âm thanh, kết thúc vòng, chạy với RGS giả lập phát lại **book thật** (lấy mẫu từ math ở bước 2).
3. Tách **bản demo** và **bản production** bằng cờ build (ví dụ `VITE_DEMO`). Chỉ bản demo có: nút tốc độ 0.25x/0.5x/1x, nút đổi variant, nút đổi skin. Bản nộp không chứa các nút này.
4. Đăng demo lên một link để chủ dự án mở được (artifact riêng tư là đủ).
5. Chụp frame bằng trình duyệt headless ở tốc độ 0.25x. **Đợi lệnh chụp xong rồi mới đọc ảnh**, và chạy lệnh dài ở nền (đọc ảnh chưa xong đã dẫn tới kết luận sai nhiều lần ở Inkblade).

**Sản phẩm:** link demo, ảnh chụp, bản build chạy được.

### Cổng QA 5: Vertical slice (agent tự kiểm, chủ dự án xem gộp)

| Tiêu chí | Bằng chứng |
|---|---|
| Một vòng đầy đủ (quay → thắng → tumble nếu có → âm thanh → kết thúc) chạy từ **book thật** | Link demo + video hoặc 3 ảnh chụp ở 0.25x |
| Live, khôi phục vòng và replay cùng một đường chạy; cả 3 đã thử | Output test hoặc ghi chú 3 lần chạy |
| 10 ván thắng: số hiển thị bằng payout của RGS giả lập (10/10) | Bảng 10 dòng |
| Bản demo và production tách bằng cờ; grep bản production không thấy nút demo | Output `grep` |
| `scripts/check_static_build.py dist` 0 lỗi; console 0 lỗi | Output lệnh, ảnh console |
| Mọi event type có trong slice có handler (0 event bị bỏ qua âm thầm) | Bảng event → handler |
| Thời gian frame trên desktop: p95 ≤ 20 ms | Số đo |
| Có `authenticate` và `play` đúng quy trình (end-round chỉ khi payout > 0) | Log mạng của RGS giả lập |

**Mặc định: chưa đạt.** **Người duyệt:** agent tự kiểm; gửi **báo cáo gộp #1** (cổng 2, 4, 5) cho chủ dự án.
**Quay lại bước 2** nếu cảm giác chơi cho thấy cần đổi cơ chế hay số liệu; thử biến thể bằng vertical slice trước khi làm art lớn.

---

## 7. Bước 6. Đủ tính năng (gồm giao gói animator)

**Mục tiêu:** mọi mode, tính năng và yêu cầu Stake đều có mặt; giao gói animator đi sớm để animation về kịp bước polish.

**Việc cần làm**
1. Mọi mode chơi được; mọi event type có handler. Meter, stage, bonus intro và summary, retrigger, Max Win.
2. **Win celebration** 5 tầng, tầng tính theo chi phí thật của mode (Phụ lục D).
3. **Luật chơi** đủ mục (Phụ lục E); số RTP, giá, bảng trả lấy từ config, không gõ tay. Có disclaimer và hướng dẫn từng nút.
4. **Replay** (Phụ lục A). **Social mode** và **đa ngôn ngữ** (Phụ lục E).
5. Hành vi bắt buộc: phím cách, xác nhận autoplay, xác nhận mode giá trên 2x, bật/tắt âm thanh, số thắng đếm dần tới tổng.
6. Bố cục 7 viewport (Phụ lục C).
7. **Gói animator** (Phụ lục F): gen bộ phận riêng đầy đủ phần bị che, ghép lên pose đã duyệt, đóng gói.
8. Math không đổi so với bước 2.

**Sản phẩm:** game chơi được đủ mode, gói animator, handoff cập nhật.

### Cổng QA 6: Đủ tính năng (agent tự kiểm, chủ dự án xem gộp)

| Tiêu chí | Bằng chứng |
|---|---|
| Mọi mode chơi được từ đầu đến cuối; mọi event type có handler | Bảng mode (mỗi mode một lượt chơi) + bảng event |
| Win celebration 5 tầng; **mua bonus lỗ so với chi phí thật thì 0 popup** (thử ít nhất 1 trường hợp) | Ảnh chụp từng tầng + 1 ảnh/clip mua bonus lỗ |
| Luật chơi có đủ: bảng trả mọi tổ hợp, RTP và max win từng mode, giá và mô tả từng mode, điều kiện kích hoạt và retrigger, hướng dẫn nút, disclaimer đủ 7 ý | Ảnh từng trang luật |
| Replay: bỏ qua authenticate; ẩn balance, nút cược, chọn cược, autoplay; hiện thắng, mức cược, tiền tệ và chi phí thật; có "Play" rồi "Play again"; nhận `currency`, `lang`, `amount`, `social` | Ảnh chụp + URL thử |
| Social: `scripts/check_social_terms.py` 0 kết quả; không chữ cấm trong ảnh; GC/SC không có `$` | Output lệnh + ảnh |
| Ngôn ngữ: 16 file đủ khóa; kiểm bằng ngôn ngữ giả `qps`; font nhúng cho ar/hi/ja/ko/zh; trạng thái người bản ngữ đọc lại ghi rõ (đã/chưa) | Output script khóa + ảnh `qps` |
| Phím cách, xác nhận autoplay, xác nhận mode > 2x, bật/tắt âm thanh: cả 4 đã thử | 4 ảnh hoặc ghi chú |
| 7 viewport: 0 control tràn; nút ≥ 36 px ở 400×225 | 7 ảnh + số đo |
| Gói animator đủ (xem dưới) | Danh sách file + ảnh so sánh |
| Math không đổi: hash LUT trùng bước 2 | Output `sha256` |

**Kiểm riêng gói animator**

| Tiêu chí | Bằng chứng |
|---|---|
| Có PSD nhiều layer, PNG từng bộ phận cắt sát, PNG full canvas, file vị trí, pose ghép, `ANIMATION_LIST.md` đủ 11 animation | Danh sách file |
| Chồng các PNG full canvas theo thứ tự vẽ **khớp pose đã duyệt** | Ảnh chồng + ảnh hiệu |
| Tỉ lệ so với concept: tỉ lệ đầu/thân và độ rộng đứng lệch ≤ 5% | Số đo hai ảnh |
| Mỗi bộ phận vẽ **đủ phần bị che** (bắp tay dưới khăn, thân dưới tay...), không có vệt nhòe bù | Ảnh từng bộ phận ở nền xám |
| Tên layer, tên PNG và tên trong file vị trí khớp nhau 100% | Output script kiểm |

**Mặc định: chưa đạt.** **Người duyệt:** agent tự kiểm (báo cáo gộp #2 sau bước 7).
**Quay lại bước 4** nếu gói bộ phận không ghép được lên pose; **bước 2** nếu cần đổi math; **bước 1** nếu cần đổi mode.

---

## 8. Bước 7. Polish

**Mục tiêu:** hiệu ứng, âm thanh, chuyển cảnh và mascot đồng bộ theo trạng thái game; mượt trên điện thoại.

**Việc cần làm**
1. **VFX theo trạng thái** (base, bonus, từng stage): nền sống bằng ánh sáng vẽ đè (sương, lá, trăng), hiệu ứng khi dừng cột, anticipation thật, hiệu ứng ô thắng. Mọi hiệu ứng tắt khi `prefers-reduced-motion`. Dùng `slot-art-vfx-director`.
2. **Âm thanh** theo `casino-audio-design`: nhạc base và bonus riêng, ducking, mix khoảng −16 LUFS (đo bằng ffmpeg), sting từng tầng thắng. Mở khóa âm thanh trên điện thoại bằng nhiều sự kiện chạm và bấm (`pointerdown`, `pointerup`, `touchend`, `click`, `keydown`, pha capture), thử lại tới khi `AudioContext` thật sự `running`.
3. **Chuyển cảnh** vào và ra bonus, dùng một ẩn dụ vật lý của theme và dùng nhất quán.
4. **Mascot:** tích hợp animation của animator, gọi theo sự kiện của book (Phụ lục F). Dùng `spine-character-rig` cho phần phát animation trong game. Hiệu ứng do code (mắt sáng, màu kiếm, hào quang) gắn lên bone gắn hiệu ứng.
5. **Win celebration** dùng `casino-win-celebration-motion`.
6. **Hiệu năng:** bộ đo thời gian frame tự giảm hiệu ứng khi dưới ~40 fps; tải lần đầu ≤ ~10 MB, asset bonus tải nền; filter chỉ áp lên container nhỏ, trong thời gian ngắn.
7. Duyệt ở **tốc độ 0.25x và 1x** (0.25x lộ lỗi VFX mà tốc độ thường không thấy: ink sweep còn đọng, vòng sáng không tắt khi turbo).

**Sản phẩm:** build có VFX, âm thanh, chuyển cảnh, mascot đã tích hợp; ảnh chụp 0.25x và 1x.

### Cổng QA 7: Polish (agent tự kiểm, chủ dự án xem gộp)

| Tiêu chí | Bằng chứng |
|---|---|
| VFX khác nhau theo trạng thái (base, bonus, từng stage), mỗi trạng thái 1 ảnh | Ảnh chụp từng trạng thái |
| Reduced motion bật thì mọi thứ đứng yên (có/không) | Ảnh trước và sau, hoặc video ngắn |
| Sau turbo, **0 hiệu ứng đọng lại** | 3 frame chụp ở 0.25x sau khi kết thúc vòng |
| Âm thanh: −16 LUFS ±1, đỉnh ≤ −1 dBTP (hoặc ≤ −3 dBFS nếu dùng limiter mềm); có ducking; bảng event → âm thanh đủ (0 event không có tiếng, trừ những event đã chọn im) | Output ffmpeg + bảng |
| `AudioContext` chạy được sau thao tác đầu tiên trên điện thoại giả lập và thiết bị thật (nếu có) | Log trạng thái `running` |
| Chuyển cảnh vào và ra bonus có mặt, chạy mượt ở 0.25x | Chuỗi frame |
| Mascot: 11 animation gắn đúng sự kiện, ngắt được với mix ≤ 0.25 s; **nếu animator chưa giao thì mục này "chưa đạt"** | Video từng animation trong game + bảng sự kiện → animation |
| Bộ đo frame tự giảm hiệu ứng khi < ~40 fps (có/không); tải lần đầu ≤ ~10 MB | Log + số đo |

**Mặc định: chưa đạt.** Chỉ được đi tiếp khi mục mascot đạt, hoặc chủ dự án ghi **bằng văn bản vào handoff** là nộp với bản tạm. **Người duyệt:** agent tự kiểm; chủ dự án xem **báo cáo gộp #2**.
**Quay lại bước 6** nếu thiếu tính năng, **bước 4** nếu animation không hợp pose.

---

## 9. Bước 8. Audit

**Mục tiêu:** tìm mọi lỗi chặn duyệt trước khi Stake tìm ra, kể cả những thứ chỉ thiết bị thật mới lộ.

**Việc cần làm**
1. Chạy skill `casino-game-audit`; đối chiếu bảng lỗi chặn mục 1 và bảng Stake dưới đây.
2. Kiểm với **RGS thật** (tham số `rgs_url`, `sessionID`, `lang`, `currency`): `authenticate`, `play`, `end-round` (chỉ khi payout > 0), khôi phục vòng đang dở, mọi mã lỗi. Thử USD, JPY, MXN, XGC, XSC; mức cược USD $0.10 đến $1.000 mặc định $1; JPY ¥10 đến ¥150.000 mặc định ¥100; MXN 1 đến 15.000 mặc định 10; tải lại giữa lúc quay giữ mức cược; đổi `rgs_url` thì game gọi URL mới.
3. Đo FPS trên **điện thoại tầm trung thật** ở free spins có hiệu ứng nặng.
4. Nhờ **người bản ngữ** đọc lại 15 ngôn ngữ ngoài tiếng Anh.
5. Xóa mọi mục "chưa làm" trong handoff, hoặc chuyển chúng thành blocker.

**Việc cần người:** thiết bị thật, tài khoản nhà phát triển Stake và RGS thật, người bản ngữ.

### Cổng QA 8: Audit (agent tự kiểm, kèm việc cần người)

| Tiêu chí | Bằng chứng |
|---|---|
| `casino-game-audit`: 0 blocker; mục Graphics & art direction ≥ 4 | Báo cáo chấm điểm |
| Bảng Stake đủ ✅: PreChecks, Thumbnail, Math, RGS, Rules, Responsive, Behaviour, Social, Replay | Bảng (Phụ lục J) |
| RGS thật: authenticate, play, end-round, resume, `rgs_url` đều đúng; 5 tiền tệ đã thử; 10 ván thắng mỗi mode khớp payout | Log và bảng |
| FPS trên điện thoại tầm trung thật: ≥ 55 fps và không tụt dưới 40 trong free spins (**cần người đo**) | Video + số đo thiết bị |
| Người bản ngữ đã đọc 15 ngôn ngữ (**cần người**) | Xác nhận từng ngôn ngữ trong handoff |
| Mục "chưa làm" trong handoff = 0 | Trích handoff |
| Tile và cover đúng kích thước, nằm trong vùng an toàn, đủ sáng, không viền tối | Ảnh tile + kết quả `tile_check` nếu dùng |

**Mặc định: chưa đạt.** **Người duyệt:** agent tự kiểm; chủ dự án xem **báo cáo gộp #3**. Không nộp khi còn việc cần người chưa làm, trừ khi chủ dự án ghi rõ chấp nhận rủi ro.
**Quay lại:** lỗi thuộc bước nào về bước đó, chạy lại cổng bước đó, rồi các cổng sau.

---

## 10. Bước 9. Đóng gói và nộp

**Mục tiêu:** có gói nộp mới nhất, đúng và đã được chủ dự án duyệt demo cuối.

**Việc cần làm**
1. Build production **mới hơn commit cuối**; chạy `scripts/check_static_build.py dist`.
2. Đóng gói: zip frontend, zip math (mỗi file ≤ 400 MiB), `index.json`, tile, cover, logo studio, danh sách event ID replay.
3. Cập nhật link demo cuối (cờ demo bật). Chủ dự án mở và chơi **mọi mode** ở 0.25x và 1x.
4. Quy trình trên dashboard: đăng ký ở stake-engine.com → team + logo nhà cung cấp (Team Settings → Branding) → tải math → tải frontend tĩnh (phục vụ ở `{team}.live.stake-engine.com/{game}/v{n}/`) → tạo tile trong Tile Editor → gửi yêu cầu math và frontend. Sau khi duyệt, template mức cược được áp (Stake.us dùng template tiền tố `us_`), cả hai yêu cầu ở trạng thái Approved & Active.

**Sản phẩm:** gói nộp, link demo cuối, bản ghi duyệt của chủ dự án.

### Cổng QA 9: Đóng gói và nộp (chủ dự án duyệt demo cuối)

| Tiêu chí | Bằng chứng |
|---|---|
| Build production mới hơn commit cuối; `check_static_build` 0 lỗi | Mã băm commit + thời gian build + output lệnh |
| Bản nộp không chứa nút demo (nút tốc độ, đổi variant, đổi skin) | Output `grep` |
| Zip frontend; zip math từng file ≤ 400 MiB; `index.json` khớp các file | Danh sách file và kích thước |
| Tile và cover đúng yêu cầu; logo studio đã đặt ở Branding | Ảnh dashboard |
| Có danh sách event ID replay cho mỗi mode | Bảng |
| Chủ dự án đã chơi **đủ mọi mode** ở 0.25x và 1x và duyệt bằng văn bản | Link demo + lời duyệt |
| Checklist Stake: mọi mục ✅ | Bảng (Phụ lục J) |
| Handoff cập nhật: phiên bản nộp, việc còn mở, cách dựng lại | File handoff |

**Mặc định: chưa đạt.** **Người duyệt:** chủ dự án. Sau khi nộp, chỉ sửa nhỏ phần hình. Mọi đổi math, mode hay cơ chế là làm game mới.
**Quay lại:** bất kỳ mục chưa đạt nào đưa về bước sở hữu nó.

---

## 11. Skill đi kèm

| Skill | Dùng ở bước |
|---|---|
| `casino-game-audit` | 8 (chấm điểm, bảng lỗi); có thể dùng thử ở 7 |
| `casino-audio-design` | 7 (nhạc, SFX, mix, ducking, sting); lập kế hoạch ở 5 |
| `slot-art-vfx-director` | 3 (định hướng art), 7 (VFX theo trạng thái) |
| `spine-character-rig` | 4 và 6 (chuẩn bị gói cho animator), 7 (phát animation trong game) |
| `casino-win-celebration-motion` | 6 và 7 (màn win theo tầng, nhịp đếm) |

`casino-symbol-art` (trong repo này) vẫn dùng được ở bước 3 như công cụ kiểm silhouette, thu nhỏ và thang xám.
Các số § cũ (§7, §8, §8.5, §12, §12.3, §13, §13.0) được giữ ở tiêu đề phụ lục vì các skill khác trong repo tham chiếu chúng.

---

# Phụ lục

Tài nguyên đi kèm (dùng nếu thư mục sát file này tồn tại; nếu không, dùng bản rút gọn ngay trong file): `scripts/validate_math.py`, `scripts/check_social_terms.py`, `scripts/check_static_build.py`, `scripts/mobile_layout.py`, `assets/rgs-client.ts`, `assets/book-player.ts`, `references/pixi-slots.md`, `references/bet-ui-hud.md`, `references/win-presentation.md`, `references/concept-design.md`, `references/stake-engine/overview.md`, `references/stake-engine/math-sdk.md`, `references/stake-engine/math-requirements.md`, `references/stake-engine/rgs-api.md` (ghi chú chi tiết từng chủ đề của docs Stake).

## Phụ lục A. RGS client và luồng một ván

```ts
export const AMOUNT_MULT = 1_000_000;            // tiền = số nguyên 6 chữ số thập phân
const q = new URLSearchParams(location.search);
const host = q.get('rgs_url') ?? '';
export const P = {
  sessionID: q.get('sessionID') ?? '', rgsUrl: /^https?:/.test(host) ? host : `https://${host}`,
  lang: q.get('lang') ?? 'en', currency: q.get('currency') ?? 'USD',
  device: q.get('device') === 'mobile' ? 'mobile' : 'desktop',
  social: q.get('social') === 'true', demo: q.get('demo') === 'true', replay: q.get('replay') === 'true',
  game: q.get('game'), version: q.get('version'), mode: q.get('mode'), event: q.get('event'),
  amount: q.get('amount') ? Number(q.get('amount')) : undefined,
};
async function post<T>(path: string, body: object): Promise<T> {
  const r = await fetch(P.rgsUrl + path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  const d: any = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(d?.code ?? d?.error?.code ?? (typeof d?.error === 'string' ? d.error : 'ERR_GEN'));
  return d;
}
export const rgs = {
  authenticate: () => post<any>('/wallet/authenticate', { sessionID: P.sessionID, language: P.lang }),
  balance: () => post<any>('/wallet/balance', { sessionID: P.sessionID }),
  play: (amountRaw: number, mode: string) => post<any>('/wallet/play', { sessionID: P.sessionID, amount: amountRaw, mode, currency: P.currency }),
  endRound: () => post<any>('/wallet/end-round', { sessionID: P.sessionID }),   // chỉ khi payout > 0
  event: (i: number) => post<any>('/bet/event', { sessionID: P.sessionID, event: String(i) }),
  replay: () => fetch(`${P.rgsUrl}/bet/replay/${P.game}/${P.version}/${P.mode}/${P.event}`).then(r => r.json()),
};
export const winRaw = (betRaw: number, payoutMultiplier: number) => Math.round(betRaw * payoutMultiplier);
export const bookToRaw = (betRaw: number, bookAmount: number) => Math.round(betRaw * bookAmount / 100);
```

**Luồng một ván:** đọc URL → `replay=true`? (bên dưới) → `authenticate` (balance, `round` đang dở hoặc vòng gần nhất, `config{minBet,maxBet,stepBet,defaultBetLevel,betLevels,betModes}`; bỏ qua `jurisdiction` và `meta`) → nếu `round` đang dở thì phát lại trạng thái của nó rồi `end-round` → chờ → `play` (trừ tiền; `round.state` = events) → vẽ → **`end-round` chỉ khi `payoutMultiplier > 0`** (vòng thua tự đóng) → cập nhật balance.

- **Mức cược:** cho chọn mọi giá trị trong `betLevels` (gồm min và max). `defaultBetLevel` là **số tiền** (ví dụ 1000000), không phải chỉ số. Lưu mức đã chọn theo tiền tệ (`localStorage` trong try/catch) để tải lại giữa lúc quay không mất. Chi phí thật = amount × cost của mode; luôn hiện ra.
- **Mã lỗi (400):** `ERR_VAL` yêu cầu sai, `ERR_IPB` thiếu số dư, `ERR_IS` phiên sai hoặc hết hạn, `ERR_ATE` xác thực lỗi hoặc token hết hạn, `ERR_GLE` vượt giới hạn cược, `ERR_LOC` vị trí không hợp lệ. (500): `ERR_GEN`, `ERR_MAINTENANCE`. Mỗi mã có thông điệp rõ ràng; ở social dùng từ social ("Not enough coins").
- **Hiển thị tiền:** amount / 1e6 theo số lẻ của tiền tệ: USD, EUR 2; JPY 0; XGC "10.00 GC"; XSC "10.00 SC" (không `$`).
- **Replay** (`replay=true`): bỏ qua authenticate và balance; tự gọi `GET {rgs_url}/bet/replay/{game}/{version}/{mode}/{event}` → `{payoutMultiplier, costMultiplier, state}`; hiện "Play", chạy vòng với đủ hoạt hình và âm thanh, rồi "Play again"; giữ số thắng cuối trên màn hình; **ẩn** balance, nút cược, chọn cược, autoplay; **hiện** số thắng, mức cược (`amount`), tiền tệ và chi phí thật có nhân mode ("BONUS 1 USD – 100 USD real cost"); tôn trọng `currency`, `lang`, `amount`, `social`.
- **Disclaimer** (mẫu chính thức, đặt ở màn luật chơi hoặc thông tin, luôn mở được): "Malfunction voids all wins and plays. A consistent internet connection is required. In the event of a disconnection, reload the game to finish any uncompleted rounds. The expected return is calculated over many plays. The game display is not representative of any physical device and is for illustrative purposes only. Winnings are settled according to the amount received from the Remote Game Server and not from events within the web browser. TM and © 2025 Stake Engine." Phải đủ 7 ý: malfunction, cần kết nối, tải lại để hoàn tất vòng, kỳ vọng tính trên nhiều ván, hiển thị chỉ minh họa, tiền thắng theo RGS, bản quyền.
- **Event chuẩn của book:** `reveal` (board, paddingPositions, gameType, anticipation), `winInfo`, `setWin` (amount, winLevel), `setTotalWin`, `freeSpinTrigger`, `freeSpinRetrigger`, `enterBonus`, `updateFreeSpin`, `tumbleBoard`, `setTumbleWin`, `updateTumbleWin`, `updateGlobalMult`, `freeSpinEnd`, `wincap`, `finalWin`. Số tiền ×100 của cược gốc. Mỗi event riêng cần một handler; giữ book gọn.
- Một handler async cho mỗi `type`, `await` theo thứ tự; type lạ ghi log ở dev rồi bỏ qua.

## Phụ lục B. Quy tắc Pixi 8 hay sai (§12, bản kiểm tra 8.22.0, tháng 11/2026)

Kiểm phiên bản hiện tại bằng `npm view pixi.js version`. Sau khi cài, đọc `node_modules/pixi.js/skills/pixijs/SKILL.md` (từ bản 8.19). Mẫu v7 (`beginFill`, `@pixi/*`, `app.view`, `BaseTexture`, truyền option vào constructor) **đều sai ở v8**.

```ts
import { Application, Assets, Container, Sprite, BitmapText } from 'pixi.js';
const app = new Application();
await app.init({ resizeTo: hostEl, background: '#000', antialias: true, autoDensity: true,
                 resolution: Math.min(window.devicePixelRatio, 2), preference: 'webgl' });
hostEl.appendChild(app.canvas);          // app.canvas, không phải app.view
```

- Gốc import duy nhất: `from 'pixi.js'`. Đồ họa: `new Graphics().rect(...).fill(...)` (vẽ hình rồi mới fill).
- `await app.init(...)` là bất đồng bộ; `resizeTo` trỏ vào container của game, không phải `window` (popout và mini-player thay đổi cỡ mà không có resize cửa sổ).
- Nạp bằng `Assets` + manifest có bundle (`boot`, `base`, `bonus`) và đường dẫn tương đối; `Assets.backgroundLoadBundle('bonus')` tải nền trong lúc người chơi quay. Không dùng `Texture.from(url)`.
- Atlas cho symbol và UI; `.webp` kèm `.png` dự phòng.
- Chữ đổi liên tục (bộ đếm thắng, balance, bet) dùng `BitmapText`; `Text` chỉ cho nhãn tĩnh. `SplitText` cho tiêu đề từng tầng thắng. Font là file nhúng, không CDN.
- `isRenderGroup: true` cho lớp lớn di chuyển nguyên khối (nền, vùng reel, HUD); `cacheAsTexture(true)` cho cây tĩnh phức tạp, gọi `cacheAsTexture(false)` trước khi hủy.
- Hạt (xu, tia lửa): `ParticleContainer` + `Particle` (`addParticle`, `particleChildren`).
- Filter (glow, blur, displacement) đắt trên điện thoại: áp vào container nhỏ, trong thời gian ngắn, `filterArea` và `padding` chặt.
- **`MeshRope` bỏ qua `width`**: nét dày bằng chiều cao texture (Pixi 8.22, đã làm Inkblade tốn 3 đến 4 vòng sửa). Muốn mỏng hơn, co `scale.x` quanh đường kẻ.
- Pixi 8.22: nhấn Tab bật lại lớp accessibility theo mặc định; thử phím cách vẫn quay và focus không kẹt trên nút ẩn; tắt bằng `accessibilityOptions.activateOnTab: false` nếu cần.
- Pixi 8.21: `Matrix.decompose()` và các hàm liên quan trả rotation thật, skew 0, `scale.x` âm cho vật bị lật; kiểm lại tween đọc các giá trị này (symbol lật).

**§12.3 Kiến trúc slot:**

```
stage
├─ bgLayer         (isRenderGroup)  nền, parallax, hạt môi trường
├─ boardLayer      (isRenderGroup)  khung reel + mask + reel
│   └─ Reel[]      Container chứa dải SymbolView (hàng nhìn thấy + 1 đến 2 hàng đệm)
├─ fxLayer                          đường thắng, viền cụm, ParticleContainer
├─ celebrationLayer                 màn Big Win trở lên, popup feature, bonus summary
└─ hudLayer        (hoặc lớp HTML)  spin, bet, balance, win, menu
```

- **Reel:** mỗi reel cuộn một dải `SymbolView` lấy từ pool, trong mask. Quay = tăng tốc → tốc độ đều → rơi vào `reveal.board[reel]` + `paddingPositions` → nảy rồi ổn định. Dừng lệch nhau 120 đến 200 ms; làm chậm reel sau khi `anticipation[reel] > 0`. **Bàn cuối luôn lấy từ book**, không bao giờ để symbol ngẫu nhiên quyết định gì.
- **Symbol:** một class `SymbolView` có trạng thái `idle | spin | land | win | dim`; dùng pool, không tạo hay hủy trong lúc quay.
- **Tumble:** xóa ô thắng (nổ), thả ô còn lại có gia tốc, tạo ô mới từ trên xuống theo `tumbleBoard`; `await` từng bước trước event kế.
- **Thời gian:** GSAP timeline hoặc `app.ticker` (`deltaMS`); turbo = `timeline.timeScale(n)`; mọi handler được `await` để live, resume và replay hành xử giống nhau.
- **Bố cục:** tính trong không gian thiết kế (1920×1080 ngang, 1080×1920 dọc), co hoặc letterbox theo cỡ host; chọn bố cục theo tỉ lệ khung hình hoặc `device=mobile`.
- **Ngân sách hiệu năng (điện thoại tầm trung, 60 fps):** < ~100 draw call ở cảnh nặng nhất; atlas ≤ 2048 đến 4096 px; tổng texture GPU lý tưởng < ~150 MB; `Assets.unloadBundle('bonus')` khi không cần; khởi động nóng mọi trạng thái symbol, filter và asset celebration một lần lúc loading; tạm dừng render khi tab ẩn (`visibilitychange`); thử mất context WebGL.
- **Tuân thủ Stake:** không CDN, font nhúng, đường dẫn tương đối; mọi hình phải khớp book.
- **Three.js** chỉ dùng khi game thật sự 3D; slot 5×3 phẳng thì Pixi nhẹ hơn. Book điều khiển cảnh, vật lý không bao giờ quyết định kết quả. Chi tiết: `references/threejs/casino-3d.md` nếu có.

## Phụ lục C. Bet UI (§13)

**Mặc định: bộ Bet UI chung của studio.** Chỉ theo theme của game khi bản theo theme **thật sự đẹp** và chủ dự án duyệt (Inkblade giữ HUD theo theme vì reviewer chưa chê, nhưng đó là ngoại lệ có quyết định). Dựng HUD dưới dạng **skin CSS trên cùng một markup** để đổi giữa bộ chung và bản theo theme không tốn công. Quyết định ghi vào handoff.

**§13.0 Đơn giản trước** (hướng dẫn rút ra từ 4 studio, không phải luật Stake):
- Khoảng 5 đến 8 phần tử cố định (spin, bet, balance, win, autoplay, menu, tối đa một trong turbo hoặc nút mode). Còn lại vào menu.
- Một nút duy nhất nổi bật: SPIN. Giá trị là chữ trên panel phẳng, không khung kim loại. Một bo góc, một kiểu icon, một màu nhấn cho spin và một cho feature.
- Yên lặng lúc nghỉ: không hoạt hình lặp trên HUD; chuyển động chỉ khi đổi trạng thái.
- Kiểm tra: che bàn chơi, người mới có gọi tên được từng nút trong 2 giây không.

**Số đo (16:9 ngang, H = chiều cao viewport)**
- Thứ tự trái sang phải: menu → balance → win → bet → spin → mode/feature. Bet sát spin.
- Dock: cao 9 đến 12% H, cách đáy 2 đến 3% H, rộng ≤ ~70% W, ở giữa; không che hàng cuối của bàn. Panel đen 70 đến 85% độ đục, bo góc 6 đến 10 px.
- Spin: đường kính 1.3 đến 1.6 lần dock (14 đến 17% H), đè lên mép trên dock; có trạng thái đang quay rõ ràng, có thể thành nút bỏ qua.
- Nút phụ: 0.5 đến 0.65 lần spin; vùng chạm ≥ 44 px CSS (riêng popout 400×225, nút ≥ 36 px).
- Nhãn chữ hoa 1.6 đến 2% H, giá trị 2.6 đến 3.2% H, số có độ rộng cố định, tiền tệ theo quy tắc từng loại. Ô win luôn chiếm chỗ cả khi bằng 0.
- Chọn mức cược: bảng chọn có **mọi** mức từ RGS gồm min và max.
- Turbo: biểu tượng tia chớp, bật/tắt rõ ràng. Autoplay: mở bảng chọn số vòng, có nút xác nhận, **không bao giờ bắt đầu ở lần nhấn đầu**. Mode giá > 2x: hộp xác nhận. Nút mua bonus ghi theo social khi `social=true`.

**Responsive**
- Desktop và laptop: bàn ở giữa (~53% rộng, 83% cao); mascot đứng một bên (~20% rộng), meter feature ở bên kia; logo phía trên; dock ở 83 đến 96% chiều cao.
- Popout L/S (800×450, 400×225): dock rút gọn (giá trị bỏ nhãn, gộp balance và win, nút phụ vào menu); spin ≥ 44 px; bàn giữ ≥ ~65% chiều cao.
- Mobile dọc: bàn rộng hết ngang, nằm ngay dưới vùng hero (16 đến 25% chiều cao, mascot nhô lên mép bàn); meter ngay dưới bàn; dải cảnh 11 đến 13% với hai nút nổi; HUD ghim đáy: hàng nút (menu, bet −, spin ~18% rộng, bet +, autoplay) ở 88 đến 94%, chân trang 3 giá trị ở 95 đến 100%. Không để dải tối trống: tổng dải chết trên 26% là trông chưa xong (`scripts/mobile_layout.py report`). Thử 360×800, 375×667, 390×844, 412×915 và điện thoại ngang.
- Mobile ngang: rail hai bên (spin giữa phải, cài đặt bên trái).
- Quy tắc hình: chữ và icon trên art luôn có nền đỡ (panel, đĩa hoặc gradient); tương phản giá trị ≥ 4.5:1; disabled ~40% độ đục; nhãn dài (de, fi, ru) và giá trị dài ("¥150,000,000") phải thử.

## Phụ lục D. Win celebration (§8)

**§8.1 Quy tắc Stake quyết định hình dạng**
- Màn ăn mừng đầy đủ **chỉ từ Big Win trở lên** (`winLevel ≥ 5`, tức ≥ 5x cược trên thang `standard` của Math SDK). Thắng nhỏ hơn không có popup, banner hay mưa xu.
- Không có jackpot; tầng cao nhất là **Max Win** (wincap của mode).
- Số tiền hiện = payout của RGS (`payoutMultiplier × bet`), format theo tiền tệ; frontend không tự bịa hay sửa.
- Nhiều lần thắng trong một vòng: ô WIN trên HUD cập nhật dần tới tổng; mọi kết quả khác 0 đều hiện số thắng cuối rõ ràng.
- Turbo vẫn đọc được thắng, tổ hợp thắng và popup. Replay phát đúng như ván gốc.
- Social: dùng từ không bị cấm ("BIG WIN" được; "BONUS BUY", "BET", "PAID" thì không), GC/SC không `$`.

**§8.2 Tầng theo chi phí thật (bài học Inkblade)**

`winLevel` của book tính theo **cược gốc**, nên với mode mua bonus nó sẽ ăn mừng cả những lần lỗ (mua 100x, trúng 120x vẫn là "Legendary"). Vì vậy:
`tỉ lệ = payout (×cược) / chi phí thật của mode (cost)`; tầng chọn theo `tỉ lệ`:

| Tỉ lệ so với chi phí thật | Trình bày |
|---|---|
| < 1x | Trung tính: số trong ô WIN, ô thắng được đánh dấu, tối đa một tiếng nhẹ |
| 1x đến < 5x | Thắng thường: highlight vị trí thắng + đếm trong ô WIN. **Không** màn ăn mừng |
| 5x đến < 15x | **BIG WIN** |
| 15x đến < 30x | **MEGA WIN** |
| 30x đến < 50x | **EPIC WIN** |
| 50x đến wincap | **LEGENDARY** (cho phép đặt tên theo theme) |
| = wincap | **MAX WIN** |

Mode mua bonus: so với `amount × cost`, không so với cược gốc. Tổng thắng bonus dùng thang `endFeature` (rộng hơn, tới 2000x+); ánh xạ cùng cách. Nếu đổi ngưỡng, đổi ở `get_win_level` của Math SDK để math và frontend không lệch. Nếu dùng `winLevel` của book thì ghi rõ lý do và kiểm tra trường hợp mua bonus.

**§8.3 Màn cần làm:** highlight thắng (mỗi `winInfo`), đếm HUD (mỗi lần thắng), celebration Big trở lên (tầng nối nhau khi số vượt ngưỡng), popup feature trigger ("10 FREE SPINS"), bonus intro và chuyển cảnh, banner retrigger ("+5 SPINS"), banner meter/stage, bonus summary (TOTAL WIN, chờ người chơi; nếu ≥ Big thì nối vào celebration), Max Win (dài nhất, vòng kết thúc ở wincap), hộp thoại hệ thống (cược, autoplay, lỗi).

**§8.4 Hành vi:** thời lượng tăng theo tầng (~2 đến 3 s Big, ~8 đến 12 s Max Win); luôn **bỏ qua được** (chạm đầu nhảy tới số cuối, chạm hai đóng); turbo rút ngắn nhưng giữ số cuối hiện ≥ ~1 s; số đếm dừng đúng ở payout, không vượt rồi sửa lại; autoplay vẫn chạy celebration (rút ngắn), Max Win có thể dừng autoplay; thử ở 400×225 và mobile dọc.

**§8.5 Nhịp vòng trong book event player** (đo trên một game tham chiếu, dùng làm cấu trúc, không dùng art của họ):
1. Clear: symbol rời bàn (~0.3 s), rồi một nhịp trống ~0.25 s.
2. Enter: các cột rơi vào cách nhau ~0.16 s, mỗi cột 0.25 đến 0.45 s; mỗi symbol chạy `land` (150 đến 300 ms, tự đặt).
3. Wild và Scatter hạ xuống thì có flash riêng (~0.8 s), không chỉ khi trả thưởng.
4. Highlight thắng: mỗi symbol thắng chạy `win` một lần ~0.65 s; hiện số thắng trên nhóm thắng cùng thời lượng; ô WIN cập nhật sau highlight (~0.85 s sau khi bắt đầu); nhiều lần thắng thì chạy nối tiếp, không chồng nhau.
5. Chỉ khi tầng ≥ Big mới có celebration, sau highlight và trước vòng sau.
Cả vòng ≈ 1.0 s (xét lại nếu > 1.4 s); turbo nhân thời lượng với ~0.5, giữ thứ tự. Bonus: bảng intro (chờ người chơi) → cùng nhịp vòng của base → bảng summary (chờ người chơi); chuyển cảnh dùng một ẩn dụ vật lý của theme, nhất quán.

## Phụ lục E. Ngôn ngữ và social mode

**Mã ngôn ngữ Stake:** `ar` `zh` `en` `fi` `fr` `de` `hi` `id` `ja` `ko` **`po` (Polish, không phải `pl`)** `pt` `ru` `es` `tr` `vi`. Mã lạ rơi về tiếng Anh không hỏng chữ. Khi `social=true` luôn dùng chuỗi tiếng Anh social.

**Quy trình**
1. **Không viết cứng chữ.** Mọi chuỗi ở `locales/<mã>`, khóa ổn định (`ui.spin`, `rules.freespins.trigger`, `win.tier.mega`), thêm `en-social` cho stake.us. Dùng ICU cho số nhiều: `{count, plural, one {# free spin} other {# free spins}}`.
2. Số (RTP, max win, giá, bảng trả) chèn từ config, không gõ tay.
3. Dịch có ngữ cảnh: mỗi khóa kèm màn hình, độ dài tối đa, giọng văn; bảng thuật ngữ cho từng ngôn ngữ (vi: Free Spins → "Vòng Quay Miễn Phí"; Wild/Scatter hay giữ tiếng Anh). Giữ tên symbol và tên game nhất quán.
4. Font nhúng cho từng chữ viết (Latin mở rộng gồm tiếng Việt, Cyrillic, Ả Rập, Devanagari, CJK), cắt tập con theo ngôn ngữ, chạy lại việc dựng font mỗi khi sửa chữ của ar/hi/ja/ko/zh. Font số thắng chỉ cần chữ số và ký hiệu tiền.
5. Bố cục: chừa ~30 đến 40% giãn chữ (de, fi, ru, pt); **tiếng Ả Rập từ phải sang trái** cho HUD và bảng chữ (bàn quay vẫn trái sang phải); dòng cao hơn cho CJK; không chữ nằm trong ảnh (nếu bắt buộc, mỗi ngôn ngữ một ảnh).
6. Ngôn ngữ giả `qps` (kéo dài và thêm dấu mọi chuỗi) để lộ chữ viết cứng hoặc bị cắt; chụp mọi màn × ngôn ngữ × cỡ.
7. Ít chữ trên màn chơi: luật nằm trong Menu; không dòng mẹo ở loading; không dòng luật ở bảng intro.
8. **Cần người bản ngữ** đọc lại 15 ngôn ngữ ngoài tiếng Anh trước khi nộp.

**Social mode (stake.us, `social=true`):** áp cho luật chơi, nhãn, popup, lỗi, cửa sổ replay và **ảnh** (không bake chữ "BUY"/"BET" vào art).

| Cấm | Thay bằng | Cấm | Thay bằng |
|---|---|---|---|
| bet, bets, betting | play, plays, playing | pay, pays, pays out | win, wins, win |
| total bet | total play | paid, paid out | won |
| bonus buy | bonus / feature | pay table | win table |
| buy bonus | get bonus | payer | winner |
| buy, purchase | play | stake | play amount |
| bought | instantly triggered | wager, gamble | play |
| cash, money, credit | coins | cost of | can be played for |
| currency | token | at the cost of | for |
| deposit | get coins | profit | net gain |
| withdraw | redeem | rebet | respin |
| loss limit | stop limit | loss streak | miss streak |
| place your bets | come and play | win feature | play feature |
| be awarded to player's accounts | appear in player's accounts | | |

Kiểm: nút cược không ghi "Bet", ô cược không ghi "Bet amount", không có "AutoBET", nhãn mua bonus và hộp xác nhận không có buy/bet, thông báo thiếu tiền sạch, GC/SC không `$`. Quét nhanh: `scripts/check_social_terms.py <thư mục locales>` hoặc
`grep -rniwE "bet|bets|betting|buy|purchase|bought|cash|money|credit|pay|pays|paid|payout|wager|gamble|stake|deposit|withdraw|profit|rebet|autobet|paytable" src/locales/en-social*`
(cụm "Stake Engine" trong disclaimer là hợp lệ).

## Phụ lục F. Quy trình mascot

**Phạm vi:** skill chỉ chuẩn hóa **phần tạo ảnh**: pose concept, gen bộ phận riêng, ghép lên pose, gói giao animator. **Animator tự rig và làm animation bằng tay** (Spine hoặc chuỗi PNG); skill không dựng rig, không viết rig bằng code và không có đường tắt dựng bản nháp tự động. Hiệu ứng bằng code (mắt sáng, màu kiếm, hào quang) chỉ gắn lên các bone gắn hiệu ứng mà animator đặt.

**Vì sao quy trình này** (đã thử 6 hướng ở Inkblade, 5 hướng đầu thất bại):
1. Một tranh trên mesh skinning: ít chuyển động, xoay quá vài độ là rách.
2. Dãy khung từng hành động từ model ảnh: mỗi khung vẽ lại nhân vật (giáp, kiếm, ngón tay đổi).
3. Model video tạo khung trung gian: thường chỉ có ở gói trả phí.
4. HTML-to-video: chỉ render chuyển động đã có, không tạo nét vẽ.
5. Cắt tranh phẳng đã duyệt thành bộ phận: phần bị che (bắp tay dưới khăn, thân dưới tay, hakama sau kiếm) không có nét thật, vá bằng inpaint thành vệt nhòe và lộ lỗ khi khớp xoay.
6. **Gen riêng từng bộ phận, vẽ đủ cả phần bị che, cùng góc nhìn với pose đã duyệt, ghép lên pose.** Chọn hướng này.

**F.1 Pose gốc (bước 4):** 5 pose; chọn pose dùng được cho nhiều animation (xem Cổng QA 4); nền magenta #FF00FF; sửa giải phẫu ngay.

**F.2 Gen bộ phận (bước 6), dùng Figma `generate_image`**
- **Công cụ này không nhận ảnh tham chiếu**, nên nó không nhìn thấy pose đã duyệt. Hệ quả: mỗi prompt phải **lặp lại đủ mô tả nhân vật, trang phục và bảng màu** (đoạn mô tả khóa), và kể rõ góc nhìn ("three-quarter view, body turned toward the viewer's right"). Một tấm vẽ góc thẳng không ghép được lên pose 3/4. Dù đã lặp mô tả, vẫn có thể lệch màu và chi tiết (đen thành xanh tím than, giáp to hơn); so với concept sau mỗi lượt gen và gen lại tấm lệch.
- Mỗi tấm = một vùng cơ thể (3 đến 4 tấm): đầu; thân + khăn/áo choàng + dây lưng + tua; hai tay theo đoạn (bắp tay, cẳng tay, bàn tay; tay cầm vật giữ luôn vật); giáp; chân (hông, đùi/quần, ống chân, bàn chân). Yêu cầu kích thước 2048×1536 (model thường trả ~1280×960).
- Quy tắc prompt đã học bằng giá đắt:
  - "exploded view, each piece a separate cut-out, LARGE clear gaps, nothing touches";
  - "every piece drawn COMPLETE, including the areas hidden behind other pieces when assembled, rounded overlapping ends at the joints";
  - cùng góc nhìn với pose đã duyệt; lặp lại mô tả và bảng màu mỗi tấm, kèm "same scale, parts of one character about N px tall";
  - gọi tên giải phẫu bàn tay ("exactly five fingers: one thumb and four fingers");
  - "No text, no labels, no full-body figure. Flat solid pure magenta (#FF00FF) background".
- Tách nền magenta (ngưỡng + halo 2 px, khử màu viền) → tách theo thành phần liên thông → **đặt tên từng thành phần bằng bảng tra theo hộp bao**, không dựa vào thứ tự phát hiện.
- Kiểm hạn mức credit trước (gói miễn phí của dịch vụ ảnh cạn rất nhanh); lưu prompt và bản gen gốc.

**F.3 Ghép lên pose đã duyệt**
- Đặt từng bộ phận bằng bảng neo → đích **đo tay** (lật, điểm neo trong PNG bộ phận, đích trên canvas pose, xoay, tỉ lệ), thứ tự vẽ sau ra trước. Giữ toàn bộ trong **một script** để chạy lại là dựng lại pose và mọi layer. Khớp tự động (IoU) chỉ là điểm xuất phát: nó hay xoay bộ phận cứng quá mức, hãy khóa góc xoay (đầu, thân, hông ±12°).
- Sau mỗi lượt ghép, so cạnh nhau với concept (silhouette, tỉ lệ đầu/thân, độ rộng chân, góc vật cầm). **Sửa tỉ lệ trước khi giao**: tỉ lệ sai là thứ chủ dự án nhận ra đầu tiên.
- Xuất: pose ghép, layer full canvas (chồng lại ra đúng pose) và layer cắt sát kèm vị trí.

**F.4 Gói giao animator** (tự đủ, một thư mục zip, để ngoài git)

| File | Nội dung |
|---|---|
| `<tên>_parts.psd` | Một layer có tên cho mỗi bộ phận, đặt sẵn trong pose, thứ tự layer = thứ tự vẽ |
| `parts_png/` | PNG nền trong suốt từng bộ phận, cắt sát, tên giống tên layer |
| `parts_png_full_canvas/` | Mỗi PNG giữ nguyên cỡ canvas và đúng vị trí; chồng theo thứ tự ra pose |
| `parts_position.json` | Vị trí góc trên trái từng PNG (y hướng xuống) và thứ tự vẽ |
| `pose_goc.png` | Pose ghép sẵn để đối chiếu |
| `ANIMATION_LIST.md` | Danh sách animation, yêu cầu kỹ thuật, bone gắn hiệu ứng, thứ tự ưu tiên (mẫu dưới) |

Tên bộ phận: tiền tố nhóm + bộ phận, trái/phải tính theo phía **người xem** (`arm_sword_upper`, `arm_free_hand`, `legs_shin_L`), hoặc theo ngôn ngữ chủ dự án chọn. Vật cầm vẽ liền với nắm tay; nếu cần tách để xoay riêng, báo trước để vẽ thêm.

**F.5 Mẫu danh sách 11 animation** (tên là API giữa game và animator; thời lượng ở tốc độ thường, turbo do game tăng tốc bằng code)

| # | Tên | Lặp | Dài | Game gọi khi | Nội dung |
|---|---|---|---|---|---|
| 1 | `idle` | có | 4 đến 4.5 s | Mặc định ở game thường | Thở nhẹ, dồn trọng tâm rất nhẹ, vải luôn chuyển động; biên độ nhỏ, không giành sự chú ý của bàn |
| 2 | `glance` | không | ~2 s | Ngẫu nhiên mỗi 6 đến 12 s, track 1 chồng lên idle | Quay nhẹ ra ngược (anticipation), liếc về bàn, giữ, về |
| 3 | `spin` | không | 0.6 đến 0.7 s | Bấm quay | Khuỵu nhẹ rồi nhấc lên, siết vật cầm; rất nhỏ |
| 4 | `win_small` | không | ~1.3 s | Thắng nhỏ (tùy chọn) | Gật đầu, nhấc vật cầm, không nhảy |
| 5 | `win_big` | không | ~2 s | Big Win | Hạ người lấy đà, giơ vật cầm lên, giữ ~0.6 s, hạ |
| 6 | `win_huge` | không | ~2.4 s | Mega trở lên và khi trúng feature | Hành động đặc trưng đầy đủ (ví dụ chém), 2 đến 3 khung đòn, vải văng mạnh |
| 7 | `bonus_enter` | không | 1.2 đến 1.5 s | Vào free spins | Vào thế bonus; khung cuối trùng khung đầu `idle_bonus` |
| 8 | `idle_bonus` | có | ~3 s | Mặc định trong free spins | Giữ thế, thở nhanh hơn, vải bay mạnh hơn |
| 9 | `stage_up` | không | ~1.2 s | Meter lên stage | Gồng rồi về thế bonus; đầu và cuối đúng tư thế `idle_bonus` |
| 10 | `feature_max` (ví dụ `awaken`) | không | ~3 s | Trạng thái cao nhất của feature | Animation lớn nhất: lấy đà sâu, bật lên, giữ rung ~1 s, về thế bonus |
| 11 | `bonus_exit` | không | ~1 s | Hết free spins | Về thế đứng thường; khung cuối trùng khung đầu `idle` |

Dòng yêu cầu kỹ thuật để đưa vào `ANIMATION_LIST.md`:
- Định dạng: Spine JSON + atlas (cạnh ≤ 2048, premultiplied alpha) **hoặc** chuỗi PNG 30 fps nền trong suốt. Ghi rõ phiên bản Spine mà game dùng và kiểm giấy phép runtime (`@esotericsoftware/spine-pixi-v8`) trước khi đưa vào build.
- 30 fps; mọi animation lặp về đúng khung đầu; chân luôn chạm một mặt đất, trôi ngang ≤ ±20 px; kích thước hiển thị ghi rõ (ví dụ cao ~800 px bên trái bàn).
- **Bone gắn hiệu ứng** (game vẽ hiệu ứng lên đó, animator chỉ đặt đúng chỗ), tên cố định: `eye_glow`, `blade_base`, `blade_tip` (hoặc tương đương của vật cầm), `aura`. Đổi theo game, nhưng giữ tên nhất quán giữa animator và code.
- Vật lý hoặc follow-through cho vải, tua, vạt áo (physics constraint của Spine hoặc key tay).
- **Quy định Stake:** không có phản ứng buồn hay thất vọng khi thua; animation ăn mừng chỉ chạy khi game gọi, mascot **không** quyết định hay làm chậm kết quả; mọi animation cắt ngang được bất cứ lúc nào (bỏ qua, turbo) với mix về idle trong 0.15 đến 0.25 s.
- Thứ tự giao: (1) `idle`, `spin`, `win_big`, `win_huge`; (2) `bonus_enter`, `idle_bonus`, `stage_up`, `bonus_exit`; (3) `feature_max`, `glance`, `win_small`. Kèm file dự án, file xuất, và video xem trước từng animation.

**F.6 Nối vào game:** `reveal` → `glance` hoặc `spin`; `winInfo` theo tầng → `win_*`; trigger feature → `win_huge` rồi `bonus_enter`; meter lên stage → `stage_up`; trạng thái tối đa → `feature_max`; `freeSpinEnd` → `bonus_exit`. Reduced motion: giữ khung đầu của `idle`.

## Phụ lục G. Danh mục asset

Số lượng lấy theo Inkblade Ronin (bản build ~13 MB, tải lần đầu nhỏ hơn nhờ tải nền bonus).

| Nhóm | Cần có | Inkblade (tham khảo) |
|---|---|---|
| Symbol | Thấp, cao, wild, scatter; atlas @1x và @2x; trạng thái thắng | 10 symbol, 2 atlas |
| Nền | Base và bonus, @1x và @2x; texture hiệu ứng (sương, lá) | 4 ảnh nền + thư mục fx |
| Bàn chơi | Khung, lưới, hiệu ứng ô và đường thắng | Khung, cuộn tranh, nét quét mực |
| Mascot | PSD, bộ phận, 11 animation, vfx của mascot | 24 bộ phận (do animator) |
| Feature | Meter (khung, thanh, đá stage), banner từng stage, bảng intro và summary | 3 đá, 4 banner |
| Win celebration | 5 bảng tầng, hiệu ứng theo theme, font số | 5 bảng Big đến Max |
| HUD | Bộ chung hoặc skin CSS | HUD sơn mài + 2 skin CSS demo |
| Thương hiệu | Logo game, tile (2 tỉ lệ), cover 16:9, loading, logo studio | Logo, tile 2 tỉ lệ, cover |
| Âm thanh | 2 nhạc nền (base, bonus), sprite SFX khoảng 60 đến 70 âm, hai định dạng (webm + mp4) | 2 nhạc, 68 SFX |
| Chữ và font | File ngôn ngữ, font nhúng, bản social | 16 ngôn ngữ |

SFX chia nhóm: giao diện, quay và rơi, nổ và tumble, scatter tăng dần, nốt thắng tăng dần, meter và stage, feature vào ra, sting 5 tầng thắng, đếm số, xu.
Art tạo trên nền magenta, tách nền bằng script chạy lại được. **Một nguồn sự thật** cho mỗi thứ: rig và vị trí bộ phận một script, chữ ở `locales`, layout ở một file.

## Phụ lục H. Mẫu trang concept (§7)

Chiều sâu và giữ chân người chơi phải đến từ 5 thứ, vì mỗi vòng độc lập (không XP, bộ sưu tập, meter lưu, nhiệm vụ hay chuỗi): cơ chế nhiều tầng, bộ mode đa dạng, căng thẳng trong từng vòng, bản sắc mạnh (art, âm thanh, thế giới), khoảnh khắc đáng chia sẻ (link replay). Chi tiết: `references/concept-design.md` nếu có.

```markdown
# <Tên game>: trang concept
**Một câu:** <≤ 25 từ, nêu cơ chế lõi>
**Theme và thế giới:** <2 đến 3 câu>   **Lưới:** <6x5 / 5x3 / ...>   **Kiểu trả thưởng:** <lines / ways / cluster / scatter pays>
**Cơ chế lõi:** <tên, cách chạy, vì sao có bản sắc>
**Meter và stage:** | Stage | Điều kiện | Đổi gì (hệ số, chiều cao cột, màu, nhạc) |
**Mode ladder:** | id | Tên | Giá (×) | Mô tả | RTP mục tiêu | Wincap | Hit-rate mục tiêu |
**Nhịp cảm xúc một phiên:** bình thường → căng → bùng nổ (mỗi pha: thấy gì, nghe gì)
**Danh sách event của book:** | Event | Dữ liệu | Handler (hiển thị gì) | Âm thanh | Mascot |
**Kiểm tra stateless:** meter nào, sống bao lâu (phải trong một vòng); không jackpot, gamble, carry-over
**Kiểm tra trách nhiệm (có/không):** không ăn mừng khi người chơi lỗ; không ép mua bonus; không "suýt thắng" giả
**Sàng lọc quy định:** IP, thương hiệu Stake/Kick, nhân vật trẻ con, tên game đã tìm
**Quyết định:** animator (bằng tay) | Bet UI (bộ chung / theme) | dịch vụ ảnh và hạn mức
```

## Phụ lục I. Mẫu handoff

Cập nhật sau mỗi cổng (một file trong repo game, ví dụ `docs/HANDOFF.md`).

```markdown
# <Tên game>: bàn giao
Cập nhật: <ngày> · repo <owner/repo> · nhánh <nhánh> · bước hiện tại: <1..9>
## Game là gì (3 đến 5 dòng) + bảng mode (id, giá, RTP, wincap)
## Cổng QA
| Bước | Cổng | Kết luận | Ngày | Link báo cáo |
## Cách chạy: dev, build demo, build production, chạy math, các script kiểm (lệnh chính xác)
## Cấu trúc thư mục chính
## Quyết định của chủ dự án (giữ nguyên): ngôn ngữ trả lời, Bet UI, phạm vi chỉnh sửa, art, nộp bản tạm hay không
## Đã giao: link demo, gói frontend, gói math (chia zip), tile và cover, gói animator
## Bẫy đã gặp (để khỏi lặp lại)
## Việc còn mở (ưu tiên, ai làm, cần người hay không)
## Mẹo kiểm tra (cờ URL, lệnh chụp frame, đo tốc độ)
```

Các mục bắt buộc phải có: quyết định của chủ dự án (không được mất giữa các phiên), cách chạy lại mọi thứ, danh sách việc còn mở có đánh dấu "cần người".

## Phụ lục J. Mẫu báo cáo cổng QA

```markdown
## Cổng QA <số>: <tên bước>
Ngày: <…> · Người chấm: agent · Người duyệt: <agent tự kiểm | chủ dự án> · **Kết luận: CHƯA ĐẠT** (đổi khi mọi dòng đạt)
| Tiêu chí | Đạt / Chưa | Bằng chứng |
|---|---|---|
| <tiêu chí đo được> | Chưa | <link ảnh, đường dẫn file, đoạn output lệnh, link demo> |
Việc cần người: <thiết bị thật, RGS thật, người bản ngữ, giấy phép> · Lỗi tìm thấy và bước sở hữu chúng: <…>
Đề nghị: <sang bước sau | quay lại bước N vì …>
```

**Quy tắc điền:** mọi dòng bắt đầu "Chưa". Chuyển sang "Đạt" chỉ khi bằng chứng đã đính kèm và mở được. Kết luận cổng chỉ đổi khi 100% dòng đạt (việc cần người chưa làm là dòng chưa đạt). Báo cáo gộp gửi chủ dự án gồm: bảng kết luận từng cổng, 3 ảnh tiêu biểu, danh sách lỗi đã sửa, câu hỏi cần quyết, và dòng "nói ngay nếu muốn đổi" cho những thứ khó đổi muộn (pose mascot, phong cách).

**Bảng chấm cho `casino-game-audit` và Stake (dùng ở bước 8 và 9):** item | ✅/❌/⚠️ | bằng chứng, trên các mục PreChecks (authenticate khi mở, `play` chạy, tên không trùng, asset phù hợp) · Thumbnail · Math (bảng mục 1) · RGS (mức cược, tải lại giữ mức cược, `rgs_url`) · Rules (bảng trả, RTP và max win từng mode, tổ hợp thắng, giá mode, điều kiện free spins, disclaimer) · Responsive (desktop, mobile, popout S/M) · Behaviour (xác nhận > 2x, xác nhận autoplay, tắt âm, phím cách, 10 ván thắng) · Stake.us (từ cấm, GC/SC) · Replay · Final. Tách blocker khỏi cải thiện chất lượng.
