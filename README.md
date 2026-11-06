# Casino Game Skills

Bộ **Agent Skills** (định dạng `SKILL.md`) giúp Claude thiết kế, xây dựng, kiểm tra và nộp duyệt game casino/slot trên **Stake Engine** (Stake.com / Stake.us). Dùng được với Claude Code, Claude.ai và các agent đọc được `SKILL.md`.

| Skill | Dùng để |
|---|---|
| [`stake-casino-game-dev`](skills/stake-casino-game-dev/SKILL.md) | Quy trình đầy đủ: lên ý tưởng game có chiều sâu và nhiều mode, toán học (Math SDK, RTP, wincap), tích hợp RGS, frontend PixiJS/Three.js, win celebration chuẩn Stake, đa ngôn ngữ, replay, checklist nộp duyệt |
| [`casino-game-audit`](skills/casino-game-audit/SKILL.md) | Audit chất lượng: đồ hoạ, render, hiệu ứng, chuyển cảnh giữa các mode, giao diện cược, khoảng cách và font chữ, win celebration, âm thanh, đa ngôn ngữ. Chấm điểm và báo cáo lỗi theo thứ tự ưu tiên |
| [`casino-audio-design`](skills/casino-audio-design/SKILL.md) | Thiết kế và lập trình âm thanh: nhạc base/bonus, hiệu ứng guồng quay, nhạc cấp thắng, mixing, Howler/Web Audio, brief cho người làm nhạc, kiểm tra âm thanh |

---

## 1. Cài đặt

### Claude Code
```sh
git clone https://github.com/MutAquaticStudio/casino-game-skills.git
# Dùng cho mọi project:
cp -r casino-game-skills/skills/* ~/.claude/skills/
# Hoặc chỉ cho một project:
mkdir -p .claude/skills && cp -r casino-game-skills/skills/* .claude/skills/
```
Mở lại Claude Code. Gõ `/skills` để kiểm tra 3 skill đã hiện.

### Claude.ai (web / desktop / mobile)
1. Nén từng thư mục skill thành file zip, ví dụ `stake-casino-game-dev.zip` (bên trong có `SKILL.md`).
2. Vào **Settings → Capabilities → Skills → Upload skill**, chọn file zip.
3. Bật skill. Từ giờ Claude tự dùng skill khi bạn hỏi về game casino.

> Script Python và code mẫu TypeScript trong `stake-casino-game-dev` chỉ chạy được ở môi trường có terminal (Claude Code hoặc máy của bạn). Trên Claude.ai, skill vẫn có bản rút gọn của script ngay trong `SKILL.md`.

### Công cụ cần cho script
```sh
pip install zstandard          # để đọc file books .jsonl.zst
```

---

## 2. Cách skill được kích hoạt

Không cần gọi tên skill. Claude tự chọn skill khi câu hỏi khớp nội dung, ví dụ khi bạn nhắc đến *game slot, game nổ hũ, game casino, Stake Engine, RTP, bonus buy, free spins, paytable, audit game, âm thanh game*… Muốn chắc chắn, bạn gọi tên trực tiếp:

```
Dùng skill stake-casino-game-dev để …
/stake-casino-game-dev …        (Claude Code)
```

Skill trả lời bằng ngôn ngữ của bạn. Code, tên file và thuật ngữ Stake giữ tiếng Anh.

---

## 3. Hướng dẫn dùng `stake-casino-game-dev`

Skill đi theo 5 bước. Bạn có thể bắt đầu ở bất kỳ bước nào.

### Bước 1 – Lên ý tưởng (game có chiều sâu, nhiều mode)
Skill không dừng ở "quay → trúng line → hết". Mỗi ý tưởng phải có:
- **Nhiều tầng cơ chế tác động lẫn nhau** trong một lượt: cách trả thưởng gốc, các hiệu ứng biến đổi bàn quay, hệ số nhân, thanh tích lũy trong lượt, các nấc leo thang trong vòng thưởng.
- **Bậc thang chế độ chơi**: BASE, BOOST/ANTE, BONUS, SUPER BONUS. Mỗi chế độ là một trải nghiệm khác.
- **Đòn bẩy giữ chân người chơi một cách lành mạnh**, kèm danh sách những chiêu không được dùng.

Câu hỏi mẫu:
```
Lên 3 ý tưởng game slot chủ đề thần thoại Việt Nam, có nhiều mode, gameplay có chiều sâu.
Chấm điểm từng ý tưởng và chọn 1 để viết tài liệu thiết kế đầy đủ.
```
```
Ý tưởng của tôi: slot 6x5 cluster pays chủ đề đại dương. Kiểm tra xem có bị nông không
và đề xuất thêm tầng cơ chế, bậc thang mode.
```
Kết quả: tài liệu ý tưởng theo mẫu gồm các tầng cơ chế, chuỗi tác động, bảng mode, mục tiêu toán học, nhịp cảm xúc, danh sách sự kiện cần có và bước kiểm tra thiết kế có trách nhiệm.

### Bước 2 – Toán học (Math SDK)
```
Dựa trên tài liệu thiết kế, viết game_config.py và gamestate.py cho Math SDK,
mode base 1x và bonus 100x, RTP 96.5%, wincap 5000x.
```
```
RTP mode bonus của tôi là 97.4% còn base 96.2%. Sửa thế nào để lọt khoảng 0.5%?
```
Sau mỗi lần chạy mô phỏng, kiểm tra file trước khi upload:
```sh
python skills/stake-casino-game-dev/scripts/validate_math.py games/<game>/library/publish_files
python skills/stake-casino-game-dev/scripts/validate_math.py <dir> --json report.json   # xuất báo cáo
```
Script kiểm tra định dạng `index.json`, sự khớp giữa lookup table và books, RTP 90–98%, chênh lệch RTP giữa các mode ≤ 0.5%, tần suất max win (≥ 1/20 triệu), hit-rate, kết quả áp đảo, và khoảng trống trong dải tiền thắng.

### Bước 3 – Frontend
```
Dựng frontend PixiJS 8 + Svelte 5 cho game này, dùng rgs-client.ts và book-player.ts
trong skill, có xử lý replay và social mode.
```
```
Tôi muốn làm phiên bản 3D bằng Three.js với guồng quay hình trụ. Hướng dẫn cách
cho vừa màn hình popout 400x225 và chạy mượt trên điện thoại.
```
Code mẫu có sẵn:
- `assets/rgs-client.ts`: đọc tham số URL, gọi các API authenticate/play/end-round/replay, xử lý tiền dạng số nguyên, mã lỗi, lưu mức cược khi tải lại trang.
- `assets/book-player.ts`: phát lần lượt các sự kiện trong book. Dùng chung cho chơi thật, chơi tiếp sau khi tải lại và replay. Phím space gắn với nút quay.

### Win Celebration (Big Win, Mega Win…)
Theo luật Stake, **chỉ từ Big Win trở lên mới có bảng ăn mừng**. Win nhỏ hơn chỉ đánh dấu ô thắng và cho số chạy ở ô Win. Không có jackpot; cấp cao nhất là **Max Win**.

| winLevel (từ Math SDK) | Hiển thị |
|---|---|
| 1–2 (< mức cược) | Trung tính, không ăn mừng |
| 3–4 (1x–5x) | Đánh dấu ô thắng + số chạy ở ô Win |
| 5 | BIG WIN |
| 6 | MEGA WIN |
| 7 | EPIC WIN |
| 8–9 | LEGENDARY |
| 10 | MAX WIN |

```
Thiết kế toàn bộ hệ thống win celebration cho game: Big/Mega/Epic/Max Win, popup free spins,
retrigger, bảng tổng kết bonus. Liệt kê asset cần làm.
```

### Đa ngôn ngữ
```
Tách toàn bộ chữ trong game ra file ngôn ngữ, dịch sang tiếng Việt, Nhật, Bồ Đào Nha,
kèm bảng thuật ngữ, và tạo bản en-social cho Stake.us.
```
Skill nắm 16 mã ngôn ngữ của Stake (lưu ý **`po` là tiếng Ba Lan**, không phải `pl`), cách bundle font cho từng hệ chữ, tiếng Ả Rập viết từ phải sang trái, và test bằng pseudo-locale.

### Bước 4 – Kiểm thử tích hợp
```sh
python skills/stake-casino-game-dev/scripts/check_social_terms.py src/locales   # từ cấm trên Stake.us
python skills/stake-casino-game-dev/scripts/check_static_build.py dist          # request ra ngoài, RGS gắn cứng, đường dẫn tuyệt đối
```
```
Liệt kê các trường hợp cần test: tiền tệ, mức cược, social mode, replay, các kích thước màn hình.
```

### Bước 5 – Replay và nộp duyệt
```
Review game của tôi theo checklist duyệt của Stake Engine. Đây là repo / link build / ảnh chụp.
```
Kết quả: bảng **mục | ✅/❌/⚠️ | bằng chứng**, tách riêng lỗi chặn duyệt và phần nên cải thiện, kèm danh sách event ID cần chuẩn bị cho replay (thắng thường, thắng lớn, wincap, thua, kích hoạt bonus).

---

## 4. Hướng dẫn dùng `casino-game-audit`

Đưa cho Claude bằng chứng càng nhiều càng tốt: link build chạy được, thư mục `dist/`, mã nguồn, hoặc ảnh chụp/video các màn hình (lúc chờ, đang quay, thắng thường, từng cấp win, vào bonus, tổng kết bonus, các bảng xác nhận, trang luật chơi, giao diện điện thoại và popout).

```
Audit game của tôi: chất lượng đồ hoạ, render, hiệu ứng, chuyển cảnh giữa các mode,
UI cược, spacing và font chữ. Đây là 15 ảnh chụp và video gameplay.
```
```
Vì sao game của tôi nhìn rẻ tiền? Ưu tiên những gì sửa nhanh mà tăng điểm sao nhiều nhất.
```
```
Chỉ audit phần win celebration và âm thanh.
```
Báo cáo luôn có cấu trúc:
1. Bằng chứng đã xem và phần chưa kiểm tra được
2. Bảng điểm 0–5 cho 9 mảng, kèm ước lượng số sao Stake (0–3★)
3. Lỗi chặn duyệt: vấn đề, vị trí, cách sửa
4. Trau chuốt mang lại nhiều điểm nhất
5. Lỗi nhỏ, những gì đã làm tốt, kế hoạch sửa trong 1–2 tuần

---

## 5. Hướng dẫn dùng `casino-audio-design`

```
Lên định hướng âm thanh và danh sách file âm thanh cho game slot chủ đề Đông Á,
có nhạc base, nhạc bonus và nhạc cho từng cấp win.
```
```
Viết AudioManager bằng Howler.js: biến thể ngẫu nhiên cho tiếng dừng guồng,
duck nhạc khi Big Win, chuyển nhạc base sang bonus, nút tắt tiếng có lưu trạng thái.
```
```
Viết brief gửi người làm nhạc, kèm thông số file và bảng sự kiện → âm thanh.
```
```
Kiểm tra âm thanh trong build của tôi theo checklist.
```
Quy tắc chính: nhạc cấp thắng chỉ phát từ Big Win trở lên, độ lớn khoảng −16 đến −14 LUFS, không phát âm thanh trước lần chạm đầu tiên, tạm dừng khi chuyển tab, và mọi file âm thanh nằm trong bản build.

---

## 6. Quy trình gợi ý từ đầu đến cuối

```
1. stake-casino-game-dev  → 3 ý tưởng → chọn 1 → tài liệu thiết kế
2. stake-casino-game-dev  → code toán học → validate_math.py đạt yêu cầu
3. stake-casino-game-dev  → frontend + win celebration + đa ngôn ngữ
4. casino-audio-design    → định hướng, file âm thanh, AudioManager
5. casino-game-audit      → audit, sửa lỗi, audit lại
6. stake-casino-game-dev  → check_social_terms + check_static_build → checklist nộp duyệt
```

---

## 7. Luật Stake Engine quan trọng có sẵn trong skill
- Game không lưu trạng thái giữa các ván: **không jackpot, không gamble, không continuation, không early cashout**.
- RTP 90–98% mỗi mode, các mode chênh nhau ≤ 0.5%; max win phải trúng được (≥ 1/20 triệu).
- Frontend là file tĩnh, không gọi ra ngoài, lấy `rgs_url` từ URL, bắt buộc hỗ trợ replay.
- Phím space gắn với nút quay, autoplay và mode giá > 2x phải có bước xác nhận, phải có nút tắt tiếng.
- Stake.us (social mode) phải thay các từ liên quan cờ bạc (bet → play, buy → play, pay → win…).
- Sau khi được duyệt, không được sửa toán học hay thêm mode.

Tóm tắt từ tài liệu chính thức (https://stakeengine.github.io/docs/) vào tháng 11/2026. Với các luật quan trọng, hãy kiểm tra lại tài liệu mới nhất.

---

## 8. Cấu trúc repo
```
skills/
├── stake-casino-game-dev/
│   ├── SKILL.md
│   ├── scripts/        validate_math.py, check_social_terms.py, check_static_build.py
│   ├── assets/         rgs-client.ts, book-player.ts
│   └── references/     stake-engine/*.md, threejs/, gamedev/
├── casino-game-audit/SKILL.md
└── casino-audio-design/SKILL.md
```

## 9. Nguồn và giấy phép
- Tài liệu và SDK của Stake Engine: https://github.com/StakeEngine (Math SDK dùng giấy phép MIT). Dự án này không liên kết với Stake hay Stake Engine.
- Hướng dẫn Three.js lấy từ [CloudAI-X/threejs-skills](https://github.com/cloudai-x/threejs-skills), giấy phép MIT, xem `references/threejs/vendor/LICENSE`.
- Hướng dẫn game dev lấy từ [gamedev-skills/awesome-gamedev-agent-skills](https://github.com/gamedev-skills/awesome-gamedev-agent-skills), giấy phép Apache-2.0, xem `references/gamedev/vendor/LICENSE` và `NOTICE`.
