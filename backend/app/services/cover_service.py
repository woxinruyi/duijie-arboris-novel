# AIMETA P=封面服务_小说封面生成|R=封面生成_图像API|NR=不含业务逻辑|E=CoverService|X=internal|A=服务类|D=openai,httpx|S=net,fs|RD=./README.ai
"""
封面生成服务：使用 Gemini 图像生成模型创建小说封面。
"""
import base64
import logging
import os
import uuid
from pathlib import Path
from typing import Optional

import httpx
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import NovelProject
from ..repositories.novel_repository import NovelRepository
from ..repositories.system_config_repository import SystemConfigRepository

logger = logging.getLogger(__name__)

# 封面存储目录
COVER_STORAGE_DIR = Path(__file__).resolve().parents[2] / "storage" / "covers"


class CoverService:
    """封面生成服务，使用 Gemini 图像生成模型。"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = NovelRepository(session)
        self.system_config_repo = SystemConfigRepository(session)

    async def generate_cover(self, project_id: str, user_id: int) -> str:
        """
        为小说项目生成封面。
        
        Args:
            project_id: 项目ID
            user_id: 用户ID（用于权限验证）
            
        Returns:
            封面文件的相对URL路径
        """
        # 获取项目信息
        project = await self.repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        if project.user_id != user_id:
            raise HTTPException(status_code=403, detail="无权访问该项目")

        # 获取蓝图信息用于生成提示词
        blueprint = project.blueprint
        if not blueprint:
            raise HTTPException(status_code=400, detail="项目蓝图不存在，无法生成封面")

        title = blueprint.title or project.title or "未命名小说"
        
        # 提取单个场景关键词
        scene_keyword = self._extract_single_keyword(blueprint)
        
        # 构建封面生成提示词
        prompt = self._build_cover_prompt(title, scene_keyword)
        
        logger.info("生成封面提示词: %s", prompt[:200])
        
        # 调用 Gemini 图像生成 API
        image_data = await self._generate_image(prompt)
        
        # 保存图片到本地存储
        cover_path = await self._save_cover_image(project_id, image_data)
        
        # 更新项目的封面 URL
        project.cover_url = cover_path
        await self.session.commit()
        
        logger.info("封面生成成功: project_id=%s, path=%s", project_id, cover_path)
        return cover_path

    async def update_cover(self, project_id: str, cover_url: str) -> str:
        """
        更新项目封面URL（管理员接口）。
        """
        project = await self.repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        
        project.cover_url = cover_url
        await self.session.commit()
        
        return cover_url

    async def save_uploaded_cover(self, project_id: str, image_data: bytes) -> str:
        """
        保存上传的封面图片。
        
        Args:
            project_id: 项目ID
            image_data: 图片二进制数据
            
        Returns:
            封面文件的相对URL路径
        """
        # 保存图片到本地存储
        cover_path = await self._save_cover_image(project_id, image_data)
        
        # 更新项目的封面 URL
        project = await self.repo.get_by_id(project_id)
        if project:
            project.cover_url = cover_path
            await self.session.commit()
            
        return cover_path

    def _extract_single_keyword(self, blueprint) -> str:
        """从蓝图中提取单个场景关键词。"""
        # 优先使用类型作为关键词
        if blueprint.genre:
            # 只取第一个词
            genre_words = blueprint.genre.replace("/", " ").replace("、", " ").split()
            if genre_words:
                return genre_words[0]
        
        # 其次尝试世界观设置
        world_setting = blueprint.world_setting or {}
        if isinstance(world_setting, dict):
            if "era" in world_setting:
                return str(world_setting["era"]).split()[0]
            if "时代" in world_setting:
                return str(world_setting["时代"]).split()[0]
            if "world_type" in world_setting:
                return str(world_setting["world_type"]).split()[0]
        
        # 默认关键词
        return "奇幻"

    def _build_cover_prompt(self, title: str, scene_keyword: str) -> str:
        """构建封面生成提示词。"""
        return f"""生成一张竖屏小说封面，比例3:4。画面背景是 [ {scene_keyword} ]。画面底部要有巨大的、霸气的金色立体中文标题："{title}"。

关于标题的特效要求极为严格：
1. 字体材质：黄金平面字，带有明显的金属厚度和光泽。
2. 形状：字体要有扭曲变形的笔刷感，充满张力。
3. 火焰特效：文字周围燃烧着猛烈的火焰。
4. 光影特效：文字要有描边、深重的投影、明亮的内发光和外发光。
5. 氛围特效：文字周围要有强烈的光束射向天空，伴随光圈和镜头光斑（追位点光）。

整体风格要极其炫酷、霸气，视觉冲击力强。"""

    async def _generate_image(self, prompt: str) -> bytes:
        """调用 Gemini 图像生成 API。"""
        # 获取 API 配置
        api_key = await self._get_config_value("llm.api_key")
        base_url = await self._get_config_value("llm.base_url")
        
        if not api_key:
            raise HTTPException(status_code=500, detail="未配置 LLM API Key")
        
        # 使用 gemini-3-pro-image-preview 模型
        model = "gemini-3-pro-image-preview"
        
        # 构建请求 URL
        if base_url:
            base_url = str(base_url).rstrip("/")
            # 如果 base_url 以 /v1 结尾，去掉它
            if base_url.endswith("/v1"):
                base_url = base_url[:-3]
            url = f"{base_url}/v1beta/models/{model}:generateContent"
        else:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        
        # 构建请求体 - Gemini 原生格式
        request_body = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"]
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        
        logger.info("调用 Gemini 图像生成 API: url=%s, model=%s", url, model)
        
        async with httpx.AsyncClient(timeout=180.0) as client:
            try:
                response = await client.post(url, json=request_body, headers=headers)
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error("Gemini API 请求失败: status=%s, response=%s", e.response.status_code, e.response.text)
                raise HTTPException(status_code=503, detail=f"图像生成服务请求失败: {e.response.status_code}")
            except httpx.RequestError as e:
                logger.error("Gemini API 连接失败: %s", str(e))
                raise HTTPException(status_code=503, detail="无法连接到图像生成服务")
        
        # 解析响应
        result = response.json()
        
        # 提取图像数据 - Gemini 格式
        try:
            candidates = result.get("candidates", [])
            if not candidates:
                logger.error("图像生成返回空候选: %s", result)
                raise HTTPException(status_code=500, detail="图像生成返回空结果")
            
            parts = candidates[0].get("content", {}).get("parts", [])
            for part in parts:
                if "inlineData" in part:
                    image_data = part["inlineData"].get("data")
                    if image_data:
                        return base64.b64decode(image_data)
            
            logger.error("图像生成返回结果中未找到图像: %s", result)
            raise HTTPException(status_code=500, detail="图像生成返回结果中未找到图像数据")
        except (KeyError, IndexError) as e:
            logger.error("解析 Gemini 响应失败: %s, response=%s", str(e), result)
            raise HTTPException(status_code=500, detail="解析图像生成结果失败")

    async def _save_cover_image(self, project_id: str, image_data: bytes) -> str:
        """保存封面图片到本地存储。"""
        # 确保存储目录存在
        COVER_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        
        # 生成唯一文件名
        filename = f"{project_id}_{uuid.uuid4().hex[:8]}.png"
        file_path = COVER_STORAGE_DIR / filename
        
        # 写入文件
        file_path.write_bytes(image_data)
        
        # 返回相对路径
        return f"/api/covers/{filename}"

    async def _get_config_value(self, key: str) -> Optional[str]:
        """获取系统配置值。"""
        record = await self.system_config_repo.get_by_key(key)
        if record:
            return record.value
        # 兼容环境变量
        env_key = key.upper().replace(".", "_")
        return os.getenv(env_key)
