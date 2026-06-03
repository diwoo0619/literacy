import os
import sqlite3
import urllib.request
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import streamlit as st
from scipy import stats

# ── 한글 폰트 설정 ───────────────────────────────────────────────
def setup_korean_font():
    font_path = "/tmp/NanumGothic.ttf"
    if not os.path.exists(font_path):
        try:
            url = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
            urllib.request.urlretrieve(url, font_path)
        except Exception:
            plt.rcParams['axes.unicode_minus'] = False
            return
    fm.fontManager.addfont(font_path)
    prop = fm.FontProperties(fname=font_path)
    plt.rcParams['font.family'] = prop.get_name()
    plt.rcParams['axes.unicode_minus'] = False

setup_korean_font()

# ── 색상 상수 ───────────────────────────────────────────────────
BLUE       = '#1E5FAA'
LIGHT_BLUE = '#5B8DD9'
CORAL      = '#D85A30'
AMBER      = '#EF9F27'
TEAL       = '#1D9E75'
GRAY       = '#888780'

# ── 페이지 설정 ─────────────────────────────────────────────────
st.set_page_config(
    page_title="한국 문해력 저하 원인 분석",
    page_icon="📚",
    layout="wide"
)

DB_FILE = "경영정보처리론2조.db"

if not os.path.exists(DB_FILE):
    st.error(f"⚠️ 데이터베이스 파일({DB_FILE})이 없습니다. 같은 폴더에 파일을 넣어주세요.")
    st.stop()

@st.cache_resource
def get_conn():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

conn = get_conn()

# ── 헤더 ────────────────────────────────────────────────────────
st.title("📚 한국 문해력 저하 원인 분석")
st.markdown("""
**독서량 감소, OTT·SNS 미디어 이용 증가, 코로나19 대면 소통 단절**이 한국인의 문해력에 미치는 영향을
세대·학력별로 비교·분석합니다. 데이터 출처: 교육부 학업성취도평가, 국가평생교육진흥원 성인문해능력조사,
문화체육관광부 국민독서실태조사, KISDI 미디어패널조사.
""")
st.divider()

# ── 사이드바 ────────────────────────────────────────────────────
st.sidebar.title("📊 차트 선택")
chart_options = {
    "전체 보기": "all",
    "차트 1 — 기초학력 미달률 추이": "chart1",
    "차트 2 — 코로나 전후 t-test": "chart2",
    "차트 3 — 연령대별 문해력 변화": "chart3",
    "차트 4 — 전략A: 청년층 Gap 변화": "chart6",
    "차트 5 — OTT 이용 ↔ 문해력": "chart5",
    "차트 6 — 독서시간 ↔ 문해력": "chart4",
    "차트 7 — 전략B: 독서 vs OTT 트레이드오프": "chart7",
    "차트 8 — 디지털 네이티브 역설": "chart8",
    "차트 9 — PIAAC 학력통제 편상관": "chart9",
}
selected = st.sidebar.radio("보고 싶은 차트를 선택하세요", list(chart_options.keys()))
mode = chart_options[selected]

def show_sql(sql):
    with st.expander("🔍 사용한 SQL 보기"):
        st.code(sql, language="sql")


# ════════════════════════════════════════════════
# 차트 1
# ════════════════════════════════════════════════
def render_chart1():
    st.subheader("📈 차트 1 — 코로나 전후 기초학력 미달률 추이 (중학교)")
    sql = """
        SELECT year, subject, fail_rate
        FROM 기초학력미달률_전처리
        WHERE school_type='중학교' AND year IS NOT NULL
        ORDER BY year, subject
    """
    df = pd.read_sql(sql, conn)
    fig, ax = plt.subplots(figsize=(11, 5))
    colors = {'국어': BLUE, '수학': AMBER, '영어': TEAL}
    for subj, grp in df.groupby('subject'):
        ax.plot(grp['year'], grp['fail_rate'], marker='o',
                label=subj, color=colors.get(subj, GRAY), linewidth=2.2, markersize=6)
        for _, row in grp.iterrows():
            ax.annotate(f"{row['fail_rate']:.1f}",
                        (row['year'], row['fail_rate']),
                        textcoords="offset points", xytext=(0, 8),
                        ha='center', fontsize=8, color=colors.get(subj, GRAY))
    ax.axvspan(2019.5, 2024.5, alpha=0.10, color='red', label='코로나 이후(2020~)')
    ax.axvline(2019.5, color='red', linestyle='--', linewidth=1, alpha=0.5)
    ax.text(2019.7, ax.get_ylim()[1] * 0.95, '코로나 이후 →', color='red', fontsize=9, alpha=0.7)
    ax.set_xlabel('연도')
    ax.set_ylabel('기초학력 미달률 (%)')
    ax.set_title('중학교 과목별 기초학력 미달률 추이 (2015~2024)', fontsize=13, fontweight='bold')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    ax.set_xticks(sorted(df['year'].unique()))
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()
    show_sql(sql)
    st.info("""
💡 **인사이트**
- 중학교 국어 미달률이 2019년 4.1%에서 2022년 11.3%로 약 3배 급등했으며, 코로나 이후에도 10% 수준을 유지하고 있습니다.
- 수학은 코로나 이전부터 높은 미달률을 보인 반면, 국어는 코로나를 기점으로 급격히 상승해 현재 수학과 유사한 수준에 도달했습니다.
- 국어 미달률의 이례적 급등은 단순 학습 공백이 아닌 대면 소통 단절에 따른 언어 발달 훼손 가능성을 시사합니다.
""")


# ════════════════════════════════════════════════
# 차트 2
# ════════════════════════════════════════════════
def render_chart2():
    st.subheader("📊 차트 2 — 코로나 전후 중학교 국어 미달률 비교 (t-test)")
    sql = """
        SELECT corona_period, fail_rate
        FROM 기초학력미달률_전처리
        WHERE school_type='중학교' AND subject='국어' AND year IS NOT NULL
    """
    df = pd.read_sql(sql, conn)
    pre  = df[df['corona_period'] == 0]['fail_rate'].values
    post = df[df['corona_period'] == 1]['fail_rate'].values
    t_stat, p_val = stats.ttest_ind(pre, post)
    pre_mean, post_mean = pre.mean(), post.mean()

    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(
        ['코로나 이전\n(2015~2019)', '코로나 이후\n(2020~2024)'],
        [pre_mean, post_mean],
        color=[BLUE, CORAL], width=0.5, edgecolor='white'
    )
    for bar, val in zip(bars, [pre_mean, post_mean]):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.15,
                f'{val:.2f}%', ha='center', fontsize=13, fontweight='bold')
    significance = "통계적으로 유의 (p < 0.05)" if p_val < 0.05 else "유의하지 않음"
    ax.set_title('중학교 국어 기초학력 미달률 — 코로나 전후 비교', fontsize=13, fontweight='bold')
    ax.set_ylabel('평균 미달률 (%)')
    ax.set_ylim(0, max(pre_mean, post_mean) * 1.3)
    ax.grid(axis='y', alpha=0.3)
    fig.text(0.5, -0.02,
             f't = {t_stat:.3f},  p = {p_val:.4f}  |  {significance}',
             ha='center', fontsize=11,
             color='#993C1D' if p_val < 0.05 else GRAY)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    col1, col2, col3 = st.columns(3)
    col1.metric("코로나 이전 평균", f"{pre_mean:.2f}%")
    col2.metric("코로나 이후 평균", f"{post_mean:.2f}%", f"+{post_mean - pre_mean:.2f}%p")
    col3.metric("p값", f"{p_val:.4f}", "유의" if p_val < 0.05 else "비유의")
    show_sql(sql)
    st.info("""
💡 **인사이트**
- 코로나 이전(2015~2019) 평균 3.14%에서 코로나 이후(2020~2024) 평균 8.58%로 약 2.7배 증가했으며, 이 차이는 통계적으로 유의합니다.
- 5 vs 5 균형 비교로 검정력을 확보했으며, 코로나 이후에도 미달률이 회복되지 않고 있다는 점이 핵심입니다.
- 상관관계이며 코로나가 직접적 원인임을 증명하는 것은 아니나, 언어 발달 환경의 훼손이 지속되고 있다는 신호로 해석됩니다.
""")


# ════════════════════════════════════════════════
# 차트 3
# ════════════════════════════════════════════════
def render_chart3():
    st.subheader("📊 차트 3 — 연령대별 문해력 수준4 비율 변화 (2017·2020·2023)")
    sql = """
        SELECT l.survey_year, a.age_group_label, l.level4_pct
        FROM 문해능력조사 l
        JOIN "연령대 기준" a ON CAST(l.age_group_id AS INTEGER) = a.age_group_id
        WHERE l.category_type='age'
        ORDER BY a.age_group_id, l.survey_year
    """
    df = pd.read_sql(sql, conn)
    pivot = df.pivot(index='age_group_label', columns='survey_year', values='level4_pct')
    age_order = ['18~29세', '30~39세', '40~49세', '50~59세', '60세이상']
    pivot = pivot.reindex([a for a in age_order if a in pivot.index])

    x = np.arange(len(pivot))
    width = 0.25
    years = sorted(df['survey_year'].unique())
    year_colors = {2017: BLUE, 2020: LIGHT_BLUE, 2023: TEAL}

    fig, ax = plt.subplots(figsize=(11, 5))
    for i, yr in enumerate(years):
        if yr in pivot.columns:
            bars = ax.bar(x + i * width, pivot[yr], width,
                          label=f'{yr}년', color=year_colors[yr], alpha=0.85)
            for bar in bars:
                if bar.get_height() > 0:
                    ax.text(bar.get_x() + bar.get_width() / 2,
                            bar.get_height() + 0.5,
                            f'{bar.get_height():.1f}', ha='center', fontsize=8)
    ax.set_title('연령대별 문해력 수준4(충분한 문해력) 비율 변화', fontsize=13, fontweight='bold')
    ax.set_xlabel('연령대')
    ax.set_ylabel('수준4 비율 (%)')
    ax.set_xticks(x + width)
    ax.set_xticklabels(pivot.index)
    ax.legend()
    ax.set_ylim(0, 115)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()
    show_sql(sql)
    st.warning("⚠️ **주의**: 연도별 표본 설계와 판정 기준이 달라 수치를 직접 비교하기보다 추세 방향만 해석해야 합니다.")
    st.info("""
💡 **인사이트**
- 18~29세는 세 연도 모두 90% 이상의 수준4 비율을 유지하며 상대적으로 높은 문해력을 보입니다.
- 60세 이상에서 수준4 비율이 가장 낮으며, 학력 수준과 문해력의 상관관계가 뚜렷합니다.
- 전체 평균은 개선 추세처럼 보이나, 학력별 분해 시 저학력층에서 역행 현상이 나타납니다.
""")


# ════════════════════════════════════════════════
# 차트 4
# ════════════════════════════════════════════════
def render_chart4():
    st.subheader("📊 차트 4 — 연령대별 독서시간 vs 문해력 수준4 (2023)")
    sql = """
        SELECT a.age_group_label, r.avg_read_min_total, l.level4_pct
        FROM 독서실태조사 r
        JOIN 문해능력조사 l ON r.age_group_id = CAST(l.age_group_id AS INTEGER)
        JOIN "연령대 기준" a ON r.age_group_id = a.age_group_id
        WHERE l.survey_year=2023 AND l.category_type='age'
        ORDER BY r.age_group_id
    """
    df = pd.read_sql(sql, conn)
    r_val, p_val = stats.pearsonr(df['avg_read_min_total'], df['level4_pct'])

    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax2 = ax1.twinx()
    x = np.arange(len(df))
    bars = ax1.bar(x, df['avg_read_min_total'], color=BLUE, alpha=0.7,
                   label='평균 독서시간(분)', width=0.4)
    for bar, val in zip(bars, df['avg_read_min_total']):
        ax1.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 0.5, f'{val:.1f}분',
                 ha='center', fontsize=9, color=BLUE)
    ax2.plot(x, df['level4_pct'], marker='o', color=CORAL,
             linewidth=2.2, markersize=7, label='수준4 비율(%)')
    for xi, yi in zip(x, df['level4_pct']):
        ax2.annotate(f'{yi:.1f}%', (xi, yi),
                     textcoords="offset points", xytext=(0, 10),
                     ha='center', fontsize=9, color=CORAL)
    ax1.set_xlabel('연령대')
    ax1.set_ylabel('평균 독서시간 (분)', color=BLUE)
    ax2.set_ylabel('수준4 비율 (%)', color=CORAL)
    ax1.set_xticks(x)
    ax1.set_xticklabels(df['age_group_label'])
    ax1.set_ylim(0, max(df['avg_read_min_total']) * 1.4)
    ax2.set_ylim(0, 115)
    ax1.tick_params(axis='y', colors=BLUE)
    ax2.tick_params(axis='y', colors=CORAL)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    ax1.set_title('연령대별 평균 독서시간 vs 문해력 수준4 비율', fontsize=13, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    significance = "p < 0.05" if p_val < 0.05 else f"p = {p_val:.3f}"
    fig.text(0.5, -0.03,
             f'피어슨 상관계수 r = {r_val:.3f}  |  {significance}  (n=5, 연령대 집계값)',
             ha='center', fontsize=10, color=GRAY)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()
    show_sql(sql)
    st.warning("⚠️ 연령대 집계값 간 비교입니다. 개인 단위 인과관계가 아닌 집계 수준 상관관계이며, 연령 효과가 혼재합니다.")
    st.info(f"""
💡 **인사이트**
- 독서시간이 많은 연령대(18~29세)에서 문해력 수준4 비율도 높게 나타나 양의 상관(r = {r_val:.3f})이 확인됩니다.
- 그러나 이는 연령 자체의 효과(교육 수준, 인지 능력 등)가 혼재할 수 있어 독서만의 순수 효과로 해석하기 어렵습니다.
- 독서시간과 문해력의 정적 상관은 확인되나, 인과관계 주장은 제한적입니다.
""")


# ════════════════════════════════════════════════
# 차트 5
# ════════════════════════════════════════════════
def render_chart5():
    st.subheader("📊 차트 5 — 연령대별 OTT 이용시간 vs 문해력 수준4 (2023)")
    sql_media = """
        SELECT m.age_group_id, a.age_group_label,
               AVG(m.OTT_주간총이용시간_분) AS avg_ott_min,
               AVG(CASE WHEN m.SNS_사용여부=1 THEN 100.0 ELSE 0 END) AS sns_pct
        FROM 미디어패널2023 m
        JOIN "연령대 기준" a ON m.age_group_id = a.age_group_id
        GROUP BY m.age_group_id, a.age_group_label
        ORDER BY m.age_group_id
    """
    sql_lit = """
        SELECT CAST(age_group_id AS INTEGER) AS age_group_id, level4_pct
        FROM 문해능력조사
        WHERE survey_year=2023 AND category_type='age'
    """
    df_m = pd.read_sql(sql_media, conn)
    df_l = pd.read_sql(sql_lit, conn)
    df = df_m.merge(df_l, on='age_group_id')
    r_ott, p_ott = stats.pearsonr(df['avg_ott_min'], df['level4_pct'])
    r_sns, p_sns = stats.pearsonr(df['sns_pct'], df['level4_pct'])

    fig, ax1 = plt.subplots(figsize=(10, 5))
    ax2 = ax1.twinx()
    x = np.arange(len(df))
    bars = ax1.bar(x, df['avg_ott_min'], color=AMBER, alpha=0.75,
                   label='OTT 주간 이용시간(분)', width=0.4)
    for bar, val in zip(bars, df['avg_ott_min']):
        ax1.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 1, f'{val:.0f}분',
                 ha='center', fontsize=9, color=AMBER)
    ax2.plot(x, df['level4_pct'], marker='s', color=BLUE,
             linewidth=2.2, markersize=7, label='수준4 비율(%)')
    for xi, yi in zip(x, df['level4_pct']):
        ax2.annotate(f'{yi:.1f}%', (xi, yi),
                     textcoords="offset points", xytext=(0, 10),
                     ha='center', fontsize=9, color=BLUE)
    ax1.set_xlabel('연령대')
    ax1.set_ylabel('OTT 주간 평균 이용시간 (분)', color=AMBER)
    ax2.set_ylabel('수준4 비율 (%)', color=BLUE)
    ax1.set_xticks(x)
    ax1.set_xticklabels(df['age_group_label'])
    ax1.set_ylim(0, max(df['avg_ott_min']) * 1.4)
    ax2.set_ylim(0, 115)
    ax1.tick_params(axis='y', colors=AMBER)
    ax2.tick_params(axis='y', colors=BLUE)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    ax1.set_title('연령대별 OTT 주간 이용시간 vs 문해력 수준4 비율', fontsize=13, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    fig.text(0.5, -0.03,
             f'OTT vs 문해력: r = {r_ott:.3f}  |  SNS vs 문해력: r = {r_sns:.3f}  (n=5, 연령대 집계값)',
             ha='center', fontsize=10, color=GRAY)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()
    show_sql(sql_media)
    st.warning("⚠️ 연령대 집계값 간 비교입니다. 개인 단위 데이터가 아니므로 생태학적 오류 가능성을 명시합니다.")
    st.info(f"""
💡 **인사이트**
- OTT 이용시간이 가장 많은 18~29세(주간 221분)에서 문해력 수준4 비율도 가장 높아(97.3%), "OTT가 문해력을 낮춘다"는 단순 가설에 의문을 제기합니다.
- 이는 연령 효과(젊을수록 교육 수준 높고 OTT도 많이 이용)가 미디어 효과보다 크게 작용하는 결과로 해석됩니다.
- OTT vs 문해력 상관(r = {r_ott:.3f})은 양의 방향으로, 미디어 이용과 문해력의 관계는 단순하지 않음을 보여줍니다.
""")




# ════════════════════════════════════════════════
# 차트 6 — 전략 A: 청년층 상대적 Gap 변화
# ════════════════════════════════════════════════
def render_chart6():
    st.subheader("📊 차트 6 — 전략A: 전체 평균 대비 연령대별 문해력 우위(Gap) 변화")
    st.markdown("""
    절대값이 아닌 **'전체 평균 대비 각 연령대의 격차(Gap)'** 를 봅니다.
    절대 점수는 올라도 상대적 우위가 좁혀지고 있다면 문해력 하락의 신호입니다.
    """)

    sql = """
        SELECT survey_year, category_type,
               CAST(age_group_id AS INTEGER) AS age_group_id,
               level4_pct
        FROM 문해능력조사
        WHERE category_type IN ('age','total')
        ORDER BY survey_year, category_type
    """
    df = pd.read_sql(sql, conn)

    rows = []
    for year in [2017, 2020, 2023]:
        total = df[(df['survey_year']==year) & (df['category_type']=='total')]['level4_pct'].values[0]
        ages  = df[(df['survey_year']==year) & (df['category_type']=='age')]
        for _, row in ages.iterrows():
            rows.append({
                'survey_year':   year,
                'age_group_id':  row['age_group_id'],
                'level4_pct':    row['level4_pct'],
                'total_avg':     total,
                'gap':           round(row['level4_pct'] - total, 1)
            })
    df_gap = pd.DataFrame(rows)

    # 연령대 레이블
    age_label = {1:'18~29세', 2:'30~39세', 3:'40~49세', 4:'50~59세', 5:'60세이상'}
    df_gap['age_label'] = df_gap['age_group_id'].map(age_label)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 왼쪽: 연도별 Gap 라인 (연령대별)
    ax = axes[0]
    colors_age = {1: BLUE, 2: LIGHT_BLUE, 3: TEAL, 4: AMBER, 5: CORAL}
    for aid, grp in df_gap.groupby('age_group_id'):
        grp = grp.sort_values('survey_year')
        ax.plot(grp['survey_year'], grp['gap'], marker='o',
                label=age_label[aid], color=colors_age[aid], linewidth=2)
        for _, row in grp.iterrows():
            ax.annotate(f"{row['gap']:+.1f}",
                        (row['survey_year'], row['gap']),
                        textcoords="offset points", xytext=(0, 8),
                        ha='center', fontsize=8, color=colors_age[aid])
    ax.axhline(0, color='black', linewidth=0.8, linestyle='--', alpha=0.5)
    ax.set_title('연령대별 문해력 Gap 변화\n(전체평균 대비 %p)', fontsize=11, fontweight='bold')
    ax.set_xlabel('조사연도')
    ax.set_ylabel('Gap (%p)')
    ax.set_xticks([2017, 2020, 2023])
    ax.legend(fontsize=9)
    ax.grid(axis='y', alpha=0.3)

    # 오른쪽: 18~29세 Gap 집중 시각화
    ax2 = axes[1]
    youth = df_gap[df_gap['age_group_id']==1].sort_values('survey_year')
    bars = ax2.bar([2017, 2020, 2023], youth['gap'],
                   color=[BLUE, LIGHT_BLUE, TEAL], width=1.8, alpha=0.85)
    for bar, val in zip(bars, youth['gap']):
        ax2.text(bar.get_x() + bar.get_width()/2,
                 bar.get_height() + 0.2, f'{val:+.1f}%p',
                 ha='center', fontsize=12, fontweight='bold')
    ax2.set_title('18~29세 청년층 문해력 우위 변화\n(전체평균 대비 %p)', fontsize=11, fontweight='bold')
    ax2.set_xlabel('조사연도')
    ax2.set_ylabel('Gap (%p)')
    ax2.set_xticks([2017, 2020, 2023])
    ax2.set_ylim(0, 25)
    ax2.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    # Gap 수치 테이블
    st.markdown("**연도별 Gap 수치 요약**")
    pivot_gap = df_gap.pivot(index='age_label', columns='survey_year', values='gap')
    pivot_gap.columns = [f'{y}년' for y in pivot_gap.columns]
    pivot_gap['변화량\n(2017→2023)'] = (
        df_gap[df_gap['survey_year']==2023].set_index('age_label')['gap'] -
        df_gap[df_gap['survey_year']==2017].set_index('age_label')['gap']
    ).round(1)
    st.dataframe(pivot_gap.style.format("{:+.1f}"), use_container_width=True)

    show_sql(sql)
    st.warning("⚠️ 연도별 표본 설계와 판정 기준이 달라 절대값 직접 비교는 제한됩니다. Gap의 추세 방향만 해석하세요.")
    gap_2017 = float(youth[youth['survey_year']==2017]['gap'])
    gap_2023 = float(youth[youth['survey_year']==2023]['gap'])
    st.info(f"""
💡 **인사이트 (전략 A)**
- 18~29세 청년층의 문해력 우위가 2017년 +{gap_2017:.1f}%p → 2023년 +{gap_2023:.1f}%p로 좁혀지고 있습니다.
- 절대적 수준4 비율은 상승했지만, 전체 평균 대비 상대적 우위는 감소하는 추세입니다.
- 이는 "청년층의 문해력이 절대적으로 낮아졌다"가 아닌 "타 연령대 대비 상대적 강점이 약화되고 있다"는 해석을 가능하게 합니다.
""")


# ════════════════════════════════════════════════
# 차트 7 — 전략 B: 독서시간 vs OTT 트레이드오프
# ════════════════════════════════════════════════
def render_chart7():
    st.subheader("📊 차트 7 — 전략B: 연령대별 독서시간 vs OTT 이용시간 트레이드오프")
    st.markdown("""
    **독서시간(감소)과 OTT 이용시간(증가)** 의 교차 패턴을 통해
    '미디어 대체' 현상과 문해력의 관계를 확인합니다.
    """)

    sql_read = "SELECT age_group_id, avg_read_min_total FROM 독서실태조사 ORDER BY age_group_id"
    sql_ott  = """
        SELECT m.age_group_id, a.age_group_label,
               AVG(m.OTT_주간총이용시간_분) AS avg_ott
        FROM 미디어패널2023 m
        JOIN "연령대 기준" a ON m.age_group_id = a.age_group_id
        GROUP BY m.age_group_id ORDER BY m.age_group_id
    """
    sql_lit  = """
        SELECT CAST(age_group_id AS INTEGER) AS age_group_id, level4_pct
        FROM 문해능력조사
        WHERE survey_year=2023 AND category_type='age'
    """
    df_r = pd.read_sql(sql_read, conn)
    df_o = pd.read_sql(sql_ott,  conn)
    df_l = pd.read_sql(sql_lit,  conn)
    df   = df_r.merge(df_o, on='age_group_id').merge(df_l, on='age_group_id')

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 왼쪽: 독서시간 vs OTT 이중축
    ax  = axes[0]
    ax2 = ax.twinx()
    x   = np.arange(len(df))

    ax.bar(x - 0.2, df['avg_read_min_total'], 0.35,
           color=BLUE, alpha=0.75, label='독서시간(분)')
    ax2.bar(x + 0.2, df['avg_ott'], 0.35,
            color=AMBER, alpha=0.75, label='OTT 이용시간(분)')

    for i, (r, o) in enumerate(zip(df['avg_read_min_total'], df['avg_ott'])):
        ax.text(i-0.2, r+0.5, f'{r:.0f}', ha='center', fontsize=8, color=BLUE)
        ax2.text(i+0.2, o+1,   f'{o:.0f}', ha='center', fontsize=8, color=AMBER)

    ax.set_xlabel('연령대')
    ax.set_ylabel('독서시간 (분/일)', color=BLUE)
    ax2.set_ylabel('OTT 이용시간 (분/주)', color=AMBER)
    ax.set_xticks(x)
    ax.set_xticklabels(df['age_group_label'])
    ax.tick_params(axis='y', colors=BLUE)
    ax2.tick_params(axis='y', colors=AMBER)
    ax.set_title('연령대별 독서시간 vs OTT 이용시간', fontsize=11, fontweight='bold')
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1+lines2, labels1+labels2, loc='upper right', fontsize=9)
    ax.grid(axis='y', alpha=0.3)

    # 오른쪽: 독서시간 대비 문해력 산점도 + 추세선
    ax3 = axes[1]
    sc  = ax3.scatter(df['avg_read_min_total'], df['level4_pct'],
                      c=df['avg_ott'], cmap='YlOrRd_r', s=180,
                      edgecolors='gray', linewidths=0.5, zorder=3)
    plt.colorbar(sc, ax=ax3, label='OTT 이용시간(분/주)')

    # 추세선
    z = np.polyfit(df['avg_read_min_total'], df['level4_pct'], 1)
    p = np.poly1d(z)
    x_line = np.linspace(df['avg_read_min_total'].min(), df['avg_read_min_total'].max(), 100)
    ax3.plot(x_line, p(x_line), color=BLUE, linestyle='--', linewidth=1.5, alpha=0.7)

    for _, row in df.iterrows():
        ax3.annotate(row['age_group_label'],
                     (row['avg_read_min_total'], row['level4_pct']),
                     textcoords="offset points", xytext=(5, 5), fontsize=8)

    from scipy.stats import pearsonr
    r_val, p_val = pearsonr(df['avg_read_min_total'], df['level4_pct'])
    ax3.set_xlabel('평균 독서시간 (분/일)')
    ax3.set_ylabel('문해력 수준4 비율 (%)')
    ax3.set_title(f'독서시간 vs 문해력 산점도\n(점 색상=OTT 이용 많을수록 밝은색)',
                  fontsize=11, fontweight='bold')
    ax3.grid(alpha=0.3)
    ax3.text(0.05, 0.05, f'r = {r_val:.3f}  (p = {p_val:.3f})',
             transform=ax3.transAxes, fontsize=10, color=BLUE,
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    show_sql(sql_ott)
    st.warning("⚠️ 독서시간(2023년)과 OTT 이용시간(2023년)은 같은 연도 집계이나, 서로 다른 조사에서 추출한 데이터입니다.")
    st.info(f"""
💡 **인사이트 (전략 B)**
- 독서시간이 많은 연령대(18~29세: 36분)에서 OTT 이용시간도 가장 많아(221분/주), 단순한 '독서 대체' 구도가 아님을 보여줍니다.
- 산점도에서 독서시간↑ → 문해력↑ 의 양의 상관(r = {r_val:.3f})이 확인되나, OTT 이용시간이 많은 집단(밝은색)이 오히려 문해력도 높은 역설적 패턴이 나타납니다.
- 이는 연령 효과(젊을수록 독서·OTT 모두 많고 교육 수준도 높음)가 미디어 대체 효과를 압도하고 있음을 시사합니다.
""")


# ════════════════════════════════════════════════
# 차트 8 — 디지털 네이티브 역설
# ════════════════════════════════════════════════
def render_chart8():
    st.subheader("📊 차트 8 — 디지털 네이티브 역설")
    st.markdown("""
    **"OTT·SNS를 많이 볼수록 문해력이 낮다"는 가설이 맞는가?**
    데이터가 보여주는 반전을 확인합니다.
    """)

    sql_media = """
        SELECT m.age_group_id, a.age_group_label,
               AVG(CASE WHEN m.OTT_이용여부=1 THEN 100.0 ELSE 0 END) AS ott_usage_pct,
               AVG(CASE WHEN m.SNS_사용여부=1 THEN 100.0 ELSE 0 END) AS sns_usage_pct,
               AVG(m.OTT_주간총이용시간_분) AS avg_ott_min
        FROM 미디어패널2023 m
        JOIN "연령대 기준" a ON m.age_group_id = a.age_group_id
        GROUP BY m.age_group_id, a.age_group_label
        ORDER BY m.age_group_id
    """
    sql_lit = """
        SELECT CAST(age_group_id AS INTEGER) AS age_group_id, level4_pct
        FROM 문해능력조사
        WHERE survey_year=2023 AND category_type='age'
    """
    df_m = pd.read_sql(sql_media, conn)
    df_l = pd.read_sql(sql_lit, conn)
    df   = df_m.merge(df_l, on='age_group_id')

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # ── 왼쪽: OTT 이용률 vs 문해력 이중축 ──
    ax1 = axes[0]
    ax2 = ax1.twinx()
    x   = np.arange(len(df))

    ax1.bar(x, df['ott_usage_pct'], color=AMBER, alpha=0.7,
            label='OTT 이용률(%)', width=0.5)
    ax2.plot(x, df['level4_pct'], marker='o', color=BLUE,
             linewidth=2.5, markersize=8, label='문해력 수준4(%)', zorder=3)

    for i, (o, l) in enumerate(zip(df['ott_usage_pct'], df['level4_pct'])):
        ax1.text(i, o + 0.8, f'{o:.1f}%', ha='center', fontsize=8, color=AMBER)
        ax2.text(i, l + 1.2, f'{l:.1f}%', ha='center', fontsize=8, color=BLUE,
                 fontweight='bold')

    ax1.set_xlabel('연령대')
    ax1.set_ylabel('OTT 이용률 (%)', color=AMBER)
    ax2.set_ylabel('문해력 수준4 비율 (%)', color=BLUE)
    ax1.set_xticks(x)
    ax1.set_xticklabels(df['age_group_label'])
    ax1.set_ylim(0, 120)
    ax2.set_ylim(0, 120)
    ax1.tick_params(axis='y', colors=AMBER)
    ax2.tick_params(axis='y', colors=BLUE)
    ax1.set_title('OTT 이용률이 높은 세대가\n문해력도 높다?', fontsize=11, fontweight='bold')
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1+lines2, labels1+labels2, loc='lower left', fontsize=9)
    ax1.grid(axis='y', alpha=0.3)

    # 두 선이 같은 방향 강조 화살표
    ax1.annotate('', xy=(4, 30), xytext=(0, 90),
                 arrowprops=dict(arrowstyle='->', color='red', lw=1.5))
    ax1.text(2.0, 60, '두 지표 모두\n같은 방향↓', ha='center',
             fontsize=9, color='red', alpha=0.8)

    # ── 오른쪽: SNS 이용률 vs 문해력 이중축 ──
    ax3 = axes[1]
    ax4 = ax3.twinx()

    ax3.bar(x, df['sns_usage_pct'], color=TEAL, alpha=0.7,
            label='SNS 이용률(%)', width=0.5)
    ax4.plot(x, df['level4_pct'], marker='s', color=CORAL,
             linewidth=2.5, markersize=8, label='문해력 수준4(%)', zorder=3)

    for i, (s, l) in enumerate(zip(df['sns_usage_pct'], df['level4_pct'])):
        ax3.text(i, s + 0.8, f'{s:.1f}%', ha='center', fontsize=8, color=TEAL)
        ax4.text(i, l - 4, f'{l:.1f}%', ha='center', fontsize=8, color=CORAL,
                 fontweight='bold')

    ax3.set_xlabel('연령대')
    ax3.set_ylabel('SNS 이용률 (%)', color=TEAL)
    ax4.set_ylabel('문해력 수준4 비율 (%)', color=CORAL)
    ax3.set_xticks(x)
    ax3.set_xticklabels(df['age_group_label'])
    ax3.set_ylim(0, 120)
    ax4.set_ylim(0, 120)
    ax3.tick_params(axis='y', colors=TEAL)
    ax4.tick_params(axis='y', colors=CORAL)
    ax3.set_title('SNS를 많이 쓰는 세대가\n문해력도 높다?', fontsize=11, fontweight='bold')
    lines3, labels3 = ax3.get_legend_handles_labels()
    lines4, labels4 = ax4.get_legend_handles_labels()
    ax3.legend(lines3+lines4, labels3+labels4, loc='lower left', fontsize=9)
    ax3.grid(axis='y', alpha=0.3)

    plt.suptitle('디지털 네이티브 역설 — OTT·SNS 이용이 높은 세대에서 문해력도 높게 나타나는 이유는?',
                 fontsize=12, fontweight='bold', y=1.02)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    show_sql(sql_media)

    # 역설 해설 박스
    st.error("""
🔄 **역설처럼 보이는 이유**
OTT·SNS 이용률이 가장 높은 18~29세(OTT 99.8%, SNS 96.6%)에서 문해력 수준4 비율도 97.3%로 가장 높습니다.
이것만 보면 "미디어를 많이 쓸수록 문해력이 높다"는 잘못된 결론에 도달할 수 있습니다.
    """)
    st.info("""
💡 **역설의 진짜 이유 — 연령 효과**
이 패턴은 미디어가 문해력을 높이기 때문이 아닙니다.
젊을수록 ① 교육 수준이 높고 ② 디지털 기기 이용도 많은 구조적 특성 때문입니다.
즉 **연령 변수 하나가 문해력과 미디어 이용 모두를 동시에 설명**하고 있어서,
둘 사이에 직접적 인과관계가 있는 것처럼 보이는 허위 상관(spurious correlation)입니다.
    """)
    st.warning("""
⚠️ **분석의 한계 명시**
개인 단위 데이터가 아닌 연령대 집계값 비교이므로, 이 결과로 개인 수준의 인과관계를 주장할 수 없습니다.
"미디어가 문해력에 미치는 순수 효과"를 측정하려면 학력·연령을 통제한 개인 단위 회귀분석이 필요합니다.
    """)


# ════════════════════════════════════════════════
# 차트 10 — PIAAC: 학력 통제 편상관
# ════════════════════════════════════════════════
def render_chart9():
    st.subheader("📊 차트 9 — PIAAC 개인단위: 학력 통제 후 독서·ICT ↔ 문해력 편상관")
    st.markdown("""
    기존 분석(집계 데이터 n=5)의 한계를 **PIAAC 개인 단위 데이터(n≈6,100)**로 보완합니다.
    학력 효과를 통제한 후에도 독서활동과 문해력의 양의 상관이 유지되는지 검증합니다.
    """)

    # PIAAC 2023 한국 사전 계산 결과 (원본: prgkorp2.csv, n=6,198)
    simple  = [0.332, 0.356]
    partial = [0.234, 0.267]
    labels  = ['독서활동↔문해력', 'ICT이용↔문해력']
    ns      = [6145,  5981]

    edu_data = pd.DataFrame({
        '학력':     ['중졸이하', '고졸',    '대졸이상'],
        '평균점수': [208.9,     236.6,     264.5],
        '표본수':   [737,       2312,      3113],
    })
    edu_colors = [CORAL, AMBER, BLUE]

    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    # ── 왼쪽: 단순 vs 편상관 막대 ───────────────────────────
    ax  = axes[0]
    x   = np.arange(len(labels))
    w   = 0.35
    b1  = ax.bar(x - w/2, simple,  w, label='단순 상관',        color=BLUE,  alpha=0.85)
    b2  = ax.bar(x + w/2, partial, w, label='학력 통제 편상관', color=TEAL,  alpha=0.85)

    for bar, val in zip(list(b1)+list(b2), simple+partial):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.005,
                f'r={val:.3f}', ha='center', fontsize=9, fontweight='bold')

    for xi, val in zip([0+w/2, 1+w/2], partial):
        ax.text(xi, val+0.025, '***', ha='center', fontsize=12, color=TEAL)

    ax.axhline(0, color='black', linewidth=0.8)
    ax.set_title('단순 상관 vs 학력 통제 편상관
(PIAAC 2023 한국, n≈6,100)', fontsize=11, fontweight='bold')
    ax.set_ylabel('피어슨 상관계수 (r)')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 0.5)
    ax.legend(fontsize=9)
    ax.grid(axis='y', alpha=0.3)

    # ── 오른쪽: 학력별 문해력 막대 ─────────────────────────
    ax2 = axes[1]
    bars = ax2.bar(edu_data['학력'], edu_data['평균점수'],
                   color=edu_colors, alpha=0.85, width=0.5)
    for bar, score, n in zip(bars, edu_data['평균점수'], edu_data['표본수']):
        ax2.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1,
                 f'{score:.0f}점
(n={n:,})', ha='center', fontsize=9, fontweight='bold')

    ax2.set_title('학력별 평균 문해력 점수
(PIAAC 2023 한국)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('문해력 평균 점수')
    ax2.set_ylim(150, 310)
    ax2.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    # 결과 테이블
    st.markdown("**편상관 분석 결과 상세**")
    result_df = pd.DataFrame({
        '변수':             ['독서활동↔문해력', 'ICT이용↔문해력'],
        '단순 r':           [f'{simple[0]:.3f}',  f'{simple[1]:.3f}'],
        '단순 p':           ['<0.0001', '<0.0001'],
        '학력통제 편상관 r': [f'{partial[0]:.3f}', f'{partial[1]:.3f}'],
        '학력통제 p':       ['<0.0001', '<0.0001'],
        'n':               [f'{ns[0]:,}', f'{ns[1]:,}'],
    })
    st.dataframe(result_df, use_container_width=True, hide_index=True)

    st.info(f"""
💡 **인사이트 (PIAAC 개인단위 분석)**
- 독서활동↔문해력: 학력 통제 전 r=+{simple[0]:.3f} → 학력 통제 후 r=+{partial[0]:.3f}. 학력 효과를 제거해도 독서와 문해력의 양의 상관이 유의하게 유지됩니다(p<0.0001, n=6,145).
- ICT이용↔문해력: 학력 통제 후에도 r=+{partial[1]:.3f}로 양의 상관 유지. 디지털 네이티브 역설이 개인 단위에서도 확인됩니다.
- 학력 통제 후 상관계수가 감소(독서: {simple[0]:.3f}→{partial[0]:.3f})하는 것은 학력 효과가 실제로 존재함을 보여주며, 그 이상의 순수 독서 효과가 있음을 시사합니다.
""")
    st.warning("⚠️ PIAAC의 독서활동 지수(READHOMEC2_T1)는 읽기 활동의 빈도·다양성을 종합한 WLE 지수로, 독서 시간(분)과 다릅니다.")


if mode == "all":
    render_chart1(); st.divider()
    render_chart2(); st.divider()
    render_chart3(); st.divider()
    render_chart6(); st.divider()
    render_chart5(); st.divider()
    render_chart4(); st.divider()
    render_chart7(); st.divider()
    render_chart8(); st.divider()
    render_chart9()
elif mode == "chart1":
    render_chart1()
elif mode == "chart2":
    render_chart2()
elif mode == "chart3":
    render_chart3()
elif mode == "chart4":
    render_chart4()
elif mode == "chart5":
    render_chart5()
elif mode == "chart6":
    render_chart6()
elif mode == "chart7":
    render_chart7()
elif mode == "chart8":
    render_chart8()
elif mode == "chart9":
    render_chart9()

st.divider()
st.caption("데이터 출처: 교육부 학업성취도평가 · 국가평생교육진흥원 · 문화체육관광부 · KISDI | 경기도교육연구원 정책연구 2022-09")
