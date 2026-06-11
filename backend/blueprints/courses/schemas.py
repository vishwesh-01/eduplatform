"""
courses/schemas.py — Marshmallow schemas for courses, goals, and learning paths.
"""

from marshmallow import Schema, fields


class GoalSchema(Schema):
    """Serialises a learning Goal."""
    id          = fields.Str()
    name        = fields.Str()
    description = fields.Str(allow_none=True)


class ModuleSchema(Schema):
    """Serialises a Module within a Course."""
    id                  = fields.Str()
    title               = fields.Str()
    position            = fields.Int()
    video_id            = fields.Str(allow_none=True)
    video_title         = fields.Str(allow_none=True)
    video_thumbnail_url = fields.Str(allow_none=True)


class CourseSchema(Schema):
    """Serialises a Course (list view — no modules)."""
    id             = fields.Str()
    goal_id        = fields.Str()
    title          = fields.Str()
    instructor     = fields.Str(allow_none=True)
    duration_hours = fields.Float(allow_none=True)
    created_at     = fields.DateTime()


class CourseDetailSchema(Schema):
    """Serialises a Course with its full Module list."""
    id             = fields.Str()
    goal_id        = fields.Str()
    title          = fields.Str()
    instructor     = fields.Str(allow_none=True)
    duration_hours = fields.Float(allow_none=True)
    created_at     = fields.DateTime()
    modules        = fields.List(fields.Nested(ModuleSchema))


class LearningPathItemSchema(Schema):
    """Serialises one item in a LearningPath."""
    id                   = fields.Str()
    course_id            = fields.Str()
    position             = fields.Int()
    estimated_skill_gain = fields.Float(allow_none=True)
    course               = fields.Nested(CourseSchema)


class LearningPathSchema(Schema):
    """Serialises a full LearningPath with its ordered items."""
    id           = fields.Str()
    user_id      = fields.Str()
    goal_id      = fields.Str()
    generated_at = fields.DateTime()
    updated_at   = fields.DateTime()
    items        = fields.List(fields.Nested(LearningPathItemSchema))


class SelectGoalSchema(Schema):
    """Validates POST /goals/select body."""
    goal_id = fields.Str(required=True)
