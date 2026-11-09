# 공공데이터포털 '한국소비자원_소비자 피해구제 정보_20260630' 간단 분석
# 실행: python3 public_data_analysis.py  (원본: ../01_raw/public_data/PD01_kca_relief_20260630_cp949.csv, CP949)
import csv, collections, json, os
here = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(here, '..', '01_raw', 'public_data', 'PD01_kca_relief_20260630_cp949.csv')
rows = list(csv.DictReader(open(src, encoding='cp949')))
out = {"source": "PD01", "total_rows": len(rows), "columns": list(rows[0].keys()),
       "periods": dict(collections.Counter(r['접수일'] for r in rows))}
# 가전 대여(렌트) 품목: 물품명에 '대여(렌트)'가 들어간 것 중 가전류만
appliance_rent = ['정수기대여(렌트)','미분류대여(렌트)','안마의자대여(렌트)','음식물처리기대여(렌트)',
                  '공기청정기대여(렌트)','비데대여(렌트)','연수기대여(렌트)']
rent = [r for r in rows if r['물품명'] in appliance_rent]
out["appliance_rent"] = {"items": appliance_rent, "rows": len(rent),
    "by_item": dict(collections.Counter(r['물품명'] for r in rent).most_common()),
    "by_reason": dict(collections.Counter(r['청구이유'] for r in rent).most_common())}
c = out["appliance_rent"]["by_reason"].get('계약해제.해지/위약금', 0)
out["appliance_rent"]["contract_cancel_share"] = round(c / len(rent) * 100, 1)
# 세탁기·건조기 (구독/구매 구분 불가)
wash_items = ['전기세탁기', '전기의류건조기']
wash = [r for r in rows if r['물품명'] in wash_items]
out["washer_dryer"] = {"rows": len(wash),
    "by_reason": dict(collections.Counter(r['청구이유'] for r in wash).most_common()),
    "by_sales_type": dict(collections.Counter(r['판매유형'] for r in wash).most_common())}
out["by_age_appliance_rent"] = dict(collections.Counter(r['연령'] for r in rent).most_common())
json.dump(out, open(os.path.join(here, 'public_data_analysis_result.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
