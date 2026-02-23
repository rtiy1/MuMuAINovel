from pathlib import Path
import shutil
import uuid

from app.services.writing_skill_service import WritingSkillService


def _write_skill(base_dir: Path, slug: str, content: str):
    skill_dir = base_dir / slug
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(content, encoding="utf-8")


def _make_local_temp_dir() -> Path:
    root = Path("backend/tests/.tmp_skill_service")
    root.mkdir(parents=True, exist_ok=True)
    case_dir = root / f"case_{uuid.uuid4().hex[:8]}"
    case_dir.mkdir(parents=True, exist_ok=True)
    return case_dir


def test_list_skills_with_front_matter():
    temp_dir = _make_local_temp_dir()
    try:
        _write_skill(
            temp_dir,
            "demo-skill",
            """---
name: demo-skill
description: 这是一个测试技能
---
# demo

## 规则
- 保留原文信息
- 句子自然流畅
""",
        )

        service = WritingSkillService(skills_root=temp_dir)
        skills = service.list_skills()

        assert len(skills) == 1
        assert skills[0]["slug"] == "demo-skill"
        assert skills[0]["name"] == "demo-skill"
        assert "测试技能" in skills[0]["description"]
        assert "保留原文信息" in skills[0]["prompt_preview"]
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_get_skill_without_front_matter_uses_fallback():
    temp_dir = _make_local_temp_dir()
    try:
        _write_skill(
            temp_dir,
            "no-meta",
            """# no-meta

请输出更自然的文本。
避免模板化表达。
""",
        )

        service = WritingSkillService(skills_root=temp_dir)
        skill = service.get_skill("no-meta")

        assert skill.slug == "no-meta"
        assert skill.name == "no-meta"
        assert "写作技能" in skill.description
        assert "请输出更自然的文本" in skill.prompt_content
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_prompt_length_is_capped():
    temp_dir = _make_local_temp_dir()
    try:
        very_long_lines = "\n".join([f"- 规则{i}：保持自然表达并避免模板化。" for i in range(1, 80)])
        _write_skill(
            temp_dir,
            "long-skill",
            f"""---
name: long-skill
description: 超长技能
---
# long-skill
{very_long_lines}
""",
        )

        service = WritingSkillService(skills_root=temp_dir)
        skill = service.get_skill("long-skill")

        assert len(skill.prompt_content) <= service.MAX_PROMPT_LENGTH + 3
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
