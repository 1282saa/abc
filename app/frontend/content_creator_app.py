"""
AI NOVA 콘텐츠 제작자 대시보드

Streamlit 기반의 AI NOVA 콘텐츠 제작자 인터페이스
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
import uuid

# API URL 설정
API_URL = os.environ.get("API_URL", "http://localhost:8000")

# 페이지 설정
st.set_page_config(
    page_title="AI NOVA - 콘텐츠 제작자 대시보드",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 헤더
st.title("📝 AI NOVA - 콘텐츠 제작자 대시보드")
st.markdown("빅카인즈 API 기반의 콘텐츠 제작 지원 서비스")

# 사이드바
st.sidebar.header("메뉴")
page = st.sidebar.radio(
    "페이지 선택",
    ["이슈 리서치", "콘텐츠 기획", "자료 생성", "팩트 체크", "워크플로우"]
)

# API 호출 함수
def call_api(endpoint, method="GET", params=None, data=None, files=None):
    try:
        url = f"{API_URL}{endpoint}"
        
        if method.upper() == "GET":
            response = requests.get(url, params=params)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, files=files)
        elif method.upper() == "PATCH":
            response = requests.patch(url, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url)
        
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"API 호출 오류: {str(e)}")
        return None

# 이미지 표시 함수
def display_image(image_data, caption=None):
    if image_data and image_data.startswith("data:image/png;base64,"):
        image_base64 = image_data.split(",")[1]
        st.image(BytesIO(base64.b64decode(image_base64)), caption=caption)

# 세션 상태 초기화
if "workflows" not in st.session_state:
    st.session_state.workflows = []
if "current_workflow_id" not in st.session_state:
    st.session_state.current_workflow_id = None
if "issue_analysis" not in st.session_state:
    st.session_state.issue_analysis = None
if "content_brief" not in st.session_state:
    st.session_state.content_brief = None
if "visual_assets" not in st.session_state:
    st.session_state.visual_assets = None
if "verified_facts" not in st.session_state:
    st.session_state.verified_facts = None
if "export_path" not in st.session_state:
    st.session_state.export_path = None

# 워크플로우 목록 불러오기
def load_workflows():
    workflows = call_api("/content-creator/workflows")
    if workflows:
        st.session_state.workflows = workflows
    return workflows

# 현재 워크플로우 조회
def get_current_workflow():
    if not st.session_state.current_workflow_id:
        return None
    
    workflow = call_api(f"/content-creator/workflows/{st.session_state.current_workflow_id}")
    return workflow

# 이슈 리서치 페이지
def show_issue_research():
    st.header("🔍 이슈 리서치")
    
    # 워크플로우 선택 또는 생성
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # 워크플로우 선택
        workflows = load_workflows()
        if workflows:
            workflow_options = ["새 워크플로우 생성"] + [f"{w['name']} ({w['id']})" for w in workflows]
            selected_workflow = st.selectbox("워크플로우 선택", workflow_options, index=0)
            
            if selected_workflow != "새 워크플로우 생성":
                workflow_id = selected_workflow.split("(")[-1].replace(")", "")
                st.session_state.current_workflow_id = workflow_id
                
                # 현재 워크플로우 표시
                workflow = get_current_workflow()
                if workflow:
                    st.info(f"현재 워크플로우: {workflow['name']} (상태: {workflow['status']})")
        else:
            st.warning("워크플로우를 불러올 수 없습니다. 새 워크플로우를 생성하세요.")
    
    with col2:
        # 새 워크플로우 생성
        if st.button("새 워크플로우 생성"):
            st.session_state.show_create_workflow = True
    
    # 새 워크플로우 생성 폼
    if st.session_state.get("show_create_workflow", False):
        with st.form("create_workflow_form"):
            st.subheader("새 워크플로우 생성")
            
            workflow_name = st.text_input("워크플로우 이름", value="새 콘텐츠 프로젝트")
            workflow_desc = st.text_area("설명", value="")
            
            templates = call_api("/content-creator/templates")
            template_options = ["템플릿 사용 안함"] + [f"{t['name']} ({t['id']})" for t in templates] if templates else ["템플릿 사용 안함"]
            selected_template = st.selectbox("템플릿 선택", template_options, index=0)
            
            submit = st.form_submit_button("워크플로우 생성")
            
            if submit:
                template_id = None
                if selected_template != "템플릿 사용 안함":
                    template_id = selected_template.split("(")[-1].replace(")", "")
                
                result = call_api(
                    "/content-creator/workflows",
                    method="POST",
                    data={
                        "name": workflow_name,
                        "description": workflow_desc,
                        "template_id": template_id
                    }
                )
                
                if result:
                    st.session_state.current_workflow_id = result["id"]
                    st.success(f"워크플로우 '{workflow_name}' 생성 완료")
                    st.session_state.show_create_workflow = False
                    st.experimental_rerun()
    
    # 이슈 검색 및 분석 폼
    st.subheader("이슈 검색 및 분석")
    
    with st.form("issue_search_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            query = st.text_input(
                "검색어",
                value="경제성장"
            )
        
        with col2:
            today = datetime.now().date()
            week_ago = today - timedelta(days=7)
            
            start_date = st.date_input(
                "시작 날짜",
                value=week_ago,
                max_value=today
            )
        
        with col3:
            end_date = st.date_input(
                "종료 날짜",
                value=today,
                max_value=today,
                min_value=start_date
            )
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 간소화를 위해 언론사와 카테고리 옵션은 생략
            max_results = st.slider("최대 검색 결과 수", 50, 500, 100, 50)
        
        with col2:
            # 고급 옵션 (간소화 버전)
            st.write("고급 옵션")
            include_quotations = st.checkbox("인용문 포함", value=True)
        
        # 검색 버튼
        search_submitted = st.form_submit_button("검색 및 분석")
    
    # 검색 후 분석 실행
    if search_submitted:
        # 워크플로우 확인
        if not st.session_state.current_workflow_id:
            st.error("먼저 워크플로우를 선택하거나 생성하세요.")
            return
        
        with st.spinner("이슈 검색 및 분석 중..."):
            # 워크플로우 단계 실행
            result = call_api(
                f"/content-creator/workflows/{st.session_state.current_workflow_id}/execute",
                method="POST",
                data={
                    "stage_id": "research",
                    "stage_data": {
                        "query": query,
                        "start_date": start_date.strftime("%Y-%m-%d"),
                        "end_date": end_date.strftime("%Y-%m-%d"),
                        "max_results": max_results
                    }
                }
            )
            
            if result and "issue_analysis" in result:
                st.session_state.issue_analysis = result["issue_analysis"]
                st.success("이슈 분석 완료")
                
                # 워크플로우 업데이트
                workflow = get_current_workflow()
                if workflow:
                    st.info(f"워크플로우 단계: {workflow['current_stage'] + 1}/{len(workflow['stages'])}")
    
    # 이슈 분석 결과 표시
    if st.session_state.issue_analysis:
        st.subheader("📊 이슈 분석 결과")
        
        issue_analysis = st.session_state.issue_analysis
        
        # 기본 정보
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("검색어", issue_analysis.get("query", ""))
        with col2:
            st.metric("기간", f"{issue_analysis.get('start_date', '')} ~ {issue_analysis.get('end_date', '')}")
        with col3:
            st.metric("뉴스 건수", issue_analysis.get("news_count", 0))
        
        # 요약 정보 표시
        if "issue_summary" in issue_analysis:
            summary = issue_analysis["issue_summary"]
            
            st.subheader(summary.get("title", "이슈 요약"))
            st.markdown(summary.get("summary_text", ""))
            
            # 키워드
            if "keywords" in summary:
                st.markdown(f"**키워드**: {', '.join(summary['keywords'])}")
            
            # 다음 단계 버튼
            if st.button("콘텐츠 기획 단계로 이동"):
                st.session_state.selected_page = "콘텐츠 기획"
                st.experimental_rerun()

# 콘텐츠 기획 페이지
def show_content_planning():
    st.header("📝 콘텐츠 기획")
    
    # 현재 워크플로우 확인
    workflow = get_current_workflow()
    if not workflow:
        st.warning("먼저 이슈 리서치 페이지에서 워크플로우를 생성하고 이슈를 분석하세요.")
        return
    
    st.info(f"현재 워크플로우: {workflow['name']} (상태: {workflow['status']})")
    
    # 이슈 분석 결과 확인
    if not st.session_state.issue_analysis:
        if "outputs" in workflow and "research" in workflow["outputs"]:
            st.session_state.issue_analysis = workflow["outputs"]["research"].get("issue_analysis")
        
        if not st.session_state.issue_analysis:
            st.warning("먼저 이슈 리서치 페이지에서 이슈를 분석하세요.")
            return
    
    # 콘텐츠 브리프 생성 또는 표시
    if not st.session_state.content_brief:
        if "outputs" in workflow and "planning" in workflow["outputs"]:
            st.session_state.content_brief = workflow["outputs"]["planning"].get("content_brief")
        
        if not st.session_state.content_brief:
            # 브리프 생성 버튼
            if st.button("콘텐츠 브리프 생성"):
                with st.spinner("콘텐츠 브리프 생성 중..."):
                    # 워크플로우 단계 실행
                    result = call_api(
                        f"/content-creator/workflows/{st.session_state.current_workflow_id}/execute",
                        method="POST",
                        data={
                            "stage_id": "planning",
                            "stage_data": {
                                "issue_analysis": st.session_state.issue_analysis
                            }
                        }
                    )
                    
                    if result and "content_brief" in result:
                        st.session_state.content_brief = result["content_brief"]
                        st.success("콘텐츠 브리프 생성 완료")
    
    # 콘텐츠 브리프 표시
    if st.session_state.content_brief:
        brief = st.session_state.content_brief
        
        # 제목 및 키워드
        st.subheader(brief.get("title", "콘텐츠 브리프"))
        st.markdown(f"**키워드**: {', '.join(brief.get('keywords', []))}")
        
        # 콘텐츠 주제 제안
        st.subheader("💡 콘텐츠 주제 제안")
        for topic in brief.get("topic_suggestions", []):
            st.markdown(f"- {topic}")
        
        # 콘텐츠 구조
        st.subheader("📋 콘텐츠 구조")
        
        tabs = st.tabs([section.get("section", f"섹션 {i+1}") for i, section in enumerate(brief.get("content_structure", []))])
        
        for i, (tab, section) in enumerate(zip(tabs, brief.get("content_structure", []))):
            with tab:
                st.markdown(f"**설명**: {section.get('description', '')}")
                
                st.markdown("**핵심 포인트**:")
                for point in section.get("key_points", []):
                    st.markdown(f"- {point}")
                
                st.markdown(f"**제안 내용**: {section.get('suggested_content', '')}")
        
        # 주요 인용구
        st.subheader("💬 주요 인용구")
        
        quotes = brief.get("key_quotes", [])
        if quotes:
            quote_cols = st.columns(min(3, len(quotes)))
            
            for i, (col, quote) in enumerate(zip(quote_cols, quotes)):
                with col:
                    st.markdown(f"> {quote.get('quote', '')}")
                    st.markdown(f"*— {quote.get('source', '')}, {quote.get('provider', '')} ({quote.get('date', '')})*")
        
        # 주요 사실
        st.subheader("📊 주요 사실 및 통계")
        
        facts = brief.get("key_facts", [])
        if facts:
            for fact in facts:
                st.markdown(f"**{fact.get('fact', '')}**")
                st.markdown(f"날짜: {fact.get('date', '')}")
                st.markdown(f"출처: {fact.get('source', '')}")
                st.markdown("---")
        
        # 다음 단계 버튼
        col1, col2 = st.columns(2)
        with col1:
            if st.button("자료 생성 단계로 이동"):
                st.session_state.selected_page = "자료 생성"
                st.experimental_rerun()
        with col2:
            if st.button("브리프 내보내기 (마크다운)"):
                with st.spinner("마크다운 파일 생성 중..."):
                    result = call_api(
                        "/content-creator/tools/export-package",
                        method="POST",
                        data={
                            "issue_data": {
                                "issue_summary": st.session_state.issue_analysis.get("issue_summary", {}),
                                "issue_flow": st.session_state.issue_analysis.get("issue_flow", {})
                            },
                            "format": "md"
                        }
                    )
                    
                    if result and "file_path" in result:
                        st.success(f"브리프 내보내기 완료: {result['file_path']}")
                        st.markdown(f"[파일 다운로드]({API_URL}/api/download/{os.path.basename(result['file_path'])})")

# 자료 생성 페이지
def show_material_generation():
    st.header("🎨 시각 자료 생성")
    
    # 현재 워크플로우 확인
    workflow = get_current_workflow()
    if not workflow:
        st.warning("먼저 이슈 리서치 페이지에서 워크플로우를 생성하고 이슈를 분석하세요.")
        return
    
    st.info(f"현재 워크플로우: {workflow['name']} (상태: {workflow['status']})")
    
    # 필요한 데이터 확인
    if not st.session_state.issue_analysis:
        if "outputs" in workflow and "research" in workflow["outputs"]:
            st.session_state.issue_analysis = workflow["outputs"]["research"].get("issue_analysis")
    
    if not st.session_state.content_brief:
        if "outputs" in workflow and "planning" in workflow["outputs"]:
            st.session_state.content_brief = workflow["outputs"]["planning"].get("content_brief")
    
    if not st.session_state.issue_analysis or not st.session_state.content_brief:
        st.warning("먼저 이슈 리서치와 콘텐츠 기획 단계를 완료하세요.")
        return
    
    # 시각 자료 생성 또는 표시
    if not st.session_state.visual_assets:
        if "outputs" in workflow and "material" in workflow["outputs"]:
            st.session_state.visual_assets = workflow["outputs"]["material"].get("visual_assets")
        
        if not st.session_state.visual_assets:
            # 자료 생성 버튼
            if st.button("시각 자료 생성"):
                with st.spinner("시각 자료 생성 중..."):
                    # 워크플로우 단계 실행
                    result = call_api(
                        f"/content-creator/workflows/{st.session_state.current_workflow_id}/execute",
                        method="POST",
                        data={
                            "stage_id": "material",
                            "stage_data": {
                                "issue_analysis": st.session_state.issue_analysis,
                                "content_brief": st.session_state.content_brief
                            }
                        }
                    )
                    
                    if result and "visual_assets" in result:
                        st.session_state.visual_assets = result["visual_assets"]
                        st.success("시각 자료 생성 완료")
    
    # 시각 자료 표시
    if st.session_state.visual_assets:
        assets = st.session_state.visual_assets
        
        # 탭으로 자료 구분
        tab1, tab2, tab3, tab4 = st.tabs(["인용구 이미지", "타임라인", "관점 비교", "통계 차트"])
        
        with tab1:
            if "quote_image" in assets:
                st.subheader("💬 인용구 이미지")
                display_image(assets["quote_image"], "인용구 이미지")
                
                # 다운로드 링크 (실제로는 API에서 제공해야 함)
                st.markdown("이 이미지를 콘텐츠에 포함하거나 소셜 미디어에 공유할 수 있습니다.")
            else:
                st.info("인용구 이미지를 생성하려면 인용문이 필요합니다.")
                
                # 수동 생성 폼
                with st.form("quote_form"):
                    quote_text = st.text_area("인용 문구", "현 시점에서 기준금리 인하는 시기상조라고 판단했다. 물가안정이 우선되어야 한다.")
                    quote_source = st.text_input("출처", "한국은행 총재")
                    
                    submit = st.form_submit_button("인용구 이미지 생성")
                    
                    if submit:
                        with st.spinner("인용구 이미지 생성 중..."):
                            result = call_api(
                                "/content-creator/tools/quote-image",
                                method="POST",
                                data={
                                    "quote": quote_text,
                                    "source": quote_source
                                }
                            )
                            
                            if result and "image_data" in result:
                                if "visual_assets" not in st.session_state:
                                    st.session_state.visual_assets = {}
                                st.session_state.visual_assets["quote_image"] = result["image_data"]
                                st.success("인용구 이미지 생성 완료")
                                st.experimental_rerun()
        
        with tab2:
            if "timeline_image" in assets:
                st.subheader("📅 타임라인")
                display_image(assets["timeline_image"], "이슈 타임라인")
                
                # 다운로드 링크 (실제로는 API에서 제공해야 함)
                st.markdown("이 타임라인을 콘텐츠에 포함하여 이슈의 발전 과정을 보여줄 수 있습니다.")
            else:
                st.info("타임라인을 생성하려면 이슈 흐름 데이터가 필요합니다.")
                
                # 수동 생성 옵션 제공
                st.markdown("이슈 흐름 분석 데이터가 필요합니다. 이슈 리서치를 다시 실행하세요.")
        
        with tab3:
            if "perspectives_image" in assets:
                st.subheader("👓 관점 비교")
                display_image(assets["perspectives_image"], "이슈 관련 다양한 관점")
                
                # 다운로드 링크 (실제로는 API에서 제공해야 함)
                st.markdown("이 차트를 통해 이슈에 대한 다양한 관점을 비교할 수 있습니다.")
            else:
                st.info("관점 비교 차트를 생성하려면 다양한 관점 데이터가 필요합니다.")
        
        with tab4:
            if "stats_chart" in assets:
                st.subheader("📊 통계 차트")
                display_image(assets["stats_chart"], "이슈 관련 주요 통계")
                
                # 다운로드 링크 (실제로는 API에서 제공해야 함)
                st.markdown("이 차트를 통해 이슈와 관련된 주요 통계를 시각화할 수 있습니다.")
            else:
                st.info("통계 차트를 생성하려면 데이터가 필요합니다.")
                
                # 수동 생성 폼
                with st.form("stats_form"):
                    st.markdown("통계 차트 생성")
                    
                    chart_title = st.text_input("차트 제목", "이슈 관련 주요 통계")
                    chart_type = st.selectbox("차트 유형", ["bar", "line", "pie"], index=0)
                    
                    # 간단한 데이터 입력 (실제로는 더 복잡한 인터페이스 필요)
                    st.markdown("데이터 입력 (쉼표로 구분)")
                    data1 = st.text_input("데이터 1 (언론사별 보도량)", "45, 32, 28, 15")
                    data2 = st.text_input("데이터 2 (분야별 기사수)", "67, 34, 19")
                    data3 = st.text_input("데이터 3 (감성분석 결과)", "52, 33, 15")
                    
                    submit = st.form_submit_button("통계 차트 생성")
                    
                    if submit:
                        with st.spinner("통계 차트 생성 중..."):
                            # 데이터 변환
                            data = {
                                "언론사별 보도량": [float(x.strip()) for x in data1.split(",")],
                                "분야별 기사수": [float(x.strip()) for x in data2.split(",")],
                                "감성분석 결과": [float(x.strip()) for x in data3.split(",")]
                            }
                            
                            result = call_api(
                                "/content-creator/tools/stats-image",
                                method="POST",
                                data={
                                    "data": data,
                                    "title": chart_title,
                                    "chart_type": chart_type
                                }
                            )
                            
                            if result and "image_data" in result:
                                if "visual_assets" not in st.session_state:
                                    st.session_state.visual_assets = {}
                                st.session_state.visual_assets["stats_chart"] = result["image_data"]
                                st.success("통계 차트 생성 완료")
                                st.experimental_rerun()
        
        # 다음 단계 버튼
        col1, col2 = st.columns(2)
        with col1:
            if st.button("팩트 체크 단계로 이동"):
                st.session_state.selected_page = "팩트 체크"
                st.experimental_rerun()
        with col2:
            if st.button("모든 시각 자료 내보내기"):
                with st.spinner("패키지 생성 중..."):
                    result = call_api(
                        "/content-creator/tools/export-package",
                        method="POST",
                        data={
                            "issue_data": {
                                "issue_summary": st.session_state.issue_analysis.get("issue_summary", {}),
                                "issue_flow": st.session_state.issue_analysis.get("issue_flow", {})
                            },
                            "format": "html"
                        }
                    )
                    
                    if result and "file_path" in result:
                        st.success(f"시각 자료 패키지 생성 완료: {result['file_path']}")
                        st.markdown(f"[파일 다운로드]({API_URL}/api/download/{os.path.basename(result['file_path'])})")

# 팩트 체크 페이지
def show_fact_checking():
    st.header("✅ 팩트 체크")
    
    # 현재 워크플로우 확인
    workflow = get_current_workflow()
    if not workflow:
        st.warning("먼저 이슈 리서치 페이지에서 워크플로우를 생성하고 이슈를 분석하세요.")
        return
    
    st.info(f"현재 워크플로우: {workflow['name']} (상태: {workflow['status']})")
    
    # 필요한 데이터 확인
    if not st.session_state.content_brief:
        if "outputs" in workflow and "planning" in workflow["outputs"]:
            st.session_state.content_brief = workflow["outputs"]["planning"].get("content_brief")
    
    if not st.session_state.content_brief:
        st.warning("먼저 콘텐츠 기획 단계를 완료하세요.")
        return
    
    # 팩트 체크 실행 또는 표시
    if not st.session_state.verified_facts:
        if "outputs" in workflow and "verification" in workflow["outputs"]:
            st.session_state.verified_facts = workflow["outputs"]["verification"].get("verified_facts")
        
        if not st.session_state.verified_facts:
            # 팩트 체크 버튼
            if st.button("팩트 체크 실행"):
                with st.spinner("팩트 체크 실행 중..."):
                    # 워크플로우 단계 실행
                    result = call_api(
                        f"/content-creator/workflows/{st.session_state.current_workflow_id}/execute",
                        method="POST",
                        data={
                            "stage_id": "verification",
                            "stage_data": {
                                "content_brief": st.session_state.content_brief,
                                "issue_analysis": st.session_state.issue_analysis
                            }
                        }
                    )
                    
                    if result and "verified_facts" in result:
                        st.session_state.verified_facts = result["verified_facts"]
                        st.success("팩트 체크 완료")
    
    # 팩트 체크 결과 표시
    if st.session_state.verified_facts:
        facts = st.session_state.verified_facts
        
        st.subheader("📋 팩트 체크 결과")
        
        # 신뢰도 요약
        confidence_counts = {"높음": 0, "중간": 0, "낮음": 0}
        for fact in facts:
            confidence_level = fact.get("confidence_level", "")
            if confidence_level in confidence_counts:
                confidence_counts[confidence_level] += 1
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("높은 신뢰도", confidence_counts["높음"])
        with col2:
            st.metric("중간 신뢰도", confidence_counts["중간"])
        with col3:
            st.metric("낮은 신뢰도", confidence_counts["낮음"])
        
        # 표로 사실 표시
        fact_data = []
        for fact in facts:
            fact_data.append({
                "사실": fact.get("fact", ""),
                "신뢰도": fact.get("confidence_level", ""),
                "점수": fact.get("confidence_score", 0),
                "출처 수": fact.get("unique_sources", 0),
                "관련 뉴스": fact.get("related_news_count", 0)
            })
        
        st.dataframe(pd.DataFrame(fact_data), use_container_width=True)
        
        # 세부 정보
        st.subheader("세부 정보")
        
        for i, fact in enumerate(facts):
            with st.expander(f"사실 {i+1}: {fact.get('fact', '')}", expanded=i==0):
                st.markdown(f"**신뢰도**: {fact.get('confidence_level', '')} ({fact.get('confidence_score', 0)}점)")
                st.markdown(f"**출처 수**: {fact.get('unique_sources', 0)}")
                st.markdown(f"**관련 뉴스 수**: {fact.get('related_news_count', 0)}")
                
                if "related_news" in fact and fact["related_news"]:
                    st.markdown("**관련 뉴스:**")
                    for news in fact["related_news"]:
                        st.markdown(f"- {news.get('title', '')} ({news.get('provider', '')})")
        
        # 다음 단계 버튼
        col1, col2 = st.columns(2)
        with col1:
            if st.button("최종 내보내기"):
                with st.spinner("최종 패키지 생성 중..."):
                    result = call_api(
                        f"/content-creator/workflows/{st.session_state.current_workflow_id}/execute",
                        method="POST",
                        data={
                            "stage_id": "export",
                            "stage_data": {
                                "format": "json"
                            }
                        }
                    )
                    
                    if result and "file_path" in result:
                        st.session_state.export_path = result["file_path"]
                        st.success(f"최종 패키지 생성 완료!")
                        st.markdown(f"[파일 다운로드]({API_URL}/api/download/{os.path.basename(result['file_path'])})")
        
        with col2:
            st.markdown("이 단계를 완료하면 콘텐츠 제작을 시작할 수 있습니다.")
        
        # 추가 사실 검증 폼
        st.subheader("추가 사실 검증")
        
        with st.form("fact_check_form"):
            fact_text = st.text_input("검증할 사실")
            fact_source = st.text_input("출처")
            
            submit = st.form_submit_button("검증")
            
            if submit and fact_text:
                with st.spinner("사실 검증 중..."):
                    # 예시 뉴스 데이터 (실제로는 API에서 검색해야 함)
                    news_list = [
                        {
                            "title": "한국은행, 기준금리 동결 발표",
                            "content": f"{fact_text}",
                            "provider": "서울경제",
                            "published_at": "2025-05-10T10:15:00"
                        }
                    ]
                    
                    result = call_api(
                        "/content-creator/tools/verify-facts",
                        method="POST",
                        data={
                            "facts": [
                                {
                                    "fact": fact_text,
                                    "source": fact_source
                                }
                            ],
                            "news_list": news_list
                        }
                    )
                    
                    if result and "verified_facts" in result:
                        st.success("사실 검증 완료")
                        
                        # 결과 표시
                        verified = result["verified_facts"][0]
                        st.markdown(f"**신뢰도**: {verified.get('confidence_level', '')} ({verified.get('confidence_score', 0)}점)")
                        st.markdown(f"**출처 수**: {verified.get('unique_sources', 0)}")
                        st.markdown(f"**관련 뉴스 수**: {verified.get('related_news_count', 0)}")

# 워크플로우 관리 페이지
def show_workflow_management():
    st.header("🔄 워크플로우 관리")
    
    # 워크플로우 목록 로드
    workflows = load_workflows()
    
    if not workflows:
        st.warning("워크플로우가 없습니다. 이슈 리서치 페이지에서 새 워크플로우를 생성하세요.")
        return
    
    # 워크플로우 목록 표시
    st.subheader("워크플로우 목록")
    
    workflow_data = []
    for workflow in workflows:
        created_at = datetime.fromisoformat(workflow.get('created_at', '').replace('Z', '+00:00')).strftime("%Y-%m-%d %H:%M")
        workflow_data.append({
            "ID": workflow.get("id", ""),
            "이름": workflow.get("name", ""),
            "생성일": created_at,
            "상태": workflow.get("status", "")
        })
    
    st.dataframe(pd.DataFrame(workflow_data), use_container_width=True)
    
    # 워크플로우 세부 정보
    st.subheader("워크플로우 세부 정보")
    
    selected_workflow_id = st.selectbox(
        "워크플로우 선택",
        [w["id"] for w in workflows],
        index=0 if workflows else None,
        format_func=lambda x: next((w["name"] for w in workflows if w["id"] == x), x)
    )
    
    if selected_workflow_id:
        # 선택된 워크플로우 상세 정보 가져오기
        workflow = call_api(f"/content-creator/workflows/{selected_workflow_id}")
        
        if workflow:
            st.session_state.current_workflow_id = selected_workflow_id
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**이름**: {workflow.get('name', '')}")
                st.markdown(f"**설명**: {workflow.get('description', '')}")
                st.markdown(f"**상태**: {workflow.get('status', '')}")
                
                created_at = datetime.fromisoformat(workflow.get('created_at', '').replace('Z', '+00:00')).strftime("%Y-%m-%d %H:%M")
                st.markdown(f"**생성일**: {created_at}")
            
            with col2:
                # 워크플로우 단계 표시
                stages = workflow.get("stages", [])
                current_stage = workflow.get("current_stage", 0)
                
                st.markdown(f"**현재 단계**: {current_stage + 1}/{len(stages)}")
                
                for i, stage in enumerate(stages):
                    stage_status = "✅" if stage.get("status") == "completed" else "⏳" if i == current_stage else "⏸️"
                    st.markdown(f"{stage_status} **{stage.get('name', '')}**: {stage.get('description', '')}")
            
            # 워크플로우 작업
            st.subheader("워크플로우 작업")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("이슈 리서치로 이동"):
                    st.session_state.selected_page = "이슈 리서치"
                    st.experimental_rerun()
            
            with col2:
                if st.button("콘텐츠 기획으로 이동"):
                    st.session_state.selected_page = "콘텐츠 기획"
                    st.experimental_rerun()
            
            with col3:
                if st.button("워크플로우 삭제"):
                    if st.session_state.current_workflow_id == selected_workflow_id:
                        st.session_state.current_workflow_id = None
                        st.session_state.issue_analysis = None
                        st.session_state.content_brief = None
                        st.session_state.visual_assets = None
                        st.session_state.verified_facts = None
                    
                    result = call_api(
                        f"/content-creator/workflows/{selected_workflow_id}",
                        method="DELETE"
                    )
                    
                    if result and result.get("success"):
                        st.success("워크플로우 삭제 완료")
                        st.experimental_rerun()
            
            # 워크플로우 출력물
            if "outputs" in workflow and workflow["outputs"]:
                st.subheader("워크플로우 출력물")
                
                for stage_id, output in workflow["outputs"].items():
                    with st.expander(f"{stage_id.capitalize()} 단계 출력물"):
                        st.json(output)
            
            # 템플릿으로 저장
            with st.form("save_template_form"):
                st.subheader("템플릿으로 저장")
                
                template_name = st.text_input("템플릿 이름", value=f"{workflow.get('name', '')} 템플릿")
                template_desc = st.text_area("설명", value="재사용 가능한 워크플로우 템플릿")
                
                submit = st.form_submit_button("템플릿 저장")
                
                if submit:
                    result = call_api(
                        "/content-creator/templates",
                        method="POST",
                        data={
                            "workflow_id": selected_workflow_id,
                            "template_name": template_name,
                            "template_description": template_desc
                        }
                    )
                    
                    if result and "id" in result:
                        st.success(f"템플릿 저장 완료: {template_name}")

# 페이지 표시
if "selected_page" in st.session_state:
    page = st.session_state.selected_page
    # 세션 상태 페이지 사용 후 초기화
    st.session_state.selected_page = None

if page == "이슈 리서치":
    show_issue_research()
elif page == "콘텐츠 기획":
    show_content_planning()
elif page == "자료 생성":
    show_material_generation()
elif page == "팩트 체크":
    show_fact_checking()
elif page == "워크플로우":
    show_workflow_management()

# 푸터
st.markdown("---")
st.markdown(
    "© 2025 서울경제신문. All rights reserved."
)