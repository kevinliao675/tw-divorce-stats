#!/usr/bin/env python3
"""抓取內政部統計處離婚統計，輸出 data/divorce-stats.json。

資料來源:內政部統計處統計查詢網(statis.moi.gov.tw),funid=c0140201
「離婚對數─按區域別分」(即 data.gov.tw 結婚/離婚登記對數系列資料集之來源)。
年資料自民國 90 年起,月資料抓最近 36 個月。無外部相依,GitHub Actions 直接跑。
"""
import csv
import io
import json
import ssl
import urllib.request
from datetime import date, timezone, timedelta
from pathlib import Path

BASE = ("https://statis.moi.gov.tw/micst/webMain.aspx?sys=220&kind=21&type=1"
        "&funid=c0140201&outmode=12&utf=1&compmode=0&fldlst=11"
        "&codspc0=0,2,3,2,6,1,9,1,12,1,15,16,&rdm=claude")

ANNUAL_START_ROC = 90


def fetch_csv(url: str) -> list[list[str]]:
    ctx = ssl.create_default_context()
    # 政府網站憑證缺 Subject Key Identifier，Python 3.13+ 預設的 strict 檢查會拒絕;
    # 放寬 strict 旗標但仍保留完整的憑證鏈驗證
    ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
    req = urllib.request.Request(url, headers={"User-Agent": "tw-divorce-stats/1.0"})
    with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
        text = resp.read().decode("utf-8-sig")
    return [row for row in csv.reader(io.StringIO(text)) if row]


def fetch_annual(roc_now: int):
    """年序列:全國歷年 + 最新完整年度各縣市快照。"""
    url = f"{BASE}&cycle=4&outkind=3&ym={ANNUAL_START_ROC}00&ymt={roc_now - 1}00"
    rows = fetch_csv(url)
    years, pairs, rates = [], [], []
    by_year: dict[int, list[dict]] = {}
    for row in rows[1:]:
        if len(row) < 3 or "/" not in row[0]:
            continue
        label, region = [s.strip() for s in row[0].split("/", 1)]
        if "年" not in label or "(" in label:  # 跳過部分年度小計如「115年 (1~6月)」
            continue
        year = int(label.replace("年", ""))
        if year >= roc_now:  # 當年度資料不完整，只保留完整年度
            continue
        try:
            n, r = int(row[1]), float(row[2])
        except ValueError:
            continue
        if region == "區域別總計":
            years.append(year); pairs.append(n); rates.append(r)
        else:
            by_year.setdefault(year, []).append({"name": region, "pairs": n, "rate": r})
    latest = max(y for y in by_year if len(by_year[y]) >= 20)
    return ({"years": years, "pairs": pairs, "rate": rates},
            {"year": latest, "items": by_year[latest]})


def fetch_monthly(roc_now: int, month_now: int):
    """月序列:最近 36 個月全國與臺中市。"""
    start_roc = roc_now - 3
    url = f"{BASE}&cycle=41&outkind=1&ym={start_roc}01&ymt={roc_now}{month_now:02d}"
    rows = fetch_csv(url)
    header = rows[0]
    col_total = next(i for i, h in enumerate(header) if "區域別總計" in h and "離婚對數" in h)
    col_tc = next(i for i, h in enumerate(header) if "臺中" in h and "離婚對數" in h)
    months, national, taichung = [], [], []
    year = None
    for row in rows[1:]:
        label = row[0].strip()
        if "(" in label:  # 年度小計列
            continue
        if "年" in label and "月" in label:
            y, m = label.replace("月", "").split("年")
            ym = f"{int(y)}{int(m):02d}"
            try:
                months.append(ym)
                national.append(int(row[col_total]))
                taichung.append(int(row[col_tc]))
            except (ValueError, IndexError):
                months.pop()
    keep = 36
    return {"months": months[-keep:], "national": national[-keep:], "taichung": taichung[-keep:]}


def main():
    now = date.today()
    roc_now = now.year - 1911
    annual, counties = fetch_annual(roc_now)
    monthly = fetch_monthly(roc_now, now.month)
    out = {
        "updated": now.isoformat(),
        "source": "內政部統計處統計查詢網（離婚對數─按區域別分）",
        "sourceUrl": "https://data.gov.tw/dataset/14243",
        "annual": annual,
        "counties": counties,
        "monthly": monthly,
    }
    dest = Path(__file__).parent / "data" / "divorce-stats.json"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"OK: {len(annual['years'])} 年、{len(monthly['months'])} 個月、"
          f"{len(counties['items'])} 縣市（{counties['year']} 年）→ {dest}")


if __name__ == "__main__":
    main()
