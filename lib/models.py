"""
lib/models.py
-------------
Pydantic data models for KPI Hub entities and DataFrame validation.
"""

from typing import Optional, List, Dict, Any, Type, Tuple
from pydantic import BaseModel, ConfigDict, Field
import pandas as pd

class BaseKPIModel(BaseModel):
    model_config = ConfigDict(extra='ignore', coerce_numbers_to_str=True)

class ProjectModel(BaseKPIModel):
    PROJECT_ID: str
    PROJECT_NAME: Optional[str] = None
    PROGRAM: Optional[str] = None
    RELEASE: Optional[str] = None
    PRODUCT_LINE: Optional[str] = None
    STATUS: Optional[str] = None
    HEALTH_STATUS: Optional[str] = None
    HEALTH_SCORE: Optional[float] = None

class MilestoneModel(BaseKPIModel):
    MILESTONE_ID: str
    PROJECT_ID: str
    MILESTONE_NAME: str
    PLANNED_DATE: Optional[str] = None
    STATUS: Optional[str] = None

class BudgetModel(BaseKPIModel):
    BUDGET_ID: str
    PROJECT_ID: str
    BUDGET_CATEGORY: Optional[str] = None
    PLANNED_AMOUNT: Optional[float] = None
    SPENT_AMOUNT: Optional[float] = None
    STATUS: Optional[str] = None

class RiskModel(BaseKPIModel):
    RISK_ID: str
    PROJECT_ID: str
    RISK_TITLE: Optional[str] = None
    SEVERITY: Optional[str] = None
    STATUS: Optional[str] = None

class ResourceAllocationModel(BaseKPIModel):
    PROJECT_ID: str
    TEAM_MEMBER: str
    ROLE: Optional[str] = None
    UTILIZATION_PCT: Optional[Any] = None

class RequirementModel(BaseKPIModel):
    REQUIREMENT_ID: str
    PROJECT_ID: str
    REQUIREMENT_TEXT: Optional[str] = None
    STATUS: Optional[str] = None
    ASIL_LEVEL: Optional[str] = None

class TestCaseModel(BaseKPIModel):
    TEST_ID: str
    PROJECT_ID: str
    TEST_CASE_NAME: Optional[str] = None
    STATUS: Optional[str] = None

class DefectModel(BaseKPIModel):
    DEFECT_ID: str
    PROJECT_ID: str
    DEFECT_TITLE: Optional[str] = None
    SEVERITY: Optional[str] = None
    STATUS: Optional[str] = None

MODEL_MAPPING: Dict[str, Type[BaseKPIModel]] = {
    "projects_status.csv": ProjectModel,
    "milestones.csv": MilestoneModel,
    "budget_tracking.csv": BudgetModel,
    "risk_register.csv": RiskModel,
    "resource_allocation.csv": ResourceAllocationModel,
    "requirements.csv": RequirementModel,
    "test_execution.csv": TestCaseModel,
    "defects.csv": DefectModel,
}

def validate_dataframe(df: pd.DataFrame, model_class: Type[BaseKPIModel]) -> Tuple[pd.DataFrame, List[str]]:
    """
    Validates rows in a pandas DataFrame against a Pydantic model.
    Returns (valid_df, error_messages).
    """
    if df is None or df.empty:
        return pd.DataFrame(), []

    valid_records = []
    errors = []

    records = df.to_dict(orient="records")
    for idx, record in enumerate(records):
        try:
            # Clean up NaN / NaT values for Pydantic validation
            cleaned_record = {k: (None if pd.isna(v) else v) for k, v in record.items()}
            model_inst = model_class(**cleaned_record)
            valid_records.append(model_inst.model_dump())
        except Exception as e:
            errors.append(f"Row {idx+1} validation failed: {str(e)}")

    valid_df = pd.DataFrame(valid_records) if valid_records else pd.DataFrame()
    return valid_df, errors
