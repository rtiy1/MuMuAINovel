"""写作 Skill 服务。

负责从本地 skills 目录加载 SKILL.md，并转换为可用于写作风格的 prompt。
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import re

from app.config import PROJECT_ROOT


@dataclass
class WritingSkill:
    """写作 Skill 结构。"""
    slug: str
    name: str
    description: str
    source_path: str
    prompt_content: str
    prompt_preview: str


class WritingSkillService:
    """写作 Skill 加载与转换服务。"""

    MAX_RULE_LINES = 18
    MAX_PROMPT_LENGTH = 2600
    PREVIEW_LENGTH = 180

    def __init__(self, skills_root: Optional[Path] = None):
        self._skills_root = skills_root

    def list_skills(self) -> List[Dict[str, str]]:
        """列出可导入的写作技能（不返回完整 prompt）。"""
        skills = self._load_all_skills()
        return [
            {
                "slug": skill.slug,
                "name": skill.name,
                "description": skill.description,
                "source_path": skill.source_path,
                "prompt_preview": skill.prompt_preview,
            }
            for skill in skills
        ]

    def get_skill(self, slug: str) -> WritingSkill:
        """按 slug 获取写作技能。"""
        for skill in self._load_all_skills():
            if skill.slug == slug:
                return skill
        raise ValueError(f"未找到写作技能: {slug}")

    def _load_all_skills(self) -> List[WritingSkill]:
        skills_root = self._resolve_skills_root()
        if not skills_root:
            return []

        skill_files = sorted(skills_root.glob("*/SKILL.md"))
        skills: List[WritingSkill] = []
        for skill_file in skill_files:
            try:
                skill = self._parse_skill_file(skill_file, skills_root)
                skills.append(skill)
            except Exception:
                # 单个技能文件异常不影响整体加载
                continue
        return skills

    def _resolve_skills_root(self) -> Optional[Path]:
        candidates: List[Path] = []
        if self._skills_root:
            candidates.append(self._skills_root)

        # 当前项目结构下，优先使用仓库根目录的 skills
        candidates.extend([
            PROJECT_ROOT.parent / "skills",
            PROJECT_ROOT / "skills",
        ])

        for path in candidates:
            if path.exists() and path.is_dir():
                return path
        return None

    def _parse_skill_file(self, skill_file: Path, skills_root: Path) -> WritingSkill:
        raw = skill_file.read_text(encoding="utf-8-sig")
        metadata, body = self._split_front_matter(raw)

        slug = skill_file.parent.name
        name = metadata.get("name") or slug
        description = metadata.get("description") or f"{name} 写作技能"
        prompt_content = self._build_prompt_from_body(name=name, description=description, body=body)
        prompt_preview = prompt_content[: self.PREVIEW_LENGTH]
        source_path = str(skill_file.relative_to(skills_root))

        return WritingSkill(
            slug=slug,
            name=name,
            description=description,
            source_path=source_path,
            prompt_content=prompt_content,
            prompt_preview=prompt_preview,
        )

    def _split_front_matter(self, raw: str) -> tuple[Dict[str, str], str]:
        text = raw.lstrip("\ufeff")
        if not text.startswith("---"):
            return {}, text

        lines = text.splitlines()
        end_index = -1
        for idx in range(1, len(lines)):
            if lines[idx].strip() == "---":
                end_index = idx
                break

        if end_index == -1:
            return {}, text

        front_lines = lines[1:end_index]
        body = "\n".join(lines[end_index + 1 :]).strip()
        metadata: Dict[str, str] = {}

        for line in front_lines:
            if not line or line.startswith(" ") or ":" not in line:
                continue
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip().strip('"').strip("'")

        return metadata, body

    def _build_prompt_from_body(self, name: str, description: str, body: str) -> str:
        rules = self._extract_rules(body)
        if not rules:
            rules = ["保持原文信息不丢失，输出自然、清晰且风格统一的中文正文。"]

        lines = [
            f"【写作技能】{name}",
            f"【技能说明】{description}",
            "请在章节创作中严格遵守以下规则：",
        ]
        for idx, rule in enumerate(rules, start=1):
            lines.append(f"{idx}. {rule}")
        lines.append("输出要求：只输出正文，不输出额外说明。")

        prompt = "\n".join(lines)
        if len(prompt) > self.MAX_PROMPT_LENGTH:
            prompt = prompt[: self.MAX_PROMPT_LENGTH].rstrip() + "..."
        return prompt

    def _extract_rules(self, body: str) -> List[str]:
        selected: List[str] = []
        in_code_block = False

        for raw_line in body.splitlines():
            line = raw_line.rstrip()
            stripped = line.strip()

            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if in_code_block:
                continue
            if not stripped:
                continue

            # 到参考文件区域后停止提取
            if stripped.startswith("## 7.") or stripped.startswith("## 参考文件"):
                break

            # 跳过标题和纯路径行
            if stripped.startswith("#"):
                continue
            if "references/" in stripped or stripped.startswith("allowed-tools"):
                continue

            normalized = self._normalize_line(stripped)
            if len(normalized) < 4:
                continue
            if normalized in selected:
                continue

            selected.append(normalized)
            if len(selected) >= self.MAX_RULE_LINES:
                break

        return selected

    def _normalize_line(self, text: str) -> str:
        s = text
        s = re.sub(r"^\d+\.\s*", "", s)
        s = re.sub(r"^[-*+]\s*", "", s)
        s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
        s = s.replace("**", "").replace("`", "")
        s = re.sub(r"\s+", " ", s).strip()
        return s


writing_skill_service = WritingSkillService()
