"""
콘텐츠 제작 워크플로우 관리

콘텐츠 제작 과정의 워크플로우를 관리하는 모듈
"""

import os
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple
import uuid

from src.modules.content_creator.tools import ContentAssistant
from src.api.bigkinds_client import BigKindsClient
from src.utils.logger import setup_logger

class ContentWorkflow:
    """콘텐츠 제작 워크플로우 관리 클래스"""
    
    def __init__(self, api_client: Optional[BigKindsClient] = None):
        """콘텐츠 워크플로우 초기화
        
        Args:
            api_client: 빅카인즈 API 클라이언트 (없으면 생성)
        """
        self.logger = setup_logger("ainova.content")
        self.api_client = api_client
        self.content_assistant = ContentAssistant()
        
        # 워크플로우 저장소
        self.workflow_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "workflows")
        os.makedirs(self.workflow_dir, exist_ok=True)
        
        # 템플릿 저장소
        self.template_dir = os.path.join(self.workflow_dir, "templates")
        os.makedirs(self.template_dir, exist_ok=True)
    
    async def create_workflow(self, 
                          name: str, 
                          description: str = "",
                          template_id: Optional[str] = None) -> Dict[str, Any]:
        """새 워크플로우 생성
        
        Args:
            name: 워크플로우 이름
            description: 워크플로우 설명
            template_id: 템플릿 ID (있으면 템플릿 기반으로 생성)
            
        Returns:
            생성된 워크플로우 정보
        """
        workflow_id = str(uuid.uuid4())
        
        # 기본 워크플로우 구조
        workflow = {
            "id": workflow_id,
            "name": name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "stages": [],
            "current_stage": 0,
            "status": "created",
            "data": {},
            "outputs": {}
        }
        
        # 템플릿 기반 생성
        if template_id:
            template_file = os.path.join(self.template_dir, f"{template_id}.json")
            if os.path.exists(template_file):
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template = json.load(f)
                    
                    # 템플릿에서 워크플로우 단계 복사
                    workflow["stages"] = template.get("stages", [])
                    
                    # 템플릿 메타데이터 추가
                    workflow["template_id"] = template_id
                    workflow["template_name"] = template.get("name", "")
                    
                    self.logger.info(f"템플릿 {template_id}를 기반으로 워크플로우 {workflow_id} 생성")
                except Exception as e:
                    self.logger.error(f"템플릿 로드 오류: {e}")
            else:
                # 기본 워크플로우 단계 설정
                self._set_default_stages(workflow)
        else:
            # 기본 워크플로우 단계 설정
            self._set_default_stages(workflow)
        
        # 워크플로우 저장
        workflow_file = os.path.join(self.workflow_dir, f"{workflow_id}.json")
        with open(workflow_file, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, ensure_ascii=False, indent=2)
        
        return workflow
    
    def _set_default_stages(self, workflow: Dict[str, Any]) -> None:
        """기본 워크플로우 단계 설정
        
        Args:
            workflow: 워크플로우 데이터
        """
        workflow["stages"] = [
            {
                "id": "research",
                "name": "이슈 리서치",
                "description": "관련 이슈 검색 및 분석",
                "status": "pending",
                "required_inputs": ["query", "start_date", "end_date"],
                "outputs": ["issue_analysis"]
            },
            {
                "id": "planning",
                "name": "콘텐츠 기획",
                "description": "콘텐츠 구조 및 방향 설정",
                "status": "pending",
                "required_inputs": ["issue_analysis"],
                "outputs": ["content_brief"]
            },
            {
                "id": "material",
                "name": "자료 생성",
                "description": "시각 자료 및 참고 자료 생성",
                "status": "pending",
                "required_inputs": ["content_brief"],
                "outputs": ["visual_assets"]
            },
            {
                "id": "verification",
                "name": "팩트 체크",
                "description": "내용 검증 및 신뢰도 평가",
                "status": "pending",
                "required_inputs": ["content_brief"],
                "outputs": ["verified_facts"]
            },
            {
                "id": "export",
                "name": "내보내기",
                "description": "최종 콘텐츠 패키지 생성",
                "status": "pending",
                "required_inputs": ["content_brief", "visual_assets", "verified_facts"],
                "outputs": ["content_package"]
            }
        ]
    
    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """워크플로우 조회
        
        Args:
            workflow_id: 워크플로우 ID
            
        Returns:
            워크플로우 정보 또는 None
        """
        workflow_file = os.path.join(self.workflow_dir, f"{workflow_id}.json")
        if os.path.exists(workflow_file):
            try:
                with open(workflow_file, 'r', encoding='utf-8') as f:
                    workflow = json.load(f)
                return workflow
            except Exception as e:
                self.logger.error(f"워크플로우 로드 오류: {e}")
                return None
        else:
            return None
    
    async def list_workflows(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """워크플로우 목록 조회
        
        Args:
            status: 상태 필터 (optional)
            
        Returns:
            워크플로우 목록
        """
        workflows = []
        
        for filename in os.listdir(self.workflow_dir):
            if filename.endswith('.json') and not filename.startswith('template_'):
                workflow_file = os.path.join(self.workflow_dir, filename)
                try:
                    with open(workflow_file, 'r', encoding='utf-8') as f:
                        workflow = json.load(f)
                    
                    # 상태 필터 적용
                    if status and workflow.get("status") != status:
                        continue
                    
                    # 기본 정보만 포함
                    workflows.append({
                        "id": workflow.get("id"),
                        "name": workflow.get("name"),
                        "description": workflow.get("description"),
                        "created_at": workflow.get("created_at"),
                        "updated_at": workflow.get("updated_at"),
                        "status": workflow.get("status"),
                        "current_stage": workflow.get("current_stage")
                    })
                except Exception as e:
                    self.logger.error(f"워크플로우 로드 오류 ({filename}): {e}")
        
        # 생성일 기준 정렬
        workflows.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return workflows
    
    async def update_workflow(self, 
                         workflow_id: str, 
                         data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """워크플로우 업데이트
        
        Args:
            workflow_id: 워크플로우 ID
            data: 업데이트할 데이터
            
        Returns:
            업데이트된 워크플로우 정보 또는 None
        """
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return None
        
        # 업데이트 가능한 필드
        updateable_fields = ["name", "description", "current_stage", "status", "data", "outputs"]
        
        for field in updateable_fields:
            if field in data:
                workflow[field] = data[field]
        
        # 타임스탬프 업데이트
        workflow["updated_at"] = datetime.now().isoformat()
        
        # 워크플로우 저장
        workflow_file = os.path.join(self.workflow_dir, f"{workflow_id}.json")
        with open(workflow_file, 'w', encoding='utf-8') as f:
            json.dump(workflow, f, ensure_ascii=False, indent=2)
        
        return workflow
    
    async def delete_workflow(self, workflow_id: str) -> bool:
        """워크플로우 삭제
        
        Args:
            workflow_id: 워크플로우 ID
            
        Returns:
            삭제 성공 여부
        """
        workflow_file = os.path.join(self.workflow_dir, f"{workflow_id}.json")
        if os.path.exists(workflow_file):
            try:
                os.remove(workflow_file)
                return True
            except Exception as e:
                self.logger.error(f"워크플로우 삭제 오류: {e}")
                return False
        else:
            return False
    
    async def execute_stage(self, 
                       workflow_id: str, 
                       stage_id: Optional[str] = None,
                       stage_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """워크플로우 단계 실행
        
        Args:
            workflow_id: 워크플로우 ID
            stage_id: 단계 ID (없으면 현재 단계)
            stage_data: 단계 실행에 필요한 데이터
            
        Returns:
            단계 실행 결과
        """
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return {"error": "워크플로우를 찾을 수 없습니다"}
        
        # 단계 ID가 없으면 현재 단계 사용
        if not stage_id:
            current_stage_index = workflow.get("current_stage", 0)
            if current_stage_index >= len(workflow.get("stages", [])):
                return {"error": "더 이상 실행할 단계가 없습니다"}
            
            stage = workflow["stages"][current_stage_index]
            stage_id = stage.get("id")
        else:
            # 단계 ID로 단계 찾기
            stage = None
            for s in workflow.get("stages", []):
                if s.get("id") == stage_id:
                    stage = s
                    break
            
            if not stage:
                return {"error": f"단계 ID {stage_id}를 찾을 수 없습니다"}
        
        # 단계별 실행 로직
        result = {}
        try:
            if stage_id == "research":
                # 이슈 리서치 단계
                result = await self._execute_research_stage(workflow, stage, stage_data)
            elif stage_id == "planning":
                # 콘텐츠 기획 단계
                result = await self._execute_planning_stage(workflow, stage, stage_data)
            elif stage_id == "material":
                # 자료 생성 단계
                result = await self._execute_material_stage(workflow, stage, stage_data)
            elif stage_id == "verification":
                # 팩트 체크 단계
                result = await self._execute_verification_stage(workflow, stage, stage_data)
            elif stage_id == "export":
                # 내보내기 단계
                result = await self._execute_export_stage(workflow, stage, stage_data)
            else:
                result = {"error": f"지원하지 않는 단계 ID: {stage_id}"}
        except Exception as e:
            self.logger.error(f"단계 실행 오류 ({stage_id}): {e}")
            result = {"error": f"단계 실행 중 오류 발생: {str(e)}"}
        
        # 결과가 성공적이면 워크플로우 업데이트
        if "error" not in result:
            # 단계 상태 업데이트
            for s in workflow["stages"]:
                if s.get("id") == stage_id:
                    s["status"] = "completed"
                    break
            
            # 단계 출력 저장
            if "outputs" not in workflow:
                workflow["outputs"] = {}
            workflow["outputs"][stage_id] = result
            
            # 다음 단계로 이동
            for i, s in enumerate(workflow["stages"]):
                if s.get("id") == stage_id and i < len(workflow["stages"]) - 1:
                    workflow["current_stage"] = i + 1
                    break
            
            # 모든 단계가 완료되었는지 확인
            all_completed = all(s.get("status") == "completed" for s in workflow["stages"])
            if all_completed:
                workflow["status"] = "completed"
            
            # 워크플로우 저장
            await self.update_workflow(workflow_id, workflow)
        
        return result
    
    async def _execute_research_stage(self, 
                                  workflow: Dict[str, Any], 
                                  stage: Dict[str, Any],
                                  stage_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """이슈 리서치 단계 실행
        
        Args:
            workflow: 워크플로우 데이터
            stage: 단계 데이터
            stage_data: 단계 실행 데이터
            
        Returns:
            단계 실행 결과
        """
        # 필수 입력 확인
        required_inputs = stage.get("required_inputs", [])
        missing_inputs = []
        for input_name in required_inputs:
            if not stage_data or input_name not in stage_data:
                missing_inputs.append(input_name)
        
        if missing_inputs:
            return {"error": f"필수 입력이 누락되었습니다: {', '.join(missing_inputs)}"}
        
        # API 엔진 초기화 (실제 구현에서는 ainova_engine 모듈 사용)
        # 이 예시에서는 실제 API 호출을 시뮬레이션
        
        # 임시 분석 결과 (실제로는 API 호출 결과)
        query = stage_data.get("query", "")
        start_date = stage_data.get("start_date", "")
        end_date = stage_data.get("end_date", "")
        
        mock_analysis = {
            "query": query,
            "start_date": start_date,
            "end_date": end_date,
            "news_count": 123,
            "issue_map": {
                "clusters": {
                    "1": {
                        "id": 1,
                        "keywords": ["경제성장", "금리인하", "물가안정"],
                        "news_count": 45,
                        "representative_title": "한국은행, 기준금리 동결 결정"
                    },
                    "2": {
                        "id": 2,
                        "keywords": ["주택시장", "부동산정책", "전세가격"],
                        "news_count": 32,
                        "representative_title": "수도권 아파트 가격 상승세 지속"
                    }
                },
                "key_clusters": [1, 2]
            },
            "issue_flow": {
                "key_events": [
                    {
                        "timestamp": "2025-05-10T09:00:00",
                        "title": "한국은행, 기준금리 동결 발표",
                        "importance": 10,
                        "related_news_count": 15
                    },
                    {
                        "timestamp": "2025-05-12T14:30:00",
                        "title": "정부, 부동산 시장 안정화 대책 발표",
                        "importance": 8,
                        "related_news_count": 12
                    },
                    {
                        "timestamp": "2025-05-15T10:00:00",
                        "title": "통계청, 4월 물가지수 발표",
                        "importance": 7,
                        "related_news_count": 10
                    }
                ],
                "phases": [
                    {
                        "phase_id": 0,
                        "name": "서론",
                        "start_time": "2025-05-10T00:00:00",
                        "end_time": "2025-05-11T23:59:59",
                        "news_count": 25,
                        "representative_news": {
                            "title": "한국은행, 기준금리 동결 결정"
                        }
                    },
                    {
                        "phase_id": 1,
                        "name": "본론",
                        "start_time": "2025-05-12T00:00:00",
                        "end_time": "2025-05-14T23:59:59",
                        "news_count": 38,
                        "representative_news": {
                            "title": "정부, 부동산 시장 안정화 대책 발표"
                        }
                    },
                    {
                        "phase_id": 2,
                        "name": "결론",
                        "start_time": "2025-05-15T00:00:00",
                        "end_time": "2025-05-16T23:59:59",
                        "news_count": 20,
                        "representative_news": {
                            "title": "전문가들 '금리 동결과 부동산 정책 효과 제한적' 평가"
                        }
                    }
                ]
            },
            "issue_summary": {
                "title": "금리동결과 부동산 시장 전망",
                "summary_text": "한국은행이 기준금리를 동결한 가운데, 정부의 부동산 시장 안정화 대책이 발표되었습니다. 전문가들은 금리 동결과 정부 정책의 효과가 제한적일 것으로 전망하고 있습니다.",
                "keywords": ["금리동결", "부동산정책", "시장안정화", "전문가전망", "경제전망"],
                "key_quotes": [
                    {
                        "quotation": "현 시점에서 기준금리 인하는 시기상조라고 판단했다. 물가안정이 우선되어야 한다.",
                        "source": "한국은행 총재",
                        "provider": "서울경제",
                        "published_at": "2025-05-10T10:15:00"
                    },
                    {
                        "quotation": "부동산 시장 안정화를 위해 투기수요는 차단하되 실수요자 지원은 강화할 것이다.",
                        "source": "부동산정책 담당 차관",
                        "provider": "서울경제",
                        "published_at": "2025-05-12T15:30:00"
                    }
                ],
                "perspectives": [
                    {
                        "type": "person/org",
                        "source": "한국은행",
                        "keywords": ["물가안정", "경기회복", "금융안정"],
                        "sample_quote": "현 시점에서 기준금리 인하는 시기상조라고 판단했다. 물가안정이 우선되어야 한다."
                    },
                    {
                        "type": "person/org",
                        "source": "정부 관계자",
                        "keywords": ["부동산정책", "시장안정", "실수요자"],
                        "sample_quote": "부동산 시장 안정화를 위해 투기수요는 차단하되 실수요자 지원은 강화할 것이다."
                    },
                    {
                        "type": "media",
                        "source": "서울경제",
                        "keywords": ["경제전망", "정책효과", "시장반응"],
                        "sample_title": "금리동결·부동산대책 '정책 조합' 효과는?"
                    }
                ]
            }
        }
        
        # 실제 구현에서는 여기서 API 엔진을 호출하여 이슈 분석 결과를 가져옴
        # 예: result = await ainova_engine.analyze_issue(query, start_date, end_date)
        
        return {"issue_analysis": mock_analysis}
    
    async def _execute_planning_stage(self, 
                                  workflow: Dict[str, Any], 
                                  stage: Dict[str, Any],
                                  stage_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """콘텐츠 기획 단계 실행
        
        Args:
            workflow: 워크플로우 데이터
            stage: 단계 데이터
            stage_data: 단계 실행 데이터
            
        Returns:
            단계 실행 결과
        """
        # 이전 단계 결과 확인
        issue_analysis = None
        if "outputs" in workflow and "research" in workflow["outputs"]:
            issue_analysis = workflow["outputs"]["research"].get("issue_analysis")
        
        if not issue_analysis and (not stage_data or "issue_analysis" not in stage_data):
            return {"error": "이슈 분석 결과가 없습니다"}
        
        # 단계 데이터에서 가져오거나 이전 단계 결과 사용
        if stage_data and "issue_analysis" in stage_data:
            issue_analysis = stage_data["issue_analysis"]
        
        # 콘텐츠 브리프 생성
        content_brief = self.content_assistant.generate_content_brief(issue_analysis)
        
        return {"content_brief": content_brief}
    
    async def _execute_material_stage(self, 
                                  workflow: Dict[str, Any], 
                                  stage: Dict[str, Any],
                                  stage_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """자료 생성 단계 실행
        
        Args:
            workflow: 워크플로우 데이터
            stage: 단계 데이터
            stage_data: 단계 실행 데이터
            
        Returns:
            단계 실행 결과
        """
        # 필요한 이전 데이터 확인
        content_brief = None
        issue_analysis = None
        
        if "outputs" in workflow:
            if "planning" in workflow["outputs"]:
                content_brief = workflow["outputs"]["planning"].get("content_brief")
            if "research" in workflow["outputs"]:
                issue_analysis = workflow["outputs"]["research"].get("issue_analysis")
        
        if not content_brief and (not stage_data or "content_brief" not in stage_data):
            return {"error": "콘텐츠 브리프가 없습니다"}
        
        if not issue_analysis and (not stage_data or "issue_analysis" not in stage_data):
            return {"error": "이슈 분석 결과가 없습니다"}
        
        # 단계 데이터에서 가져오거나 이전 단계 결과 사용
        if stage_data:
            if "content_brief" in stage_data:
                content_brief = stage_data["content_brief"]
            if "issue_analysis" in stage_data:
                issue_analysis = stage_data["issue_analysis"]
        
        # 시각 자료 생성
        visual_assets = {}
        
        # 인용구 이미지 생성
        if issue_analysis and "issue_summary" in issue_analysis and "key_quotes" in issue_analysis["issue_summary"]:
            quotes = issue_analysis["issue_summary"]["key_quotes"]
            if quotes:
                quote = quotes[0]
                quote_text = quote.get("quotation", "")
                source = quote.get("source", "")
                visual_assets["quote_image"] = self.content_assistant.create_quote_image(quote_text, source)
        
        # 타임라인 이미지 생성
        if issue_analysis and "issue_flow" in issue_analysis and "key_events" in issue_analysis["issue_flow"]:
            events = issue_analysis["issue_flow"]["key_events"]
            if events:
                visual_assets["timeline_image"] = self.content_assistant.create_timeline_image(
                    events, "이슈 주요 이벤트 타임라인"
                )
        
        # 관점 비교 이미지 생성
        if issue_analysis and "issue_summary" in issue_analysis and "perspectives" in issue_analysis["issue_summary"]:
            perspectives = issue_analysis["issue_summary"]["perspectives"]
            if perspectives:
                visual_assets["perspectives_image"] = self.content_assistant.create_perspective_comparison(
                    perspectives, "이슈 관련 다양한 관점"
                )
        
        # 통계 차트 생성 (예시 데이터 사용)
        example_stats = {
            "언론사별 보도량": [45, 32, 28, 15],
            "분야별 기사수": [67, 34, 19],
            "감성분석 결과": [52, 33, 15]
        }
        visual_assets["stats_chart"] = self.content_assistant.create_statistics_image(
            example_stats, "이슈 관련 주요 통계", "bar"
        )
        
        return {"visual_assets": visual_assets}
    
    async def _execute_verification_stage(self, 
                                     workflow: Dict[str, Any], 
                                     stage: Dict[str, Any],
                                     stage_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """팩트 체크 단계 실행
        
        Args:
            workflow: 워크플로우 데이터
            stage: 단계 데이터
            stage_data: 단계 실행 데이터
            
        Returns:
            단계 실행 결과
        """
        # 필요한 이전 데이터 확인
        content_brief = None
        issue_analysis = None
        
        if "outputs" in workflow:
            if "planning" in workflow["outputs"]:
                content_brief = workflow["outputs"]["planning"].get("content_brief")
            if "research" in workflow["outputs"]:
                issue_analysis = workflow["outputs"]["research"].get("issue_analysis")
        
        if not content_brief and (not stage_data or "content_brief" not in stage_data):
            return {"error": "콘텐츠 브리프가 없습니다"}
        
        # 단계 데이터에서 가져오거나 이전 단계 결과 사용
        if stage_data:
            if "content_brief" in stage_data:
                content_brief = stage_data["content_brief"]
            if "issue_analysis" in stage_data:
                issue_analysis = stage_data["issue_analysis"]
        
        # 검증할 사실 추출
        facts_to_verify = []
        if content_brief and "key_facts" in content_brief:
            facts_to_verify.extend(content_brief["key_facts"])
        
        # 뉴스 목록 가져오기 (예시)
        news_list = []
        if issue_analysis:
            # 실제 구현에서는 뉴스 목록을 API에서 가져오거나 이슈 분석 결과에서 추출
            # 여기서는 더미 데이터 사용
            news_list = [
                {
                    "title": "한국은행, 기준금리 동결 발표",
                    "content": "한국은행이 기준금리를 동결했다. 한국은행 총재는 '현 시점에서 기준금리 인하는 시기상조라고 판단했다. 물가안정이 우선되어야 한다.'고 밝혔다.",
                    "provider": "서울경제",
                    "published_at": "2025-05-10T10:15:00"
                },
                {
                    "title": "정부, 부동산 시장 안정화 대책 발표",
                    "content": "정부가 부동산 시장 안정화 대책을 발표했다. 부동산정책 담당 차관은 '부동산 시장 안정화를 위해 투기수요는 차단하되 실수요자 지원은 강화할 것이다.'라고 밝혔다.",
                    "provider": "서울경제",
                    "published_at": "2025-05-12T15:30:00"
                }
            ]
        
        # 사실 검증
        verified_facts = self.content_assistant.verify_facts(facts_to_verify, news_list)
        
        # 추가 사실 추출 (예시)
        additional_facts = [
            {
                "fact": "한국은행 기준금리는 현재 3.0%로 5개월 연속 동결",
                "source": "한국은행",
                "date": "2025-05-10"
            },
            {
                "fact": "4월 소비자물가지수는 전년 대비 2.1% 상승",
                "source": "통계청",
                "date": "2025-05-15"
            }
        ]
        
        # 추가 사실 검증
        additional_verified = self.content_assistant.verify_facts(additional_facts, news_list)
        verified_facts.extend(additional_verified)
        
        return {"verified_facts": verified_facts}
    
    async def _execute_export_stage(self, 
                               workflow: Dict[str, Any], 
                               stage: Dict[str, Any],
                               stage_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """내보내기 단계 실행
        
        Args:
            workflow: 워크플로우 데이터
            stage: 단계 데이터
            stage_data: 단계 실행 데이터
            
        Returns:
            단계 실행 결과
        """
        # 이전 단계 결과 확인
        if "outputs" not in workflow:
            return {"error": "이전 단계 결과가 없습니다"}
        
        # 필요한 데이터 수집
        content_brief = None
        issue_analysis = None
        visual_assets = None
        verified_facts = None
        
        if "planning" in workflow["outputs"]:
            content_brief = workflow["outputs"]["planning"].get("content_brief")
        
        if "research" in workflow["outputs"]:
            issue_analysis = workflow["outputs"]["research"].get("issue_analysis")
        
        if "material" in workflow["outputs"]:
            visual_assets = workflow["outputs"]["material"].get("visual_assets")
        
        if "verification" in workflow["outputs"]:
            verified_facts = workflow["outputs"]["verification"].get("verified_facts")
        
        # 단계 데이터에서 추가 정보 가져오기
        format = "json"  # 기본 형식
        if stage_data:
            if "format" in stage_data:
                format = stage_data["format"]
        
        # 내보내기 데이터 구성
        export_data = {
            "issue_analysis": issue_analysis,
            "content_brief": content_brief,
            "visual_assets": visual_assets,
            "verified_facts": verified_facts
        }
        
        # 내보내기 실행
        file_path = self.content_assistant.export_content_package(
            issue_analysis if issue_analysis else {},
            format
        )
        
        return {
            "content_package": export_data,
            "file_path": file_path,
            "format": format
        }
    
    async def save_as_template(self, 
                          workflow_id: str, 
                          template_name: str,
                          template_description: str = "") -> Dict[str, Any]:
        """워크플로우를 템플릿으로 저장
        
        Args:
            workflow_id: 워크플로우 ID
            template_name: 템플릿 이름
            template_description: 템플릿 설명
            
        Returns:
            템플릿 정보
        """
        workflow = await self.get_workflow(workflow_id)
        if not workflow:
            return {"error": "워크플로우를 찾을 수 없습니다"}
        
        # 템플릿 ID 생성
        template_id = str(uuid.uuid4())
        
        # 템플릿 데이터 구성
        template = {
            "id": template_id,
            "name": template_name,
            "description": template_description,
            "created_at": datetime.now().isoformat(),
            "source_workflow_id": workflow_id,
            "stages": workflow.get("stages", [])
        }
        
        # 템플릿 저장
        template_file = os.path.join(self.template_dir, f"{template_id}.json")
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        
        return template
    
    async def list_templates(self) -> List[Dict[str, Any]]:
        """템플릿 목록 조회
        
        Returns:
            템플릿 목록
        """
        templates = []
        
        for filename in os.listdir(self.template_dir):
            if filename.endswith('.json'):
                template_file = os.path.join(self.template_dir, filename)
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template = json.load(f)
                    
                    # 기본 정보만 포함
                    templates.append({
                        "id": template.get("id"),
                        "name": template.get("name"),
                        "description": template.get("description"),
                        "created_at": template.get("created_at")
                    })
                except Exception as e:
                    self.logger.error(f"템플릿 로드 오류 ({filename}): {e}")
        
        # 생성일 기준 정렬
        templates.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return templates