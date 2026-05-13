# AIMETA P=增强分析API_多维情感和故事轨迹|R=多维情感_轨迹分析_创意指导|NR=不含基础分析|E=route:GET_/api/analytics/enhanced/*|X=http|A=多维情感_轨迹_指导|D=fastapi,redis|S=db,cache|RD=./README.ai
"""
增强的情感曲线和故事分析 API（已废弃，统一管线收敛后不再提供实际分析）。"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.dependencies import get_current_user
from ...db.session import get_session
from ...schemas.user import UserInDB
router = APIRouter(prefix="/api/analytics", tags=["Analytics"])
_DEPRECATED_ERROR = HTTPException(
    status_code=410,
    detail={
        "error": "FEATURE_DEPRECATED",
        "message": "Enhanced analytics endpoints are deprecated in the unified pipeline.",
        "replacement": None,
    },
)

# ==================== 数据模型 ====================

class MultidimensionalEmotionPoint(BaseModel):
    """多维情感数据点"""
    chapter_number: int
    chapter_id: str
    title: str
    
    # 主情感
    primary_emotion: str  # joy, sadness, anger, fear, surprise, anticipation, trust, neutral
    primary_intensity: float = Field(..., ge=0, le=10)
    
    # 次要情感
    secondary_emotions: List[tuple[str, float]] = []
    
    # 叙事阶段
    narrative_phase: str  # exposition, rising_action, climax, falling_action, resolution
    
    # 节奏
    pace: str  # slow, medium, fast
    
    # 转折点
    is_turning_point: bool
    turning_point_type: Optional[str] = None
    
    # 描述
    description: str


class StoryTrajectoryResponse(BaseModel):
    """故事轨迹分析响应"""
    project_id: str
    project_title: str
    
    # 轨迹形状
    shape: str  # rags_to_riches, riches_to_rags, man_in_hole, icarus, cinderella, oedipus, flat
    shape_confidence: float = Field(..., ge=0, le=1)
    
    # 统计数据
    total_chapters: int
    avg_intensity: float
    intensity_range: tuple[float, float]
    volatility: float
    
    # 关键点
    peak_chapters: List[int]
    valley_chapters: List[int]
    turning_points: List[int]
    
    # 描述和建议
    description: str
    recommendations: List[str]


class GuidanceItem(BaseModel):
    """指导项"""
    type: str  # plot_development, emotion_pacing, character_arc, conflict_escalation, etc.
    priority: str  # critical, high, medium, low
    title: str
    description: str
    specific_suggestions: List[str]
    affected_chapters: List[int]
    examples: List[str] = []


class CreativeGuidanceResponse(BaseModel):
    """创意指导响应"""
    project_id: str
    project_title: str
    current_chapter: int
    
    # 总体评估
    overall_assessment: str
    strengths: List[str]
    weaknesses: List[str]
    
    # 具体指导
    guidance_items: List[GuidanceItem]
    
    # 建议
    next_chapter_suggestions: List[str]
    long_term_planning: List[str]


class ComprehensiveAnalysisResponse(BaseModel):
    """综合分析响应（包含所有分析结果）"""
    project_id: str
    project_title: str
    
    # 多维情感分析
    emotion_points: List[MultidimensionalEmotionPoint]
    
    # 故事轨迹分析
    trajectory: StoryTrajectoryResponse
    
    # 创意指导
    guidance: CreativeGuidanceResponse


# ==================== API 端点 ====================

@router.get(
    "/projects/{project_id}/emotion-curve-enhanced",
    response_model=List[MultidimensionalEmotionPoint],
    summary="获取增强的多维情感曲线"
)
async def get_enhanced_emotion_curve(
    project_id: str,
    use_cache: bool = Query(True, description="是否使用缓存"),
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> List[MultidimensionalEmotionPoint]:
    raise _DEPRECATED_ERROR


@router.get(
    "/projects/{project_id}/story-trajectory",
    response_model=StoryTrajectoryResponse,
    summary="获取故事轨迹分析"
)
async def get_story_trajectory(
    project_id: str,
    use_cache: bool = Query(True, description="是否使用缓存"),
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> StoryTrajectoryResponse:
    raise _DEPRECATED_ERROR


@router.get(
    "/projects/{project_id}/creative-guidance",
    response_model=CreativeGuidanceResponse,
    summary="获取创意指导"
)
async def get_creative_guidance(
    project_id: str,
    use_cache: bool = Query(True, description="是否使用缓存"),
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> CreativeGuidanceResponse:
    raise _DEPRECATED_ERROR


@router.get(
    "/projects/{project_id}/comprehensive-analysis",
    response_model=ComprehensiveAnalysisResponse,
    summary="获取综合分析（包含所有分析结果）"
)
async def get_comprehensive_analysis(
    project_id: str,
    use_cache: bool = Query(True, description="是否使用缓存"),
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> ComprehensiveAnalysisResponse:
    raise _DEPRECATED_ERROR


@router.post(
    "/projects/{project_id}/invalidate-cache",
    summary="清除项目的分析缓存"
)
async def invalidate_analysis_cache(
    project_id: str,
    session: AsyncSession = Depends(get_session),
    current_user: UserInDB = Depends(get_current_user),
) -> Dict[str, str]:
    raise _DEPRECATED_ERROR
