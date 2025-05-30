"""
AI NOVA 대시보드

Streamlit 기반의 AI NOVA 웹 인터페이스
"""

import streamlit as st
import requests
import json
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import base64
from io import BytesIO
import os
from typing import List, Dict, Any, Optional

# API URL 설정
API_URL = os.environ.get("API_URL", "http://localhost:8000")

# 페이지 설정
st.set_page_config(
    page_title="AI NOVA - 이슈 분석 시스템",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 앱 제목
st.title("📰 AI NOVA - 키워드 중심 뉴스 클러스터링 및 종합 요약 시스템")
st.markdown("빅카인즈 API 기반의 이슈 중심 뉴스 분석 및 요약 서비스")

# 사이드바
st.sidebar.header("메뉴")
page = st.sidebar.radio(
    "페이지 선택",
    ["오늘의 이슈", "이슈 분석", "키워드 트렌드", "정보"]
)

# API 호출 함수
def call_api(endpoint, method="GET", params=None, data=None):
    try:
        url = f"{API_URL}{endpoint}"
        
        if method.upper() == "GET":
            response = requests.get(url, params=params)
        else:  # POST
            response = requests.post(url, json=data)
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API 호출 오류: {str(e)}")
        return None

# 이미지 표시 함수
def display_image(image_data):
    if image_data and image_data.startswith("data:image/png;base64,"):
        image_base64 = image_data.split(",")[1]
        st.image(BytesIO(base64.b64decode(image_base64)))

# 오늘의 이슈 페이지
def show_today_issues():
    st.header("🔍 오늘의 이슈")
    
    # 날짜 선택
    today = datetime.now().date()
    selected_date = st.date_input(
        "날짜 선택",
        value=today,
        max_value=today,
        min_value=today - timedelta(days=30)
    )
    
    date_str = selected_date.strftime("%Y-%m-%d")
    
    # 이슈 수 선택
    top_n = st.slider("표시할 이슈 수", min_value=3, max_value=10, value=5)
    
    # 이슈 가져오기
    with st.spinner("이슈를 가져오는 중..."):
        response = call_api(
            "/api/today-issues",
            params={"date": date_str, "top_n": top_n}
        )
    
    if response:
        issues = response.get("issues", [])
        
        if issues:
            # 이슈 목록 표시
            for i, issue in enumerate(issues):
                with st.expander(f"#{issue['rank']} {issue['topic']}", expanded=i==0):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**카테고리:** {issue['category']}")
                        st.markdown(f"**키워드:** {', '.join(issue['keywords'])}")
                        st.markdown(f"**뉴스 건수:** {issue['news_count']} | **언론사 수:** {issue['provider_count']}")
                        
                        # 관련 뉴스 테이블
                        if issue.get('related_news'):
                            st.markdown("##### 관련 뉴스")
                            news_data = []
                            for news in issue['related_news']:
                                published_at = datetime.fromisoformat(
                                    news['published_at'].replace('Z', '+00:00')
                                ).strftime("%Y-%m-%d %H:%M")
                                
                                news_data.append({
                                    "제목": news['title'],
                                    "언론사": news['provider'],
                                    "발행시간": published_at
                                })
                            
                            st.dataframe(pd.DataFrame(news_data), use_container_width=True)
                    
                    with col2:
                        # 이슈 분석 버튼
                        if st.button("이슈 분석", key=f"analyze_{i}"):
                            # 이슈 키워드로 이슈 분석 페이지 설정
                            st.session_state['selected_page'] = "이슈 분석"
                            st.session_state['query'] = issue['topic']
                            st.session_state['start_date'] = (selected_date - timedelta(days=7)).strftime("%Y-%m-%d")
                            st.session_state['end_date'] = date_str
                            st.rerun()
        else:
            st.info(f"{date_str}에 이슈 데이터가 없습니다.")
    
    # 오늘의 키워드
    st.header("📊 오늘의 키워드")
    
    with st.spinner("키워드를 가져오는 중..."):
        keywords_response = call_api("/api/today-keywords")
    
    if keywords_response:
        categories = keywords_response.get("categories", {})
        charts = keywords_response.get("charts", {})
        
        tabs = st.tabs(list(categories.keys()))
        
        for i, (category, tab) in enumerate(zip(categories.keys(), tabs)):
            with tab:
                col1, col2 = st.columns([3, 2])
                
                with col1:
                    # 차트 표시
                    if category in charts:
                        display_image(charts[category])
                
                with col2:
                    # 유형별 키워드
                    category_data = categories[category]
                    
                    if category_data.get("person"):
                        st.markdown("##### 인물")
                        person_df = pd.DataFrame(category_data["person"])
                        st.dataframe(person_df[["keyword", "count"]], hide_index=True)
                    
                    if category_data.get("organization"):
                        st.markdown("##### 기관")
                        org_df = pd.DataFrame(category_data["organization"])
                        st.dataframe(org_df[["keyword", "count"]], hide_index=True)
                    
                    if category_data.get("location"):
                        st.markdown("##### 장소")
                        location_df = pd.DataFrame(category_data["location"])
                        st.dataframe(location_df[["keyword", "count"]], hide_index=True)

# 이슈 분석 페이지
def show_issue_analysis():
    st.header("🔍 이슈 분석")
    
    # 검색 폼
    with st.form("search_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            query = st.text_input(
                "검색어",
                value=st.session_state.get('query', '윤석열')
            )
        
        with col2:
            today = datetime.now().date()
            week_ago = today - timedelta(days=7)
            
            start_date = st.date_input(
                "시작 날짜",
                value=datetime.strptime(
                    st.session_state.get('start_date', week_ago.strftime("%Y-%m-%d")),
                    "%Y-%m-%d"
                ).date(),
                max_value=today
            )
        
        with col3:
            end_date = st.date_input(
                "종료 날짜",
                value=datetime.strptime(
                    st.session_state.get('end_date', today.strftime("%Y-%m-%d")),
                    "%Y-%m-%d"
                ).date(),
                max_value=today,
                min_value=start_date
            )
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 간소화를 위해 언론사와 카테고리 옵션은 생략
            max_results = st.slider("최대 검색 결과 수", 50, 500, 100, 50)
        
        with col2:
            # 검색 버튼
            search_submitted = st.form_submit_button("검색 및 분석")
    
    # 검색 후 분석 실행
    if search_submitted:
        with st.spinner("검색 및 분석 중..."):
            # 검색 요청 데이터
            search_data = {
                "query": query,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "max_results": max_results
            }
            
            # API 호출
            analysis_result = call_api(
                "/api/analyze",
                method="POST",
                data=search_data
            )
            
            # 결과 저장
            if analysis_result:
                st.session_state['analysis_result'] = analysis_result
                st.session_state['query'] = query
                st.session_state['start_date'] = start_date.strftime("%Y-%m-%d")
                st.session_state['end_date'] = end_date.strftime("%Y-%m-%d")
    
    # 분석 결과 표시
    if 'analysis_result' in st.session_state:
        result = st.session_state['analysis_result']
        
        # 분석 요약
        st.subheader("📊 분석 요약")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("뉴스 건수", result.get("news_count", 0))
        
        with col2:
            if "issue_map" in result and "clusters" in result["issue_map"]:
                st.metric("이슈 클러스터 수", len(result["issue_map"]["clusters"]))
        
        with col3:
            if "issue_flow" in result and "key_events" in result["issue_flow"]:
                st.metric("주요 이벤트 수", len(result["issue_flow"]["key_events"]))
        
        # 탭으로 결과 구분
        tab1, tab2, tab3 = st.tabs(["이슈 맵", "이슈 흐름", "이슈 요약"])
        
        # 이슈 맵 탭
        with tab1:
            if "issue_map" in result:
                issue_map = result["issue_map"]
                
                # 이슈 맵 이미지
                if "issue_map_image" in issue_map:
                    st.subheader("🔍 이슈 맵")
                    display_image(issue_map["issue_map_image"])
                
                # 클러스터 차트
                if "cluster_chart" in issue_map:
                    st.subheader("📊 이슈 클러스터")
                    display_image(issue_map["cluster_chart"])
                
                # 주요 클러스터 정보
                if "clusters" in issue_map and "key_clusters" in issue_map:
                    st.subheader("📋 주요 이슈")
                    
                    clusters = issue_map["clusters"]
                    key_clusters = issue_map["key_clusters"]
                    
                    for cluster_id in key_clusters:
                        if str(cluster_id) in clusters:
                            cluster = clusters[str(cluster_id)]
                            
                            with st.expander(f"이슈: {cluster['representative_title']}", expanded=False):
                                st.markdown(f"**키워드:** {', '.join(cluster['keywords'])}")
                                st.markdown(f"**뉴스 건수:** {cluster['news_count']}")
        
        # 이슈 흐름 탭
        with tab2:
            if "issue_flow" in result:
                issue_flow = result["issue_flow"]
                
                # 타임라인 차트
                if "timeline_chart" in issue_flow:
                    st.subheader("📈 뉴스 타임라인")
                    display_image(issue_flow["timeline_chart"])
                
                # 키워드 트렌드 차트
                if "trend_chart" in issue_flow and issue_flow["trend_chart"]:
                    st.subheader("📊 키워드 트렌드")
                    display_image(issue_flow["trend_chart"])
                
                # 이슈 흐름 그래프
                if "flow_graph_image" in issue_flow:
                    st.subheader("🔄 이슈 흐름")
                    display_image(issue_flow["flow_graph_image"])
                
                # 주요 이벤트
                if "key_events" in issue_flow and issue_flow["key_events"]:
                    st.subheader("📋 주요 이벤트")
                    
                    events_data = []
                    for event in issue_flow["key_events"]:
                        timestamp = event["timestamp"]
                        if isinstance(timestamp, str):
                            timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        
                        events_data.append({
                            "시간": timestamp.strftime("%Y-%m-%d %H:%M"),
                            "제목": event["title"],
                            "중요도": event["importance"],
                            "관련 뉴스 수": event["related_news_count"]
                        })
                    
                    if events_data:
                        st.dataframe(pd.DataFrame(events_data), use_container_width=True)
                
                # 이슈 단계
                if "phases" in issue_flow and issue_flow["phases"]:
                    st.subheader("📑 이슈 단계")
                    
                    phases = issue_flow["phases"]
                    cols = st.columns(len(phases))
                    
                    for i, (phase, col) in enumerate(zip(phases, cols)):
                        with col:
                            st.markdown(f"### {phase['name']}")
                            start_time = phase["start_time"]
                            end_time = phase["end_time"]
                            
                            if isinstance(start_time, str):
                                start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
                            if isinstance(end_time, str):
                                end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                            
                            st.markdown(f"**기간:** {start_time.strftime('%Y-%m-%d')} ~ {end_time.strftime('%Y-%m-%d')}")
                            st.markdown(f"**뉴스 건수:** {phase['news_count']}")
                            
                            if "representative_news" in phase and "title" in phase["representative_news"]:
                                st.markdown(f"**대표 뉴스:** {phase['representative_news']['title']}")
        
        # 이슈 요약 탭
        with tab3:
            if "issue_summary" in result:
                summary = result["issue_summary"]
                
                # 요약 제목
                if "title" in summary:
                    st.subheader(summary["title"])
                
                # 요약 텍스트
                if "summary_text" in summary:
                    st.markdown("### 📝 요약")
                    st.markdown(summary["summary_text"])
                
                # 키워드 차트
                if "keyword_chart" in summary:
                    st.markdown("### 🔑 주요 키워드")
                    display_image(summary["keyword_chart"])
                
                # 주요 인용문
                if "key_quotes" in summary and summary["key_quotes"]:
                    st.markdown("### 💬 주요 인용문")
                    
                    for quote in summary["key_quotes"]:
                        with st.expander(f"{quote.get('source', '관계자')} 발언", expanded=False):
                            st.markdown(f"> {quote.get('quotation', '')}")
                            st.markdown(f"*출처: {quote.get('provider', '')} ({quote.get('published_at', '')[:10]})*")
                
                # 다양한 관점
                if "perspectives" in summary and summary["perspectives"]:
                    st.markdown("### 👓 다양한 관점")
                    
                    perspectives = summary["perspectives"]
                    for perspective in perspectives:
                        source = perspective.get("source", "")
                        perspective_type = perspective.get("type", "")
                        
                        if perspective_type == "media":
                            title = f"📰 {source} 보도 관점"
                        else:
                            title = f"👤 {source} 관점"
                        
                        with st.expander(title, expanded=False):
                            st.markdown(f"**키워드:** {', '.join(perspective.get('keywords', []))}")
                            
                            if perspective.get("sample_title"):
                                st.markdown(f"**관련 기사:** {perspective.get('sample_title')}")
                            
                            if perspective.get("sample_quote"):
                                st.markdown(f"**발언:** {perspective.get('sample_quote')}")

# 키워드 트렌드 페이지
def show_keyword_trends():
    st.header("📈 키워드 트렌드")
    
    # 키워드 입력
    with st.form("trend_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            keywords = st.text_input(
                "키워드 (쉼표로 구분)",
                value="윤석열,이재명,안철수"
            )
        
        with col2:
            today = datetime.now().date()
            month_ago = today - timedelta(days=30)
            
            start_date = st.date_input(
                "시작 날짜",
                value=month_ago,
                max_value=today
            )
        
        with col3:
            end_date = st.date_input(
                "종료 날짜",
                value=today,
                max_value=today,
                min_value=start_date
            )
        
        # 간격 선택
        interval = st.selectbox(
            "시간 단위",
            options=["day", "month", "year"],
            index=0
        )
        
        # 트렌드 조회 버튼
        trend_submitted = st.form_submit_button("트렌드 조회")
    
    # 트렌드 조회
    if trend_submitted:
        keywords_list = [k.strip() for k in keywords.split(",")]
        
        if not keywords_list:
            st.error("키워드를 입력해주세요.")
            return
        
        st.subheader("📊 키워드 트렌드")
        
        # 각 키워드별 트렌드 조회 및 표시
        for keyword in keywords_list:
            with st.expander(f"키워드: {keyword}", expanded=True):
                with st.spinner(f"{keyword} 트렌드 조회 중..."):
                    try:
                        # API 클라이언트 직접 구현 및 호출은 실제 구현에서 필요
                        # 여기서는 간략한 예시로 표시
                        st.info(f"{keyword}에 대한 트렌드 데이터를 표시합니다. (API 연동 필요)")
                        
                        # 예시 차트 (실제로는 API에서 반환된 데이터로 대체)
                        chart_data = pd.DataFrame({
                            'date': pd.date_range(start=start_date, end=end_date),
                            'count': np.random.randint(10, 100, size=(end_date - start_date).days + 1)
                        })
                        
                        st.line_chart(chart_data.set_index('date'))
                    except Exception as e:
                        st.error(f"트렌드 조회 오류: {str(e)}")

# 정보 페이지
def show_info():
    st.header("ℹ️ AI NOVA 정보")
    
    st.markdown("""
    ### 프로젝트 설명
    
    **AI NOVA**는 빅카인즈 API를 기반으로 한 이슈 중심의 뉴스 분석 및 요약 서비스입니다.
    본 시스템은 개별 뉴스를 이슈별로 클러스터링하고, 이슈의 맥락과 흐름을 분석하여 사용자에게 종합적인 뉴스 인사이트를 제공합니다.
    
    ### 주요 기능
    
    - **이슈 맵**: 뉴스 기사를 키워드 기반으로 클러스터링하여 이슈 맵을 생성합니다.
    - **이슈 흐름**: 시간에 따른 이슈의 흐름을 분석하고 주요 이벤트를 식별합니다.
    - **이슈 요약**: 이슈별로 주요 내용을 요약하고 다양한 관점과 인사이트를 제공합니다.
    
    ### 사용 데이터
    
    본 서비스는 빅카인즈의 다음 API를 활용합니다:
    
    - 뉴스 검색 API
    - 오늘의 이슈 API
    - 연관어 분석 API
    - 키워드 트렌드 API
    - 뉴스 인용문 검색 API
    - 특성 추출 API
    - 키워드 추출 API
    
    ### 개발 정보
    
    - **개발**: 서울경제신문 디지털혁신팀
    - **버전**: 1.0.0
    - **문의**: 담당자 이메일
    """)

# 페이지 표시
if page == "오늘의 이슈":
    show_today_issues()
elif page == "이슈 분석":
    show_issue_analysis()
elif page == "키워드 트렌드":
    show_keyword_trends()
elif page == "정보":
    show_info()

# 푸터
st.markdown("---")
st.markdown(
    "© 2025 서울경제신문. All rights reserved."
)