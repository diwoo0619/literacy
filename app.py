"""
한국 문해력 저하 원인 분석 — 다중회귀분석
데이터: 경영정보처리론2조.db > PIAAC_2023_한국 테이블
변수: 독서활동, ICT이용(미디어), 학력, 연령대 → 문해력
"""

import sqlite3
import pandas as pd
import numpy as np
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler

# ── 1. DB 연결 및 데이터 로드 ──────────────────────────────────
conn = sqlite3.connect('경영정보처리론2조.db')  # DB 파일과 같은 폴더에서 실행

df = pd.read_sql('SELECT * FROM PIAAC_2023_한국', conn)
conn.close()

print(f'로드 완료: {len(df):,}행 × {len(df.columns)}열')

# ── 2. 분석 변수 수치 변환 ────────────────────────────────────
for col in ['가정독서활동_지수', 'ICT_가정이용_지수']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

df['문해력'] = pd.to_numeric(df['문해력_평균점수'], errors='coerce')
df['독서']   = pd.to_numeric(df['가정독서활동_지수'], errors='coerce')
df['미디어'] = pd.to_numeric(df['ICT_가정이용_지수'], errors='coerce')
df['학력']   = pd.to_numeric(df['학력_코드'], errors='coerce')
df['연령대'] = pd.to_numeric(df['연령대_코드'], errors='coerce')

# ── 3. 결측값 제거 ────────────────────────────────────────────
valid = df[['문해력', '독서', '미디어', '학력', '연령대']].dropna()
print(f'유효 샘플: {len(valid):,}명')
print()

# ── 4. 기초 통계 확인 ─────────────────────────────────────────
print('=== 기초 통계 ===')
print(valid.describe().round(2).to_string())
print()

# ── 5. 표준화 (Beta 계수 비교를 위해) ────────────────────────
scaler = StandardScaler()
X_scaled = pd.DataFrame(
    scaler.fit_transform(valid[['독서', '미디어', '학력', '연령대']]),
    columns=['독서', '미디어', '학력', '연령대']
)
X = sm.add_constant(X_scaled)
Y = valid['문해력'].values

# ── 6. OLS 다중회귀분석 ──────────────────────────────────────
model = sm.OLS(Y, X).fit()

# ── 7. 전체 결과 출력 ─────────────────────────────────────────
print('=== OLS 회귀분석 전체 결과 ===')
print(model.summary())
print()

# ── 8. 핵심 결과 요약 ─────────────────────────────────────────
print('=' * 55)
print('표준화 회귀계수 (Beta) 요약')
print('=' * 55)
print(f'  R²      = {model.rsquared:.3f}')
print(f'  Adj.R²  = {model.rsquared_adj:.3f}')
print(f'  F통계량 = {model.fvalue:.1f}  (p = {model.f_pvalue:.4f})')
print(f'  n       = {len(valid):,}명')
print()
print(f'  {"변수":<8} {"Beta":>8}  {"p값":>8}  {"유의성":<5}  영향 방향')
print('-' * 55)

var_names = ['독서', '미디어', '학력', '연령대']
for var, coef, pval in zip(var_names, model.params[1:], model.pvalues[1:]):
    sig = '***' if pval < 0.001 else ('**' if pval < 0.01 else ('*' if pval < 0.05 else 'n.s.'))
    direction = '▲ 높을수록 문해력↑' if coef > 0 else '▼ 높을수록 문해력↓'
    print(f'  {var:<8} {coef:>+8.3f}  {pval:>8.4f}  {sig:<5}  {direction}')
print()

# ── 9. 영향력 순위 ────────────────────────────────────────────
print('=== 영향력 크기 순위 (|Beta| 기준) ===')
results = sorted(
    zip(var_names, model.params[1:], model.pvalues[1:]),
    key=lambda x: abs(x[1]), reverse=True
)
for rank, (var, coef, pval) in enumerate(results, 1):
    print(f'  {rank}위: {var} (|β|={abs(coef):.3f})')

print()

# ── 10. 학력별 평균 문해력 (참고) ────────────────────────────
print('=== 학력별 평균 문해력 점수 ===')
edu_map = {1: '중졸이하', 2: '고졸', 3: '대졸이상'}
valid_copy = valid.copy()
valid_copy['학력명'] = valid_copy['학력'].map(edu_map)
print(valid_copy.groupby('학력명')['문해력'].agg(['mean', 'count']).round(1).to_string())
print()

# ── 11. 연령대별 평균 문해력 (참고) ──────────────────────────
print('=== 연령대별 평균 문해력 점수 ===')
age_map = {1: '16~25세', 2: '26~35세', 3: '36~45세', 4: '46~55세', 5: '56~65세'}
valid_copy['연령대명'] = valid_copy['연령대'].map(age_map)
print(valid_copy.groupby('연령대명')['문해력'].agg(['mean', 'count']).round(1).to_string())
