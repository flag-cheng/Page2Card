# page2card

**貼一個連結，收進你的閱讀卡片。**

page2card 是一個單機版的「文章收藏器」。貼上一篇文章網址，它會在伺服器端抓下
網頁、擷取出**標題與內文**，存成一張卡片，並可依**分類／議題**整理。

> 這是教學用的 **starter**。它刻意只做到「抓取 → 顯示 → 收藏 → 分類」。
> **AI 中文摘要與分享圖卡尚未實作** —— 那是後續用 Codex 完成的任務，
> 詳見 [`PAGE2CARD_ISSUE.md`](../PAGE2CARD_ISSUE.md)。

## 功能（Starter）

- 貼網址 → 伺服器抓取 → 擷取標題與內文
- 收藏成卡片清單，最新的在前
- 為每篇貼上分類／議題標籤，並可依分類篩選
- 查看單篇文章的完整內文
- 刪除文章

## 需求

- Python 3.12 以上
- [`uv`](https://docs.astral.sh/uv/)（專案、虛擬環境與依賴管理）
- 不需要 Node.js，也沒有前端框架（UI 由 Jinja2 模板 + 純 CSS 產生）

## 安裝與啟動

```bash
uv sync --frozen
uv run uvicorn page2card.main:app --reload
```

啟動後開啟 <http://127.0.0.1:8000>。

## 常用指令

```bash
uv run pytest                 # 測試
uv run ruff check .           # lint
uv run ruff format --check .  # 格式檢查
```

## 資料庫位置

SQLite 資料檔預設位於 `data/page2card.db`，首次連線時自動建立 `data/` 目錄。
`.gitignore` 已忽略 `data/*.db`。測試使用暫存資料庫，不會動到正式資料檔。
時間以**台灣時間（UTC+8）**儲存與顯示。

## 下一步（交給 Codex）

starter 在文章詳細頁保留了一塊空的「摘要卡片」區（`summary-slot`）。
接下來的 Codex 任務會：

1. 接上 OpenAI API，為文章產生**繁體中文摘要**
2. 把摘要排版成一張可截圖分享的**圖卡**

完整需求與驗收條件見 [`PAGE2CARD_ISSUE.md`](../PAGE2CARD_ISSUE.md)。

## 第一版限制

- 只抓取靜態 HTML（不執行 JavaScript）；動態渲染或反爬蟲嚴格的頁面可能抓不到內文
- 無 AI 摘要、無圖卡（留給 Codex 任務）
- 無定時、無通知、無登入；僅適合本機單一使用者示範
