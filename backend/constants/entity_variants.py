# -*- coding: utf-8 -*-
"""
카테고리별 엔티티(종목) 및 동의어 매핑

각 카테고리별로 엔티티와 그 동의어들을 관리합니다.
검색 쿼리 확장 및 동의어 처리에 사용됩니다.
"""

from typing import Dict, List, Any, Optional

# 카테고리 정의
CATEGORIES = {
    "domestic_stock": "국내주식",
    "foreign_stock": "해외주식",
    "commodity": "상품",
    "forex_bond": "환율/채권",
    "real_estate": "부동산",
    "crypto": "가상자산"
}

# 카테고리별 엔티티 및 동의어 매핑
ENTITY_VARIANTS: Dict[str, Dict[str, Any]] = {
    "domestic_stock": {
        "name": "국내주식",
        "description": "국내 상장 기업 주식",
        "entities": [
            {"id": "samsung", "variants": ["삼성전자", "Samsung Electronics", "005930"], "name": "삼성전자", "code": "005930"},
            {"id": "sk_hynix", "variants": ["SK하이닉스", "SK Hynix", "000660"], "name": "SK하이닉스", "code": "000660"},
            {"id": "hyundai", "variants": ["현대자동차", "Hyundai Motor", "005380"], "name": "현대자동차", "code": "005380"},
            {"id": "naver", "variants": ["네이버", "Naver", "035420"], "name": "네이버", "code": "035420"},
            {"id": "kakao", "variants": ["카카오", "Kakao", "035720"], "name": "카카오", "code": "035720"},
            {"id": "celltrion", "variants": ["셀트리온", "Celltrion", "068270"], "name": "셀트리온", "code": "068270"},
            {"id": "lg_chem", "variants": ["LG화학", "LG Chem", "051910"], "name": "LG화학", "code": "051910"},
            {"id": "posco", "variants": ["포스코", "POSCO", "005490"], "name": "포스코", "code": "005490"},
            {"id": "kia", "variants": ["기아", "Kia", "000270"], "name": "기아", "code": "000270"},
            {"id": "lotte_chem", "variants": ["롯데케미칼", "Lotte Chemical", "011170"], "name": "롯데케미칼", "code": "011170"},
            {"id": "hanwha_sol", "variants": ["한화솔루션", "Hanwha Solutions", "009830"], "name": "한화솔루션", "code": "009830"},
            {"id": "hyundai_mobis", "variants": ["현대모비스", "Hyundai Mobis", "012330"], "name": "현대모비스", "code": "012330"},
            {"id": "sk_innovation", "variants": ["SK이노베이션", "SK Innovation", "096770"], "name": "SK이노베이션", "code": "096770"},
            {"id": "kepco", "variants": ["한국전력", "KEPCO", "015760"], "name": "한국전력", "code": "015760"},
            {"id": "ktng", "variants": ["KT&G", "케이티앤지", "033780"], "name": "KT&G", "code": "033780"},
            {"id": "shinhan", "variants": ["신한지주", "Shinhan Financial", "055550"], "name": "신한지주", "code": "055550"},
            {"id": "kb", "variants": ["KB금융", "KB Financial", "105560"], "name": "KB금융", "code": "105560"},
            {"id": "hana", "variants": ["하나금융지주", "하나금융", "Hana Financial", "086790"], "name": "하나금융지주", "code": "086790"},
            {"id": "lg_household", "variants": ["LG생활건강", "LG Household", "051900"], "name": "LG생활건강", "code": "051900"},
            {"id": "lg_elec", "variants": ["LG전자", "LG Electronics", "066570"], "name": "LG전자", "code": "066570"},
            {"id": "doosan", "variants": ["두산중공업", "두산에너빌리티", "Doosan Heavy", "034020"], "name": "두산에너빌리티", "code": "034020"},
            {"id": "hanwha_aero", "variants": ["한화에어로스페이스", "한화에어로", "Hanwha Aerospace", "012450"], "name": "한화에어로스페이스", "code": "012450"},
            {"id": "cj", "variants": ["CJ제일제당", "CJ CheilJedang", "097950"], "name": "CJ제일제당", "code": "097950"},
            {"id": "amore", "variants": ["아모레퍼시픽", "Amorepacific", "090430"], "name": "아모레퍼시픽", "code": "090430"},
            {"id": "hyundai_steel", "variants": ["현대제철", "Hyundai Steel", "004020"], "name": "현대제철", "code": "004020"},
            {"id": "tiger_service", "variants": ["TIGER 서비스업", "TIGER Services", "091180"], "name": "TIGER 서비스업", "code": "091180"},
            {"id": "kodex200", "variants": ["KODEX 200", "코덱스 200", "KODEX Kospi200", "069500"], "name": "KODEX 200", "code": "069500"},
            {"id": "kodex_kosdaq", "variants": ["KODEX 코스닥150", "코덱스 코스닥150", "KODEX KOSDAQ150", "229200"], "name": "KODEX 코스닥150", "code": "229200"},
            {"id": "mirae", "variants": ["미래에셋증권", "Mirae Asset", "006800"], "name": "미래에셋증권", "code": "006800"},
            {"id": "ksoe", "variants": ["한국조선해양", "Korea Shipbuilding", "009540"], "name": "한국조선해양", "code": "009540"}
        ]
    },
    
    "foreign_stock": {
        "name": "해외주식",
        "description": "미국 등 해외 상장 기업 주식",
        "entities": [
            {"id": "apple", "variants": ["Apple", "애플", "AAPL"], "name": "Apple", "code": "AAPL"},
            {"id": "microsoft", "variants": ["Microsoft", "마이크로소프트", "MSFT"], "name": "Microsoft", "code": "MSFT"},
            {"id": "amazon", "variants": ["Amazon", "아마존", "AMZN"], "name": "Amazon", "code": "AMZN"},
            {"id": "google", "variants": ["Alphabet", "Google", "구글", "GOOGL", "GOOG"], "name": "Alphabet", "code": "GOOGL"},
            {"id": "tesla", "variants": ["Tesla", "테슬라", "TSLA"], "name": "Tesla", "code": "TSLA"},
            {"id": "meta", "variants": ["Meta", "Facebook", "메타", "페이스북", "META", "FB"], "name": "Meta", "code": "META"},
            {"id": "nvidia", "variants": ["NVIDIA", "엔비디아", "NVDA"], "name": "NVIDIA", "code": "NVDA"},
            {"id": "netflix", "variants": ["Netflix", "넷플릭스", "NFLX"], "name": "Netflix", "code": "NFLX"},
            {"id": "jpmorgan", "variants": ["JPMorgan", "제이피모건", "JP Morgan", "JPM"], "name": "JPMorgan", "code": "JPM"},
            {"id": "visa", "variants": ["Visa", "비자", "V"], "name": "Visa", "code": "V"},
            {"id": "mastercard", "variants": ["Mastercard", "마스터카드", "MA"], "name": "Mastercard", "code": "MA"},
            {"id": "jnj", "variants": ["Johnson & Johnson", "J&J", "존슨앤존슨", "JNJ"], "name": "Johnson & Johnson", "code": "JNJ"},
            {"id": "walmart", "variants": ["Walmart", "월마트", "WMT"], "name": "Walmart", "code": "WMT"},
            {"id": "pg", "variants": ["Procter & Gamble", "P&G", "프록터앤갬블", "PG"], "name": "Procter & Gamble", "code": "PG"},
            {"id": "disney", "variants": ["Disney", "디즈니", "DIS"], "name": "Disney", "code": "DIS"},
            {"id": "intel", "variants": ["Intel", "인텔", "INTC"], "name": "Intel", "code": "INTC"},
            {"id": "cisco", "variants": ["Cisco", "시스코", "CSCO"], "name": "Cisco", "code": "CSCO"},
            {"id": "exxon", "variants": ["ExxonMobil", "엑슨모빌", "XOM"], "name": "ExxonMobil", "code": "XOM"},
            {"id": "chevron", "variants": ["Chevron", "셰브런", "CVX"], "name": "Chevron", "code": "CVX"},
            {"id": "pepsi", "variants": ["PepsiCo", "펩시코", "펩시", "PEP"], "name": "PepsiCo", "code": "PEP"},
            {"id": "mcdonalds", "variants": ["McDonald's", "맥도날드", "MCD"], "name": "McDonald's", "code": "MCD"},
            {"id": "boeing", "variants": ["Boeing", "보잉", "BA"], "name": "Boeing", "code": "BA"},
            {"id": "adobe", "variants": ["Adobe", "어도비", "ADBE"], "name": "Adobe", "code": "ADBE"},
            {"id": "salesforce", "variants": ["Salesforce", "세일즈포스", "CRM"], "name": "Salesforce", "code": "CRM"},
            {"id": "oracle", "variants": ["Oracle", "오라클", "ORCL"], "name": "Oracle", "code": "ORCL"},
            {"id": "abbvie", "variants": ["AbbVie", "애브비", "ABBV"], "name": "AbbVie", "code": "ABBV"},
            {"id": "coca_cola", "variants": ["Coca-Cola", "코카콜라", "KO"], "name": "Coca-Cola", "code": "KO"},
            {"id": "nike", "variants": ["Nike", "나이키", "NKE"], "name": "Nike", "code": "NKE"},
            {"id": "starbucks", "variants": ["Starbucks", "스타벅스", "SBUX"], "name": "Starbucks", "code": "SBUX"},
            {"id": "berkshire", "variants": ["Berkshire Hathaway", "버크셔 해서웨이", "BRK.B", "BRK.A"], "name": "Berkshire Hathaway", "code": "BRK.B"}
        ]
    },
    
    "commodity": {
        "name": "상품",
        "description": "원자재 및 상품",
        "entities": [
            {"id": "gold", "variants": ["금", "Gold", "XAU", "골드"], "name": "금", "code": "XAU"},
            {"id": "silver", "variants": ["은", "Silver", "XAG", "실버"], "name": "은", "code": "XAG"},
            {"id": "platinum", "variants": ["백금", "Platinum", "XPT", "플래티늄"], "name": "백금", "code": "XPT"},
            {"id": "palladium", "variants": ["팔라듐", "Palladium", "XPD"], "name": "팔라듐", "code": "XPD"},
            {"id": "wti", "variants": ["원유", "WTI", "Crude Oil", "CL", "서부텍사스유"], "name": "WTI 원유", "code": "CL"},
            {"id": "brent", "variants": ["브렌트유", "Brent", "Crude Oil Brent", "BRN", "브렌트원유"], "name": "브렌트유", "code": "BRN"},
            {"id": "copper", "variants": ["구리", "Copper", "HG", "동"], "name": "구리", "code": "HG"},
            {"id": "natural_gas", "variants": ["천연가스", "Natural Gas", "NG"], "name": "천연가스", "code": "NG"},
            {"id": "wheat", "variants": ["밀", "Wheat", "ZW", "소맥"], "name": "밀", "code": "ZW"},
            {"id": "corn", "variants": ["옥수수", "Corn", "ZC", "콘"], "name": "옥수수", "code": "ZC"},
            {"id": "soybean", "variants": ["대두", "Soybean", "ZS", "콩"], "name": "대두", "code": "ZS"},
            {"id": "sugar", "variants": ["설탕", "Sugar", "SB"], "name": "설탕", "code": "SB"},
            {"id": "coffee", "variants": ["커피", "Coffee", "KC"], "name": "커피", "code": "KC"},
            {"id": "cotton", "variants": ["면화", "Cotton", "CT", "목화"], "name": "면화", "code": "CT"},
            {"id": "nickel", "variants": ["니켈", "Nickel", "NI"], "name": "니켈", "code": "NI"},
            {"id": "aluminum", "variants": ["알루미늄", "Aluminum", "AL"], "name": "알루미늄", "code": "AL"},
            {"id": "iron_ore", "variants": ["철광석", "Iron Ore", "IO"], "name": "철광석", "code": "IO"},
            {"id": "palm_oil", "variants": ["팜유", "Palm Oil", "PO", "팜오일"], "name": "팜유", "code": "PO"},
            {"id": "lumber", "variants": ["원목", "Lumber", "LB", "목재"], "name": "원목", "code": "LB"},
            {"id": "lng", "variants": ["LNG", "액화천연가스"], "name": "LNG", "code": "LNG"}
        ]
    },
    
    "forex_bond": {
        "name": "환율/채권",
        "description": "외환 및 채권 관련",
        "entities": [
            {"id": "usdkrw", "variants": ["USD/KRW", "달러원", "달러/원", "달러원환율"], "name": "달러원", "code": "USD/KRW"},
            {"id": "eurkrw", "variants": ["EUR/KRW", "유로원", "유로/원", "유로원환율"], "name": "유로원", "code": "EUR/KRW"},
            {"id": "jpykrw", "variants": ["JPY/KRW", "엔화원", "엔/원", "엔화원환율", "엔원"], "name": "엔화원", "code": "JPY/KRW"},
            {"id": "cnykrw", "variants": ["CNY/KRW", "위안화원", "위안/원", "위안화원환율", "위안원"], "name": "위안화원", "code": "CNY/KRW"},
            {"id": "gbpkrw", "variants": ["GBP/KRW", "파운드원", "파운드/원", "파운드원환율"], "name": "파운드원", "code": "GBP/KRW"},
            {"id": "audkrw", "variants": ["AUD/KRW", "호주달러원", "호주달러/원", "호주달러원환율"], "name": "호주달러원", "code": "AUD/KRW"},
            {"id": "dxy", "variants": ["달러인덱스", "DXY", "Dollar Index", "달러지수"], "name": "달러인덱스", "code": "DXY"},
            {"id": "base_rate", "variants": ["기준금리", "기준 금리", "정책금리"], "name": "기준금리", "code": "BASE_RATE"},
            {"id": "ktb3y", "variants": ["국고채 3년", "국고채3년", "3년물 국고채"], "name": "국고채 3년", "code": "KTB3Y"},
            {"id": "ktb10y", "variants": ["국고채 10년", "국고채10년", "10년물 국고채"], "name": "국고채 10년", "code": "KTB10Y"},
            {"id": "credit_spread", "variants": ["회사채 스프레드", "신용스프레드", "Credit Spread"], "name": "회사채 스프레드", "code": "CREDIT_SPREAD"},
            {"id": "credit_rating", "variants": ["신용등급", "Credit Rating", "신용평가"], "name": "신용등급", "code": "CREDIT_RATING"},
            {"id": "forex_reserve", "variants": ["외환보유고", "Forex Reserves", "외환보유액"], "name": "외환보유고", "code": "FOREX_RESERVE"},
            {"id": "currency_swap", "variants": ["통화스왑", "Currency Swap"], "name": "통화스왑", "code": "CURRENCY_SWAP"},
            {"id": "cd_rate", "variants": ["CD금리", "CD Rate", "양도성예금증서금리"], "name": "CD금리", "code": "CD_RATE"},
            {"id": "rp_rate", "variants": ["RP금리", "RP Rate", "환매조건부채권금리"], "name": "RP금리", "code": "RP_RATE"},
            {"id": "bok_minutes", "variants": ["한국은행 금통위 회의록", "BOK Monetary Policy Minutes", "금통위 의사록"], "name": "한은 금통위 회의록", "code": "BOK_MINUTES"},
            {"id": "eonia", "variants": ["EONIA", "유로 단기 금리"], "name": "EONIA", "code": "EONIA"},
            {"id": "sofr", "variants": ["SOFR", "미국 단기 금리"], "name": "SOFR", "code": "SOFR"},
            {"id": "euribor", "variants": ["EURIBOR", "유로 인터뱅크 금리"], "name": "EURIBOR", "code": "EURIBOR"}
        ]
    },
    
    "real_estate": {
        "name": "부동산",
        "description": "부동산 관련",
        "entities": [
            {"id": "real_estate", "variants": ["부동산", "Real Estate"], "name": "부동산", "code": "REAL_ESTATE"},
            {"id": "apartment", "variants": ["아파트", "Apartment", "APT"], "name": "아파트", "code": "APT"},
            {"id": "officetel", "variants": ["오피스텔", "Officetel"], "name": "오피스텔", "code": "OFFICETEL"},
            {"id": "reits", "variants": ["리츠", "REITs", "부동산투자신탁"], "name": "리츠", "code": "REITS"},
            {"id": "presale", "variants": ["분양", "Pre-sale", "신규분양"], "name": "분양", "code": "PRESALE"},
            {"id": "jeonse", "variants": ["전세", "Jeonse"], "name": "전세", "code": "JEONSE"},
            {"id": "sale", "variants": ["매매", "Sale", "매매가"], "name": "매매", "code": "SALE"},
            {"id": "jeonse_ratio", "variants": ["전세가율", "Jeonse-to-price Ratio"], "name": "전세가율", "code": "JEONSE_RATIO"},
            {"id": "housing_price", "variants": ["주택가격", "Housing Price", "집값"], "name": "주택가격", "code": "HOUSING_PRICE"},
            {"id": "housing_volume", "variants": ["주택거래량", "Housing Transaction Volume"], "name": "주택거래량", "code": "HOUSING_VOLUME"},
            {"id": "construction", "variants": ["건설사", "Construction Company", "건설회사"], "name": "건설사", "code": "CONSTRUCTION"},
            {"id": "brokerage", "variants": ["부동산중개업", "Real Estate Brokerage", "공인중개사"], "name": "부동산중개업", "code": "BROKERAGE"},
            {"id": "land", "variants": ["토지", "Land"], "name": "토지", "code": "LAND"},
            {"id": "commercial", "variants": ["상가", "Commercial Property", "상업용부동산"], "name": "상가", "code": "COMMERCIAL"},
            {"id": "reconstruction", "variants": ["재건축", "Reconstruction"], "name": "재건축", "code": "RECONSTRUCTION"},
            {"id": "redevelopment", "variants": ["재개발", "Redevelopment"], "name": "재개발", "code": "REDEVELOPMENT"},
            {"id": "subscription", "variants": ["청약", "Subscription", "아파트청약"], "name": "청약", "code": "SUBSCRIPTION"},
            {"id": "presale_right", "variants": ["분양권", "Pre-sale Right"], "name": "분양권", "code": "PRESALE_RIGHT"},
            {"id": "rent", "variants": ["임대료", "Rent", "월세"], "name": "임대료", "code": "RENT"},
            {"id": "monthly_rent", "variants": ["전월세", "Monthly Rent / Jeonse", "전세월세"], "name": "전월세", "code": "MONTHLY_RENT"}
        ]
    },
    
    "crypto": {
        "name": "가상자산",
        "description": "암호화폐 및 가상자산",
        "entities": [
            {"id": "bitcoin", "variants": ["비트코인", "Bitcoin", "BTC"], "name": "비트코인", "code": "BTC"},
            {"id": "ethereum", "variants": ["이더리움", "Ethereum", "ETH", "이더"], "name": "이더리움", "code": "ETH"},
            {"id": "ripple", "variants": ["리플", "Ripple", "XRP"], "name": "리플", "code": "XRP"},
            {"id": "dogecoin", "variants": ["도지코인", "Dogecoin", "DOGE", "도지"], "name": "도지코인", "code": "DOGE"},
            {"id": "solana", "variants": ["솔라나", "Solana", "SOL"], "name": "솔라나", "code": "SOL"},
            {"id": "cardano", "variants": ["카르다노", "Cardano", "ADA", "에이다"], "name": "카르다노", "code": "ADA"},
            {"id": "polkadot", "variants": ["폴카닷", "Polkadot", "DOT"], "name": "폴카닷", "code": "DOT"},
            {"id": "chainlink", "variants": ["체인링크", "Chainlink", "LINK"], "name": "체인링크", "code": "LINK"},
            {"id": "tezos", "variants": ["테조스", "Tezos", "XTZ"], "name": "테조스", "code": "XTZ"},
            {"id": "litecoin", "variants": ["라이트코인", "Litecoin", "LTC"], "name": "라이트코인", "code": "LTC"},
            {"id": "eos", "variants": ["이오스", "EOS"], "name": "이오스", "code": "EOS"},
            {"id": "tron", "variants": ["트론", "TRON", "TRX"], "name": "트론", "code": "TRX"},
            {"id": "stellar", "variants": ["스텔라루멘", "스텔라", "Stellar", "XLM"], "name": "스텔라", "code": "XLM"},
            {"id": "usdc", "variants": ["USD Coin", "유에스디코인", "USDC"], "name": "USD Coin", "code": "USDC"},
            {"id": "tether", "variants": ["테더", "Tether", "USDT"], "name": "테더", "code": "USDT"},
            {"id": "bnb", "variants": ["바이낸스코인", "Binance Coin", "BNB"], "name": "바이낸스코인", "code": "BNB"},
            {"id": "uniswap", "variants": ["유니스왑", "Uniswap", "UNI"], "name": "유니스왑", "code": "UNI"},
            {"id": "avalanche", "variants": ["아발란체", "Avalanche", "AVAX"], "name": "아발란체", "code": "AVAX"},
            {"id": "filecoin", "variants": ["파일코인", "Filecoin", "FIL"], "name": "파일코인", "code": "FIL"},
            {"id": "defi", "variants": ["디파이", "DeFi", "DeFi Token", "탈중앙화금융"], "name": "DeFi", "code": "DEFI"},
            {"id": "metaverse", "variants": ["메타버스", "Metaverse Token", "메타버스토큰"], "name": "메타버스", "code": "METAVERSE"},
            {"id": "cryptocurrency", "variants": ["암호화폐", "Cryptocurrency", "크립토"], "name": "암호화폐", "code": "CRYPTO"},
            {"id": "virtual_currency", "variants": ["가상화폐", "Virtual Currency"], "name": "가상화폐", "code": "VIRTUAL"},
            {"id": "nft", "variants": ["NFT", "Non-Fungible Token", "대체불가토큰"], "name": "NFT", "code": "NFT"},
            {"id": "stablecoin", "variants": ["스테이블코인", "Stablecoin"], "name": "스테이블코인", "code": "STABLE"},
            {"id": "blockchain", "variants": ["블록체인", "Blockchain"], "name": "블록체인", "code": "BLOCKCHAIN"},
            {"id": "mining", "variants": ["채굴", "Mining", "마이닝"], "name": "채굴", "code": "MINING"},
            {"id": "decentralization", "variants": ["탈중앙화", "Decentralization"], "name": "탈중앙화", "code": "DECENTRAL"},
            {"id": "upbit", "variants": ["업비트", "Upbit"], "name": "업비트", "code": "UPBIT"},
            {"id": "bithumb", "variants": ["빗썸", "Bithumb"], "name": "빗썸", "code": "BITHUMB"}
        ]
    }
}

def get_all_entities() -> List[Dict[str, Any]]:
    """모든 카테고리의 엔티티 목록 반환"""
    all_entities = []
    for category_key, category_data in ENTITY_VARIANTS.items():
        for entity in category_data["entities"]:
            all_entities.append({
                "category": category_key,
                "category_name": category_data["name"],
                **entity
            })
    return all_entities

def get_entity_by_keyword(keyword: str) -> Optional[Dict[str, Any]]:
    """키워드로 엔티티 검색"""
    keyword_lower = keyword.lower()
    
    for category_key, category_data in ENTITY_VARIANTS.items():
        for entity in category_data["entities"]:
            # variants에서 검색 (대소문자 무시)
            for variant in entity["variants"]:
                if variant.lower() == keyword_lower:
                    return {
                        "category": category_key,
                        "category_name": category_data["name"],
                        **entity
                    }
    return None

def get_entities_by_category(category: str) -> List[Dict[str, Any]]:
    """특정 카테고리의 엔티티 목록 반환"""
    if category not in ENTITY_VARIANTS:
        return []
    
    return ENTITY_VARIANTS[category]["entities"]

def expand_query_with_variants(keyword: str, exclude_prism: bool = True) -> str:
    """키워드의 모든 동의어로 확장된 검색 쿼리 생성 (개선된 버전)"""
    entity = get_entity_by_keyword(keyword)
    if entity:
        # 모든 동의어를 OR 연산자로 연결
        variants = entity["variants"]
        terms = [f'"{variant}"' for variant in variants]
        
        # 중복 제거
        unique_terms = list(dict.fromkeys(terms))
        
        # OR 연산자로 연결
        if len(unique_terms) > 1:
            base_query = f"({' OR '.join(unique_terms)})"
        else:
            base_query = unique_terms[0] if unique_terms else f'"{keyword}"'
        
        # PRISM 기사 제외 (필요한 경우)
        if exclude_prism:
            base_query += ' AND NOT "PRISM"'
            
        return base_query
    else:
        # 엔티티에 등록되지 않은 키워드는 기본 검색
        base_query = f'"{keyword}"'
        if exclude_prism:
            base_query += ' AND NOT "PRISM"'
        return base_query

def expand_query_with_boosted_variants(keyword: str, boost_primary: float = 2.0, exclude_prism: bool = True) -> str:
    """키워드의 동의어 확장 쿼리 생성 (부스트 가중치 커스터마이징 가능)"""
    entity = get_entity_by_keyword(keyword)
    if entity:
        terms = []
        
        # 정식명칭에 부스트 적용 (더 정확한 매칭을 위해)
        terms.append(f'"{entity["name"]}"^{boost_primary}')
        
        # 코드가 있으면 부스트 적용  
        if entity.get("code") and entity["code"] != entity["name"]:
            terms.append(f'"{entity["code"]}"^{boost_primary}')
        
        # 나머지 동의어들 (상대적으로 낮은 가중치)
        for variant in entity["variants"]:
            if variant not in [entity["name"], entity.get("code", "")]:
                # 동의어는 약간의 가중치만 부여
                terms.append(f'"{variant}"^{max(1.0, boost_primary * 0.7)}')
        
        base_query = f"({' OR '.join(terms)})"
        
        # PRISM 기사 제외 (필요한 경우)
        if exclude_prism:
            base_query += ' AND NOT "PRISM"'
            
        return base_query
    
    base_query = f'"{keyword}"'
    if exclude_prism:
        base_query += ' AND NOT "PRISM"'
    return base_query

def expand_query_with_fuzzy_search(keyword: str, fuzziness: int = 1, exclude_prism: bool = True) -> str:
    """퍼지 검색을 포함한 동의어 확장 쿼리 생성"""
    entity = get_entity_by_keyword(keyword)
    if entity:
        exact_terms = []
        fuzzy_terms = []
        
        # 정확한 매칭 우선 (더 높은 가중치)
        for variant in entity["variants"]:
            exact_terms.append(f'"{variant}"^3')  # 정확한 매칭에 더 높은 가중치
            # 퍼지 검색 추가 (정확도가 떨어지므로 낮은 가중치)
            if len(variant) > 3:  # 3글자 이상인 경우만 퍼지 검색
                fuzzy_terms.append(f'{variant}~{fuzziness}^0.5')  # 퍼지 검색은 낮은 가중치
        
        all_terms = exact_terms + fuzzy_terms
        base_query = f"({' OR '.join(all_terms)})"
        
        # PRISM 기사 제외 (필요한 경우)
        if exclude_prism:
            base_query += ' AND NOT "PRISM"'
            
        return base_query
    
    base_query = f'"{keyword}"'
    if exclude_prism:
        base_query += ' AND NOT "PRISM"'
    return base_query

def search_entities(query: str) -> List[Dict[str, Any]]:
    """쿼리로 엔티티 검색 (부분 일치 포함)"""
    query_lower = query.lower()
    results = []
    
    for category_key, category_data in ENTITY_VARIANTS.items():
        for entity in category_data["entities"]:
            # name이나 variants에서 부분 일치 검색
            if query_lower in entity["name"].lower():
                results.append({
                    "category": category_key,
                    "category_name": category_data["name"],
                    **entity,
                    "match_type": "name"
                })
            else:
                for variant in entity["variants"]:
                    if query_lower in variant.lower():
                        results.append({
                            "category": category_key,
                            "category_name": category_data["name"],
                            **entity,
                            "match_type": "variant",
                            "matched_variant": variant
                        })
                        break  # 같은 엔티티 중복 방지
    
    # 중복 제거 (id 기준)
    seen_ids = set()
    unique_results = []
    for result in results:
        if result["id"] not in seen_ids:
            seen_ids.add(result["id"])
            unique_results.append(result)
    
    return unique_results

