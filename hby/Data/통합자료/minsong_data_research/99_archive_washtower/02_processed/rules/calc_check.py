# 규칙 검산용 간단 스크립트 (python3 calc_check.py)
import math

def penalty_rate(used_months, contract_months):
    if contract_months == 24:
        return 0.20 if used_months < 12 else 0.10
    if used_months < 12: return 0.30
    if used_months < 24: return 0.20
    return 0.10

def termination_cost(base_fee, contract_months, used_months, recovery_fee=111000, gift=0, arrears=0):
    remain = max(contract_months - used_months, 0)
    penalty = round(base_fee * remain * penalty_rate(used_months, contract_months)) if remain else 0
    return penalty, penalty + recovery_fee + gift + arrears

def transport_fee(km):
    # [Mock 가정] 10km 이상부터 10km 구간마다 추가 (10~19km=1구간, 20~29km=2구간). 실제 올림 방식은 확인 필요
    if km < 10: return 40000
    if km < 100: return 40000 + 20000 * (int((km - 10) // 10) + 1)
    return 40000 + 180000 + 10000 * (int((km - 100) // 10) + 1)

def relocation_cost(km, free_benefit_left=True):
    base = 0 if free_benefit_left else 97000 + 134000
    return base + transport_fee(km)

p, t = termination_cost(59000, 36, 18)
print("C001 위약금", p, "해지비용", t)            # 212400 / 323400
print("이전 25km(무상 남음)", relocation_cost(25))  # 80000
print("이전 8km(무상 사용)", relocation_cost(8, False))  # 271000
