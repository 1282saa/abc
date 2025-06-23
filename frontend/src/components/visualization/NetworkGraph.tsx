import React, { useEffect, useRef, useState, useCallback } from "react";
import ForceGraph2D from "react-force-graph-2d";
import { motion, AnimatePresence } from "framer-motion";

interface NetworkNode {
  id: string;
  name: string;
  type: "keyword" | "article" | "person" | "location" | "organization";
  category?: "person" | "location" | "organization" | "keyword";
  size: number;
  color: string;
  weight?: number;
  level?: number;
  title?: string;
  provider?: string;
  url?: string;
  published_at?: string;
  // 위치 고정을 위한 속성 추가
  fx?: number;
  fy?: number;
  // 실제 위치 속성 (D3 시뮬레이션에서 사용)
  x?: number;
  y?: number;
}

interface NetworkLink {
  source: string;
  target: string;
  strength: number;
  width: number;
  type?: string;
}

interface NetworkData {
  nodes: NetworkNode[];
  links: NetworkLink[];
}

interface NetworkGraphProps {
  data: NetworkData;
  onNodeClick?: (node: NetworkNode) => void;
  onNodeDoubleClick?: (node: NetworkNode) => void;
  height?: number;
  width?: number;
}

interface NodeDetailPopup {
  node: NetworkNode;
  x: number;
  y: number;
}

const NetworkGraph: React.FC<NetworkGraphProps> = ({
  data,
  onNodeClick,
  onNodeDoubleClick,
  height = 500,
  width = 800,
}) => {
  const fgRef = useRef<any>();
  const [selectedNode, setSelectedNode] = useState<NodeDetailPopup | null>(
    null
  );
  const [hoveredNode, setHoveredNode] = useState<NetworkNode | null>(null);
  const [draggedNode, setDraggedNode] = useState<NetworkNode | null>(null);
  const [pinnedNodes, setPinnedNodes] = useState<Set<string>>(new Set());
  const [nodeLimit, setNodeLimit] = useState(50); // 기본 노드 수 제한
  const [filteredData, setFilteredData] = useState<NetworkData>(data);
  const [visibleCategories, setVisibleCategories] = useState<Set<string>>(new Set(["person", "location", "organization", "keyword"]));

  // 노드 수와 카테고리에 따라 데이터 필터링
  useEffect(() => {
    const filterDataByNodeLimitAndCategory = () => {
      if (!data || !data.nodes) return data;

      // 1. 먼저 카테고리별로 필터링
      const categoryFilteredNodes = data.nodes.filter(node => {
        const nodeCategory = node.category || node.type || "keyword";
        return visibleCategories.has(nodeCategory);
      });

      // 2. 노드 수 제한 적용
      const maxNodes = Math.max(5, Math.floor((nodeLimit / 100) * categoryFilteredNodes.length));
      
      // 노드를 중요도/가중치 순으로 정렬
      const sortedNodes = [...categoryFilteredNodes].sort((a, b) => {
        // 가중치 기준 정렬
        return (b.weight || 0) - (a.weight || 0);
      });

      // 상위 노드들만 선택
      const filteredNodes = sortedNodes.slice(0, maxNodes);
      const nodeIds = new Set(filteredNodes.map(node => node.id));

      // 선택된 노드들과 연결된 링크만 필터링
      const filteredLinks = data.links.filter(link => 
        nodeIds.has(link.source as string) && nodeIds.has(link.target as string)
      );

      return {
        nodes: filteredNodes,
        links: filteredLinks
      };
    };

    setFilteredData(filterDataByNodeLimitAndCategory());
  }, [data, nodeLimit, visibleCategories]);

  // 그래프 초기화
  useEffect(() => {
    if (fgRef.current && filteredData && filteredData.nodes.length > 0) {
      // 모든 노드의 고정 해제
      filteredData.nodes.forEach((node: any) => {
        node.fx = undefined;
        node.fy = undefined;
      });
      
      // 시뮬레이션 재시작
      fgRef.current.d3ReheatSimulation();
      setPinnedNodes(new Set());
    }
  }, [filteredData]);

  const handleNodeClick = (node: NetworkNode, event: any) => {
    // 팝업 표시
    setSelectedNode({
      node,
      x: event.layerX,
      y: event.layerY,
    });

    if (onNodeClick) {
      onNodeClick(node);
    }
  };

  const handleNodeDoubleClick = (node: NetworkNode) => {
    if (node.type === "article" && node.url) {
      // 기사 노드 더블클릭 시 새 탭에서 열기
      window.open(node.url, "_blank");
    } else if (node.type === "keyword" && onNodeDoubleClick) {
      // 키워드 노드 더블클릭 시 확장 검색
      onNodeDoubleClick(node);
    }
  };

  const handleNodeHover = (node: NetworkNode | null) => {
    setHoveredNode(node);
  };

  const handleNodeDrag = (node: NetworkNode) => {
    // 드래그 시작 시 현재 노드만 고정
    if (!draggedNode) {
      setDraggedNode(node);
    }

    // 드래그 중인 노드만 위치 업데이트
    if (draggedNode?.id === node.id || !draggedNode) {
      if (node.x !== undefined && node.y !== undefined) {
        node.fx = node.x;
        node.fy = node.y;
      }
    }
  };

  const handleNodeDragEnd = (node: NetworkNode) => {
    if (draggedNode && draggedNode.id === node.id) {
      // 드래그 종료 시 해당 노드만 고정
      if (node.x !== undefined && node.y !== undefined) {
        node.fx = node.x;
        node.fy = node.y;
      }

      // 고정된 노드 목록에 추가
      const newPinnedNodes = new Set(pinnedNodes);
      newPinnedNodes.add(node.id);
      setPinnedNodes(newPinnedNodes);
      setDraggedNode(null);
    }
  };

  const handleNodeDoubleClickInternal = (node: NetworkNode) => {
    // 더블클릭 시 노드 고정 해제
    if (pinnedNodes.has(node.id)) {
      node.fx = undefined;
      node.fy = undefined;
      setPinnedNodes((prev) => {
        const newSet = new Set(prev);
        newSet.delete(node.id);
        return newSet;
      });

      // 연결된 노드들도 약간 움직이도록 시뮬레이션 활성화
      if (fgRef.current) {
        const simulation = fgRef.current.d3Force("simulation");
        if (simulation) {
          simulation.alpha(0.2).restart();
          simulation.alphaTarget(0.05); // 아주 느린 움직임 유지
        }
      }
    }

    // 기존 더블클릭 로직 실행
    handleNodeDoubleClick(node);
  };

  const nodeCanvasObject = (node: any, ctx: CanvasRenderingContext2D) => {
    const label = node.name;
    const fontSize = node.type === "keyword" ? 13 : 11;
    const isHovered = hoveredNode?.id === node.id;
    const isDragged = draggedNode?.id === node.id;
    const isPinned = pinnedNodes.has(node.id);

    // 노드 위치와 크기 유효성 검사
    const x = isFinite(node.x) ? node.x : 0;
    const y = isFinite(node.y) ? node.y : 0;
    const size = isFinite(node.size) && node.size > 0 ? node.size : 10;

    // 노드 색상에 따른 그라데이션 설정
    const gradient = ctx.createRadialGradient(x, y, 0, x, y, size);
    const baseColor = node.color || "#3B82F6";
    
    // 색상별 그라데이션 매핑
    const colorGradients: { [key: string]: [string, string] } = {
      "#F59E0B": ["#FCD34D", "#D97706"], // 주황색 (인물)  
      "#06B6D4": ["#67E8F9", "#0891B2"], // 청록색 (장소)
      "#3B82F6": ["#93C5FD", "#1D4ED8"], // 파란색 (기관)
      "#EF4444": ["#FCA5A5", "#DC2626"], // 빨간색 (키워드)
    };
    
    const [lightColor, darkColor] = colorGradients[baseColor] || ["#93C5FD", "#1D4ED8"];
    
    if (isHovered || isDragged) {
      gradient.addColorStop(0, "#FFFFFF");
      gradient.addColorStop(0.3, lightColor);
      gradient.addColorStop(1, darkColor);
    } else {
      gradient.addColorStop(0, lightColor);
      gradient.addColorStop(1, darkColor);
    }

    // 그림자 효과
    if (isHovered || isDragged) {
      ctx.shadowColor = "rgba(0, 0, 0, 0.3)";
      ctx.shadowBlur = 10;
      ctx.shadowOffsetX = 2;
      ctx.shadowOffsetY = 2;
    }

    // 노드 원 그리기
    ctx.beginPath();
    ctx.arc(x, y, size, 0, 2 * Math.PI, false);
    ctx.fillStyle = gradient;
    ctx.fill();

    // 그림자 리셋
    ctx.shadowColor = "transparent";
    ctx.shadowBlur = 0;
    ctx.shadowOffsetX = 0;
    ctx.shadowOffsetY = 0;

    // 테두리 (상태별 스타일링)
    ctx.beginPath();
    ctx.arc(x, y, size, 0, 2 * Math.PI, false);
    
    if (isDragged) {
      ctx.strokeStyle = "#F59E0B"; // 주황색 테두리
      ctx.lineWidth = 3;
      ctx.stroke();
    } else if (isPinned) {
      ctx.strokeStyle = "#10B981"; // 초록색 점선 테두리
      ctx.lineWidth = 2;
      ctx.setLineDash([4, 4]);
      ctx.stroke();
      ctx.setLineDash([]);
    } else if (isHovered) {
      ctx.strokeStyle = "rgba(255, 255, 255, 0.8)";
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    // 라벨 텍스트 스타일링 (더 깔끔하게)
    const adjustedFontSize = Math.max(10, Math.min(16, size * 0.4)); // 노드 크기에 비례
    ctx.font = `700 ${adjustedFontSize}px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`;
    const textMetrics = ctx.measureText(label);
    const textWidth = textMetrics.width;
    const textHeight = adjustedFontSize;
    
    // 키워드 배경 박스 (더 나은 가독성)
    const padding = 4;
    const boxWidth = textWidth + padding * 2;
    const boxHeight = textHeight + padding;
    
    // 배경 박스
    ctx.fillStyle = "rgba(255, 255, 255, 0.9)";
    ctx.fillRect(x - boxWidth/2, y - boxHeight/2, boxWidth, boxHeight);
    
    // 박스 테두리
    ctx.strokeStyle = "rgba(0, 0, 0, 0.1)";
    ctx.lineWidth = 1;
    ctx.strokeRect(x - boxWidth/2, y - boxHeight/2, boxWidth, boxHeight);
    
    // 텍스트 렌더링
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillStyle = isHovered || isDragged ? "#1F2937" : "#374151"; // 호버 시 더 진하게
    ctx.fillText(label, x, y);

    // 고정된 노드 표시 (이모지 대신 점으로 표시)
    if (isPinned) {
      ctx.beginPath();
      ctx.arc(x + size - 3, y - size + 3, 4, 0, 2 * Math.PI);
      ctx.fillStyle = "#10B981";
      ctx.fill();
      ctx.strokeStyle = "white";
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    // 키워드 노드의 중요도 표시 (외부 링)
    if (node.type === "keyword" && node.weight && node.weight > 0.6) {
      ctx.beginPath();
      ctx.arc(x, y, size + 4, 0, 2 * Math.PI, false);
      ctx.strokeStyle = `rgba(251, 191, 36, ${node.weight})`;
      ctx.lineWidth = 2;
      ctx.stroke();
    }
  };

  const linkCanvasObject = (link: any, ctx: CanvasRenderingContext2D) => {
    const start = link.source;
    const end = link.target;

    if (typeof start !== "object" || typeof end !== "object") return;
    
    // 링크 노드 좌표 유효성 검사
    if (!isFinite(start.x) || !isFinite(start.y) || !isFinite(end.x) || !isFinite(end.y)) {
      return;
    }

    // 링크 강도에 따른 스타일링
    const strength = link.strength || 0.5;
    const maxWidth = 3;
    const minWidth = 0.8;
    const lineWidth = Math.max(minWidth, Math.min(maxWidth, strength * 2));

    // 키워드 간 연결 스타일링
    if (link.type === "keyword_relation" || link.type === "similarity_relation") {
      // 곡선 연결선
      const midX = (start.x + end.x) / 2;
      const midY = (start.y + end.y) / 2;
      const distance = Math.sqrt((end.x - start.x) ** 2 + (end.y - start.y) ** 2);
      const curveOffset = Math.min(30, distance * 0.2); // 곡선 높이 조정

      // 그라데이션 색상 (강도에 따라)
      const gradient = ctx.createLinearGradient(start.x, start.y, end.x, end.y);
      
      if (link.type === "similarity_relation") {
        // 유사성 연결 - 보라색 계열
        gradient.addColorStop(0, `rgba(147, 51, 234, ${0.6 + strength * 0.3})`);
        gradient.addColorStop(1, `rgba(99, 102, 241, ${0.6 + strength * 0.3})`);
      } else {
        // 동시 출현 연결 - 청록색 계열
        gradient.addColorStop(0, `rgba(6, 182, 212, ${0.7 + strength * 0.3})`);
        gradient.addColorStop(1, `rgba(34, 197, 94, ${0.7 + strength * 0.3})`);
      }

      ctx.strokeStyle = gradient;
      ctx.lineWidth = lineWidth;
      
      // 부드러운 곡선 그리기
      ctx.beginPath();
      ctx.moveTo(start.x, start.y);
      ctx.quadraticCurveTo(midX, midY - curveOffset, end.x, end.y);
      ctx.stroke();
      
    } else {
      // 기본 직선 연결 (키워드-기사)
      const gradient = ctx.createLinearGradient(start.x, start.y, end.x, end.y);
      gradient.addColorStop(0, `rgba(59, 130, 246, ${0.6 + strength * 0.3})`);
      gradient.addColorStop(1, `rgba(239, 68, 68, ${0.6 + strength * 0.3})`);

      ctx.strokeStyle = gradient;
      ctx.lineWidth = lineWidth;
      
      ctx.beginPath();
      ctx.moveTo(start.x, start.y);
      ctx.lineTo(end.x, end.y);
      ctx.stroke();
    }
  };

  return (
    <div className="relative bg-gradient-to-br from-gray-50 to-white dark:from-gray-900 dark:to-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-lg overflow-hidden">
      {/* 좌측 컨트롤 패널 */}
      <div className="absolute top-4 left-4 z-20 bg-white/95 backdrop-blur-sm rounded-xl shadow-xl border border-gray-200/50 p-4 min-w-72">
        
        {/* 상단 분류 버튼들 */}
        <div className="flex gap-1 mb-4">
          <button 
            onClick={() => {
              const newCategories = new Set(visibleCategories);
              if (newCategories.has("person")) {
                newCategories.delete("person");
              } else {
                newCategories.add("person");
              }
              setVisibleCategories(newCategories);
            }}
            className={`flex-1 py-2 px-3 text-sm font-medium rounded transition-all ${
              visibleCategories.has("person") 
                ? "bg-orange-500 text-white shadow-lg" 
                : "bg-gray-200 text-gray-600 hover:bg-gray-300"
            }`}
          >
            인물<br /><span className="text-xs">{data?.nodes?.filter(n => (n.category || n.type) === "person").length || 0}</span>
          </button>
          <button 
            onClick={() => {
              const newCategories = new Set(visibleCategories);
              if (newCategories.has("location")) {
                newCategories.delete("location");
              } else {
                newCategories.add("location");
              }
              setVisibleCategories(newCategories);
            }}
            className={`flex-1 py-2 px-3 text-sm font-medium rounded transition-all ${
              visibleCategories.has("location") 
                ? "bg-teal-500 text-white shadow-lg" 
                : "bg-gray-200 text-gray-600 hover:bg-gray-300"
            }`}
          >
            장소<br /><span className="text-xs">{data?.nodes?.filter(n => (n.category || n.type) === "location").length || 0}</span>
          </button>
          <button 
            onClick={() => {
              const newCategories = new Set(visibleCategories);
              if (newCategories.has("organization")) {
                newCategories.delete("organization");
              } else {
                newCategories.add("organization");
              }
              setVisibleCategories(newCategories);
            }}
            className={`flex-1 py-2 px-3 text-sm font-medium rounded transition-all ${
              visibleCategories.has("organization") 
                ? "bg-blue-500 text-white shadow-lg" 
                : "bg-gray-200 text-gray-600 hover:bg-gray-300"
            }`}
          >
            기관<br /><span className="text-xs">{data?.nodes?.filter(n => (n.category || n.type) === "organization").length || 0}</span>
          </button>
          <button 
            onClick={() => {
              const newCategories = new Set(visibleCategories);
              if (newCategories.has("keyword")) {
                newCategories.delete("keyword");
              } else {
                newCategories.add("keyword");
              }
              setVisibleCategories(newCategories);
            }}
            className={`flex-1 py-2 px-3 text-sm font-medium rounded transition-all ${
              visibleCategories.has("keyword") 
                ? "bg-red-500 text-white shadow-lg" 
                : "bg-gray-200 text-gray-600 hover:bg-gray-300"
            }`}
          >
            키워드<br /><span className="text-xs">{data?.nodes?.filter(n => (n.category || n.type) === "keyword").length || 0}</span>
          </button>
        </div>

        {/* 빠른 필터 옵션 */}
        <div className="mb-4">
          <h4 className="text-sm font-semibold mb-2">빠른 필터</h4>
          <div className="flex gap-2">
            <button 
              onClick={() => setVisibleCategories(new Set(["person", "location", "organization", "keyword"]))}
              className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 transition-colors"
            >
              전체 보기
            </button>
            <button 
              onClick={() => setVisibleCategories(new Set(["person", "organization"]))}
              className="px-3 py-1 bg-gray-200 text-gray-700 text-sm rounded hover:bg-gray-300 transition-colors"
            >
              인물/기관만
            </button>
          </div>
        </div>

        {/* 노드 수 조절 */}
        <div className="mb-4">
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-gray-700">
              표시 노드 수: <span className="text-blue-600 font-semibold">{filteredData?.nodes?.length || 0}</span>개
            </label>
          </div>
          <div className="flex items-center gap-3 mb-3">
            <span className="text-xs text-gray-500 w-8">적음</span>
            <div className="flex-1 relative">
              <input
                type="range"
                min="10"
                max="100"
                step="5"
                value={nodeLimit}
                onChange={(e) => setNodeLimit(parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                style={{
                  background: `linear-gradient(to right, #3B82F6 0%, #3B82F6 ${nodeLimit}%, #E5E7EB ${nodeLimit}%, #E5E7EB 100%)`
                }}
              />
            </div>
            <span className="text-xs text-gray-500 w-8">많음</span>
          </div>
          <div className="flex items-center gap-2">
            <button 
              onClick={() => setNodeLimit(Math.max(10, nodeLimit - 10))}
              className="w-8 h-8 bg-gradient-to-r from-gray-200 to-gray-300 hover:from-gray-300 hover:to-gray-400 rounded-lg text-gray-700 flex items-center justify-center transition-all duration-200 shadow-sm hover:shadow-md"
              title="노드 수 감소"
            >
              −
            </button>
            <div className="flex-1 text-center">
              <span className="text-sm font-medium text-gray-600">{nodeLimit}%</span>
            </div>
            <button 
              onClick={() => setNodeLimit(Math.min(100, nodeLimit + 10))}
              className="w-8 h-8 bg-gradient-to-r from-gray-200 to-gray-300 hover:from-gray-300 hover:to-gray-400 rounded-lg text-gray-700 flex items-center justify-center transition-all duration-200 shadow-sm hover:shadow-md"
              title="노드 수 증가"
            >
              +
            </button>
            <button 
              onClick={() => {
                // 시뮬레이션 재시작으로 그래프 재배치
                if (fgRef.current) {
                  // 모든 노드 고정 해제
                  if (filteredData && filteredData.nodes) {
                    filteredData.nodes.forEach((node: any) => {
                      node.fx = undefined;
                      node.fy = undefined;
                    });
                  }
                  setPinnedNodes(new Set());
                  
                  // 시뮬레이션 재시작
                  fgRef.current.d3ReheatSimulation();
                }
              }}
              className="px-3 py-2 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white text-sm rounded-lg transition-all duration-200 shadow-sm hover:shadow-md transform hover:scale-105"
              title="그래프 재배치"
            >
              재배치
            </button>
          </div>
        </div>

      </div>

      {/* 우측 상단 컨트롤 */}
      <div className="absolute top-4 right-4 z-20 flex gap-2">
        <button 
          onClick={() => {
            // 전체화면 토글 (실제 구현은 부모 컴포넌트에서)
            console.log('전체화면 토글');
          }}
          className="w-8 h-8 bg-white border border-gray-300 rounded shadow hover:bg-gray-50 flex items-center justify-center transition-colors"
          title="전체화면"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
          </svg>
        </button>
        <button 
          onClick={() => {
            // 그래프 설정 토글
            console.log('설정 토글');
          }}
          className="w-8 h-8 bg-white border border-gray-300 rounded shadow hover:bg-gray-50 flex items-center justify-center transition-colors"
          title="설정"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </button>
      </div>

      {/* 하단 기능 버튼들 */}
      <div className="absolute bottom-4 left-4 z-20 flex gap-2">
        <button 
          onClick={() => {
            // 그래프 이미지 다운로드
            if (fgRef.current) {
              const canvas = fgRef.current.renderer().domElement;
              const link = document.createElement('a');
              link.download = 'network-graph.png';
              link.href = canvas.toDataURL();
              link.click();
            }
          }}
          className="flex items-center gap-2 px-4 py-2 bg-black text-white rounded-full shadow-lg hover:bg-gray-800 transition-colors"
          title="그래프 이미지 다운로드"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span className="text-sm">이미지</span>
        </button>
        <button 
          onClick={() => {
            // 데이터 JSON 다운로드
            const dataStr = JSON.stringify(filteredData, null, 2);
            const blob = new Blob([dataStr], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.download = 'network-data.json';
            link.href = url;
            link.click();
            URL.revokeObjectURL(url);
          }}
          className="flex items-center gap-2 px-3 py-2 bg-gray-600 text-white rounded-full shadow-lg hover:bg-gray-700 transition-colors"
          title="데이터 JSON 다운로드"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span className="text-sm">데이터</span>
        </button>
      </div>

      <div className="relative">
        <ForceGraph2D
          ref={fgRef}
          graphData={filteredData}
          width={width}
          height={height}
          nodeCanvasObject={nodeCanvasObject}
          linkCanvasObject={linkCanvasObject}
          onNodeClick={handleNodeClick}
          onNodeHover={handleNodeHover}
          onNodeRightClick={handleNodeDoubleClickInternal}
          onNodeDrag={handleNodeDrag}
          onNodeDragEnd={handleNodeDragEnd}
          cooldownTicks={200}
          d3AlphaDecay={0.01}
          d3VelocityDecay={0.4}
          d3AlphaMin={0.05}
          warmupTicks={50}
          linkDirectionalParticles={0}
          backgroundColor="transparent"
          enableNodeDrag={true}
          onEngineStop={() => {
            // 시뮬레이션이 자연스럽게 멈췄을 때 연속적인 작은 움직임 유지
            if (fgRef.current) {
              const simulation = fgRef.current.d3Force("simulation");
              if (simulation) {
                simulation.alphaTarget(0.03); // 매우 작은 움직임 유지
              }
            }
          }}
        />

        {/* 노드 상세 정보 팝업 */}
        <AnimatePresence>
          {selectedNode && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              className="absolute z-10 bg-white/95 dark:bg-gray-800/95 backdrop-blur-sm rounded-xl shadow-xl p-4 border border-gray-200 dark:border-gray-600 max-w-xs"
              style={{
                left: Math.min(selectedNode.x, width - 300),
                top: Math.max(selectedNode.y - 100, 10),
              }}
            >
              <button
                onClick={() => setSelectedNode(null)}
                className="absolute top-2 right-2 text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>

              <div className="pr-6">
                <div className="flex items-center mb-2">
                  <div
                    className="w-3 h-3 rounded-full mr-2"
                    style={{ backgroundColor: selectedNode.node.color }}
                  />
                  <span className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">
                    {selectedNode.node.type === "person" ? "인물" : 
                     selectedNode.node.type === "location" ? "장소" :
                     selectedNode.node.type === "organization" ? "기관" :
                     selectedNode.node.type === "keyword" ? "키워드" : "기사"}
                  </span>
                </div>

                <h4 className="font-semibold text-gray-900 dark:text-white mb-2">
                  {selectedNode.node.type === "article"
                    ? selectedNode.node.title
                    : selectedNode.node.name}
                </h4>

                {selectedNode.node.type === "article" && (
                  <>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                      📰 {selectedNode.node.provider}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                      📅{" "}
                      {new Date(
                        selectedNode.node.published_at || ""
                      ).toLocaleDateString()}
                    </p>
                    {selectedNode.node.url && (
                      <a
                        href={selectedNode.node.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                      >
                        기사 보기 →
                      </a>
                    )}
                  </>
                )}

                {selectedNode.node.type === "keyword" && (
                  <div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      가중치:{" "}
                      {((selectedNode.node.weight || 0) * 100).toFixed(1)}%
                    </p>
                    <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{
                          width: `${(selectedNode.node.weight || 0) * 100}%`,
                        }}
                      />
                    </div>
                    <button
                      onClick={() => {
                        if (onNodeDoubleClick) {
                          onNodeDoubleClick(selectedNode.node);
                        }
                        setSelectedNode(null);
                      }}
                      className="mt-3 text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 flex items-center"
                    >
                      <span>이 키워드로 검색하기</span>
                      <svg
                        className="w-4 h-4 ml-1"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M14 5l7 7m0 0l-7 7m7-7H3"
                        />
                      </svg>
                    </button>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

      </div>
    </div>
  );
};

export default NetworkGraph;