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

st.title("📚 한국 문해력 저하 현상 원인 분석")
st.markdown("---") # 깔끔한 구분선으로 본문과 분리

# 2. 데이터베이스 연결 설정
DB_FILE = "경영정보처리론2조.db"
if not os.path.exists(DB_FILE):
    st.error(f"⚠️ 데이터베이스 파일({DB_FILE})이 없습니다. 같은 폴더에 파일을 넣어주세요.")
    st.stop()

@st.cache_resource
def get_conn():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

conn = get_conn()


# ── 사이드바 ────────────────────────────────────────────────────
st.sidebar.title("📊 분석 카테고리 선택")

# 1. 대분류(분석 카테고리) 선택
category = st.sidebar.selectbox(
    "분석 주제를 선택하세요",
    [
        "분석1 : 세대·학력별 문해력 수준",
        "분석2 : 연령대별 독서시간과 문해력 수준의 상관관계",
        "분석3 : 연령대별 미디어 매체 이용과 문해력 수준의 비교",
        "PIAAC 분석"
    ]
)

# 2. 대분류 선택에 따른 소분류(차트) 매핑 정보 정의 (차트3과 차트4의 순서 및 모드 매핑 교환)
if category == "분석1 : 세대·학력별 문해력 수준":
    chart_options = {
        "차트 1 — 기초학력 미달률 추이": "chart1",
        "차트 2 — 코로나 전후 t-test": "chart2",
        "차트 3 — 세대별 문해력 분포": "chart_box",       # 기존 차트4에서 차트3으로 변경
        "차트 4 — 전략A: 청년층 Gap 변화": "chart6",       # 기존 차트3에서 차트4로 변경
    }
elif category == "분석2 : 연령대별 독서시간과 문해력 수준의 상관관계":
    chart_options = {
        "차트 7 — 독서시간 ↔ 문해력": "chart4",
        "차트 8 — 전략B: 독서 vs 미디어 트레이드오프": "chart7",
    }
elif category == "분석3 : 연령대별 미디어 매체 이용과 문해력 수준의 비교":
    chart_options = {
        "차트 5 — 미디어 이용 ↔ 문해력": "chart5",
        "차트 6 — 디지털 네이티브 역설": "chart8",
    }
else:  # "PIAAC 분석" 선택 시
    chart_options = {
        "차트 9 — PIAAC 다중회귀분석": "chart_regression"
    }

# 3. 소분류 라디오 버튼 렌더링
selected_chart = st.sidebar.radio("보고 싶은 차트를 선택하세요", list(chart_options.keys()))
mode = chart_options[selected_chart]

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
- 수학은 코로나 이전부터 미달률이 높았던 반ment, 국어는 코로나를 기점으로 이례적으로 급등해 수학과 유사한 수준에 도달했습니다.
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


# ════════════════════════════
