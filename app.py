import os
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
import streamlit as st
from scipy import stats

# 1. Matplotlib 한글 깨짐 방지 설정
try:
    font_list = [f for f in fm.findSystemFonts() if 'Nanum' in f or 'malgun' in f.lower() or 'apple' in f.lower()]
    if font_list:
        plt.rcParams['font.family'] = fm.FontProperties(fname=font_list[0]).get_name()
    plt.rcParams['axes.unicode_minus'] = False
except Exception as e:
    st.sidebar.warning(f"폰트 설정 중 오류: {e}")

sns.set_theme(style="whitegrid")
if font_list:
    plt.rcParams['font.family'] = fm.FontProperties(fname=font_list[0]).get_name()

DB_FILE = "경정처2조.db"

# 데이터베이스 미발견 시 시뮬레이션용 더미 DB 생성 기능 활성화
def init_dummy_database():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # "연령대 기준", "학력기준", "기초학력미달률_전처리", "문해능력조사", "독서실태조사", "미디어패널2023" 테이블 빌드
    # (세부 더미 데이터 삽입 코드 생략 - app.py 본파일 참조)
    conn.commit()
    conn.close()

st.set_page_config(page_title="한국 문해력 저하 원인 분석 대시보드", page_icon="📊", layout="wide")

if not os.path.exists(DB_FILE):
    st.error(f"⚠️ 데이터베이스 파일({DB_FILE})이 없습니다. 같은 폴더에 파일을 넣어주세요.")
    if st.button("🛠️ 시뮬레이션 데이터베이스 생성하여 즉시 시연하기"):
        init_dummy_database()
        st.success("🎉 데이터베이스 파일이 자체 생성되었습니다! 화면을 새로고침합니다.")
        st.rerun()
    st.stop()

# 대시보드 구조 및 5개 시각화 차트 빌드... (차트별 individual 렌더링)