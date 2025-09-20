from sqlalchemy import Column, Integer, Float, String, DateTime, Date, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime, date
import enum

Base = declarative_base()


class MealType(str, enum.Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    SNACK = "snack"
    DINNER = "dinner"


class FCI(Base):
    __tablename__ = "fci"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True, nullable=False)
    value = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<FCI(date={self.date}, value={self.value})>"


class MealRecord(Base):
    __tablename__ = "meal_records"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    meal_type = Column(Enum(MealType), nullable=False)

    # Данные на момент еды
    glucose_start = Column(Float, nullable=False)  # СК_старт
    pause_time = Column(Integer, nullable=True)  # Пауза в минутах
    carbs_main = Column(Float, nullable=False)  # Основные углеводы
    carbs_additional = Column(Float, default=0.0)  # Дополнительные углеводы
    proteins = Column(Float, nullable=True)  # Белки
    insulin_food = Column(Float, nullable=False)  # Инсулин на еду

    # Данные через 4-5 часов
    glucose_end = Column(Float, nullable=False)  # СК_отработка

    # Подколки
    insulin_additional = Column(Float, default=0.0)  # Подколки с коррекцией

    # Результат
    uk_value = Column(Float, nullable=False)  # УК

    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<MealRecord(date={self.date}, meal={self.meal_type}, uk={self.uk_value})>"


class AdditionalInjection(Base):
    __tablename__ = "additional_injections"

    id = Column(Integer, primary_key=True, index=True)
    meal_record_id = Column(Integer, nullable=False, index=True)
    time_from_meal = Column(Integer, nullable=False)  # Время от еды в минутах
    dose = Column(Float, nullable=False)  # Исходная доза
    dose_corrected = Column(Float, nullable=False)  # Скорректированная доза

    created_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"<AdditionalInjection(meal_id={self.meal_record_id}, time={self.time_from_meal}, dose={self.dose_corrected})>"
