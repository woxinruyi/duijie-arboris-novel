"""
Deterministic post-generation validator to enforce POV/character/outline constraints.

Rules (minimal deterministic set):
- E_POV_LEAK: omniscient cues or non-POV inner monologue.
- E_CHARACTER_ABRUPT_INTRO: new character appears without intro markers or with direct background drop.
- E_OUTLINE_COMPRESSION: forbidden outline node keywords appear (compression/skip pacing).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


POV_CUES_STRONG = [
    r"他并不知道",
    r"她并不知道",
    r"他们并不知道",
    r"殊不知",
]
POV_CUES_SOFT = [
    r"与此同时",
    r"另一边",
    r"远在",
    r"同一时间",
    r"在.*不知道的地方",
]
POV_INNER_MONOLOGUE = r"(?:心想|暗想|暗道|打定主意|意识到|暗自决定|盘算)"
BACKGROUND_KEYWORDS = ["掌门", "皇子", "真身", "真实身份", "幕后", "背后", "身为", "血脉", "继承人"]
INTRO_MARKERS = ["名叫", "叫做", "外号", "传闻", "据说", "是个", "来自", "身穿", "看起来", "自称", "介绍", "第一次见"]
OUTLINE_STAGE_LEAPS = ["反杀", "回击", "反转", "决战", "大胜", "终局", "最终对决"]


@dataclass
class ValidationErrorDetail:
    code: str
    message: str
    severity: str  # BLOCK | WARN
    evidence_snippets: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationResult:
    ok: bool
    errors: List[ValidationErrorDetail] = field(default_factory=list)
    action: str = "accept"  # accept | reject | retry
    retry_directive: Optional[str] = None


class PostGenValidator:
    def validate(self, text: str, *, context: Dict[str, Any]) -> ValidationResult:
        errors: List[ValidationErrorDetail] = []

        pov_error = self._check_pov_leak(text, context)
        if pov_error:
            errors.append(pov_error)

        abrupt_error = self._check_abrupt_intro(text, context)
        if abrupt_error:
            errors.append(abrupt_error)

        outline_error = self._check_outline_compression(text, context)
        if outline_error:
            errors.append(outline_error)

        if not errors:
            return ValidationResult(ok=True, errors=[], action="accept")

        retry_directive = self._build_retry_directive(errors, context)
        action = "accept" if all(err.severity == "WARN" for err in errors) else "retry"
        return ValidationResult(ok=action == "accept", errors=errors, action=action, retry_directive=retry_directive)

    def _check_pov_leak(self, text: str, context: Dict[str, Any]) -> Optional[ValidationErrorDetail]:
        pov_name = (context.get("pov") or {}).get("pov_name")
        pov_switch_allowed = (context.get("pov") or {}).get("pov_switch_allowed", False)
        allowed_pov_names = (context.get("pov") or {}).get("allowed_pov_names") or []
        introduced = [c.get("name") for c in context.get("introduced_characters", []) if c.get("name")]
        names_to_check = [n for n in introduced if n and n != pov_name]

        snippets: List[str] = []
        severity = "BLOCK"

        if not pov_switch_allowed:
            strong_pattern = re.compile("|".join(POV_CUES_STRONG))
            soft_pattern = re.compile("|".join(POV_CUES_SOFT))
            for match in strong_pattern.finditer(text):
                snippet = text[max(0, match.start() - 10): match.end() + 10]
                snippets.append(snippet.strip())
                severity = "BLOCK"
            for match in soft_pattern.finditer(text):
                snippet = text[max(0, match.start() - 10): match.end() + 10]
                snippets.append(snippet.strip())
                if severity != "BLOCK":
                    severity = "WARN"

        for name in names_to_check:
            if pov_switch_allowed and name in allowed_pov_names:
                continue
            pattern = re.compile(rf"{re.escape(name)}.{0,6}{POV_INNER_MONOLOGUE}")
            for match in pattern.finditer(text):
                snippet = text[max(0, match.start() - 5): match.end() + 5]
                snippets.append(snippet.strip())
                severity = "BLOCK"

        if snippets:
            return ValidationErrorDetail(
                code="E_POV_LEAK",
                message="检测到全知视角或非POV内心描写",
                severity=severity,
                evidence_snippets=snippets[:5],
                metadata={"pov": pov_name},
            )
        return None

    def _check_abrupt_intro(self, text: str, context: Dict[str, Any]) -> Optional[ValidationErrorDetail]:
        introduced = {c.get("name") for c in context.get("introduced_characters", []) if c.get("name")}
        ephemeral_whitelist = set((context.get("ephemeral_roles_whitelist") or ["店小二", "伙计", "路人", "侍女", "保安", "司机"]))
        candidates = self._extract_name_candidates(text)
        new_names = [n for n in candidates if n not in introduced]
        if not new_names:
            return None

        evidence_block: List[str] = []
        evidence_warn: List[str] = []
        for name in new_names:
            idx = text.find(name)
            window = text[max(0, idx - 25): idx + 25]
            intro_hit = any(marker in window for marker in INTRO_MARKERS)
            background_hit = any(k in window for k in BACKGROUND_KEYWORDS)
            if name in ephemeral_whitelist and not background_hit:
                # downgrade to warn for ephemeral roles
                if not intro_hit:
                    evidence_warn.append(window.strip())
                continue
            if background_hit or not intro_hit:
                evidence_block.append(window.strip())

        if evidence_block or evidence_warn:
            severity = "BLOCK" if evidence_block else "WARN"
            return ValidationErrorDetail(
                code="E_CHARACTER_ABRUPT_INTRO",
                message="检测到未介绍的新角色或直接给出背景",
                severity=severity,
                evidence_snippets=(evidence_block + evidence_warn)[:5],
                metadata={"new_characters": new_names},
            )
        return None

    def _check_outline_compression(self, text: str, context: Dict[str, Any]) -> Optional[ValidationErrorDetail]:
        constraints = context.get("outline_constraints", {}) or {}
        forbidden_nodes = constraints.get("forbidden_outline_nodes") or []
        evidence = []
        hit_nodes = []

        lower_text = text.lower()

        for node in forbidden_nodes:
            node_id = node.get("id") or node.get("node_id")
            keywords = node.get("keywords") or []
            hits = 0
            strong_hit = False
            for kw in keywords:
                if not kw:
                    continue
                if kw.lower() in lower_text:
                    hits += lower_text.count(kw.lower())
                    if kw in OUTLINE_STAGE_LEAPS:
                        strong_hit = True
            if hits >= 2:
                hit_nodes.append(node_id or "unknown")
                evidence.append({"node": node_id or "unknown", "hits": hits, "keywords": keywords, "strong": strong_hit})

        for kw in OUTLINE_STAGE_LEAPS:
            if kw in text:
                hit_nodes.append("stage_leap")
                evidence.append({"node": "stage_leap", "hits": 1, "keywords": [kw], "strong": True})

        if evidence:
            any_strong = any(e.get("strong") for e in evidence)
            severity = "BLOCK" if any_strong else "WARN"
            return ValidationErrorDetail(
                code="E_OUTLINE_COMPRESSION",
                message="检测到章节推进超出允许的大纲节点",
                severity=severity,
                evidence_snippets=[str(e) for e in evidence[:5]],
                metadata={"forbidden_nodes_hit": hit_nodes},
            )
        return None

    def _build_retry_directive(self, errors: List[ValidationErrorDetail], context: Dict[str, Any]) -> str:
        lines = ["请修正以下问题后重写本章："]
        for err in errors:
            if err.code == "E_POV_LEAK":
                lines.append("1) 严禁全知视角措辞（如“殊不知/与此同时/他并不知道”），仅写 POV 所知。")
                pov_name = (context.get("pov") or {}).get("pov_name")
                if pov_name:
                    lines.append(f"POV 角色：{pov_name}，禁止描写其他角色的内心活动。")
            if err.code == "E_CHARACTER_ABRUPT_INTRO":
                lines.append("2) 新角色首次出现的两句内必须有外观/身份/与POV关系的介绍，禁止直接暴露真实身份。")
            if err.code == "E_OUTLINE_COMPRESSION":
                allowed = (context.get("outline_constraints") or {}).get("allowed_outline_nodes") or []
                forbidden = (context.get("outline_constraints") or {}).get("forbidden_outline_nodes") or []
                lines.append(f"3) 只推进节点：{allowed}；禁止推进：{[n.get('id') for n in forbidden]}")
                lines.append("禁止出现“反杀/回击/反转/决战/大胜”等强推进词。")
        return "\n".join(lines)

    @staticmethod
    def _extract_name_candidates(text: str) -> List[str]:
        # Very simple Chinese name pattern (2-4 chars) and capitalized ASCII words
        chinese_pattern = re.compile(r"[\u4e00-\u9fa5]{2,4}")
        ascii_pattern = re.compile(r"[A-Z][a-z]{1,15}")
        names = set(chinese_pattern.findall(text))
        names.update(ascii_pattern.findall(text))
        return list(names)


__all__ = ["PostGenValidator", "ValidationResult", "ValidationErrorDetail"]
