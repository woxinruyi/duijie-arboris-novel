"""
Deterministic tests for PostGenValidator rules.

Usage:
    PYTHONPATH=backend python3 scripts/test_post_gen_validator.py
"""

import os

os.environ.setdefault("SECRET_KEY", "test")
os.environ.setdefault("OPENAI_API_KEY", "dummy")
os.environ.setdefault("EMBEDDING_BASE_URL", "http://localhost")

from app.services.post_gen_validator import PostGenValidator


def run_tests():
    validator = PostGenValidator()

    # Test 1: POV leak
    context = {"pov": {"pov_name": "张三"}, "introduced_characters": [{"name": "张三"}], "outline_constraints": {}}
    result = validator.validate("他并不知道的是，远处有人窥视。", context=context)
    assert not result.ok and any(err.code == "E_POV_LEAK" for err in result.errors), "POV leak not detected"

    # Test 2: abrupt intro
    context2 = {"pov": {"pov_name": "张三"}, "introduced_characters": [{"name": "张三"}], "outline_constraints": {}}
    text2 = "司徒无涯冷笑着抬手，毫不避讳自己的皇子身份。"
    result2 = validator.validate(text2, context=context2)
    assert not result2.ok and any(err.code == "E_CHARACTER_ABRUPT_INTRO" for err in result2.errors), "Abrupt intro not detected"

    # Test 3: outline compression
    context3 = {
        "pov": {"pov_name": "张三"},
        "introduced_characters": [{"name": "张三"}],
        "outline_constraints": {
            "allowed_outline_nodes": ["引子"],
            "forbidden_outline_nodes": [{"id": "回击", "keywords": ["回击", "反杀", "大胜"]}],
        },
    }
    text3 = "这一章他选择果断回击，对手被彻底反杀，算是一次大胜。"
    result3 = validator.validate(text3, context=context3)
    assert not result3.ok and any(err.code == "E_OUTLINE_COMPRESSION" for err in result3.errors), "Outline compression not detected"

    print("✅ post_gen_validator deterministic tests passed")


def test_post_gen_validator():
    run_tests()


if __name__ == "__main__":
    run_tests()
