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

DB_FILE = "경정처2조.db"

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
    "차트 4 — 독서시간 ↔ 문해력": "chart4",
    "차트 5 — OTT 이용 ↔ 문해력": "chart5",
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
# 렌더링
# ════════════════════════════════════════════════
if mode == "all":
    render_chart1(); st.divider()
    render_chart2(); st.divider()
    render_chart3(); st.divider()
    render_chart4(); st.divider()
    render_chart5()
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

st.divider()
st.caption("데이터 출처: 교육부 학업성취도평가 · 국가평생교육진흥원 · 문화체육관광부 · KISDI | 경기도교육연구원 정책연구 2022-09")
