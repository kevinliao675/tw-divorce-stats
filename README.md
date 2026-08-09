# tw-divorce-stats

台灣離婚統計開放資料的自動彙整。GitHub Actions 每月自動抓取內政部統計並更新 `data/divorce-stats.json`，供 [lawyerliao75.lawyer](https://lawyerliao75.lawyer) 離婚趨勢頁面讀取。

## 資料內容

`data/divorce-stats.json`：

- `annual`：全國歷年離婚對數與粗離婚率（民國 90 年起，僅完整年度）
- `counties`：最新完整年度各縣市離婚對數與粗離婚率
- `monthly`：最近 36 個月全國與臺中市離婚對數

## 資料來源

內政部統計處統計查詢網「離婚對數─按區域別分」，同 [政府資料開放平臺資料集 14243](https://data.gov.tw/dataset/14243) 之來源。依政府資料開放授權條款（OGDL-Taiwan-1.0）利用。

## 更新機制

`.github/workflows/update.yml` 每月 15 日自動執行 `fetch_stats.py`，有變更才 commit。手動更新：

```bash
python3 fetch_stats.py
```
