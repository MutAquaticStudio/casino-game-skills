# Casino Game Skills

Bộ **Agent Skills** (định dạng `SKILL.md`) giúp Claude thiết kế, xây dựng, kiểm tra và nộp duyệt game casino/slot trên **Stake Engine** (Stake.com / Stake.us). Dùng được với Claude Code, Claude.ai và các agent đọc được `SKILL.md`.

| Skill | Dùng để |
|---|---|
| [`stake-casino-game-dev`](skills/stake-casino-game-dev/SKILL.md) | Quy trình đầy đủ: lên ý tưởng game có chiều sâu và nhiều mode, toán học (Math SDK, RTP, wincap), tích hợp RGS, frontend PixiJS/Three.js, win celebration chuẩn Stake, đa ngôn ngữ, replay, checklist nộp duyệt |
| [`casino-game-audit`](skills/casino-game-audit/SKILL.md) | Audit chất lượng: đồ hoạ, render, hiệu ứng, chuyển cảnh giữa các mode, giao diện cược, khoảng cách và font chữ, win celebration, âm thanh, đa ngôn ngữ. Chấm điểm và báo cáo lỗi theo thứ tự ưu tiên |
| [`casino-audio-design`](skills/casino-audio-design/SKILL.md) | Thiết kế và lập trình âm thanh: nhạc base/bonus, hiệu ứng guồng quay, nhạc cấp thắng, mixing, Howler/Web Audio, brief cho người làm nhạc, kiểm tra âm thanh |
| [`casino-symbol-art`](skills/casino-symbol-art/SKILL.md) | Tạo art 2D cho game slot: style guide, symbol (low/high pay, Wild, Scatter, Bonus, bài) dạng SVG nhiều layer, kiểm tra độ đọc được ở kích thước thật và popout, xuất spritesheet cho PixiJS v8, tách layer cho Spine, art win title/khung guồng/nền/icon, brief cho hoạ sĩ. Có ba hướng: SVG vẽ tay (kèm bộ hướng dẫn svg-design), art raster vẽ bằng code với hơn 80 phong cách (nền, màn win, symbol có texture), và **art tranh vẽ do mô hình tạo ảnh sinh từng lớp** (nền, nhân vật, khung, nền guồng, bộ symbol) rồi ghép bằng code, kèm nghiên cứu style Valkyrie Studio và Hacksaw Gaming |

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
Mở lại Claude Code. Gõ `/skills` để kiểm tra 4 skill đã hiện.

### Claude.ai (web / desktop / mobile)
1. Nén từng thư mục skill thành file zip, ví dụ `stake-casino-game-dev.zip` (bên trong có `SKILL.md`).
2. Vào **Settings → Capabilities → Skills → Upload skill**, chọn file zip.
3. Bật skill. Từ giờ Claude tự dùng skill khi bạn hỏi về game casino.

> Script Python và code mẫu TypeScript trong `stake-casino-game-dev` chỉ chạy được ở môi trường có terminal (Claude Code hoặc máy của bạn). Trên Claude.ai, skill vẫn có bản rút gọn của script ngay trong `SKILL.md`.

> Skill `casino-symbol-art` có kèm thư viện bên thứ ba (khoảng 7 MB, trong `references/vendor/`). Khi nén zip để upload lên Claude.ai, nhớ nén cả thư mục này.

### Công cụ cần cho script
```sh
pip install zstandard          # để đọc file books .jsonl.zst
pip install pillow numpy       # cho casino-symbol-art/scripts (svg_to_atlas.py, raster_cutout.py) và thư viện vẽ bằng code
# cùng một bộ render SVG: librsvg (lệnh rsvg-convert, vd: apt install librsvg2-bin / brew install librsvg)
# hoặc: pip install cairosvg
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
Skill có mục riêng cho **PixiJS 8.22** (bản mới nhất, kiểm tra tháng 11/2026): các mẫu code v8 đúng chuẩn, kiến trúc game slot (guồng quay, symbol Spine, tumble, các lớp hiển thị), ngân sách hiệu năng trên điện thoại, các thay đổi từ 8.16 đến 8.22 dễ gây lỗi, và bộ 26 skill PixiJS chính thức đi kèm. Mục riêng cho Three.js dành cho game 3D.

Phần **Bet UI / HUD** (mục 13) rút ra từ 4 game của 4 studio khác nhau: nguyên tắc đơn giản trước (khoảng 5–8 nút cố định, nút quay là yếu tố duy nhất nổi bật, giá trị chỉ là chữ trên nền phẳng, không khung trang trí), 3 kiểu bố cục (dải dưới đáy, cụm nút nổi, cột nút hai bên), thông số tỷ lệ theo chiều cao màn hình, quy tắc cho ante/mode/autoplay theo luật Stake, và các bản cho popout, điện thoại dọc và ngang.

```
Thiết kế Bet UI cho game này theo kiểu dải điều khiển dưới đáy, tối giản, có bản popout 400x225.
```
```
Guồng quay của tôi bị giật khi dừng và rớt FPS lúc Big Win trên điện thoại. Tối ưu theo PixiJS 8 mới nhất.
```
```
Nâng project Web SDK từ pixi.js 8.8.1 lên bản mới nhất, liệt kê những gì cần test lại.
```
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

## 6. Hướng dẫn dùng `casino-symbol-art`

Dùng khi cần **tạo art 2D** cho game: symbol, khung guồng, nền, win title, icon. Skill đi theo vòng: chốt style guide (`art/style.json`) → vẽ từng symbol (SVG nhiều layer, hoặc raster vẽ bằng code cho art có texture) → xem preview ở kích thước thật → xuất atlas cho PixiJS.

```
Tạo style guide và bộ symbol cho slot chủ đề thần thoại Việt: 5 low pay (bài 10–A),
5 high pay, Wild, Scatter, Bonus. Symbol hiển thị 140px trên màn hình.
```
```
Làm lại 3 symbol high pay này cho khác nhau hơn về hình dáng, kiểm tra ở kích thước popout 400x225.
```
```
Xuất bộ symbol này thành atlas cho Pixi, hỗ trợ màn retina, và viết SymbolView có đủ
trạng thái idle/spin/land/win/dim.
```
```
Tách layer symbol rồng để làm animation Spine cho vòng quay thắng lớn.
```
```
Viết brief cho hoạ sĩ vẽ tay bộ symbol này, kèm thông số kỹ thuật và tiêu chí đọc được.
```

**Ba hướng làm art:**
- **SVG** (mặc định): symbol, icon, khung, kiểu flat hoặc glossy casino. Phần khó (cung tròn, gradient, mask, filter, tối ưu SVGO mà không làm mất tên layer) có hướng dẫn trong `references/svg-craft.md`, dựa trên bộ [svg-design](https://github.com/tryopendata/skills) (plugin opendesign).
- **Raster vẽ bằng code**: nền, màn win, loading, key art, và symbol cao cấp có texture (mực, sơn dầu, màu nước, mosaic, kính màu, comic, pixel…). Dùng thư viện numpy + Pillow của [claude-drawing-skill](https://github.com/cloveric/claude-drawing-skill) với 82 phong cách. Xem `references/raster-art.md`.

- **Lớp tranh do mô hình tạo ảnh sinh** (chất lượng tranh vẽ kiểu studio slot lớn): mỗi lớp một lần gọi mô hình ảnh (nền, nhân vật, khung, nền guồng, bảng symbol), nền màu magenta phẳng để tách, rồi ghép bằng code. Chữ, huy hiệu hệ số, nút quay và thanh điều khiển vẽ bằng code. Chỉ dùng khi có công cụ tạo ảnh và bạn đồng ý chi phí (mỗi lớp là một lần gọi, tốn credit). Xem `references/style-valkyrie-hacksaw.md` (phần 6 là quy trình, phần 1–5 là nghiên cứu style).

```
Làm nền base game và nền bonus cho slot chủ đề Ai Cập cổ, kiểu tranh tường mộ cổ, giữ vùng giữa yên tĩnh cho guồng quay.
```
```
Vẽ symbol High 1 là mặt nạ vàng bằng sơn dầu, tách nền, rồi xuất atlas cùng các symbol SVG.
```

Ví dụ cho hướng tranh do mô hình sinh:
```
Làm bộ art tranh vẽ cho slot chủ đề thần thoại Việt theo cấu trúc studio lớn: nền nhiều lớp,
nhân vật lớn bên trái, khung rồng, nền guồng có hoa văn mờ và vạch chia cột, bộ symbol đầy đủ
(chữ bài A–10 mỗi hạng một màu, 8 premium trong huy hiệu tròn, Wild, Scatter, Bonus).
Hỏi tôi trước khi tốn credit tạo ảnh.
```

Script đi kèm (cần `pillow` và `rsvg-convert` hoặc `cairosvg`, xem mục 1):
```sh
python3 skills/casino-symbol-art/scripts/svg_to_atlas.py lint    art/svg      # file SVG an toàn cho Stake chưa
python3 skills/casino-symbol-art/scripts/svg_to_atlas.py preview art/svg --out art/preview.png --shrink 140
python3 skills/casino-symbol-art/scripts/svg_to_atlas.py layers  art/svg --out art/layers
python3 skills/casino-symbol-art/scripts/svg_to_atlas.py build   art/svg --out public/assets/symbols --size 160 --scales 1,2
```
- `lint`: báo URL ngoài, `<text>`, script, thiếu viewBox, trùng id gradient, canvas không đồng nhất.
- `preview`: bản full size trên nền caro và bản **kích thước thật trong guồng** trên nền tối. Luôn mở ảnh này ra xem, đừng chỉ tin code render được.
- `layers`: xuất mỗi `<g id>` cấp cao thành PNG cùng canvas, kèm `layers.json` ghi thứ tự xếp lớp, để đưa vào Spine.
- `build`: ra `symbols@1x/@2x.json + .png (hoặc .webp)` theo định dạng Pixi đọc thẳng, `meta.scale` khớp ảnh. Đã kiểm tra nạp được bằng PixiJS 8.22. `build` và `preview` nhận cả file PNG trong suốt đặt chung thư mục (SVG trùng tên thì SVG thắng).
- `compose_layered_screen.py` (cần `pillow`, `numpy`, `scipy`): ghép các lớp do mô hình sinh thành một màn slot: tách nền magenta bằng bộ lọc nghiêm ngặt, đặt nền guồng có hoa văn và vạch chia cột, xếp symbol, nhân vật, khung, thanh điều khiển vẽ bằng code. Là bản mẫu để sửa theo game của bạn, đọc `references/style-valkyrie-hacksaw.md` §6 trước.
- `art_harness.py`: nhận một file theme (nơi chốn, nhân vật, 8 vật thể premium, bảng màu) và sinh `art/style.json` cùng một prompt khoá cho từng lớp, đã mang sẵn cấu trúc studio lớn (preset `valkyrie` hoặc `hacksaw`). Chọn kiểu symbol premium bằng `premium_container`: `roundel` (huy hiệu tròn), `tile` (ô vuông bo góc) hoặc `freeform` (mỗi symbol là một vật thể tự do, không khung). Từ chối theme có tên hãng hay thương hiệu. Không gọi mô hình, không tốn credit.
- `references/layout-wireframes.md` (+ ảnh wireframe trong `references/examples/wireframes/` và spec đo được trong `references/examples/desktop_specs/`): wireframe **desktop** (mascot đứng ở một trong hai bên bàn chơi, 5 game bên trái, 3 game bên phải, bảng tính năng ở bên đối diện, board giữa màn hình khoảng 53% bề ngang và 83% chiều cao, dock điều khiển giống nhau ở đáy), bảng số đo 9 game, quy tắc, và bảng chuyển khối từ PC sang điện thoại (mascot thành nửa thân trên phía trên board, bảng tính năng xuống thanh ngang dưới board). Lệnh `mobile_layout.py wireframe` vẽ wireframe từ spec.
- `mobile_layout.py`, `mobile_capture.mjs` (trong `skills/stake-casino-game-dev/scripts/`) và `references/mobile-ui.md`: hướng dẫn giao diện **điện thoại dọc**. Chụp game ở nhiều cỡ điện thoại và PC (kèm nhật ký tải asset để so sánh), vẽ lưới 10% để đọc toạ độ, kiểm tra bố cục theo quy tắc (board full bề ngang, vùng hero phía trên với mascot đè mép board, bảng tính năng sát dưới board, dải cảnh 11–13% có nút nổi, HUD ghim đáy, dải trống tổng tối đa 26%), và tính bố cục khuyến nghị. Có bảng số đo của 5 game và ví dụ áp dụng cho game Inkblade Ronin. Kết quả quan trọng: game tham chiếu dùng **một bộ asset cho cả PC và điện thoại** (181 file, 32.5 MB, `device=mobile` không đổi danh sách), mọi khác biệt do code sắp xếp theo kích thước cửa sổ; mascot ở điện thoại chỉ lộ nửa thân trên phía trên khung board.
- `tile_check.py` và `references/tile-thumbnail.md`: kiểm tra tile (thumbnail) theo các mục đo được trong checklist Stake: độ sáng, viền và góc tối, trọng tâm có chi tiết, tiêu đề nằm trong lề an toàn. Harness thêm hai lớp tile tuỳ chọn (nền sáng và nhân vật tách nền). Kích thước và đường dẫn guideline thật chỉ có trong Tile Editor của dashboard, chưa được ghi ở đây.
- `symbol_fx.json`, `symbol_fx.mjs`, `symbol_fx_preview.py` và `references/symbol-fx.md`: công thức animation symbol bằng code (drop_in, land, win, win_loop, appear, tease, kèm dim và idle tuỳ chọn) dạng dữ liệu, bộ tính dùng được trong ticker PixiJS, script kiểm tra (vòng lặp khớp, về đúng vị trí nghỉ, bảo toàn thể tích, không che ô bên cạnh) và dựng video xem trước. Hình dạng `win`, nhịp stagger theo cột và độ dài một vòng lấy từ đo đạc một game tham chiếu; phần còn lại tự soạn. Chưa thử trong PixiJS.
- `anim_probe.py` và `references/animation-timing.md`: đo cách một game tham chiếu xử lý animation từ video quay demo công khai (trích khung, bảng khung hình, đọc số thắng bằng OCR, đo chu trình vòng chơi) và ghi lại nhịp, thứ tự, nguyên tắc để áp dụng bằng art của riêng mình, không sao chép style. Kết quả hiện có: một vòng chơi trung vị 1.00 giây (rơi ra, bảng trống, rơi vào từng cột cách nhau khoảng 0.16 giây), highlight thắng nhỏ khoảng 0.65 giây không làm tối symbol khác, luồng vòng thưởng với bảng giới thiệu và bảng TOTAL WIN chờ bấm. Mẫu nhỏ: một game, một phiên.
- `silhouette_check.py`: tô đen từng symbol ở kích thước thật và so độ trùng khít hình dáng (IoU) từng cặp. Dùng cho kiểu `freeform`: không cặp nào được vượt 0.80. Với huy hiệu tròn hoặc ô vuông thì điểm cao là bình thường vì cùng một đường viền.
- `style_check.py` (cần `pillow`, `numpy`, `scipy`): đo độ lệch phong cách của từng asset so với bộ gốc (khoảng cách tới bảng màu, độ sáng, độ bão hoà, tỷ lệ màu ấm, độ sáng viền, hướng sáng), so trong từng nhóm (symbol với symbol, nền với nền). WARN là cần xem lại, FAIL là sinh lại. Đã kiểm tra trên bản lệch cố ý: đổi tông màu bị FAIL, lật hướng sáng và tăng bão hoà bị WARN. Không thấy được hình dáng hay nét vẽ, nên vẫn phải xem contact sheet bằng mắt. Cách dùng và quy trình giữ nhất quán: `references/style-valkyrie-hacksaw.md` §7.
- `build_symbol_set.py`: cắt các bảng symbol do mô hình sinh (chữ bài, premium, đặc biệt), vẽ huy hiệu "x5" của Wild và nhãn "SCATTER" bằng code, xuất từng symbol PNG, ảnh tổng hợp và ảnh kiểm tra đọc được ở 96 px (màu và thang xám).
- `raster_cutout.py`: tách nền cho ảnh raster (màu key hoặc tự dò từ 4 góc, flood-fill từ viền nên màu giống nền nằm bên trong symbol vẫn giữ), làm mềm và khử viền, cắt và căn giữa vào ô vuông. Ví dụ: `python3 skills/casino-symbol-art/scripts/raster_cutout.py art/raw art/svg --cell 512 --key "#ff00ff"`.

**Chọn hướng nào:**

| Cần làm | Hướng | Đọc |
|---|---|---|
| Symbol, icon, khung, kiểu flat hoặc glossy casino | SVG | `SKILL.md` §3, `references/svg-craft.md` |
| Nền, màn win, loading, key art, art có texture | Raster vẽ bằng code | `references/raster-art.md` |
| Symbol cao cấp có texture (sơn dầu, mực…) | Raster: tấm trong suốt `sticker.Art` hoặc vẽ trên màu key rồi `raster_cutout.py` | `references/raster-art.md` §3 |
| Art tranh vẽ chất lượng studio (nền, nhân vật, khung, bộ symbol đầy đủ) | Lớp do mô hình tạo ảnh sinh, ghép bằng code (cần công cụ tạo ảnh và đồng ý chi phí) | `references/style-valkyrie-hacksaw.md` §6 |
| Art vẽ tay hoặc photoreal | Hoạ sĩ: skill viết brief, pipeline vẫn dùng cho preview và atlas | `references/symbol-design.md` §7 |

**Giữ phong cách nhất quán giữa nhiều lần gọi:** mô hình ảnh không nhớ phong cách giữa các lần gọi, và không có đường dùng ảnh tham chiếu (Figma `generate_image` không nhận ảnh tham chiếu, Weave cần liên kết tài khoản Figma trước). Vì vậy skill dùng: khối `style_lock` khoá cứng dán nguyên văn ở đầu mọi prompt, cùng một mô hình cho cả bộ, mỗi lần gọi một họ asset, sinh bộ neo trước, đo bằng `style_check.py`, sinh lại tối đa 3 lần rồi sửa bằng code. Lưu prompt cuối cùng vào `art/prompts/`.

Art cho win celebration: danh sách asset theo từng màn, quy tắc leo thang theo cấp (bằng tỷ lệ màu ấm và kích thước, không đổi style), đặt tên file và bàn giao nằm ở `references/win-celebration-art.md`. Đây là đặc tả, chưa sản xuất thử.

Lưu ý khi dùng hướng mô hình sinh: đã chạy thử trọn vẹn một lần (nền, nhân vật, khung, nền guồng, 16 symbol, ghép một màn). Chưa có: hoạt ảnh win celebration, tách layer nhân vật cho Spine. Phần style Hacksaw trong game dựa trên ảnh bìa và bài viết công khai, vì chưa chơi được bản demo của họ.

Lưu ý khi dùng raster: thư viện vẽ cả cảnh (một ảnh 1080p mất khoảng 10 giây trở lên), không phải công cụ vẽ icon; mỗi bộ symbol chỉ nên dùng một hướng và ghi vào `style.json` (`engine`, `seed`); không vẽ chữ vào nền hoặc title vì cần chữ thật cho đa ngôn ngữ; raster không tách layer cho Spine được. Cảnh ví dụ trong thư viện chỉ để học cách dùng, không dùng làm art cho game.

Luật Stake vẫn áp dụng: art phải độc quyền, không dùng nhân vật/thương hiệu có bản quyền, không dùng asset mẫu của Web SDK, bản build tĩnh không gọi font hoặc ảnh từ ngoài.

---

## 7. Quy trình gợi ý từ đầu đến cuối

Mỗi bước nhận đầu ra của bước trước và có một cổng kiểm tra trước khi sang bước sau. Bảng đầy đủ nằm ở mục "Workflow map" trong `skills/stake-casino-game-dev/SKILL.md`.

| Bước | Skill | Nhận | Tạo ra | Cổng kiểm tra |
|---|---|---|---|---|
| 1. Ý tưởng | `stake-casino-game-dev` (§7) | ý tưởng hoặc brief | tài liệu thiết kế: tầng cơ chế, bậc thang mode, danh sách event, chủ đề, lưới, RTP/wincap | qua kiểm tra luật (§2); mode đã chốt vì không thêm được sau duyệt |
| 2. Toán học | `stake-casino-game-dev` (Phase 2) | tài liệu thiết kế | game_config, books, lookup table, `winLevel` | `validate_math.py` sạch |
| 3. Art | `casino-symbol-art` | chủ đề, danh sách mode, kích thước symbol thật | `art/style.json` (có `style_lock`), `art/motion.json` (công thức animation), `art/fx/` (đĩa loé, vòng sáng, glint, bản "lit" của premium), atlas symbol, khung, nền guồng, nền, art win và chuyển cảnh | `style_check.py` không FAIL; test thu nhỏ và thang xám; art gốc |
| 4. Frontend | `stake-casino-game-dev` (Phase 3, §8.5) | books, atlas, `art/motion.json`, danh sách event | bản build tĩnh nối RGS, HUD, win celebration, đa ngôn ngữ; vòng chơi theo quy tắc nhịp §8.5 (xoá bảng, nhịp trống, từng cột rơi vào, highlight thắng, HUD cập nhật sau) | `check_static_build.py` sạch; mọi loại event đều có handler |
| 5. Âm thanh | `casino-audio-design` | danh sách event, bảng cấp win | file âm thanh + AudioManager | bảng event → âm thanh đầy đủ |
| 6. Kiểm thử tích hợp | `stake-casino-game-dev` (Phase 4) | bản build | kết quả test tiền tệ, mode, kích thước | 10 lần thắng mỗi mode khớp RGS |
| 7. Audit | `casino-game-audit` | build hoặc ảnh chụp | báo cáo chấm điểm | không còn lỗi chặn; mảng Graphics & art direction ≥ 4 |
| 8. Nộp duyệt | `stake-casino-game-dev` (Phase 5) | bản build đã audit | event ID replay, tile, hồ sơ nộp | checklist Stake đủ ✅ |

Nếu một bước phát hiện lỗi thuộc về bước trước (ví dụ cấp win thiếu art, symbol không đọc được ở popout), quay lại bước đó và chạy lại cổng của nó, không vá lỗi ở bước sau.

---

## 8. Luật Stake Engine quan trọng có sẵn trong skill
- Game không lưu trạng thái giữa các ván: **không jackpot, không gamble, không continuation, không early cashout**.
- RTP 90–98% mỗi mode, các mode chênh nhau ≤ 0.5%; max win phải trúng được (≥ 1/20 triệu).
- Frontend là file tĩnh, không gọi ra ngoài, lấy `rgs_url` từ URL, bắt buộc hỗ trợ replay.
- Phím space gắn với nút quay, autoplay và mode giá > 2x phải có bước xác nhận, phải có nút tắt tiếng.
- Stake.us (social mode) phải thay các từ liên quan cờ bạc (bet → play, buy → play, pay → win…).
- Sau khi được duyệt, không được sửa toán học hay thêm mode.

Tóm tắt từ tài liệu chính thức (https://stakeengine.github.io/docs/) vào tháng 11/2026. Với các luật quan trọng, hãy kiểm tra lại tài liệu mới nhất.

---

## 9. Cấu trúc repo
```
skills/
├── stake-casino-game-dev/
│   ├── SKILL.md                 quy trình 13 mục: ý tưởng, toán, frontend, win celebration, đa ngôn ngữ, PixiJS 8.22, Bet UI
│   ├── scripts/                 validate_math.py, check_social_terms.py, check_static_build.py
│   ├── assets/                  rgs-client.ts, book-player.ts
│   └── references/
│       ├── stake-engine/        overview, math-requirements, math-sdk, rgs-api, frontend-requirements, approval-checklist
│       ├── pixijs/vendor/       26 skill PixiJS chính thức (đổi SKILL.md thành GUIDE.md)
│       ├── threejs/             casino-3d.md + vendor/ (13 hướng dẫn Three.js)
│       └── gamedev/vendor/      11 hướng dẫn game dev (game-feel, audio, UI/UX, hiệu năng, shader…)
├── casino-game-audit/SKILL.md
├── casino-audio-design/SKILL.md
└── casino-symbol-art/
    ├── SKILL.md
    ├── scripts/                 svg_to_atlas.py (lint, preview, layers, build), raster_cutout.py,
    │                            compose_layered_screen.py, build_symbol_set.py, style_check.py,
    │                            art_harness.py, silhouette_check.py, tile_check.py,
    │                            symbol_fx.json, symbol_fx.mjs, symbol_fx_preview.py, anim_probe.py
    └── references/
        ├── symbol-design.md     style.json, palette, trạng thái symbol, asset khác, brief hoạ sĩ
        ├── export-and-pixi.md   atlas, tải trong Pixi v8, SymbolView, Spine
        ├── svg-craft.md         hướng SVG: chỗ nào đọc svg-design, chỗ nào ghi đè
        ├── raster-art.md        hướng raster: chọn phong cách, 2 cách làm symbol, ràng buộc
        ├── style-valkyrie-hacksaw.md  nghiên cứu style Valkyrie/Hacksaw, quy trình lớp do mô hình sinh, giao thức giữ nhất quán
        ├── win-celebration-art.md     asset art cho win celebration, quy tắc leo thang theo cấp, bàn giao
        ├── tile-thumbnail.md          tile (thumbnail) cho Tile Editor: các lớp, kiểm tra, giới hạn
        ├── symbol-fx.md               animation symbol bằng code: công thức, kiểm tra, trạng thái
        ├── animation-timing.md        nhịp và cấu trúc animation đo từ một game tham chiếu (vòng chơi, thắng, vòng thưởng)
        └── vendor/
            ├── svg-design/      hướng dẫn SVG (opendesign, MIT)
            └── claude-drawing/  thư viện vẽ bằng code: lib/ (83 module), examples/ (86 script), docs/ (MIT)
```

## 10. Nguồn và giấy phép
- Tài liệu và SDK của Stake Engine: https://github.com/StakeEngine (Math SDK dùng giấy phép MIT). Dự án này không liên kết với Stake hay Stake Engine.
- Skill PixiJS chính thức lấy từ gói npm `pixi.js@8.22.0` ([pixijs/pixijs](https://github.com/pixijs/pixijs)), giấy phép MIT, xem `references/pixijs/vendor/LICENSE`.
- Hướng dẫn Three.js lấy từ [CloudAI-X/threejs-skills](https://github.com/cloudai-x/threejs-skills), giấy phép MIT, xem `references/threejs/vendor/LICENSE`.
- Hướng dẫn SVG (`casino-symbol-art/references/vendor/svg-design`) lấy từ [tryopendata/skills](https://github.com/tryopendata/skills), plugin opendesign v1.3.2, giấy phép MIT, xem `LICENSE` trong thư mục đó.
- Thư viện vẽ bằng code (`casino-symbol-art/references/vendor/claude-drawing`: `lib/`, `examples/*.py`, tài liệu) lấy từ [cloveric/claude-drawing-skill](https://github.com/cloveric/claude-drawing-skill), giấy phép MIT, xem `LICENSE` trong thư mục đó. Không kèm ảnh render mẫu (151 MB). Xem `references/vendor/README.md` để biết đã đổi gì so với bản gốc.
- `casino-symbol-art/references/style-valkyrie-hacksaw.md` là ghi chép quan sát riêng từ các bản demo công khai (Valkyrie Studio) và ảnh bìa chính thức (Hacksaw Gaming), chỉ rút nguyên tắc và số đo, không sao chép nhân vật hay logo của họ. Dự án này không liên kết với Valkyrie Studio hay Hacksaw Gaming.
- Hướng dẫn game dev lấy từ [gamedev-skills/awesome-gamedev-agent-skills](https://github.com/gamedev-skills/awesome-gamedev-agent-skills), giấy phép Apache-2.0, xem `references/gamedev/vendor/LICENSE` và `NOTICE`.
