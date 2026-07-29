# Day 04 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. Xong trước 16:30 để làm tài liệu phụ trợ khi demo.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. Có thể hoàn thiện sau buổi debate để nộp bài.

## Team

- Team:

| Role | Tên thành viên | Mã sinh viên |
|---|---|---|
| Eval | Hoàng Thanh Sơn | 2A202601818 |
| Tools | Vũ Bảo Chinh | 2A202601448 |
| System prompt | Trịnh Hoàng Nam | 2A202601376 |
| UI/UX | Đinh Hoàng Quân | 2A202602034 |

- Provider/model: OpenRouter / openai/gpt-4o-mini

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

**Research Paper Scout** hỗ trợ tìm bài báo khoa học trên arXiv theo chủ đề, đọc nội dung PDF của paper được chọn và tạo bản tóm tắt có nguồn. Agent cũng có thể sinh trích dẫn BibTeX từ arXiv ID/URL để người dùng chèn trực tiếp vào báo cáo LaTeX.

**Link dùng thử (truy cập được trong showdown):**

> UI chạy bằng Streamlit. Khi demo trực tiếp trên máy trình chiếu, dùng URL sau:
>
> URL: `http://localhost:8501`

## A2. Tool agent có

> Các tool chính trong workflow Research Paper Scout:

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| papers | tìm paper trên arXiv theo từ khóa/chủ đề | không |
| paper_text | tải PDF arXiv và trích text để đọc/tóm tắt paper | không |
| paper_bibtex | tạo trích dẫn BibTeX chuẩn từ arXiv ID hoặc URL | có |

## A3. Câu hỏi mẫu để thử

1. `Tìm 3 paper về thuật toán RRT.`
2. `So sánh RRT và RRT*.`
3. `Đọc paper arXiv 1706.03762 và tóm tắt phương pháp, kết quả chính trong 500 từ.`
4. `Cho tôi BibTeX chuẩn của paper 1706.03762 để chèn vào báo cáo LaTeX.`
5. `Tôi đang viết tổng quan về Transformer. Hãy tìm paper gốc, tóm tắt và tạo luôn BibTeX.`

## A4. Kịch bản demo đã rehearse

> Chuẩn bị 3–5 scenario. Mỗi scenario cần cho thấy tool đã làm gì và một thay đổi cụ thể giữa các version.

| Scenario | Tool trace cần thấy | Câu chuyện cải thiện version | Fallback run/transcript |
|---|---|---|---|
| Tìm 3 paper về RRT | `papers(query="RRT", max_results=3)` → `paper_text` | v0 là baseline; v1 cải thiện routing/tool declaration, đưa case accuracy base từ 65% lên 90%. | Transcript: `live_openrouter_20260729T161437109390.transcript.json` |
| Tổng quan Transformer + BibTeX | `papers` → `paper_text` → `paper_bibtex` | Bổ sung capability mới để tạo citation có thể dùng trực tiếp trong LaTeX. | Transcript: `live_openrouter_20260729T163020005491.transcript.json` |
| Workflow nhiều lượt: tìm → đọc → cite | `papers` → `paper_text` → `paper_bibtex` | Người dùng chuyển dần từ tìm paper sang đọc nội dung rồi tạo citation; agent sử dụng đúng tool theo ý định từng lượt. | Transcript: `live_openrouter_20260729T161558316542.transcript.json`, turns 6–8 |

---

# PHẦN B — Chi tiết / Bằng chứng

> Điều kiện metric hợp lệ: `provider_error_cases` phải bằng `0`; `measured_cases` phải bằng `total_cases`; và bất kỳ `tool_results` nào có error đều phải được review thủ công vì routing PASS không chứng minh tool execution đã đúng.

## B1. Version evidence

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run File |
|---|---|---|---|---:|---:|---|
| v0 (Son) | Baseline, chưa thay đổi artifact. | Đo hành vi chưa tối ưu trước khi sửa. | case_accuracy | – | 0.70 | `runs/v0_B_base_openrouter_20260729T151659721845.json` |
| v1 (Nam) | `system_prompt.md`: thay 4 instruction sai — không hỏi lại, tự đoán handle/URL, tự gửi và chỉ chọn một tool. | Boundary rõ ràng sẽ giảm đoán bừa, tự gửi, và cho phép gọi đủ tool cần thiết. | case_accuracy | 0.70 | 0.90 | `runs/v1_B_base_openrouter_20260729T160241896256.json` |
| v2 (Nam) | `tools.yaml`: mô tả rõ trigger cho `lookup`, `clarify`, `send`; thêm `topic=news` + `timeframe=day` cho “tin hôm nay”. | Tool declaration cụ thể sẽ sửa R03 và củng cố routing từ v1. | case_accuracy | 0.90 | 0.95 | `runs/v2_B_base_openrouter_20260729T161005670311.json` |
| v3 (Nam) | `system_prompt.md`: thêm rule tool switching khi user nói bỏ một nguồn/tool. | Không được gọi lại tool đã bị user loại bỏ dù rule parallel tool calls đang active. | case_accuracy | 0.95 | 0.95 | `runs/v3_B_base_openrouter_20260729T164727139562.json` |
| v4 (Son, validation bổ sung) | `system_prompt.md`: confirmation `yes_no` là bước đầu tiên của mọi send request. | Không dùng `clarify(response_type=text)` thay cho confirmation; sửa R12 và đạt 20/20. | case_accuracy | 0.95 | 1.00 | `runs/v4_B_base_openrouter_20260729T165210400392.json` |

Các run trên đều có `provider_error_cases = 0` và `measured_cases = total_cases`. Có một run v0 lỗi do thiếu `OPENROUTER_API_KEY` (`v0_B_base_openrouter_20260729T145712343559.json`, 0/20 measured); run này không được dùng để so sánh metric.

## B2. Failure analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R08_out_of_scope | out_of_scope | `send` | Câu hỏi tích phân phải không gọi tool nhưng agent gọi `send`. | v1: từ chối ngắn gọn câu ngoài phạm vi, không gọi tool. |
| R10_missing_handle | missing_info | `timeline(screenname="sama")` | Thiếu tài khoản nhưng agent tự đoán handle thay vì hỏi lại. | v1/v2: `clarify(response_type=text)` khi thiếu handle. |
| R11_missing_url | missing_info | `fetch(url="https://example.com/article")` | Không có URL nhưng agent tự đoán link. | v1/v2: hỏi URL bằng `clarify`, không đoán URL. |
| R12_confirm_before_send | wrong_boundary | `send` ở v0; `clarify(response_type=text)` ở v3 | Boundary gửi chưa đúng: v0 tự gửi, v3 hỏi sai kiểu xác nhận. | v4: bắt buộc `clarify(response_type=yes_no)` là bước đầu tiên. |
| R13_parallel_web_and_tweets | wrong_tool | `lookup(query="AI news")`, `social_search(query="AI")` | `lookup` sai query và thiếu `topic="news"`. | v2: mô tả rõ `topic=news`, `timeframe=day` cho "tin hôm nay". |
| M06_switch_tool | wrong_tool | Thừa `social_search` | User đã nói bỏ Twitter nhưng agent vẫn giữ social search. | v3: bổ sung rule tool switching. |

## B3. Team eval cases

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_search_papers_arxiv | Tìm paper theo chủ đề LLM Agent. | `papers(query="LLM Agent")` | PASS |
| G02_read_paper_text | Đọc paper từ arXiv ID. | `paper_text(arxiv_url="1706.03762")` | PASS |
| G03_get_paper_bibtex | Sinh citation từ URL arXiv. | `paper_bibtex(arxiv_url="https://arxiv.org/abs/2303.08774")` | PASS |
| G04_missing_paper_id_clarify | Thiếu ID/URL khi xin BibTeX. | `clarify(response_type="text")` | PASS |
| G05_out_of_scope_math | Câu toán học ngoài phạm vi. | Không gọi tool. | PASS |
| G06_search_then_get_bibtex | Chuyển intent từ tìm paper sang lấy BibTeX ở lượt sau. | `paper_bibtex(arxiv_url="1706.03762")` | PASS |
| G07_carryover_max_pages | Kế thừa URL và cập nhật số trang đọc. | `paper_text(..., max_pages=10)` | PASS |
| G08_clarify_then_read_paper | User bổ sung arXiv ID ở lượt sau. | `paper_text(arxiv_url="2203.02155")` | PASS |
| G09_confirm_before_send_bibtex | Đăng citation lên Telegram. | `clarify(response_type="yes_no")` | PASS |
| G10_multi_no_tool_chat | Câu cảm ơn/câu hỏi meta trong multi-turn. | Không gọi tool. | PASS |

Kết quả suite group: `case_accuracy = 1.00`, `tool_routing_accuracy = 1.00`, `argument_accuracy = 1.00`, `multiturn_accuracy = 1.00`, `provider_error_cases = 0`. Evidence: `runs/v2_B_group_openrouter_20260729T164912969780.json`.

## B4. Live chat evidence

| Scenario/Turn | Version | Tool Calls + Args | Transcript/Run | Outcome |
|---|---|---|---|---|
| Tìm 3 paper về RRT | live | `papers(query="RRT", max_results=3)` | `transcripts/live_openrouter_20260729T161437109390.transcript.json`, turn 1 | Trả về 3 paper RRT, không có tool error. |
| Chọn và tóm tắt một paper RRT | live | `paper_text(arxiv_url=...)` | `transcripts/live_openrouter_20260729T161437109390.transcript.json`, turn 2 | Đọc text PDF của paper được chọn, không có tool error. |
| Tổng quan Transformer + citation | live | `papers` → `paper_text` → `paper_bibtex` | `transcripts/live_openrouter_20260729T163020005491.transcript.json`, turn 1 | Hoàn tất tìm paper, tóm tắt và trả BibTeX trong một yêu cầu. |
| BibTeX theo arXiv ID | live | `paper_bibtex(arxiv_url="1706.03762")` | `transcripts/live_openrouter_20260729T161558316542.transcript.json`, turn 8 | Sinh citation BibTeX, không có tool error. |

## B5. Tool capability evidence

Phân loại rõ tool mới bắt buộc, optional built-in và tool đủ điều kiện bonus. Chỉ ghi Telegram/PDF nếu nhóm thực sự dùng; base report không cần chúng.

UI is core deliverable, not bonus. Do not list it here.

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: tool mới đầu tiên — `paper_bibtex` | `tools/paper_bibtex/tool.py`, `tools/paper_bibtex/TOOL.md`, `tools/__init__.py`, `artifacts/tools.yaml`; transcript turn 8: `live_openrouter_20260729T161558316542.transcript.json` | Nhận arXiv ID/URL, lấy metadata arXiv và tạo `@article{...}` gồm title, authors, year, URL. | Validate arXiv ID/URL; xử lý lỗi API/không tìm thấy paper qua response `error`. |
| Optional built-in — `papers`, `paper_text` | `tools/papers/tool.py`, `tools/paper_text/tool.py`; transcript `live_openrouter_20260729T161437109390.transcript.json` | Tìm paper arXiv và đọc nội dung PDF của paper đã chọn. | arXiv có rate limit; `paper_text` giới hạn số trang/ký tự để tránh output quá lớn. |
| Runtime error cần review | `transcripts/live_openrouter_20260729T161558316542.transcript.json`, turn 3 và 5; `live_openrouter_20260729T170519402823.transcript.json`, turn 1 | Trace UI và transcript giữ lại lỗi để review. | `lookup` có `RuntimeError`; một live run `papers` có `ReadTimeout`. Không dùng các lượt lỗi này làm evidence capability PASS. |

## B6. Reflection

- **Fix thuộc `system_prompt.md`:** quy tắc hỏi lại khi thiếu thông tin, confirmation boundary trước send, out-of-scope và tool switching phụ thuộc trạng thái hội thoại. Đây là các chính sách hành vi xuyên nhiều tool.
- **Fix thuộc `tools.yaml`:** mô tả trigger/argument cụ thể cho `lookup`, `clarify` và `send`. Mô tả tool tốt giúp model map đúng intent sang tool/args.
- **Lỗi cần review thủ công:** routing PASS không bảo đảm tool thực thi thành công. Transcript ghi nhận `lookup` có `RuntimeError` và `papers` có `ReadTimeout`; các lỗi API/network này phải tách khỏi lỗi routing.
- **Cải thiện tiếp theo:** giới hạn UI Paper Scout chỉ expose `papers`, `paper_text`, `paper_bibtex`; thêm guardrail để query mơ hồ như `A*` phải được làm rõ hoặc chuẩn hóa thành `A-star path planning`; chuẩn hóa output để luôn hiển thị đủ số paper user yêu cầu.
