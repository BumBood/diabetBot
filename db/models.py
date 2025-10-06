from sqlalchemy import Column, Integer, Float, String, DateTime, Date, Enum, BigInteger, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, date
import enum

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=func.now())

    # Связи
    fci_records = relationship("FCI", back_populates="user")
    meal_records = relationship("MealRecord", back_populates="user")
    insulin_records = relationship("InsulinRecord", back_populates="user")

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username={self.username})>"


class MealType(str, enum.Enum):
    BREAKFAST = "breakfast"
    LUNCH = "lunch"
    SNACK = "snack"
    DINNER = "dinner"


class InsulinType(str, enum.Enum):
    FOOD = "food"  # На еду
    CORRECTION = "correction"  # Коррекция


class FCI(Base):
    __tablename__ = "fci"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    value = Column(Float, nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Связи
    user = relationship("User", back_populates="fci_records")

    def __repr__(self):
        return f"<FCI(user_id={self.user_id}, date={self.date}, value={self.value})>"


class InsulinRecord(Base):
    __tablename__ = "insulin_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    insulin_type = Column(Enum(InsulinType), nullable=False)
    amount = Column(Float, nullable=False)  # Количество инсулина в единицах
    is_manual = Column(
        Integer, nullable=False, default=0
    )  # 0 = автоматически из ввода УК, 1 = ручной ввод пользователя
    created_at = Column(DateTime, default=func.now())

    # Связи
    user = relationship("User", back_populates="insulin_records")

    def __repr__(self):
        return f"<InsulinRecord(user_id={self.user_id}, date={self.date}, type={self.insulin_type}, amount={self.amount}, is_manual={self.is_manual})>"


class MealRecord(Base):
    __tablename__ = "meal_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
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

    # Связи
    user = relationship("User", back_populates="meal_records")
    additional_injections = relationship("AdditionalInjection", back_populates="meal_record")

    def __repr__(self):
        return f"<MealRecord(user_id={self.user_id}, date={self.date}, meal={self.meal_type}, uk={self.uk_value})>"


class AdditionalInjection(Base):
    __tablename__ = "additional_injections"

    id = Column(Integer, primary_key=True, index=True)
    meal_record_id = Column(Integer, ForeignKey("meal_records.id"), nullable=False, index=True)
    time_from_meal = Column(Integer, nullable=False)  # Время от еды в минутах
    dose = Column(Float, nullable=False)  # Исходная доза
    dose_corrected = Column(Float, nullable=False)  # Скорректированная доза

    created_at = Column(DateTime, default=func.now())

    # Связи
    meal_record = relationship("MealRecord", back_populates="additional_injections")

    def __repr__(self):
        return f"<AdditionalInjection(meal_id={self.meal_record_id}, time={self.time_from_meal}, dose={self.dose_corrected})>"
