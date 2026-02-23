"""写作风格 Schema"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class WritingStyleBase(BaseModel):
    """写作风格基础模型"""
    name: str = Field(..., description="风格名称")
    style_type: str = Field(..., description="风格类型：preset/custom")
    preset_id: Optional[str] = Field(None, description="预设风格ID")
    description: Optional[str] = Field(None, description="风格描述")
    prompt_content: str = Field(..., description="风格提示词内容")


class WritingStyleCreate(BaseModel):
    """创建写作风格（仅用于创建用户自定义风格）"""
    name: str = Field(..., description="风格名称")
    style_type: Optional[str] = Field(None, description="风格类型：preset/custom")
    preset_id: Optional[str] = Field(None, description="预设风格ID")
    description: Optional[str] = Field(None, description="风格描述")
    prompt_content: str = Field(..., description="风格提示词内容")


class WritingStyleUpdate(BaseModel):
    """更新写作风格"""
    name: Optional[str] = None
    description: Optional[str] = None
    prompt_content: Optional[str] = None


class SetDefaultStyleRequest(BaseModel):
    """设置默认风格请求"""
    project_id: str = Field(..., description="项目ID")


class WritingStyleResponse(BaseModel):
    """写作风格响应"""
    id: int
    user_id: Optional[str] = None  # NULL 表示全局预设风格
    name: str
    style_type: str
    preset_id: Optional[str] = None
    description: Optional[str] = None
    prompt_content: str
    is_default: bool
    order_index: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class WritingStyleListResponse(BaseModel):
    """写作风格列表响应"""
    total: int
    styles: list[WritingStyleResponse]


class WritingSkillResponse(BaseModel):
    """可导入写作 Skill 信息"""
    slug: str
    name: str
    description: str
    source_path: str
    prompt_preview: str


class ImportWritingSkillRequest(BaseModel):
    """导入写作 Skill 请求"""
    skill_slug: str = Field(..., description="技能标识")
    overwrite_existing: bool = Field(default=True, description="是否覆盖已导入的同名技能风格")
    set_as_default: bool = Field(default=False, description="是否导入后设为项目默认风格")
    project_id: Optional[str] = Field(default=None, description="项目ID（set_as_default=true 时必填）")


class ImportWritingSkillResponse(BaseModel):
    """导入写作 Skill 响应"""
    message: str
    created: bool
    default_applied: bool
    skill_slug: str
    style: WritingStyleResponse
