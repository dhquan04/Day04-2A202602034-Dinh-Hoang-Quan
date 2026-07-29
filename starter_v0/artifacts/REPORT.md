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
| So sánh RRT và RRT* | `lookup` + `papers` → `paper_text` | Showcase một yêu cầu nghiên cứu dùng nhiều nguồn/tool, không chỉ một lượt tìm kiếm. | Transcript: `live_openrouter_20260729T161226261182.transcript.json` |
| Tổng quan Transformer + BibTeX | `papers` → `paper_text` → `paper_bibtex` | Bổ sung capability mới để tạo citation có thể dùng trực tiếp trong LaTeX. | Transcript: `live_openrouter_20260729T163020005491.transcript.json` |
| Tìm paper tiếng Việt về Machine Learning | `papers` + `lookup` → `paper_text` → `paper_bibtex` | Cho thấy agent theo dõi ngữ cảnh nhiều lượt và kết hợp tìm kiếm, đọc paper, tạo citation. | Transcript: `live_openrouter_20260729T161558316542.transcript.json` |

---

# PHẦN B — Chi tiết / Bằng chứng

> Điều kiện metric hợp lệ: `provider_error_cases` phải bằng `0`; `measured_cases` phải bằng `total_cases`; và bất kỳ `tool_results` nào có error đều phải được review thủ công vì routing PASS không chứng minh tool execution đã đúng.

## B1. Version evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Prompt/tool change | Hypothesis | Metric name | Before | After | Run File |
|---|---|---|---|---:|---:|---|
| v0 | baseline |  |  |  |  |  |
| v1 |  |  |  |  |  |  |
| v2 |  |  |  |  |  |  |
| v3 |  |  |  |  |  |  |

## B2. Failure analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
|  |  |  |  |  |

## B3. Team eval cases

List the 10 cases added to `data/eval_group.json`:

- 5 single-turn
- 5 multi-turn

This section is for the mandatory team-authored eval set. Optional built-ins do
not belong here.

File template để trống có chủ đích; nhóm phải tự thiết kế đủ 10 case.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
|  |  |  |  |

## B4. Live chat evidence

Use `transcripts/*.transcript.json`.

| Scenario/Turn | Version | Tool Calls + Args | Transcript/Run | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B5. Tool capability evidence

Phân loại rõ tool mới bắt buộc, optional built-in và tool đủ điều kiện bonus. Chỉ ghi Telegram/PDF nếu nhóm thực sự dùng; base report không cần chúng.

UI is core deliverable, not bonus. Do not list it here.

| Category | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Must-have: tool mới đầu tiên |  |  |  |
| Optional built-in |  |  |  |
| Bonus: tool mới thứ 4 trở đi |  |  |  |

## B6. Reflection

- Which fixes belonged in `system_prompt.md`?
- Which fixes belonged in `tools.yaml`?
- Which failure needed manual review instead of automatic grading?
- What would you improve next?
