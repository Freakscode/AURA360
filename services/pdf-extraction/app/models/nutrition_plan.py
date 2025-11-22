"""Pydantic models for nutrition plan structured data extraction."""

from typing import Optional

from pydantic import BaseModel, Field


class Metadata(BaseModel):
    """Metadata about the nutrition plan."""

    patient_name: Optional[str] = Field(
        default=None, description="Name of the patient"
    )
    nutritionist_name: Optional[str] = Field(
        default=None, description="Name of the nutritionist"
    )
    issue_date: Optional[str] = Field(
        default=None, description="Issue date in YYYY-MM-DD format"
    )
    valid_from: Optional[str] = Field(
        default=None, description="Validity start date in YYYY-MM-DD format"
    )
    valid_until: Optional[str] = Field(
        default=None, description="Validity end date in YYYY-MM-DD format"
    )
    daily_calories: Optional[float] = Field(
        default=None, description="Daily calorie target"
    )


class BodyComposition(BaseModel):
    """Body composition measurements."""

    weight_kg: Optional[float] = Field(default=None, description="Weight in kilograms")
    height_cm: Optional[float] = Field(
        default=None, description="Height in centimeters"
    )
    bmi: Optional[float] = Field(default=None, description="Body Mass Index")
    body_fat_percentage: Optional[float] = Field(
        default=None, description="Body fat percentage"
    )
    muscle_mass_kg: Optional[float] = Field(
        default=None, description="Muscle mass in kilograms"
    )
    visceral_fat: Optional[float] = Field(default=None, description="Visceral fat level")
    metabolic_age: Optional[int] = Field(default=None, description="Metabolic age")
    bone_mass_kg: Optional[float] = Field(
        default=None, description="Bone mass in kilograms"
    )
    total_body_water_percentage: Optional[float] = Field(
        default=None, description="Total body water percentage"
    )


class ExchangeItem(BaseModel):
    """Individual food item in an exchange table."""

    food: str = Field(description="Food name")
    portion: str = Field(description="Portion size description")
    grams: str = Field(description="Weight in grams")


class ExchangeTable(BaseModel):
    """Food exchange table for a specific category."""

    category: str = Field(
        description="Category name (e.g., Harinas, Carnes, Grasas, Verduras, Lácteos, Frutas, Azúcares)"
    )
    items: list[ExchangeItem] = Field(
        description="List of food items in this category"
    )


class MealExchanges(BaseModel):
    """Number of exchanges per category for a meal."""

    harinas: float = Field(default=0, description="Number of starch exchanges")
    carnes: float = Field(default=0, description="Number of protein/meat exchanges")
    grasas: float = Field(default=0, description="Number of fat exchanges")
    verduras: float = Field(default=0, description="Number of vegetable exchanges")
    lacteos: float = Field(default=0, description="Number of dairy exchanges")
    frutas: float = Field(default=0, description="Number of fruit exchanges")
    azucares: float = Field(default=0, description="Number of sugar exchanges")


class Meal(BaseModel):
    """Individual meal in the nutrition plan."""

    name: str = Field(
        description="Meal name (e.g., Desayuno, Media Mañana, Almuerzo, Merienda, Cena)"
    )
    time: Optional[str] = Field(
        default=None, description="Meal time in HH:MM format (e.g., 07:00)"
    )
    exchanges: MealExchanges = Field(
        description="Number of exchanges per category for this meal"
    )
    notes: Optional[str] = Field(default=None, description="Additional notes or instructions")


class DailyExchanges(BaseModel):
    """Total daily exchanges across all meals."""

    harinas: float = Field(default=0, description="Total daily starch exchanges")
    carnes: float = Field(default=0, description="Total daily protein/meat exchanges")
    grasas: float = Field(default=0, description="Total daily fat exchanges")
    verduras: float = Field(default=0, description="Total daily vegetable exchanges")
    lacteos: float = Field(default=0, description="Total daily dairy exchanges")
    frutas: float = Field(default=0, description="Total daily fruit exchanges")
    azucares: float = Field(default=0, description="Total daily sugar exchanges")


class NutritionPlan(BaseModel):
    """Complete nutrition plan extracted from PDF."""

    metadata: Metadata = Field(description="Plan metadata and patient information")
    body_composition: BodyComposition = Field(
        description="Body composition measurements"
    )
    exchange_tables: list[ExchangeTable] = Field(
        description="Food exchange tables by category"
    )
    meals: list[Meal] = Field(description="List of meals in the plan")
    daily_exchanges: DailyExchanges = Field(
        description="Total daily exchanges summary"
    )
    notes: Optional[str] = Field(
        default=None, description="General notes or recommendations"
    )
