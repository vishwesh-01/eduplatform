"""
ai/llm_service.py — LLMService: Gemini API integration.

Uses google-generativeai SDK. Compatible with gemini-1.5-flash (default, free tier)
and gemini-1.5-pro. Model is configured via GEMINI_MODEL_NAME env var.

Provides:
    generate_learning_path()  — personalised ordered course recommendations
    generate_quiz_questions() — adaptive quiz questions at a given difficulty level

All calls:
  - Retry once on failure or schema validation error
  - Fall back to seeded DB content on repeated failure
  - Persist every attempt to content_versions table for audit
"""

import json
import logging
import os
import re
from typing import Optional

import google.generativeai as genai
from pydantic import BaseModel, Field, ValidationError

from ...extensions import db
from ...models import ContentVersion

logger = logging.getLogger(__name__)


# ── Pydantic response schemas ─────────────────────────────────────────────────

class CourseRecommendation(BaseModel):
    """One AI-recommended course."""
    title:                str
    description:          str
    estimated_hours:      float = Field(gt=0, default=10.0)
    skill_level_required: int   = Field(ge=0, le=100, default=0)
    estimated_skill_gain: int   = Field(ge=0, le=100, default=10)


class LearningPathResponse(BaseModel):
    """Validated learning path from LLM."""
    courses: list[CourseRecommendation]


class QuizQuestionItem(BaseModel):
    """One AI-generated quiz question."""
    question_text:        str
    options:              list[str]
    correct_option_index: int = Field(ge=0, le=3)
    difficulty:           int = Field(ge=1, le=5)


class QuizQuestionsResponse(BaseModel):
    """Validated quiz questions from LLM."""
    questions: list[QuizQuestionItem]


# ── LLMService ────────────────────────────────────────────────────────────────

class LLMService:
    """
    Internal service for Gemini API calls.
    Not exposed as HTTP — imported directly by other services.
    """

    def __init__(self):
        """Configure the Gemini SDK. Reads api_key and model from environment."""
        self._api_key   = os.environ.get("GEMINI_API_KEY", "")
        # Default to gemini-1.5-flash — free tier, reliable JSON output
        self._model_name = os.environ.get("GEMINI_MODEL_NAME", "gemini-1.5-flash")
        if self._api_key:
            genai.configure(api_key=self._api_key)

    def generate_learning_path(
        self,
        user_id: str,
        goal: str,
        skill_level: int,
        completed_courses: list,
        course_count: int = 5,
    ) -> Optional[LearningPathResponse]:
        """
        Ask the LLM to generate a personalised ordered course list.

        Args:
            user_id:           Learner UUID (for content versioning audit).
            goal:              Career goal string e.g. 'Python Developer'.
            skill_level:       Assessed score 0-100.
            completed_courses: List of already-completed course title strings.
            course_count:      How many courses to recommend.

        Returns:
            LearningPathResponse on success, None on failure (caller uses fallback).
        """
        if not self._api_key:
            logger.warning("GEMINI_API_KEY not set — skipping LLM call")
            return None

        completed_str = (
            "\n".join(f"  - {t}" for t in completed_courses)
            if completed_courses
            else "  (none yet)"
        )

        level_label = (
            "beginner" if skill_level < 40
            else "intermediate" if skill_level < 70
            else "advanced"
        )

        prompt = f"""You are an expert curriculum designer for an online coding education platform.

A learner wants to become a {goal}.
Their assessed skill level is {skill_level}/100 ({level_label}).
They have already completed:
{completed_str}

Generate exactly {course_count} course recommendations tailored to their level.
Do NOT repeat courses they have already completed.
Order them from easiest to hardest based on skill_level_required.

Respond ONLY with a valid JSON object — no markdown, no explanation, no code fences:
{{
  "courses": [
    {{
      "title": "Course title here",
      "description": "What the learner will gain (max 200 chars)",
      "estimated_hours": 12,
      "skill_level_required": 0,
      "estimated_skill_gain": 15
    }}
  ]
}}"""

        return self._call_with_retry(
            prompt=prompt,
            schema_class=LearningPathResponse,
            entity_type="learning_path",
            entity_id=user_id,
        )

    def generate_quiz_questions(
        self,
        goal: str,
        difficulty: int,
        count: int = 5,
    ) -> Optional[QuizQuestionsResponse]:
        """
        Ask the LLM to generate multiple-choice quiz questions.

        Args:
            goal:       Career goal string.
            difficulty: Target difficulty level 1-5.
            count:      Number of questions to produce.

        Returns:
            QuizQuestionsResponse on success, None on failure.
        """
        if not self._api_key:
            return None

        level_map = {1: "complete beginner", 2: "basic", 3: "intermediate",
                     4: "advanced", 5: "expert"}
        level_label = level_map.get(difficulty, "intermediate")

        prompt = f"""You are an expert educator creating a coding assessment.

Generate exactly {count} multiple-choice questions about {goal} at {level_label} level (difficulty {difficulty}/5).
Each question must have exactly 4 options and one correct answer.

Respond ONLY with a valid JSON object — no markdown, no explanation, no code fences:
{{
  "questions": [
    {{
      "question_text": "What is ... ?",
      "options": ["Option A", "Option B", "Option C", "Option D"],
      "correct_option_index": 0,
      "difficulty": {difficulty}
    }}
  ]
}}"""

        return self._call_with_retry(
            prompt=prompt,
            schema_class=QuizQuestionsResponse,
            entity_type="quiz_question",
            entity_id=None,
        )

    def generate_adaptive_path_update(
        self,
        user_id: str,
        goal: str,
        current_skill: int,
        completed_courses: list,
        remaining_path_titles: list,
        module_just_completed: str,
    ) -> Optional[LearningPathResponse]:
        """
        Re-generate the remaining learning path after a module is completed.

        This is called after each module completion to adapt the remaining
        path based on updated progress.

        Args:
            user_id:               Learner UUID.
            goal:                  Career goal string.
            current_skill:         Current assessed skill level 0-100.
            completed_courses:     Fully completed course titles.
            remaining_path_titles: Current remaining path course titles.
            module_just_completed: Title of the module the learner just finished.

        Returns:
            LearningPathResponse with updated remaining courses, or None.
        """
        if not self._api_key:
            return None

        completed_str = (
            "\n".join(f"  - {t}" for t in completed_courses) if completed_courses else "  (none)"
        )
        remaining_str = (
            "\n".join(f"  - {t}" for t in remaining_path_titles) if remaining_path_titles else "  (none)"
        )

        prompt = f"""You are an expert adaptive learning system for {goal}.

A learner just completed the module: "{module_just_completed}"
Their current skill level: {current_skill}/100
Courses they have fully completed: 
{completed_str}

Their current remaining learning path:
{remaining_str}

Based on their progress, update the remaining learning path.
Keep courses that are still relevant. Replace or reorder if the learner has advanced significantly.
Recommend 4-5 next courses appropriate for their current level.

Respond ONLY with a valid JSON object — no markdown, no explanation, no code fences:
{{
  "courses": [
    {{
      "title": "Course title",
      "description": "What they will learn",
      "estimated_hours": 10,
      "skill_level_required": 30,
      "estimated_skill_gain": 12
    }}
  ]
}}"""

        return self._call_with_retry(
            prompt=prompt,
            schema_class=LearningPathResponse,
            entity_type="adaptive_path_update",
            entity_id=user_id,
        )

    # ── Private helpers ───────────────────────────────────────────────────

    def _call_with_retry(
        self,
        prompt: str,
        schema_class,
        entity_type: str,
        entity_id: Optional[str],
    ):
        """
        Call Gemini API with one automatic retry.
        Extracts JSON from response, validates with Pydantic schema.
        Stores every attempt in content_versions.
        Returns None if both attempts fail.
        """
        raw_response = ""
        for attempt in range(1, 3):
            try:
                model = genai.GenerativeModel(
                    model_name=self._model_name,
                    generation_config=genai.GenerationConfig(
                        temperature=0.2,
                        max_output_tokens=2048,
                    ),
                )
                response = model.generate_content(prompt)
                raw_response = response.text.strip() if response.text else ""

                # Extract JSON — strip markdown code fences if present
                json_text = self._extract_json(raw_response)
                if not json_text:
                    raise ValueError(f"No valid JSON found in response: {raw_response[:200]}")

                parsed = schema_class.model_validate_json(json_text)

                self._store_version(entity_type, entity_id, prompt, parsed.model_dump(), raw_response)
                logger.info(f"LLM call succeeded: {entity_type} (attempt {attempt})")
                return parsed

            except Exception as exc:
                logger.warning(f"LLM attempt {attempt} failed for {entity_type}: {exc}")
                self._store_version(entity_type, entity_id, prompt, {}, raw_response)
                if attempt == 2:
                    logger.error(f"LLM failed after 2 attempts for {entity_type} — using fallback")
                    return None

    def _extract_json(self, text: str) -> Optional[str]:
        """
        Extract a JSON object from text that may contain markdown code fences
        or surrounding prose. Returns the JSON string or None.
        """
        if not text:
            return None

        # Remove markdown code fences: ```json ... ``` or ``` ... ```
        fenced = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if fenced:
            return fenced.group(1).strip()

        # Find the first { ... } block spanning the whole response
        brace_start = text.find('{')
        brace_end   = text.rfind('}')
        if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
            candidate = text[brace_start:brace_end + 1]
            # Quick validation
            try:
                json.loads(candidate)
                return candidate
            except json.JSONDecodeError:
                pass

        # Last resort: try the raw text directly
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            return None

    def _store_version(
        self,
        entity_type: str,
        entity_id: Optional[str],
        prompt: str,
        generated_content: dict,
        raw_response: str,
    ) -> None:
        """Persist a content_versions audit record for every LLM call."""
        try:
            from sqlalchemy import func
            latest = (
                db.session.query(func.max(ContentVersion.version_number))
                .filter_by(entity_type=entity_type, entity_id=entity_id)
                .scalar()
            ) or 0

            record = ContentVersion(
                entity_type=entity_type,
                entity_id=entity_id,
                version_number=latest + 1,
                prompt_used=prompt,
                generated_content=generated_content,
                raw_response=raw_response[:5000],  # cap to avoid huge DB rows
            )
            db.session.add(record)
            db.session.commit()
        except Exception as exc:
            logger.error(f"Failed to store content_version: {exc}")
            db.session.rollback()
