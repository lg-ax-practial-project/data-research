"""확인한 공개자료를 구조화하고 오프라인 비교 보고서를 생성한다. 외부 호출 없음."""
from pathlib import Path
from html import escape
from collections import Counter
import json

ROOT = Path(__file__).resolve().parent
DATE = '2026-11-20'
sources = []
rows = []

def source(sid, title, publisher, url, status, note, published=None):
    sources.append(dict(ID=sid, 제목=title, 발행기관=publisher, URL=url,
                        열람상태=status, 확인사항=note, 발행일=published, 수집일=DATE))

def point(sid, category, product, period, metric, value, unit, scope, caveat='', kind='공개값'):
    rows.append(dict(ID=f'지표-{len(rows)+1:03}', 출처ID=sid, 지표군=category,
                     제품=product, 기준기간=period, 지표=metric, 값=value, 단위=unit,
                     모집단과분모=scope, 해석제한=caveat, 값유형=kind))

source('S01','LG 디오스 광파오븐 판매 성장','LG',
       'https://www.lg.co.kr/media/release/22401','본문 확인',
       '인공지능쿡 탑재 제품의 2020년 1~8월 및 8월 판매 증감. 전체 광파오븐 시장 통계 아님.', '2020-09-09')
source('S02','주방의 필수가전, 전자레인지 차트뉴스','다나와',
       'https://dpg.danawa.com/mobile/news/view?boardSeq=293&listSeq=4918153&past=Y','본문 확인',
       '다나와 집계의 판매 추이와 사양별 판매량 비중. 전국 시장으로 일반화 불가.', '2021-12-20')
source('S03','복합형 오븐 차트뉴스','다나와',
       'https://dpg.danawa.com/news/view?boardSeq=293&listSeq=5750257','본문 확인',
       '2021~2024년 복합형 오븐 판매·제조사 비중. 광파 외 가열 방식도 포함.', '2025-02-17')
source('S04','2021년 기준 제12차 가구에너지패널조사 연구','에너지경제연구원',
       'https://kesis.keei.re.kr/pdfOpen.es?bid=0010&list_no=627&seq=1','PDF 텍스트 확인·이미지 검증 실패',
       '인쇄면 732쪽, 통계표4 기타기기 추정값. 2021년 말 보유 및 연중 사용 기준. 보유대수와 보유율은 다름.')
source('S05','마켓70 주방·생활가전 보유율, 코로나 이전','한국갤럽',
       'https://panel.gallup.co.kr/Contents/GallupReport/GallupReport_Market70_01%2820190621%29.pdf','PDF 텍스트 확인',
       '2018.5~2019.3, 제주 제외 만13세 이상 9,600명 면접. 가구 내 보유 응답률.', '2019-06-21')
source('S06','2021년 가전 보유율 조사 소개','아이보스·매드타임스, 한국갤럽 인용',
       'https://www.i-boss.co.kr/ab-2877-6731','2차 출처 본문 확인',
       '2020.9~2021.3, 제주 제외 만13세 이상 5,100명. 갤럽 원 보고서 미확보.', '2021-06-03')
source('S07','엔데믹이 불러온 급격한 시장의 변화','GfK',
       'https://www.gfk.com/hubfs/GfK%20%ED%95%9C%EA%B5%AD%20%EA%B0%80%EC%A0%84%20%EC%8B%9C%EC%9E%A5%20%EB%A6%AC%ED%8F%AC%ED%8A%B8_2023.03.pdf','PDF 텍스트 확인·이미지 검증 실패',
       '2022년 매출 기준 성장률. 대표 27개 품목. 전자레인지 +10%는 판매대수 성장률 아님.', '2023-03')
source('S08','인플레이션과 가전 시장의 하락','GfK',
       'https://www.gfk.com/hubfs/GfK_%ED%95%9C%EA%B5%AD%EA%B0%80%EC%A0%84%EC%8B%9C%EC%9E%A5%EB%A6%AC%ED%8F%AC%ED%8A%B8_1%EC%B0%A8_2024.03.pdf','PDF 텍스트 확인',
       '2023년 대표 38개 품목. S07의 27개 품목 규모와 단순 연결 금지.', '2024-03')
source('S09','생활건강가전 트렌드 리포트 2021 공개 요약','오픈서베이 블로그',
       'https://blog.opensurvey.co.kr/trendreport/appliances-2021/','공개 요약 본문 확인',
       '2021.6.14, 보유 가전 중 직접 구매·렌탈한 제품이 있는 20~59세 1,000명. 개별 광파오븐 구매의향 수치는 미확보.', '2021-06-28')
source('S10','전자레인지 네이버 월간 검색량 소개','랭킷',
       'https://rankit.kr/keyword/%EC%A0%84%EC%9E%90%EB%A0%88%EC%9D%B8%EC%A7%80','본문 확인·제3자 재가공값',
       '페이지 갱신일 2026.10.28. 측정 기간·네이버 원 응답 미확인. 코로나 지표 아님.')
source('S11','광파오븐 네이버 월간 검색량 소개','랭킷',
       'https://rankit.kr/keyword/%EA%B4%91%ED%8C%8C%EC%98%A4%EB%B8%90','검색 결과 발췌만 확인·본문 실패',
       '페이지 갱신일 2026.11.13. S10과 시점이 달라 비율 산출 금지. 코로나 지표 아님.')
source('S12','2020년 국내 가전 시장 성장률 발표','GfK, 뉴스와이어 배포',
       'https://www.newswire.co.kr/newsRead.php?no=919394','본문 확인',
       '23개 대표 가전 POS. 매출 기준이며 두 제품만의 판매 성장과 구분.', '2021-03-04')
source('S13','2021년 상반기 국내 가전 시장 성장률 발표','GfK, 뉴스와이어 배포',
       'https://www.newswire.co.kr/newsRead.php?no=929685&picno=492466','검색 결과 발췌 확인',
       '반기 자료. 연간 통계와 구분.')
source('S14','2023 ICT 실태조사, 정보통신응용기반기기 수출액','한국정보통신진흥협회',
       'https://www.kait.or.kr/kukudocs/getFile/pWRFgUjCZuj/pdf','PDF 텍스트 확인·이미지 검증 실패',
       '인쇄면 106쪽, 1.5.2, 단위 천US$. 전자레인지 2017~2022년. 연간 수출액 교차 확인용.')
source('S15','SK매직 신용평가, 주방가전 품목별 점유율 및 판매량','한국신용평가',
       'https://kisrating.com/fileDown.do?fileName=rs20231020-9.pdf&gubun=2&menuCd=R8','자료 위치 확인·수치 채택 보류',
       '인쇄면 3쪽 차트. 회사 자체 시장조사. 추출 도구가 막대높이를 근사한 값을 제시해 정량 표에서는 제외.', '2023-10-20')
source('S16','사우디 전자레인지 시장 트렌드','KOTRA',
       'https://dream.kotra.or.kr/kotranews/cms/news/actionKotraBoardDetail.do?CONTENTS_NO=1&MENU_ID=180&SITE_NO=3&bbsGbn=243&bbsSn=243&pNttSn=194261','검색 결과 상세 발췌 확인·본문 실패',
       '현지 판매대수·유통채널·수입 자료. 국내 수요와 별도 참고.')
source('S17','활기를 되찾고 있는 페루 백색가전제품 시장','KOTRA',
       'https://dream.kotra.or.kr/kotranews/cms/news/actionKotraBoardDetail.do?CONTENTS_NO=1&MENU_ID=180&SITE_NO=3&bbsGbn=243&bbsSn=243&pNttSn=192691','검색 결과 상세 발췌 확인',
       'Veritrade 수입액 인용. 2021년은 1~11월 누계. 현지 판매액 아님.')
source('S18','중국 전자레인지 시장동향','KOTRA',
       'https://dream.kotra.or.kr/kotranews/cms/news/actionKotraBoardDetail.do?CONTENTS_NO=2&MENU_ID=190&SITE_NO=3&bbsGbn=254&bbsSn=254&pNttSn=184830','검색 결과 상세 발췌 확인·본문 실패',
       '중국 생산·수출 및 도시·농촌 보유대수. 7,063.4만대의 판매 범위는 국내 소매인지 불명확해 미채택.', '2020-09-29')
source('S19','통합 검색어 트렌드 설명','네이버 개발자센터',
       'https://developers.naver.com/docs/serviceapi/datalab/search/search.md','본문 확인',
       '검색 관심도는 상대지수. API 인증 필요. 실제 2018~2024년 결과를 받은 것은 아님.')
source('S20','Google Trends 데이터 해석 안내','Google News Initiative',
       'https://newsinitiative.withgoogle.com/resources/trainings/google-trends-understanding-the-data/','본문 확인',
       '검색 표본·정규화 지수 설명. 이번 작업에서 관심도 시계열 실측값 미확보.')

imports = [
    (2018,105371.86,1476200,81647.14,23297.44),
    (2019,105031.60,1570910,80023.98,24379.02),
    (2020,111701.71,1589250,86021.69,25207.53),
    (2021,130375.28,1638830,103666.53,26232.17),
    (2022,135950.98,1579980,110964.36,24647.59),
    (2023,107101.75,1379990,89254.66,17337.60),
    (2024,112263.50,1545070,96161.06,15537.81),
]
exports = [(2018,30673.54,210926),(2020,2271.35,26692),(2021,226.68,2764),
           (2022,168.61,2075),(2023,186.10,2112),(2024,347.73,2811)]
trade_note = 'HS851650 통관 기준. 광파오븐 별도 분리 없음. 국내 소매판매·한국 브랜드 세계판매와 다름. 수량은 WITS 표시값이며 추정 여부를 개별 검증하지 않음.'
for i,(year,amount,qty,china,malaysia) in enumerate(imports,21):
    sid=f'S{i:02}'
    source(sid,f'한국 전자레인지 {year}년 수입','세계은행 WITS·UN Comtrade',
           f'https://wits.worldbank.org/trade/comtrade/en/country/KOR/year/{year}/tradeflow/Imports/partner/ALL/product/851650',
           '본문 표 확인',trade_note)
    for metric,value,unit in [('총수입액',amount,'천USD'),('표시 수입수량',qty,'개'),
                              ('중국발 수입액',china,'천USD'),('말레이시아발 수입액',malaysia,'천USD')]:
        point(sid,'무역','전자레인지(HS851650)',str(year),metric,value,unit,'한국 신고·전세계 상대국',trade_note)
for i,(year,amount,qty) in enumerate(exports,28):
    sid=f'S{i:02}'
    source(sid,f'한국 전자레인지 {year}년 수출','세계은행 WITS·UN Comtrade',
           f'https://wits.worldbank.org/trade/comtrade/en/country/KOR/year/{year}/tradeflow/Exports/partner/ALL/product/851650',
           '본문 표 확인',trade_note)
    point(sid,'무역','전자레인지(HS851650)',str(year),'총수출액',amount,'천USD','한국 신고·전세계 상대국',trade_note)
    point(sid,'무역','전자레인지(HS851650)',str(year),'표시 수출수량',qty,'개','한국 신고·전세계 상대국',trade_note)
for sid,year,n in [('S34',2019,535),('S35',2020,579),('S36',2022,637),('S37',2023,2555)]:
    source(sid,f'{year}년 기준 가구에너지패널조사 연구','에너지경제연구원',
           f'https://kesis.keei.re.kr/pdfOpen.es?bid=0010&list_no={n}&seq=1','파일 크기 제한으로 미수집',
           '공식 목록에서 연결 확인. 해당 연도 보유대수는 추출하지 못했음.')
source('S38','가구에너지패널조사 연도별 보고서 목록','에너지경제연구원',
       'https://kesis.keei.re.kr/board.es?bid=0010&mid=a10202040100','목록 본문 확인',
       'S34~S37의 원문 링크 확인. 조사 기준연도와 발행연도 구분에 사용.')

point('S01','판매','LG 인공지능쿡 탑재 광파오븐','2020.01~08 / 2019.01~08','판매량 증감률',30,'약 %','동일 기능 탑재 LG 제품','시장 전체·연간 값 아님')
point('S01','판매','LG 인공지능쿡 탑재 광파오븐','2020.08 / 2019.08','판매량 배율',2,'약 배','동일 기능 탑재 LG 제품','단월 값; 정확한 판매대수 비공개')
point('S03','판매','복합형 오븐','2022 / 2021','판매량 증감률',28,'%','다나와 리서치 집계','광파·컨벡션 등을 포함; 전국 시장 아님')
for year,value in [(2021,9.9),(2024,30.7)]:
    point('S03','판매','삼성 복합형 오븐',str(year),'제조사 판매량 점유율',value,'%','다나와 복합형 오븐 판매량','광파오븐의 전체 판매 비중과 다름')
point('S03','판매','SK매직 복합형 오븐','2024','제조사 판매량 점유율',5.4,'%','다나와 복합형 오븐 판매량','집계 채널 한정')
for product,metric,value in [('20L 전자레인지','용량별 판매 비중',29.81),('23L 전자레인지','용량별 판매 비중',62.29),
                             ('700W 전자레인지','출력별 판매 비중',64.71),('1000W 전자레인지','출력별 판매 비중',30.68)]:
    point('S02','판매',product,'2021.12 기사 집계',metric,value,'%','다나와 전자레인지 판매량','정확한 집계 시작·종료 기간은 본문에서 확인 안 됨')
for sid,period,product,value in [('S05','2018.05~2019.03','전자레인지',96),('S05','2018.05~2019.03','오븐',22),
                                  ('S06','2020.09~2021.03','전자레인지',97),('S06','2020.09~2021.03','오븐',21),
                                  ('S06','2020.09~2021.03','에어프라이어',60)]:
    point(sid,'보유',product,period,'가구 내 보유 응답률',value,'%','제주 제외 만13세 이상 개인 응답자',
          '가구 가중 보급률·구매율 아님. 오븐은 광파오븐보다 넓은 범주. 표본오차·설계 고려 필요')
for product,per,total in [('전자레인지',0.76,16239935),('전기오븐',0.02,354205),('광파오븐',0.04,862465)]:
    point('S04','보유·이용',product,'2021','가구당 보유대수',per,'대/가구','가구에너지패널 추정 모집단',
          '인쇄면732. 연중 사용 기준이 적용된 보유대수. 구매율·보유 가구 비율로 치환 금지')
    point('S04','보유·이용',product,'2021','총 보유대수 추정',total,'대','가구에너지패널 추정 모집단',
          '인쇄면732. 텍스트 추출 기준; 표 이미지 재검증 필요. 갤럽 보유율과 직접 접합 금지')
for product,value in [('전자레인지',10),('주방가전 전체',-10),('대표 가전27개',-10),('튀김기',-29)]:
    point('S07','시장 배경',product,'2022 / 2021','매출액 증감률',value,'%','GfK POS 집계','서브 제품 포함 가능. 판매수량 증가로 해석 금지')
for metric,value,unit in [('매출액 증감률',-12,'%'),('판매수량 증감률',-17,'%'),('평균가격 증감률',6.4,'%')]:
    point('S08','시장 배경','대표 가전38개','2023 / 2022',metric,value,unit,'GfK POS 집계','S07과 집계 제품 수 다름')
for metric,value in [('온라인 쇼핑몰 구매채널 이용률',58.2),('1인가구 사이즈 중시 응답률',26.5)]:
    point('S09','관심·구매 고려','생활건강가전 전반','2021.06.14',metric,value,'%','20~59세 직접 구매·렌탈 경험 조건부 표본 1,000명','두 제품 개별 관심도·구매전환율 아님')
for metric,value in [('사이즈 중요도 전년대비 변화',4.8),('성능 중요도 전년대비 변화',-3.9),('브랜드 중요도 전년대비 변화',-3.7)]:
    point('S09','관심·구매 고려','생활건강가전 전반','2021 / 2020',metric,value,'%p','오픈서베이 조건부 표본','제품별 결과 아님; 전년 조사 설계 추가 확인 필요')
for sid,product,period,values in [('S10','전자레인지','2026.10.28 갱신',(132500,20200,112300)),
                                    ('S11','광파오븐','2026.11.13 갱신',(12090,2600,9490))]:
    for metric,value in zip(['네이버 월간 검색량 소개값','PC 검색량 소개값','모바일 검색량 소개값'],values):
        point(sid,'현재 관심 참고',product,period,metric,value,'회/월 소개값','제3자 페이지의 단일 키워드',
              '원천 응답·정확한 산출 기간 미검증. 갱신일 상이; 두 키워드 비율·코로나 전후 변화 산출 금지')
for metric,value in [('전체가전 매출액 증감률',14),('주방가전 매출액 증감률',20),('온라인 매출액 증감률',25),('오프라인 매출액 증감률',8)]:
    point('S12','시장 배경','대표 가전23개','2020 / 2019',metric,value,'%','GfK 대표 제품 POS','두 제품만의 성장률 아님')
for year,value in [(2019,34.4),(2020,37.6)]:
    point('S12','유통','대표 가전23개',str(year),'온라인 매출 비중',value,'%','GfK 집계 가전 매출액','제품별 구매 비중 아님')
point('S13','시장 배경','전체 가전','2021상반기 / 2020상반기','매출액 증감률',5,'%','GfK 집계','검색 발췌 확인; 반기 수치')
for year,value in [(2017,66560),(2018,30674),(2019,2806),(2020,2271),(2021,227),(2022,169)]:
    point('S14','무역 교차확인','전자레인지',str(year),'총수출액(반올림 표)',value,'천USD','한국 ICT 실태조사 수출 표','WITS 동일 연도와 중복 관측; 합산 금지')
for year,value in [(2017,2291),(2018,2114),(2019,2178),(2020,3069)]:
    point('S16','해외 참고','전자레인지',str(year),'사우디 수입액',value,'만USD','사우디 대세계 수입','본문 서술 반올림값; 국내 시장 아님')
for year,value in [(2020,51),(2021,54)]:
    point('S16','해외 참고','전자레인지',str(year),'사우디 판매대수',value,'약 만대','사우디 시장','현지 시장조사 인용·근사치')
for year,value in [(2020,6.7),(2021,7.2)]:
    point('S16','해외 참고','전자레인지',str(year),'사우디 전자상거래 유통 비중',value,'%','사우디 유통 집계','금액·수량 기준은 발췌에서 미확인')
for year,value in [('2019',13210),('2020',12966),('2021.01~11',13416)]:
    point('S17','해외 참고','전자레인지(HS851650)',year,'페루 수입액',value,'천USD','페루 대세계 수입','2021은 연간 값 아님; 2020연간 대비 성장률 계산 금지')
for product,value in [('도시',56.9),('농촌',17.3)]:
    point('S18','해외 참고','전자레인지·중국 '+product,'2018','100가구당 보유대수',value,'대/100가구','중국 도시·농촌 각각','한국 보유율과 비교 금지')

assert len({s['ID'] for s in sources}) == len(sources)
source_map = {s['ID']:s for s in sources}
assert all(r['출처ID'] in source_map for r in rows)
assert all(isinstance(r['값'],(int,float)) for r in rows)
derived = []
for year,amount,qty,china,malaysia in imports:
    previous = next((x for x in imports if x[0]==year-1),None)
    derived.append(dict(연도=year, 수입액_백만USD=round(amount/1000,5),
                        수입액_전년비=None if previous is None else round((amount/previous[1]-1)*100,2),
                        표시수입수량=qty, 중국발수입액비중=round(china/amount*100,2)))

gaps = [
    '광파오븐 대 전자레인지의 전국 연간 판매량·매출액·구매 가구 비율을 동일 기준으로 직접 비교한 공개 시계열은 미확보.',
    '광파오븐의 독립 수출 HS 코드를 확인하지 못함. HS851650이나 넓은 오븐류 HS851660 전체를 광파오븐 수출로 간주하지 않음.',
    '네이버·Google의 2018~2024년 월별 관심도 실측값 미확보. Google Trends 웹 열람 불가, 브라우저 호스트 연결 불가. API 인증 정보 미제공.',
    '2019·2020·2022·2023년 에너지패널 PDF는 약32~77MB로 열람 도구 크기 제한. 원문 파일 자체를 내려받아 저장한 상태가 아님.',
    'PDF 표는 검색 도구의 텍스트 추출로 확인. 이미지 열람 실패 자료는 시각 검증을 완료했다고 표시하지 않음.',
    'WITS 2019년 한국 수출 페이지 열람 실패. 2019년 수출액은 S14의 반올림값만 확보; 수량을 추정해 채우지 않음.',
]
design = dict(
    분석기간='2018~2019 코로나 이전 / 2020~2021 코로나기 / 2022 전환기 / 2023~2024 이후. 연구용 구분이며 공인 방역 구분이 아님.',
    국가='한국 중심. 사우디·페루·중국은 별도 참고.',
    단위정의='구매율=기간 중 구매 가구/조사 가구; 보유율=보유 응답자/전체 응답자; 판매점유율=카테고리 판매 중 제품 판매; 성장률=동일 대상 전년 대비 변화. 상호 대체 불가.',
    관심도추가수집=dict(기간=['2018-01-01','2024-12-31'],주기='월',
        검색어그룹={'전자레인지':['전자레인지','전자렌지'],'광파오븐':['광파오븐','광파 오븐']},
        별도민감도그룹={'복합오븐':['복합오븐','복합 오븐'],'삼성큐커':['삼성 큐커','비스포크 큐커']},
        계산='동일 요청·기간·조건에서 비교. 월별 계절성 통제 후 2019 평균=100으로 각 시계열 재지수화. 검색량을 구매자 수로 변환하지 않음.',
        상태='설계만 작성; 실측값 미수집'),
    인과해석='전후 증감만으로 코로나 효과를 입증할 수 없음. 가격·프로모션·신제품·가구수·유통채널 변화가 함께 작용할 수 있음.',
)
data = dict(보고서ID='조사-전자레인지-광파오븐-20261120', 수집일=DATE,
            범위=design, 출처목록=sources, 공개수치관측=rows, 계산값=derived, 미확보=gaps)
(ROOT/'evidence.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def link(sid):
    s=source_map[sid]
    return f'<a href="{escape(s["URL"],quote=True)}" target="_blank" rel="noopener">{sid} · {escape(s["발행기관"])}</a>'

def table(headers, content):
    return '<div class="tablewrap"><table><thead><tr>'+''.join(f'<th>{escape(x)}</th>' for x in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{x}</td>' for x in row)+'</tr>' for row in content)+'</tbody></table></div>'

trade_table=[]
for item in derived:
    year=item['연도']; ex=next((x for x in exports if x[0]==year),None)
    extext=f'{ex[1]:,.2f}' if ex else '2,806（S14 반올림）'
    exsid=f'S{28+[x[0] for x in exports].index(year):02}' if ex else 'S14'
    trade_table.append([str(year),f'{item["수입액_백만USD"]:,.3f}',
        '기준 없음' if item['수입액_전년비'] is None else f'{item["수입액_전년비"]:+.2f}%',
        f'{item["표시수입수량"]:,}',extext,link(f'S{21+year-2018:02}')+' / '+link(exsid)])

facts = [
    ('비교-01','코로나기 광파오븐 판매','LG 인공지능쿡 탑재 제품: 2020년 1~8월 판매량 약 +30%, 8월 약 2배.','S01','특정 제품군 실적이며 전체 시장점유율은 아님.'),
    ('비교-02','전자레인지 판매 추이','다나와에서 2020년 상반기 급증, 2021년 2~6월 감소 추세를 설명. 오븐류 판매량의 절반 이상이 전자레인지.','S02','정확한 전년비는 미공개. 수요 선구매라는 원인 설명은 기사의 가설.'),
    ('비교-03','전환기 복합형 오븐','다나와 집계 2022년 판매량은 2021년보다 28% 증가.','S03','복합형 오븐 전체이며 광파오븐만을 뜻하지 않음.'),
    ('비교-04','전환기 전자레인지 매출','GfK 집계 2022년 전자레인지 매출은 전년보다 10% 증가.','S07','판매수량 +10%라고 읽으면 안 됨. 비교-03과 직접 우열 비교 불가.'),
    ('비교-05','가구 내 보유 응답','전자레인지 96%→97%, 오븐 22%→21%: 코로나 이전 갤럽 조사와 2021 조사 소개.','S06','코로나 이전 출처 S05. 오븐 전체와 광파오븐을 구분. 1%p 차이의 유의성 미검증.'),
    ('비교-06','같은 조사 안의 제품별 보유대수','2021 에너지패널: 전자레인지 0.76대/가구, 전기오븐 0.02대/가구, 광파오븐 0.04대/가구.','S04','구매율·가구 보유율로 치환 금지. 갤럽과 조사 정의가 다름.'),
    ('비교-07','구매 고려 요인','2021년 가전 구매에서 사이즈 중요도가 전년보다 4.8%p 상승. 1인가구의 사이즈 중시 응답은 26.5%.','S09','두 제품 개별 관심도는 아니며 조건부 표본.'),
]
fact_html=table(['ID','비교 지표','확인 결과','출처','해석 범위'],[[a,b,c,link(d),e] for a,b,c,d,e in facts])
all_rows=table(['ID','제품','기간','지표','값','단위','출처','모집단·분모','한계'],
    [[r['ID'],escape(r['제품']),escape(r['기준기간']),escape(r['지표']),f'{r["값"]:,}',escape(r['단위']),
      link(r['출처ID']),escape(r['모집단과분모']),escape(r['해석제한'])] for r in rows])
catalog=table(['ID','출처','열람 상태','발행일','활용·제한'],[
    [s['ID'],f'<a href="{escape(s["URL"],quote=True)}">{escape(s["제목"])}</a><br>{escape(s["발행기관"])}',
     escape(s['열람상태']),escape(s['발행일'] or '미확인'),escape(s['확인사항'])] for s in sources])
current=table(['키워드','월간 검색량 소개값','PC','모바일','페이지 갱신일','확인 수준'],[
    ['전자레인지','132,500','20,200','112,300','2026-10-28',link('S10')+' 본문'],
    ['광파오븐','12,090','2,600','9,490','2026-11-13',link('S11')+' 검색 발췌']])
stats=Counter(r['지표군'] for r in rows)
html='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>전자레인지·광파오븐 공개 지표 비교</title><style>
body{font-family:"Malgun Gothic","맑은 고딕",sans-serif;color:#1c2839;background:#f5f7fb;margin:0;line-height:1.65}
main{max-width:1450px;margin:auto;padding:34px}h1{font-size:30px;margin:8px 0 16px}h2{font-size:22px;margin-top:38px}
p,li{max-width:1000px}a{color:#2459a5}header{background:#132d4e;color:white;padding:32px;border-radius:16px}header p{color:#d7e3f4}
.note{background:#fff4d9;padding:18px;border-left:5px solid #d99b1b;margin:24px 0}.card{background:white;padding:20px;border-radius:12px;margin:18px 0}
.tablewrap{overflow:auto;background:white;border:1px solid #d9e1eb;border-radius:8px;margin:18px 0}table{border-collapse:collapse;min-width:850px;width:100%;font-size:14px}
td,th{text-align:left;padding:12px;border-bottom:1px solid #e4eaf1;vertical-align:top}th{background:#e9eff7;white-space:nowrap}tr:hover{background:#f5f9ff}
input{font:inherit;padding:10px;border:1px solid #a6b9d0;border-radius:8px;width:min(600px,90%)}small{color:#5a6b80}.pill{display:inline-block;padding:5px 12px;background:#e4edf8;border-radius:20px;margin:4px}
@media print{body{background:white}main{padding:0}header{background:white;color:#132d4e}header p{color:#132d4e}input{display:none}.tablewrap{overflow:visible}table{min-width:0;font-size:10px}td,th{padding:5px}a{color:inherit;overflow-wrap:anywhere}h2{break-after:avoid}tr{break-inside:avoid}}
</style><main><header><small style="color:#c2d6ef">조사-전자레인지-광파오븐-20261120 · 공개자료 조사</small><h1>전자레인지와 광파오븐,<br>코로나 전후 무엇을 비교할 수 있나</h1><p>한국 중심 · 판매 / 구매 관련 지표 / 보유·이용 / 수출입 / 검색 관심 참고<br>수집일 2026년 11월 20일</p></header>'''
html+=f'<div class="card"><b>정리 규모</b><p>출처·자료 경로 {len(sources)}건, 공개 수치 관측 {len(rows)}개. WITS 연도별 페이지 13건을 포함하며, 서로 독립적인 조사 {len(sources)}개라는 뜻은 아닙니다. 계산값 {len(derived)}행은 공개 수치 개수와 분리했습니다.</p>'+''.join(f'<span class="pill">{escape(k)} {v}</span>' for k,v in stats.items())+'</div>'
html+='<div class="note"><b>[해석-01] 현재 확보한 자료로는 전국 구매율의 승자를 판정할 수 없습니다.</b><p>광파오븐은 복합형 오븐의 일부이고, 일부 통계는 전자레인지와 기능·분류가 겹칩니다. 특정 브랜드 판매 증가, 유통채널 점유율, 가구 보유 응답, 통관 수출액은 각각의 분모를 유지해야 합니다.</p></div>'
html+='<h2>1. 바로 활용할 수 있는 비교 근거</h2>'+fact_html
html+='<p>보유 응답의 코로나 이전 수치는 '+link('S05')+'에서 확인했습니다. 관측된 전후 변화만으로 코로나의 인과 효과를 확정할 수 없습니다.</p>'
html+='<h2>2. 한국 전자레인지 수출입: 2018~2024년</h2><p>[무역-01] HS851650 기준입니다. 수입액은 백만USD, 수출액은 천USD로 명시했습니다. 수출의 작은 규모가 한국 브랜드의 세계 판매 감소를 곧바로 뜻하지는 않습니다.</p>'
html+=table(['연도','수입액(백만USD)','수입액 전년비(계산)','표시 수입수량(개)','수출액(천USD)','출처'],trade_table)
growth20=(imports[2][1]/imports[1][1]-1)*100
growth21=(imports[3][1]/imports[1][1]-1)*100
html+=f'<p>[계산-01] 수입액은 2019→2020년 {growth20:+.2f}%, 2019→2021년 {growth21:+.2f}%입니다. 2022년에는 수입액이 늘었지만 표시 수량은 줄었습니다. 통관금액 증가를 구매자·판매대수 증가로 바꾸어 읽지 않아야 합니다. 중국·말레이시아발 수입액도 전체 수치 목록에 포함했습니다.</p>'
html+='<p>[무역-02] 한국 통관 수출액 감소는 코로나 이전인 2018→2019년에도 관측됩니다. 이후의 감소를 코로나만의 효과로 설명할 수 없습니다. 생산거점·품목분류·신고구조 변화의 기여는 이번 자료만으로 확인되지 않았습니다.</p>'
html+='<h2>3. 관심도·구매 고려: 확보한 값과 남은 공백</h2><p>[관심-01] 코로나 당시의 제품별 월별 검색 관심도는 확보하지 못했습니다. 아래는 현재의 제3자 참고값입니다. 갱신일이 달라 두 값을 나눠 검색 점유율이나 관심 배수를 만들지 않았습니다.</p>'+current
html+='<p>[관심-02] 코로나기 소비자 조사로는 '+link('S09')+'의 사이즈·브랜드·성능 고려도와 온라인 구매채널 이용률을 확보했습니다. 이 값은 가전 전반의 맥락이며, 광파오븐과 전자레인지의 개별 구매의향 비교를 대신하지 않습니다.</p>'
html+='<div class="card"><b>[추가수집-01] 관심도 비교 조건</b><p>2018.01~2024.12 월 단위로 전자레인지·전자렌지를 한 그룹, 광파오븐·광파 오븐을 다른 그룹으로 묶고 동일 요청 안에서 비교합니다. 복합오븐·큐커는 별도 민감도 분석으로 둡니다. 네이버는 국내 검색, Google은 대한민국 지역으로 맞춥니다.</p><p>상대지수는 검색횟수나 구매율이 아닙니다. 동일 조건의 원자료를 받은 뒤 각 제품의 2019년 월평균을 100으로 재지수화하면 시기별 변화는 비교하기 좋지만, 제품 간 절대 검색량 차이는 사라집니다. 두 비교 목적을 구분해야 합니다.</p><p>공식 설명: '+link('S19')+' / '+link('S20')+'</p></div>'
html+='<h2>4. 어떤 문장까지 근거로 쓸 수 있나</h2><ul><li>[해석-02] “코로나기에 LG의 인공지능쿡 탑재 광파오븐 판매가 증가했다”는 S01로 뒷받침됩니다. 전체 시장 확대 폭으로 일반화하지 않습니다.</li><li>[해석-03] “전자레인지는 널리 보유된 제품이고, 다나와의 복합형 오븐 판매는 2022년 증가했다”는 각각의 자료로 설명할 수 있습니다. 두 제품이 서로를 대체했다는 것은 추가 검증이 필요한 가설입니다.</li><li>[해석-04] 가전 전반의 온라인화와 사이즈 고려 증가는 비교의 배경입니다. 두 제품만의 관심 변화나 구매전환 개선이 입증된 것은 아닙니다.</li></ul>'
html+='<h2>5. 전체 수치 목록</h2><p>검색창은 이 표의 제품·기간·지표·출처·제한을 함께 검색합니다. 공개값을 수기로 구조화했으며, 원문 전체를 복제한 크롤링 덤프가 아닙니다.</p><label for="filter">수치 검색 </label><input id="filter" placeholder="예: 광파오븐, 2020, 총수입액, 관심">'
html+='<section id="observations">'+all_rows+'</section>'
html+='<h2>6. 출처 목록 및 열람 상태</h2>'+catalog
html+='<h2>7. 미확보·추가 검증 항목</h2><ul>'+''.join(f'<li>{escape(g)}</li>' for g in gaps)+'</ul>'
html+='<p>[수집-01] 같은 LG 발표를 재전송한 여러 기사는 중복 근거로 세지 않았습니다. 순위형 제휴 블로그, 출처 불명 확정 수치, PDF 차트 막대의 임의 근삿값은 제외했습니다. 공개 열람 도구만 사용했고 유료 Firecrawl 호출·계정 신규 등록·토론 세션 실행은 하지 않았습니다.</p>'
html+='<p><a href="evidence.json">구조화 수치·출처 JSON</a> · <a href="collection_notes.txt">수집 기록과 미확보 사항</a></p><script>document.getElementById("filter").addEventListener("input",function(){const q=this.value.toLowerCase();document.querySelectorAll("#observations tbody tr").forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q));});</script></main></html>'
(ROOT/'report.html').write_text(html,encoding='utf-8')
notes = [f'[수집-기록-01] 전자레인지·광파오븐 공개자료 조사 / {DATE}',
         f'출처 경로 {len(sources)}건, 공개 수치 {len(rows)}개, 파생 계산표 {len(derived)}행.',
         '파일: report.html(읽기·수치 검색), evidence.json(전체 구조화 데이터), build_report.py(오프라인 재생성).',
         '보고서·JSON은 원문 수치의 구조화·요약이며 기사·PDF 전문 수집본이 아니다.',
         '기존 세션·원본 발언·완료 자료는 수정하지 않았다.',
         '', '[수집-기록-02] 방법',
         '전자레인지/전자렌지, 광파오븐, 복합형 오븐의 판매·보유·관심·수출 관련 검색을 병행했다.',
         '한국 공식 통계·기업 원발표·시장조사기관·유통 판매 분석을 우선했다.',
         '같은 발표를 전재한 기사들은 별도 조사로 집계하지 않았다.',
         '세계은행 WITS는 HS851650, 한국 신고, 전세계 상대국, 연간 수입·수출 페이지에서 값을 확인했다.',
         '2019년 수출은 WITS 열람 실패로 KAIT의 반올림값을 별도 보존했다.',
         'PDF 원문을 로컬로 내려받으려는 네트워크 요청도 연결 거부되어 원문 PDF 파일은 저장하지 못했다.',
         '웹 PDF 스크린샷 실패 자료는 이미지 검증 완료로 취급하지 않았다.',
         '', '[수집-기록-03] 분석 범위', json.dumps(design,ensure_ascii=False,indent=2),
         '', '[수집-기록-04] 미확보', *gaps, '', '[수집-기록-05] 출처 경로']
notes += [f'{s["ID"]} | {s["제목"]} | {s["열람상태"]}\n{s["URL"]}\n{s["확인사항"]}' for s in sources]
(ROOT/'collection_notes.txt').write_text('\n'.join(notes),encoding='utf-8')
print(json.dumps({'출처경로':len(sources),'공개수치':len(rows),'계산표행':len(derived),'지표군':dict(stats)},ensure_ascii=False))
