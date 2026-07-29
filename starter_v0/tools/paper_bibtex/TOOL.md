# Tool: `paper_bibtex`

Tạo chuỗi trích dẫn BibTeX chuẩn từ arXiv ID hoặc URL.

## Contract
- **Input:** `arxiv_url` (chuỗi dạng ID `1706.03762` hoặc URL `https://arxiv.org/abs/1706.03762`)
- **Output:** Trả về dict chứa `arxiv_id`, `bibtex` (định dạng `@article{...}`) và `items`.
