import os
import sqlite3
import urllib.request
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import streamlit as st
from scipy import stats

# ── 한글 폰트 설정 ──────────────────────────────────────────────
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
    "전체 보기":                               "all",
    "차트 1 — 기초학력 미달률 추이":            "chart1",
    "차트 2 — 코로나 전후 t-test":             "chart2",
    "차트 3 — 세대별 문해력 분포":              "chart_box",
    "차트 4 — 전략A: 청년층 Gap 변화":         "chart6",
    "차트 5 — OTT 이용 ↔ 문해력":             "chart5",
    "차트 6 — 디지털 네이티브 역설":            "chart8",
    "차트 7 — 독서시간 ↔ 문해력":              "chart4",
    "차트 8 — 전략B: 독서 vs OTT 트레이드오프": "chart7",
    "차트 9 — PIAAC 다중회귀분석 (보완 분석)":  "chart_regression",
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
    st.subheader("📈 차트 1 — 코로나 전후 기초학력 미달률 추이 (중·고등학교)")
    sql = """
        SELECT year, school_type, subject, fail_rate
        FROM 기초학력미달률_전처리
        WHERE year IS NOT NULL
        ORDER BY year, school_type, subject
    """
    df = pd.read_sql(sql, conn)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    colors = {'국어': BLUE, '수학': AMBER, '영어': TEAL}

    for ax, school in zip(axes, ['중학교', '고등학교']):
        df_s = df[df['school_type'] == school]
        for subj, grp in df_s.groupby('subject'):
            ax.plot(grp['year'], grp['fail_rate'], marker='o',
                    label=subj, color=colors.get(subj, GRAY), linewidth=2.2, markersize=5)
            for _, row in grp.iterrows():
                ax.annotate(f"{row['fail_rate']:.1f}", (row['year'], row['fail_rate']),
                            textcoords="offset points", xytext=(0, 7),
                            ha='center', fontsize=7, color=colors.get(subj, GRAY))
        ax.axvspan(2019.5, 2024.5, alpha=0.10, color='red', label='코로나 이후(2020~)')
        ax.axvline(2019.5, color='red', linestyle='--', linewidth=1, alpha=0.5)
        ax.set_xlabel('연도'); ax.set_ylabel('기초학력 미달률 (%)')
        ax.set_title(f'{school} 과목별 기초학력 미달률 추이', fontsize=11, fontweight='bold')
        ax.legend(fontsize=9); ax.grid(axis='y', alpha=0.3)
        ax.set_xticks(sorted(df['year'].unique()))
        ax.tick_params(axis='x', rotation=45)

    plt.suptitle('기초학력 미달률 추이 (2015~2024)', fontsize=13, fontweight='bold')
    plt.tight_layout()
    st.pyplot(fig); plt.close()
    show_sql(sql)
    st.info("""
💡 **인사이트**
- 중학교 국어 미달률이 2019년 4.1%에서 2022년 11.3%로 약 3배 급등했으며, 고등학교도 4.0%→8.0%로 2배 상승했습니다.
- 수학은 코로나 이전부터 미달률이 높았던 반면, 국어는 코로나를 기점으로 이례적으로 급등해 수학과 유사한 수준에 도달했습니다.
- 중학교가 고등학교보다 국어 미달률 상승폭이 더 크며, 이는 언어 발달 핵심 시기인 중학생 시기의 소통 단절 효과가 더 크게 작용했음을 시사합니다.
""")


# ════════════════════════════════════════════════
# 차트 2
# ════════════════════════════════════════════════
def render_chart2():
    st.subheader("📊 차트 2 — 코로나 전후 국어 미달률 비교 t-test (중·고등학교)")
    sql = """
        SELECT school_type, corona_period, fail_rate
        FROM 기초학력미달률_전처리
        WHERE subject='국어' AND year IS NOT NULL
    """
    df = pd.read_sql(sql, conn)
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    for ax, school in zip(axes, ['중학교', '고등학교']):
        df_s  = df[df['school_type'] == school]
        pre   = df_s[df_s['corona_period'] == 0]['fail_rate'].values
        post  = df_s[df_s['corona_period'] == 1]['fail_rate'].values
        t_stat, p_val = stats.ttest_ind(pre, post)
        pre_mean, post_mean = float(pre.mean()), float(post.mean())

        bars = ax.bar(['코로나 이전\n(2015~2019)', '코로나 이후\n(2020~2024)'],
                      [pre_mean, post_mean], color=[BLUE, CORAL], width=0.45, edgecolor='white')
        for bar, val in zip(bars, [pre_mean, post_mean]):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.12,
                    f'{val:.2f}%', ha='center', fontsize=12, fontweight='bold')
        sig = "유의 (p<0.05)" if p_val < 0.05 else "비유의"
        ax.set_title(f'{school} 국어 미달률\n코로나 전후 비교', fontsize=11, fontweight='bold')
        ax.set_ylabel('평균 미달률 (%)')
        ax.set_ylim(0, max(pre_mean, post_mean) * 1.4)
        ax.grid(axis='y', alpha=0.3)
        ax.text(0.5, 0.04, f't={t_stat:.3f}, p={p_val:.4f} | {sig}',
                transform=ax.transAxes, ha='center', fontsize=9,
                color='#993C1D' if p_val < 0.05 else GRAY,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

    plt.suptitle('국어 기초학력 미달률 — 코로나 전후 비교 (t-test)', fontsize=13, fontweight='bold')
    plt.tight_layout()
    st.pyplot(fig); plt.close()

    st.markdown("**학교급별 상세**")
    cols = st.columns(4)
    for i, school in enumerate(['중학교', '고등학교']):
        df_s = df[df['school_type'] == school]
        pre  = df_s[df_s['corona_period'] == 0]['fail_rate'].values
        post = df_s[df_s['corona_period'] == 1]['fail_rate'].values
        cols[i*2].metric(f"{school} 이전", f"{pre.mean():.2f}%")
        cols[i*2+1].metric(f"{school} 이후", f"{post.mean():.2f}%",
                            f"+{post.mean()-pre.mean():.2f}%p")
    show_sql(sql)
    st.info("""
💡 **인사이트**
- 중학교 국어: 코로나 이전 3.14% → 이후 8.58%로 약 2.7배 증가 (통계적으로 유의).
- 고등학교 국어: 코로나 이전 3.98% → 이후 8.36%로 약 2.1배 증가 (통계적으로 유의).
- 두 학교급 모두 코로나 이후 국어 미달률이 통계적으로 유의하게 상승했으며, 코로나 이후에도 회복되지 않고 있습니다.
- 상관관계이며 코로나가 직접적 원인임을 증명하는 것은 아니나, 언어 발달 환경의 훼손이 지속되고 있다는 신호로 해석됩니다.
""")


# ════════════════════════════════════════════════
# 차트 3 — 전략A: Gap 변화
# ════════════════════════════════════════════════
def render_chart6():
    st.subheader("📊 차트 4 — 전략A: 전체 평균 대비 연령대별 문해력 우위(Gap) 변화")
    st.markdown("""
    절대값이 아닌 **'전체 평균 대비 각 연령대의 격차(Gap)'** 를 봅니다.
    절대 점수는 올라도 상대적 우위가 좁혀지고 있다면 문해력 하락의 신호입니다.
    """)
    sql = """
        SELECT survey_year, category_type,
               CAST(age_group_id AS INTEGER) AS age_group_id, level4_pct
        FROM 문해능력조사
        WHERE category_type IN ('age','total')
        ORDER BY survey_year, category_type
    """
    df = pd.read_sql(sql, conn)
    rows = []
    for year in [2017, 2020, 2023]:
        total = df[(df['survey_year']==year) & (df['category_type']=='total')]['level4_pct'].values[0]
        for _, row in df[(df['survey_year']==year) & (df['category_type']=='age')].iterrows():
            rows.append({'survey_year': year, 'age_group_id': row['age_group_id'],
                         'gap': round(row['level4_pct'] - total, 1)})
    df_gap = pd.DataFrame(rows)
    age_label = {1:'18~29세', 2:'30~39세', 3:'40~49세', 4:'50~59세', 5:'60세이상'}
    df_gap['age_label'] = df_gap['age_group_id'].map(age_label)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    colors_age = {1: BLUE, 2: LIGHT_BLUE, 3: TEAL, 4: AMBER, 5: CORAL}
    ax = axes[0]
    for aid, grp in df_gap.groupby('age_group_id'):
        grp = grp.sort_values('survey_year')
        ax.plot(grp['survey_year'], grp['gap'], marker='o',
                label=age_label[aid], color=colors_age[aid], linewidth=2)
        for _, row in grp.iterrows():
            ax.annotate(f"{row['gap']:+.1f}", (row['survey_year'], row['gap']),
                        textcoords="offset points", xytext=(0, 8),
                        ha='center', fontsize=8, color=colors_age[aid])
    ax.axhline(0, color='black', linewidth=0.8, linestyle='--', alpha=0.5)
    ax.set_title('연령대별 문해력 Gap 변화\n(전체평균 대비 %p)', fontsize=11, fontweight='bold')
    ax.set_xlabel('조사연도'); ax.set_ylabel('Gap (%p)')
    ax.set_xticks([2017, 2020, 2023]); ax.set_xlim(2016, 2024)
    ax.legend(fontsize=9); ax.grid(axis='y', alpha=0.3)

    ax2 = axes[1]
    youth = df_gap[df_gap['age_group_id']==1].sort_values('survey_year')
    bars = ax2.bar([2017, 2020, 2023], youth['gap'],
                   color=[BLUE, LIGHT_BLUE, TEAL], width=1.8, alpha=0.85)
    for bar, val in zip(bars, youth['gap']):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.2,
                 f'{val:+.1f}%p', ha='center', fontsize=12, fontweight='bold')
    ax2.set_title('18~29세 청년층 문해력 우위 변화\n(전체평균 대비 %p)', fontsize=11, fontweight='bold')
    ax2.set_xlabel('조사연도'); ax2.set_ylabel('Gap (%p)')
    ax2.set_xticks([2017, 2020, 2023]); ax2.set_ylim(0, 25)
    ax2.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig); plt.close()

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
# 차트 4 — 세대별 문해력 분포
# ════════════════════════════════════════════════
def render_chart_box():
    st.subheader("📊 차트 3 — 세대별 문해력 점수 분포 (PIAAC 2023 한국)")
    st.markdown("""
    PIAAC 개인 단위 데이터(n=6,198)로 세대별 문해력 점수 분포를 확인합니다.
    평균값 차이뿐 아니라 **분포의 형태와 격차**를 함께 볼 수 있습니다.
    """)
    sql = """
        SELECT 연령대, 연령대_코드,
               CAST(문해력_평균점수 AS REAL) AS 문해력
        FROM PIAAC_2023_한국
        WHERE 문해력_평균점수 IS NOT NULL
        ORDER BY 연령대_코드
    """
    df_p = pd.read_sql(sql, conn)
    df_p['문해력'] = pd.to_numeric(df_p['문해력'], errors='coerce')
    df_p = df_p.dropna(subset=['문해력'])

    age_order  = ['16~25세', '26~35세', '36~45세', '46~55세', '56~65세']
    age_colors = [BLUE, LIGHT_BLUE, TEAL, AMBER, CORAL]
    bp_data     = [df_p[df_p['연령대']==a]['문해력'].values for a in age_order if a in df_p['연령대'].values]
    valid_ages  = [a for a in age_order if a in df_p['연령대'].values]
    valid_colors= [age_colors[age_order.index(a)] for a in valid_ages]

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    ax = axes[0]
    bp = ax.boxplot(bp_data, labels=valid_ages, patch_artist=True,
                    notch=False, showfliers=False,
                    medianprops=dict(color='white', linewidth=2.5))
    for patch, color in zip(bp['boxes'], valid_colors):
        patch.set_facecolor(color); patch.set_alpha(0.8)
    for w in bp['whiskers']: w.set_color(GRAY); w.set_alpha(0.6)
    for c in bp['caps']:     c.set_color(GRAY); c.set_alpha(0.6)
    for i, (age, color) in enumerate(zip(valid_ages, valid_colors), 1):
        ax.text(i, df_p[df_p['연령대']==age]['문해력'].mean() + 4,
                f"{df_p[df_p['연령대']==age]['문해력'].mean():.0f}",
                ha='center', fontsize=9, fontweight='bold', color=color)
    ax.set_title('연령대별 문해력 점수 분포\n(PIAAC 2023 한국)', fontsize=11, fontweight='bold')
    ax.set_ylabel('문해력 평균 점수'); ax.set_ylim(0, 430)
    ax.tick_params(axis='x', rotation=15); ax.grid(axis='y', alpha=0.3)

    ax2 = axes[1]
    parts = ax2.violinplot(bp_data, positions=range(1, len(valid_ages)+1),
                           showmeans=True, showmedians=False)
    for pc, color in zip(parts['bodies'], valid_colors):
        pc.set_facecolor(color); pc.set_alpha(0.7)
    parts['cmeans'].set_color('white'); parts['cmeans'].set_linewidth(2)
    parts['cbars'].set_color(GRAY); parts['cmins'].set_color(GRAY); parts['cmaxes'].set_color(GRAY)
    ax2.set_xticks(range(1, len(valid_ages)+1)); ax2.set_xticklabels(valid_ages, rotation=15)
    ax2.set_title('연령대별 문해력 점수 밀도 분포\n(바이올린 플롯)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('문해력 평균 점수'); ax2.set_ylim(0, 430); ax2.grid(axis='y', alpha=0.3)
    plt.suptitle('세대별 문해력 점수 분포 비교 (PIAAC 2023 한국, n=6,198)', fontsize=12, fontweight='bold')
    plt.tight_layout()
    st.pyplot(fig); plt.close()

    st.markdown("**연령대별 문해력 점수 요약**")
    summary = df_p.groupby('연령대')['문해력'].agg(
        평균=lambda x: round(x.mean(), 1),
        중앙값=lambda x: round(x.median(), 1),
        표준편차=lambda x: round(x.std(), 1),
        n='count'
    ).reindex(valid_ages)
    st.dataframe(summary, use_container_width=True)
    show_sql(sql)
    st.info("""
💡 **인사이트**
- 16~25세(평균 277점)에서 56~65세(평균 213점)로 갈수록 문해력이 뚜렷하게 감소합니다.
- 바이올린 플롯에서 젊은 층은 분포가 좁고 높은 편에 집중되는 반면, 고령층은 분포가 넓고 낮은 점수에 퍼져 있습니다.
- 세대 간 문해력 격차는 단순 평균 차이(64점)뿐 아니라 분포 형태에서도 뚜렷하게 나타납니다.
""")
    st.warning("⚠️ 연령 효과는 세대 차이(교육 환경, 디지털 노출 등) 복합 요인이 반영된 결과로, 단순히 '나이가 들면 문해력이 낮아진다'는 인과 해석은 제한됩니다.")


# ════════════════════════════════════════════════
# 차트 5 — OTT vs 문해력
# ════════════════════════════════════════════════
def render_chart5():
    st.subheader("📊 차트 5 — 연령대별 OTT 이용시간 vs 문해력 수준4 (2023)")
    sql_media = """
        SELECT m.age_group_id, a.age_group_label,
               AVG(m.OTT_주간총이용시간_분) AS avg_ott_min,
               AVG(CASE WHEN m.SNS_사용여부=1 THEN 100.0 ELSE 0 END) AS sns_pct
        FROM 미디어패널2023 m
        JOIN "연령대 기준" a ON m.age_group_id = a.age_group_id
        GROUP BY m.age_group_id, a.age_group_label ORDER BY m.age_group_id
    """
    sql_lit = """
        SELECT CAST(age_group_id AS INTEGER) AS age_group_id, level4_pct
        FROM 문해능력조사 WHERE survey_year=2023 AND category_type='age'
    """
    df_m = pd.read_sql(sql_media, conn)
    df_l = pd.read_sql(sql_lit, conn)
    df   = df_m.merge(df_l, on='age_group_id')
    r_ott, _ = stats.pearsonr(df['avg_ott_min'], df['level4_pct'])
    r_sns, _ = stats.pearsonr(df['sns_pct'],     df['level4_pct'])

    fig, ax1 = plt.subplots(figsize=(12, 5))
    ax2 = ax1.twinx()
    x = np.arange(len(df))
    bars = ax1.bar(x, df['avg_ott_min'], color=AMBER, alpha=0.75, label='OTT 주간 이용시간(분)', width=0.4)
    for bar, val in zip(bars, df['avg_ott_min']):
        ax1.text(bar.get_x()+bar.get_width()/2, bar.get_height()+1, f'{val:.0f}분', ha='center', fontsize=9, color=AMBER)
    ax2.plot(x, df['level4_pct'], marker='s', color=BLUE, linewidth=2.2, markersize=7, label='수준4 비율(%)')
    for xi, yi in zip(x, df['level4_pct']):
        ax2.annotate(f'{yi:.1f}%', (xi, yi), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=9, color=BLUE)
    ax1.set_xlabel('연령대'); ax1.set_ylabel('OTT 주간 평균 이용시간 (분)', color=AMBER)
    ax2.set_ylabel('수준4 비율 (%)', color=BLUE)
    ax1.set_xticks(x); ax1.set_xticklabels(df['age_group_label'], rotation=15)
    ax1.set_ylim(0, max(df['avg_ott_min'])*1.4); ax2.set_ylim(0, 115)
    ax1.tick_params(axis='y', colors=AMBER); ax2.tick_params(axis='y', colors=BLUE)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1+lines2, labels1+labels2, loc='upper right')
    ax1.set_title('연령대별 OTT 주간 이용시간 vs 문해력 수준4 비율', fontsize=13, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    fig.text(0.5, -0.03, f'OTT vs 문해력: r={r_ott:.3f}  |  SNS vs 문해력: r={r_sns:.3f}  (n=5, 연령대 집계값)',
             ha='center', fontsize=10, color=GRAY)
    plt.tight_layout()
    st.pyplot(fig); plt.close()
    show_sql(sql_media)
    st.warning("⚠️ 연령대 집계값 간 비교입니다. 개인 단위 데이터가 아니므로 생태학적 오류 가능성을 명시합니다.")
    st.info(f"""
💡 **인사이트**
- OTT 이용시간이 가장 많은 18~29세(주간 221분)에서 문해력 수준4 비율도 가장 높아(97.3%), "OTT가 문해력을 낮춘다"는 단순 가설에 의문을 제기합니다.
- 이는 연령 효과(젊을수록 교육 수준 높고 OTT도 많이 이용)가 미디어 효과보다 크게 작용하는 결과로 해석됩니다.
- OTT vs 문해력 상관(r={r_ott:.3f})은 양의 방향으로, 미디어 이용과 문해력의 관계는 단순하지 않음을 보여줍니다.
""")


# ════════════════════════════════════════════════
# 차트 6 — 디지털 네이티브 역설
# ════════════════════════════════════════════════
def render_chart8():
    st.subheader("📊 차트 6 — 디지털 네이티브 역설")
    st.markdown("""
    **"OTT·SNS를 많이 볼수록 문해력이 낮다"는 가설이 맞는가?**
    데이터가 보여주는 반전을 확인합니다.
    """)
    sql_media = """
        SELECT m.age_group_id, a.age_group_label,
               AVG(CASE WHEN m.OTT_이용여부=1 THEN 100.0 ELSE 0 END) AS ott_usage_pct,
               AVG(CASE WHEN m.SNS_사용여부=1 THEN 100.0 ELSE 0 END) AS sns_usage_pct
        FROM 미디어패널2023 m
        JOIN "연령대 기준" a ON m.age_group_id = a.age_group_id
        GROUP BY m.age_group_id, a.age_group_label ORDER BY m.age_group_id
    """
    sql_lit = """
        SELECT CAST(age_group_id AS INTEGER) AS age_group_id, level4_pct
        FROM 문해능력조사 WHERE survey_year=2023 AND category_type='age'
    """
    df_m = pd.read_sql(sql_media, conn)
    df_l = pd.read_sql(sql_lit, conn)
    df   = df_m.merge(df_l, on='age_group_id')

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    x = np.arange(len(df))

    ax1 = axes[0]; ax2 = ax1.twinx()
    ax1.bar(x, df['ott_usage_pct'], color=AMBER, alpha=0.7, label='OTT 이용률(%)', width=0.5)
    ax2.plot(x, df['level4_pct'], marker='o', color=BLUE, linewidth=2.5, markersize=8, label='문해력 수준4(%)', zorder=3)
    for i, (o, l) in enumerate(zip(df['ott_usage_pct'], df['level4_pct'])):
        ax1.text(i, o+0.8, f'{o:.1f}%', ha='center', fontsize=8, color=AMBER)
        ax2.text(i, l+1.2, f'{l:.1f}%', ha='center', fontsize=8, color=BLUE, fontweight='bold')
    ax1.set_xlabel('연령대'); ax1.set_ylabel('OTT 이용률 (%)', color=AMBER)
    ax2.set_ylabel('문해력 수준4 비율 (%)', color=BLUE)
    ax1.set_xticks(x); ax1.set_xticklabels(df['age_group_label'])
    ax1.set_ylim(0, 120); ax2.set_ylim(0, 120)
    ax1.tick_params(axis='y', colors=AMBER); ax2.tick_params(axis='y', colors=BLUE)
    ax1.set_title('OTT 이용률이 높은 세대가\n문해력도 높다?', fontsize=11, fontweight='bold')
    lines1, l1 = ax1.get_legend_handles_labels(); lines2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1+lines2, l1+l2, loc='lower left', fontsize=9)
    ax1.grid(axis='y', alpha=0.3)
    ax1.annotate('', xy=(4, 30), xytext=(0, 90), arrowprops=dict(arrowstyle='->', color='red', lw=1.5))
    ax1.text(2.0, 60, '두 지표 모두\n같은 방향↓', ha='center', fontsize=9, color='red', alpha=0.8)

    ax3 = axes[1]; ax4 = ax3.twinx()
    ax3.bar(x, df['sns_usage_pct'], color=TEAL, alpha=0.7, label='SNS 이용률(%)', width=0.5)
    ax4.plot(x, df['level4_pct'], marker='s', color=CORAL, linewidth=2.5, markersize=8, label='문해력 수준4(%)', zorder=3)
    for i, (s, l) in enumerate(zip(df['sns_usage_pct'], df['level4_pct'])):
        ax3.text(i, s+0.8, f'{s:.1f}%', ha='center', fontsize=8, color=TEAL)
        ax4.text(i, l-4,   f'{l:.1f}%', ha='center', fontsize=8, color=CORAL, fontweight='bold')
    ax3.set_xlabel('연령대'); ax3.set_ylabel('SNS 이용률 (%)', color=TEAL)
    ax4.set_ylabel('문해력 수준4 비율 (%)', color=CORAL)
    ax3.set_xticks(x); ax3.set_xticklabels(df['age_group_label'])
    ax3.set_ylim(0, 120); ax4.set_ylim(0, 120)
    ax3.tick_params(axis='y', colors=TEAL); ax4.tick_params(axis='y', colors=CORAL)
    ax3.set_title('SNS를 많이 쓰는 세대가\n문해력도 높다?', fontsize=11, fontweight='bold')
    lines3, l3 = ax3.get_legend_handles_labels(); lines4, l4 = ax4.get_legend_handles_labels()
    ax3.legend(lines3+lines4, l3+l4, loc='lower left', fontsize=9)
    ax3.grid(axis='y', alpha=0.3)
    plt.suptitle('디지털 네이티브 역설 — OTT·SNS 이용이 높은 세대에서 문해력도 높게 나타나는 이유는?',
                 fontsize=12, fontweight='bold', y=1.02)
    plt.tight_layout()
    st.pyplot(fig); plt.close()
    show_sql(sql_media)
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
# 차트 7 — 독서시간 vs 문해력
# ════════════════════════════════════════════════
def render_chart4():
    st.subheader("📊 차트 7 — 연령대별 독서시간 vs 문해력 수준4 (2023)")
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

    fig, ax1 = plt.subplots(figsize=(12, 5))
    ax2 = ax1.twinx()
    x = np.arange(len(df))
    bars = ax1.bar(x, df['avg_read_min_total'], color=BLUE, alpha=0.7, label='평균 독서시간(분)', width=0.4)
    for bar, val in zip(bars, df['avg_read_min_total']):
        ax1.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5, f'{val:.1f}분', ha='center', fontsize=9, color=BLUE)
    ax2.plot(x, df['level4_pct'], marker='o', color=CORAL, linewidth=2.2, markersize=7, label='수준4 비율(%)')
    for xi, yi in zip(x, df['level4_pct']):
        ax2.annotate(f'{yi:.1f}%', (xi, yi), textcoords="offset points", xytext=(0, 10), ha='center', fontsize=9, color=CORAL)
    ax1.set_xlabel('연령대'); ax1.set_ylabel('평균 독서시간 (분)', color=BLUE)
    ax2.set_ylabel('수준4 비율 (%)', color=CORAL)
    ax1.set_xticks(x); ax1.set_xticklabels(df['age_group_label'], rotation=15)
    ax1.set_ylim(0, max(df['avg_read_min_total'])*1.4); ax2.set_ylim(0, 115)
    ax1.tick_params(axis='y', colors=BLUE); ax2.tick_params(axis='y', colors=CORAL)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1+lines2, labels1+labels2, loc='upper right')
    ax1.set_title('연령대별 평균 독서시간 vs 문해력 수준4 비율', fontsize=13, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    sig_text = "p < 0.05" if p_val < 0.05 else f"p = {p_val:.3f}"
    fig.text(0.5, -0.03, f'피어슨 상관계수 r={r_val:.3f}  |  {sig_text}  (n=5, 연령대 집계값)',
             ha='center', fontsize=10, color=GRAY)
    plt.tight_layout()
    st.pyplot(fig); plt.close()
    show_sql(sql)
    st.warning("⚠️ 연령대 집계값 간 비교입니다. 개인 단위 인과관계가 아닌 집계 수준 상관관계이며, 연령 효과가 혼재합니다.")
    st.info(f"""
💡 **인사이트**
- 독서시간이 많은 연령대(18~29세)에서 문해력 수준4 비율도 높게 나타나 양의 상관(r={r_val:.3f})이 확인됩니다.
- 그러나 이는 연령 자체의 효과(교육 수준, 인지 능력 등)가 혼재할 수 있어 독서만의 순수 효과로 해석하기 어렵습니다.
- 독서시간과 문해력의 정적 상관은 확인되나, 인과관계 주장은 제한적입니다.
""")


# ════════════════════════════════════════════════
# 차트 8 — PIAAC 다중회귀 (편상관 대체)
# ════════════════════════════════════════════════
def render_chart_regression():
    st.subheader("📊 차트 9 — PIAAC 개인단위 다중회귀분석: 연령·학력 통제 후 독서·ICT와 문해력")
    st.markdown("""
    기존 집계 수준 분석(차트 5~8)의 한계를 보완합니다.
    **PIAAC 2023 한국 개인 단위 마이크로데이터(n≈6,000)**를 활용해
    연령·학력·성별을 통제한 후 독서활동과 ICT 이용이
    문해력과 갖는 **독립적 관련성**을 검증합니다.

    > 분석 방법: 10개 Plausible Value(PVLIT1~10)를 각각 WLS로 추정한 뒤
    > Rubin's rule로 계수·표준오차를 결합.
    """)

    R2 = {"M1\n연령만": 0.181, "M2\n+학력·성별": 0.251, "M3\n+독서·ICT": 0.283}

    coef_data = {
        "변수":  ["25-34세", "35-44세", "45-54세", "55-65세",
                  "고졸", "전문대이상", "여성", "독서활동", "가정 ICT이용"],
        "그룹":  ["연령대","연령대","연령대","연령대",
                  "학력","학력","성별","독서·ICT","독서·ICT"],
        "계수":  [-7.4,-20.6,-29.9,-57.6, +20.8,+33.1, +1.2, +3.79,+5.42],
        "SE":    [3.6,  3.6,  3.6,  3.8,   4.7,  4.7,  1.8,  1.03, 0.87],
        "p":     [0.038,0.000,0.000,0.000, 0.000,0.000, 0.461,0.000,0.000],
        "기준":  ["(기준: 16-24세)","(기준: 16-24세)","(기준: 16-24세)","(기준: 16-24세)",
                  "(기준: 중졸이하)","(기준: 중졸이하)","(기준: 남성)","(표준화)","(표준화)"],
    }
    df_coef = pd.DataFrame(coef_data)
    df_coef["유의"]    = df_coef["p"].apply(lambda p: "***" if p<0.001 else ("**" if p<0.01 else ("*" if p<0.05 else "—")))
    df_coef["CI_low"]  = df_coef["계수"] - 1.96*df_coef["SE"]
    df_coef["CI_high"] = df_coef["계수"] + 1.96*df_coef["SE"]

    GROUP_COLOR = {"연령대": CORAL, "학력": BLUE, "성별": GRAY, "독서·ICT": TEAL}

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("PIAAC 2023 한국 문해력 다중회귀분석\n(Rubin's rule · 10 PV · WLS 가중치, n≈6,000)",
                 fontsize=13, fontweight="bold", y=1.02)

    # 왼쪽: R² 막대
    ax = axes[0]
    bars = ax.bar(list(R2.keys()), list(R2.values()),
                  color=[CORAL, BLUE, TEAL], alpha=0.85, width=0.5, edgecolor="white", linewidth=1.5)
    for bar, val in zip(bars, R2.values()):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.005,
                f"R²={val:.3f}", ha="center", va="bottom", fontsize=11, fontweight="bold")
    for x1, x2, y_pos, label in [(0,1,0.251,"+0.070\n(학력 추가)"),(1,2,0.283,"+0.032\n(독서·ICT 추가)")]:
        ax.annotate("", xy=(x2-0.05, y_pos-0.003), xytext=(x1+0.05, y_pos-0.003),
                    arrowprops=dict(arrowstyle="->", color=GRAY, lw=1.5))
        ax.text((x1+x2)/2, y_pos+0.008, label, ha="center", va="bottom", fontsize=9, color=GRAY)
    ax.set_ylim(0, 0.36)
    ax.set_ylabel("R² (문해력 분산 설명 비율)", fontsize=10)
    ax.set_title("모델별 R² 설명력 분해\n(변수 블록 추가에 따른 변화)", fontsize=11, fontweight="bold")
    ax.grid(axis="y", alpha=0.3)
    ax.axhline(0.283, color=TEAL, linewidth=0.8, linestyle="--", alpha=0.5)
    ax.text(2.35, 0.286, "최종 R²=0.283\n미설명 71.7%", fontsize=8, color=TEAL, va="bottom")
    for xi, color, txt in [(0,CORAL,"■ 연령"),(1,BLUE,"■ +학력"),(2,TEAL,"■ +독서·ICT")]:
        ax.text(xi, -0.035, txt, color=color, fontsize=9, ha="center", transform=ax.get_xaxis_transform())

    # 오른쪽: 계수 플롯 (성별 제외)
    ax2 = axes[1]
    plot_df = df_coef[df_coef["그룹"] != "성별"].copy().reset_index(drop=True)
    y_pos = np.arange(len(plot_df))
    ax2.barh(y_pos, plot_df["계수"],
             xerr=[plot_df["계수"]-plot_df["CI_low"], plot_df["CI_high"]-plot_df["계수"]],
             color=[GROUP_COLOR[g] for g in plot_df["그룹"]], alpha=0.82, capsize=4, height=0.6)
    ax2.axvline(0, color="black", linewidth=0.9, linestyle="--")
    ax2.set_yticks(y_pos)
    ax2.set_yticklabels([f"{r['변수']}  {r['기준']}" for _, r in plot_df.iterrows()], fontsize=8.5)
    ax2.invert_yaxis()
    ax2.set_xlabel("회귀계수 (문해력 점수 단위)", fontsize=10)
    ax2.set_title("M3 최종모델: 독립변수별 계수\n(95% CI, 성별 제외)", fontsize=11, fontweight="bold")
    ax2.grid(axis="x", alpha=0.3)
    for i, row in plot_df.iterrows():
        star = row["유의"].strip()
        if star and star != "—":
            ax2.text(row["CI_high"]+0.5, i, star, va="center", fontsize=9,
                     color=GROUP_COLOR[row["그룹"]], fontweight="bold")
    ax2.legend(handles=[
        mpatches.Patch(color=CORAL, alpha=0.82, label="연령대 (기준: 16-24세)"),
        mpatches.Patch(color=BLUE,  alpha=0.82, label="학력 (기준: 중졸이하)"),
        mpatches.Patch(color=TEAL,  alpha=0.82, label="독서·ICT (표준화)"),
    ], fontsize=8, loc="lower right")
    plt.tight_layout()
    st.pyplot(fig); plt.close()

    # ── 계수 테이블 (유의 열 제거) ──────────────────────────
    st.markdown("**다중회귀 계수표 (M3 최종모델, Rubin's rule WLS)**")
    display_df = df_coef[["그룹", "변수", "기준", "계수", "SE", "p"]].copy()
    display_df["계수"] = display_df["계수"].map(lambda x: f"{x:+.2f}")
    display_df["SE"]   = display_df["SE"].map(lambda x: f"{x:.2f}")
    display_df["p"]    = display_df["p"].map(lambda x: "<0.001" if x < 0.001 else f"{x:.3f}")
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    st.caption("기준집단: 16-24세, 중졸이하, 남성")

    # ── R² 메트릭 ───────────────────────────────────────────
    st.markdown("**모델별 R² 및 설명력 증가**")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("M1 R² (연령만)",     "0.181", help="연령대만으로 문해력 분산의 18.1% 설명")
    c2.metric("M2 R² (+학력·성별)", "0.251", delta="+0.070", help="학력·성별 추가 시 7.0%p 추가 설명")
    c3.metric("M3 R² (+독서·ICT)", "0.283",  delta="+0.032", help="독서·ICT 추가 시 3.2%p 추가 설명")
    c4.metric("미설명 분산",         "71.7%", help="부모 학력, 직업 특성 등 미포함 변수")

    # ── 결과 해석 ───────────────────────────────────────────
    st.divider()
    st.markdown("### 📝 결과 해석")
    col_l, col_r = st.columns(2)
    with col_l:
        st.markdown("#### ① 연령 효과")
        st.info("""
학력·성별·독서·ICT를 모두 통제한 후에도
**55-65세는 16-24세보다 약 57.6점 낮게** 나타났다 (p<.001).

통제 전 M1의 −58.3점과 거의 차이가 없다는 점이 핵심이다.
연령대별 문해력 격차가 단순히 학력 구성 차이만으로 설명되기 어렵고,
코호트가 성장한 교육·문화 환경, 독서 습관 형성 시기 등
**연령 또는 세대와 관련된 다른 요인**이 여전히 크게 남아 있음을 보여준다.
        """)
        st.markdown("#### ③ 독서활동 효과")
        st.success("""
연령·학력·성별·ICT 이용 등 다른 요인을 모두 감안하고 나서도,
독서를 많이 하는 사람일수록 문해력이 높은 경향이
유의미하게 확인됐다 (β=+3.79, p<.001).

이 분석에서 가장 견고하게 지지되는 행동 변수다.
        """)
    with col_r:
        st.markdown("#### ② 학력 효과")
        st.info("""
학력은 문해력 점수를 설명하는 **중요한 요인**으로 나타났다.
저학력 대비 고학력의 회귀계수는 **+33.1점** (p<.001)으로,
연령을 통제한 이후에도 학력 수준에 따른 격차가 뚜렷했다.

단, 절댓값 기준으로 연령 계수(55-65세 −57.6)가
학력 계수(+33.1)보다 크므로,
"학력이 가장 강한 예측변수"라는 표현은 적절하지 않다.
        """)
        st.markdown("#### ④ ICT 이용 효과")
        st.warning("""
가정 ICT이용지수는 학력·연령을 통제한 후에도
문해력과 양의 관계를 보였다 (β=+5.42, p<.001).

**⚠️ 해석 주의**
PIAAC의 ICT 이용지수는 OTT·SNS 시청시간이 아니라
**이메일, 문서 작성, 정보 검색** 등 텍스트 기반
디지털 활동을 포함한 종합 지수다.

"디지털 미디어 이용이 문해력을 높인다"는 증거로
직접 사용하기에는 한계가 있다.
        """)

    # ── 분석 한계 ────────────────────────────────────────────
    st.divider()
    st.error("""
⚠️ **분석의 한계**

본 분석은 2023년 단일 시점 횡단 자료에 기반하므로, 관찰된 연령대 간 차이가
나이 듦에 따른 변화(연령 효과)인지, 세대 간 성장 환경 차이(코호트 효과)인지를
분리하기 어렵다. 또한 회귀계수는 통제 후 조건부 연관성을 나타낼 뿐,
독서활동이나 ICT 이용이 문해력을 높인다는 인과 주장의 근거가 되지 않는다.
    """)

    # ── 최종 결론 ────────────────────────────────────────────
    st.divider()
    st.markdown("### 🎯 최종 결론")
    st.success("""
한국 성인의 문해력 격차는 미디어 이용보다 세대·학력 구조에서 비롯되며,
그 안에서 **독서활동만이 통제 후에도 문해력과 독립적 양의 관계를 유지한 유일한 행동 변수**다.
    """)
    st.markdown("""
PIAAC 2023 한국 개인 단위 데이터를 활용한 다중회귀분석 결과,
연령대와 본인 학력은 문해력 점수와 강한 관련을 보였다.
특히 고령층은 학력·성별·독서활동·ICT 이용을 통제한 후에도
청년층보다 낮은 문해력 점수를 보였으며,
이는 기존의 연령대별 문해력 격차가 단순한 집계상 착시만은 아님을 보여준다.

연령·학력·성별·ICT 이용 등 다른 요인을 모두 감안하고 나서도,
독서를 많이 하는 사람일수록 문해력이 높은 경향이 유의미하게 확인됐다.
반면 ICT 이용지수 역시 양의 관계를 보였기 때문에,
디지털 이용 증가가 곧바로 문해력 저하로 이어진다는 단순 가설은 지지되기 어렵다.
다만 PIAAC의 ICT 지수는 OTT·SNS 이용시간이 아니라 텍스트 기반 디지털 활동을
포함하므로, 미디어 이용 효과로 직접 해석하는 데에는 한계가 있다.
    """)


# ════════════════════════════════════════════════
# 차트 9 — 전략B: 트레이드오프
# ════════════════════════════════════════════════
def render_chart7():
    st.subheader("📊 차트 8 — 전략B: 연령대별 독서시간 vs OTT 이용시간 트레이드오프")
    st.markdown("""
    **독서시간(감소)과 OTT 이용시간(증가)** 의 교차 패턴을 통해
    '미디어 대체' 현상과 문해력의 관계를 확인합니다.
    """)
    sql_read = "SELECT age_group_id, avg_read_min_total FROM 독서실태조사 ORDER BY age_group_id"
    sql_ott  = """
        SELECT m.age_group_id, a.age_group_label, AVG(m.OTT_주간총이용시간_분) AS avg_ott
        FROM 미디어패널2023 m JOIN "연령대 기준" a ON m.age_group_id = a.age_group_id
        GROUP BY m.age_group_id ORDER BY m.age_group_id
    """
    sql_lit  = """
        SELECT CAST(age_group_id AS INTEGER) AS age_group_id, level4_pct
        FROM 문해능력조사 WHERE survey_year=2023 AND category_type='age'
    """
    df = pd.read_sql(sql_read, conn).merge(pd.read_sql(sql_ott, conn), on='age_group_id')\
                                    .merge(pd.read_sql(sql_lit, conn), on='age_group_id')

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    ax = axes[0]; ax2 = ax.twinx()
    x = np.arange(len(df))
    ax.bar(x-0.2, df['avg_read_min_total'], 0.35, color=BLUE, alpha=0.75, label='독서시간(분)')
    ax2.bar(x+0.2, df['avg_ott'], 0.35, color=AMBER, alpha=0.75, label='OTT 이용시간(분)')
    for i, (r, o) in enumerate(zip(df['avg_read_min_total'], df['avg_ott'])):
        ax.text(i-0.2, r+0.5, f'{r:.0f}', ha='center', fontsize=8, color=BLUE)
        ax2.text(i+0.2, o+1,  f'{o:.0f}', ha='center', fontsize=8, color=AMBER)
    ax.set_xlabel('연령대'); ax.set_ylabel('독서시간 (분/일)', color=BLUE)
    ax2.set_ylabel('OTT 이용시간 (분/주)', color=AMBER)
    ax.set_xticks(x); ax.set_xticklabels(df['age_group_label'])
    ax.tick_params(axis='y', colors=BLUE); ax2.tick_params(axis='y', colors=AMBER)
    ax.set_title('연령대별 독서시간 vs OTT 이용시간', fontsize=11, fontweight='bold')
    lines1, l1 = ax.get_legend_handles_labels(); lines2, l2 = ax2.get_legend_handles_labels()
    ax.legend(lines1+lines2, l1+l2, loc='upper right', fontsize=9)
    ax.grid(axis='y', alpha=0.3)

    ax3 = axes[1]
    sc = ax3.scatter(df['avg_read_min_total'], df['level4_pct'],
                     c=df['avg_ott'], cmap='YlOrRd_r', s=180, edgecolors='gray', linewidths=0.5, zorder=3)
    plt.colorbar(sc, ax=ax3, label='OTT 이용시간(분/주)')
    z = np.polyfit(df['avg_read_min_total'], df['level4_pct'], 1)
    x_line = np.linspace(df['avg_read_min_total'].min(), df['avg_read_min_total'].max(), 100)
    ax3.plot(x_line, np.poly1d(z)(x_line), color=BLUE, linestyle='--', linewidth=1.5, alpha=0.7)
    for _, row in df.iterrows():
        ax3.annotate(row['age_group_label'], (row['avg_read_min_total'], row['level4_pct']),
                     textcoords="offset points", xytext=(5, 5), fontsize=8)
    r_val, p_val = stats.pearsonr(df['avg_read_min_total'], df['level4_pct'])
    ax3.set_xlabel('평균 독서시간 (분/일)'); ax3.set_ylabel('문해력 수준4 비율 (%)')
    ax3.set_title('독서시간 vs 문해력 산점도\n(점 색상=OTT 이용 많을수록 밝은색)', fontsize=11, fontweight='bold')
    ax3.grid(alpha=0.3)
    ax3.text(0.05, 0.05, f'r={r_val:.3f}  (p={p_val:.3f})',
             transform=ax3.transAxes, fontsize=10, color=BLUE,
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    plt.tight_layout()
    st.pyplot(fig); plt.close()
    show_sql(sql_ott)
    st.warning("⚠️ 독서시간(2023년)과 OTT 이용시간(2023년)은 같은 연도 집계이나, 서로 다른 조사에서 추출한 데이터입니다.")
    st.info(f"""
💡 **인사이트 (전략 B)**
- 독서시간이 많은 연령대(18~29세: 36분)에서 OTT 이용시간도 가장 많아(221분/주), 단순한 '독서 대체' 구도가 아님을 보여줍니다.
- 산점도에서 독서시간↑ → 문해력↑ 의 양의 상관(r={r_val:.3f})이 확인되나, OTT 이용시간이 많은 집단(밝은색)이 오히려 문해력도 높은 역설적 패턴이 나타납니다.
- 이는 연령 효과(젊을수록 독서·OTT 모두 많고 교육 수준도 높음)가 미디어 대체 효과를 압도하고 있음을 시사합니다.
""")


# ════════════════════════════════════════════════
# 라우팅
# ════════════════════════════════════════════════
if mode == "all":
    render_chart1();           st.divider()
    render_chart2();           st.divider()
    render_chart_box();        st.divider()
    render_chart6();           st.divider()
    render_chart5();           st.divider()
    render_chart8();           st.divider()
    render_chart4();           st.divider()
    render_chart7();           st.divider()   # 차트 8 트레이드오프
    render_chart_regression()                 # 차트 9 다중회귀 (마지막)
elif mode == "chart1":            render_chart1()
elif mode == "chart2":            render_chart2()
elif mode == "chart4":            render_chart4()
elif mode == "chart5":            render_chart5()
elif mode == "chart6":            render_chart6()
elif mode == "chart7":            render_chart7()
elif mode == "chart8":            render_chart8()
elif mode == "chart_box":         render_chart_box()
elif mode == "chart_regression":  render_chart_regression()

st.divider()
st.caption("데이터 출처: 교육부 학업성취도평가 · 국가평생교육진흥원 · 문화체육관광부 · KISDI | 경기도교육연구원 정책연구 2022-09")
