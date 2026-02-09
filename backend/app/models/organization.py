"""
TaskPulse - AI Assistant - Organization Model
Multi-tenant organization support
"""

from sqlalchemy import Column, String, Enum, Text, Boolean
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class PlanTier(str, enum.Enum):
    """Organization subscription plan tiers."""
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    ENTERPRISE_PLUS = "enterprise_plus"


class Organization(Base):
    """
    Organization model for multi-tenancy.
    Each organization is a separate tenant with its own users, tasks, and settings.
    """

    __tablename__ = "organizations"

    # Basic info
    name = Column(String(255), nullable=False)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)

    # Subscription
    plan = Column(
        Enum(PlanTier),
        default=PlanTier.STARTER,
        nullable=False
    )

    # Settings stored as JSON string (SQLite doesn't have native JSON)
    settings_json = Column(Text, default="{}")

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    users = relationship("User", back_populates="organization", lazy="selectin")
    # tasks = relationship("Task", back_populates="organization", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name}, plan={self.plan})>"

    @property
    def settings(self) -> dict:
        """Parse settings JSON string to dict."""
        import json
        try:
            return json.loads(self.settings_json or "{}")
        except json.JSONDecodeError:
            return {}

    @settings.setter
    def settings(self, value: dict) -> None:
        """Serialize settings dict to JSON string."""
        import json
        self.settings_json = json.dumps(value)

    @property
    def is_enterprise(self) -> bool:
        """Check if organization has enterprise plan."""
        return self.plan in (PlanTier.ENTERPRISE, PlanTier.ENTERPRISE_PLUS)

    @property
    def max_users(self) -> int:
        """Get maximum users allowed for plan."""
        limits = {
            PlanTier.STARTER: 25,
            PlanTier.PROFESSIONAL: 100,
            PlanTier.ENTERPRISE: 500,
            PlanTier.ENTERPRISE_PLUS: 10000
        }
        return limits.get(self.plan, 25)

    @property
    def features(self) -> dict:
        """Get features available for plan."""
        base_features = {
            "task_management": True,
            "basic_checkins": True,
            "basic_reports": True
        }

        plan_features = {
            PlanTier.STARTER: {
                **base_features,
                "ai_decomposition_limit": 5,
                "integrations_limit": 2,
                "api_access": "read_only"
            },
            PlanTier.PROFESSIONAL: {
                **base_features,
                "ai_decomposition_limit": -1,  # Unlimited
                "full_rag": True,
                "basic_predictions": True,
                "basic_skill_graph": True,
                "integrations_limit": 5,
                "api_access": "full"
            },
            PlanTier.ENTERPRISE: {
                **base_features,
                "ai_decomposition_limit": -1,
                "full_rag": True,
                "custom_knowledge_base": True,
                "full_predictions": True,
                "full_skill_graph": True,
                "automation_detection": True,
                "agent_creation": True,
                "sso_saml": True,
                "soc2_report": True,
                "integrations_limit": -1,
                "api_access": "full_graphql",
                "basic_workforce_intelligence": True
            },
            PlanTier.ENTERPRISE_PLUS: {
                **base_features,
                "ai_decomposition_limit": -1,
                "full_rag": True,
                "custom_knowledge_base": True,
                "custom_ai_models": True,
                "full_predictions": True,
                "full_skill_graph": True,
                "automation_detection": True,
                "agent_creation": True,
                "custom_agents": True,
                "sso_saml": True,
                "soc2_report": True,
                "white_labeling": True,
                "on_premise": True,
                "integrations_limit": -1,
                "api_access": "full_sdk",
                "full_workforce_intelligence": True,
                "restructuring_simulator": True,
                "workforce_reduction_planning": True
            }
        }

        return plan_features.get(self.plan, base_features)
