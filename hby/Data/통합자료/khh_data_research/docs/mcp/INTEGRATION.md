# FastMCP 서버·클라이언트 연결 참고

상태: **설명용 예시 / 실행 미검증**. 전체 업무 서버를 구현한 파일은 아니다. 프로젝트에 적용할 의존성 버전은 팀과 먼저 맞춘다.

## 연결 방식 선택

| 상황 | 방식 | 확인할 점 |
| --- | --- | --- |
| 함수·MCP 계약 테스트 | `Client(mcp)` 메모리 내 연결 | 네트워크 없이 스키마·직렬화·호출을 점검 |
| 개인 로컬 개발 | stdio | Client가 프로세스를 실행, Python 절대 경로와 작업 경로 확인 |
| 여러 팀원이 접근하는 Backend | Streamable HTTP | 서버 주소, 인증, timeout, 배포 생명주기 확인 |

위 방식은 [FastMCP 테스트](https://gofastmcp.com/servers/testing)와 [서버 실행](https://gofastmcp.com/deployment/running-server)에 설명되어 있다. HTTP를 켠 것만으로 인증이 생기지 않는다. FastMCP의 기본 `auth=None` 동작과 HTTP 인증 설정은 [인증 문서](https://gofastmcp.com/servers/auth/authentication)를 확인한다. 로컬 Mock 개발은 loopback에 두고, 공유 배포는 인증 사용자와 계약 소유권 검사를 구현한다.

## 1단계: 계약 조회 하나로 왕복 확인

아래는 저장소 루트에 `server_demo.py`를 만든다고 가정한 학습 예시다. C001 합성 데이터만 읽으며 실제 서비스 인증을 구현하지 않는다. 운영 인터페이스는 [도구 계약](TOOL_CONTRACTS.md)에 맞춰 확장한다.

```python
import json
import sqlite3
from pathlib import Path
from fastmcp import FastMCP

mcp = FastMCP("Move Care reference demo")
db_path = Path(__file__).resolve().parent / "mock" / "lg_move_care.sqlite"

@mcp.tool(annotations={"readOnlyHint": True})
def get_customer_contract(customer_id: str) -> dict:
    """C001 합성 계약의 기본 정보만 조회하는 로컬 학습 예시."""
    data = {"status": "not_found"}
    if customer_id == "C001":
        db = sqlite3.connect(db_path.as_uri() + "?mode=ro", uri=True)
        try:
            row = db.execute(
                "SELECT payload FROM contracts WHERE customer_id = ?",
                (customer_id,),
            ).fetchone()
            if row:
                contract = json.loads(row[0])
                data = {"status": "found", "contract_id": contract["contract_id"],
                        "monthly_base_fee": contract["monthly_base_fee"]}
        finally:
            db.close()
    return {"ok": True, "data": data, "error": None,
            "meta": {"is_synthetic": True}}

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

DB 연결은 호출 안에서 만들고 닫는다. 동기 도구를 여러 worker가 실행하는 환경에서 하나의 SQLite 연결을 전역 공유하는 실수를 피하기 위한 예시다. SQL 값은 바인딩한다. stdio 서버의 일반 로그는 stderr로 보내고 stdout을 임의 `print` 로그로 오염시키지 않는다.

아래 Client 예시는 위 파일을 import할 수 있는 같은 디렉터리에서 실행하는 가정이다. 실제 서버가 없는 현재 자료 저장소에서 바로 실행하는 명령은 아니다.

```python
import asyncio
from fastmcp import Client
from server_demo import mcp

async def check_reference():
    async with Client(mcp) as client:
        catalog = await client.list_tools()
        assert "get_customer_contract" in {tool.name for tool in catalog}
        result = await client.call_tool(
            "get_customer_contract", {"customer_id": "C001"},
            timeout=5.0, raise_on_error=False,
        )
        assert not result.is_error
        assert result.structured_content["data"]["monthly_base_fee"] == 59000

if __name__ == "__main__":
    asyncio.run(check_reference())
```

`.structured_content`는 구조화 JSON, `.is_error`는 도구 실패 표시다. 호출이 연결 오류로 예외를 던지는 경우와 업무 도구가 오류 결과를 반환하는 경우를 나눠 처리한다. `raise_on_error=False`를 썼다고 네트워크 실패까지 정상 응답으로 바뀌지는 않는다. [FastMCP Calling Tools](https://gofastmcp.com/clients/tools).

## 2단계: Agent 담당자에게 넘길 것

| 전달물 | 내용 |
| --- | --- |
| 도구 목록 | 이름·설명·입출력 스키마, 현재 지원 기능 |
| 접속 방법 | stdio 실행 명령 또는 HTTP URL, 환경변수 이름, 버전 |
| 응답 계약 | 정상/보류/오류 예시, `ok`와 `isError`의 대응 |
| 데모 데이터 | C001 정상, C999 없음, C005/C006 경계 시나리오 |
| 호출 정책 | timeout, 재시도, 예약은 같은 idempotency key 재사용 |
| 생명주기 | Client를 여는 곳·닫는 곳, 종료 시 정리 방식 |
| 예약 확인 | 화면 승인과 MCP create 사이에 전달할 서버 발급 증거 |

모든 도구가 읽기인지 쓰기인지 명시하고, 입력 금액을 Agent가 임의 수정할 수 없도록 한다. tool 결과를 자연어 텍스트로 재파싱하지 말고 구조화 데이터를 Backend 응답에 연결한다.

## LangChain은 선택 가능한 Client 계층

기획에 LangChain이 있어도 MCP 도구를 반드시 LLM이 자동 선택해야 하는 것은 아니다. Backend가 정해진 흐름으로 `fastmcp.Client.call_tool()`을 호출하고 LLM은 설명만 만드는 구성도 가능하다. 이는 역할 분리를 위한 설계 선택이다.

자동 도구 호출을 택하면 조사일의 [LangChain 공식 연동 문서](https://docs.langchain.com/oss/python/langchain/mcp)를 확인한다. 현재 안내는 `MCPAdapter`, `langchain[mcp]>=1.4.0`, beta다. 이 자료 묶음에서는 새로운 LangChain 의존성을 설치하거나 기존 Agent 구조를 바꾸지 않았다.

별도 `cx-agent`의 참고 구현에서는 `fastmcp.Client`를 직접 사용하고 `structured_content`를 검증한다. 해당 프로젝트는 TV 상담용이고 도구명·오류 정책·스레드 실행 구조가 다르므로, Move Care에 파일을 그대로 복사하는 대신 접속·응답 처리 방식만 참고한다.

## Inspector로 수동 점검

공식 [MCP Inspector](https://modelcontextprotocol.io/docs/2026-07-28/tools/inspector)는 도구 목록과 호출을 확인할 수 있는 개발 도구다. 조사일 문서는 Node 22.19.0 이상을 요구한다. 사용 시 버전을 고정하고 `--help`로 실제 옵션을 확인한다.

권장 확인 순서: 서버 연결 → 도구 5개 노출 → 필수 필드 검사 → C001 응답 → C999 응답 → 금액·날짜 누락 → 예약 확인 누락. Inspector 연결 성공만으로 업무 규칙이나 동시 예약 처리가 검증되지는 않는다.

## 흔한 문제와 확인 지점

| 증상 | 우선 확인 |
| --- | --- |
| `fastmcp` import 실패 | 실행 Python과 패키지 설치 환경이 같은지, 고정 버전 확인 |
| 서버가 터미널에서 가만히 대기 | stdio는 Client 요청을 기다릴 수 있음. Inspector/Client로 호출 |
| SQLite 파일을 못 찾음 | 현재 작업 디렉터리 대신 설정·파일 위치 기준 절대 경로 사용 |
| 결과가 문자열만 있음 | 반환 모델과 구조화 출력, Client가 읽는 속성 확인 |
| 테스트는 되는데 배포 연결 실패 | HTTP 경로·인증·네트워크 설정·Client/서버 버전 확인 |
| timeout 뒤 예약이 두 번 생김 | 재시도 키 유지와 DB 원자성 확인. timeout이 rollback을 보장하지 않음 |
