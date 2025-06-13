import logging
import httpx
from fastapi import APIRouter, Query, Response, HTTPException
from fastapi.responses import StreamingResponse
import io
import re
from urllib.parse import unquote

router = APIRouter(prefix="/proxy", tags=["프록시"])

logger = logging.getLogger("api.proxy")

@router.get("/image")
async def proxy_image(url: str = Query(..., description="프록시할 이미지 URL")):
    """
    외부 이미지를 프록시하여 CORS 문제를 우회합니다.
    """
    try:
        # URL 디코딩
        decoded_url = unquote(url)
        logger.info(f"이미지 프록시 요청: {decoded_url}")
        
        # URL 유효성 검사
        if not url:
            logger.error("빈 URL 요청")
            raise HTTPException(status_code=400, detail="URL이 제공되지 않았습니다.")
        
        # 경로가 /로 끝나는 경우 (이미지 파일 경로가 없는 경우)
        if decoded_url.endswith("/resources/images/") or decoded_url.endswith("/"):
            logger.error(f"잘못된 이미지 URL 형식(슬래시로 끝남): {decoded_url}")
            raise HTTPException(status_code=400, detail="유효하지 않은 이미지 URL입니다. 이미지 파일 경로가 포함되어야 합니다.")
        
        # BigKinds 이미지 URL 패턴 확인
        if "bigkinds.or.kr/resources/images" in decoded_url:
            # 더 유연한 패턴 - 이미지 파일 확장자 확인 (jpg, png, gif, jpeg 등)
            if not re.search(r'\.(jpg|jpeg|png|gif)$', decoded_url, re.IGNORECASE):
                logger.warning(f"URL이 이미지 파일 확장자로 끝나지 않음: {decoded_url}")
            
            # 일반적인 BigKinds 이미지 패턴 확인
            pattern = r'/\d+/\d{4}/\d{2}/\d{2}/.*?\.\d+\.\d+\.(jpg|jpeg|png|gif)'
            if not re.search(pattern, decoded_url, re.IGNORECASE):
                logger.warning(f"BigKinds 이미지 URL 패턴과 일치하지 않을 수 있음: {decoded_url}")
        
        # 커스텀 헤더 추가
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.bigkinds.or.kr/",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8"
        }
        
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            logger.debug(f"이미지 요청 시작: {decoded_url}")
            response = await client.get(decoded_url, headers=headers)
            
            # 응답 코드 확인
            if response.status_code != 200:
                logger.error(f"이미지 가져오기 실패, 상태 코드: {response.status_code}, URL: {decoded_url}")
                # 실패 응답의 처음 200자 로깅 (디버깅용)
                error_content = response.text[:200] if response.text else "응답 내용 없음"
                logger.error(f"오류 응답 내용(일부): {error_content}")
                raise HTTPException(status_code=response.status_code, detail=f"이미지 가져오기 실패: {response.reason_phrase}")
            
            # Content-Type 확인
            content_type = response.headers.get("Content-Type", "")
            if not content_type.startswith(("image/", "application/octet-stream")):
                logger.warning(f"응답이 이미지가 아닐 수 있음, Content-Type: {content_type}, URL: {decoded_url}")
            
            content_length = len(response.content)
            logger.info(f"이미지 프록시 성공, 크기: {content_length} bytes, Content-Type: {content_type}, URL: {decoded_url}")
            
            # 응답 내용이 너무 작으면 경고
            if content_length < 1000:
                logger.warning(f"이미지 크기가 비정상적으로 작음: {content_length} bytes, URL: {decoded_url}")
            
            # 스트리밍 응답으로 이미지 반환
            return StreamingResponse(
                io.BytesIO(response.content),
                media_type=content_type or "image/jpeg",
                headers={
                    "Cache-Control": "public, max-age=86400",  # 24시간 캐싱
                    "Content-Length": str(content_length),
                    "Access-Control-Allow-Origin": "*",  # CORS 허용
                }
            )
    
    except httpx.RequestError as e:
        logger.error(f"이미지 프록시 요청 오류: {str(e)}, URL: {url}")
        raise HTTPException(status_code=500, detail=f"이미지 프록시 요청 오류: {str(e)}")
    except Exception as e:
        logger.error(f"이미지 프록시 예상치 못한 오류: {str(e)}, URL: {url}")
        raise HTTPException(status_code=500, detail=f"내부 서버 오류: {str(e)}") 