"""
Pydanticモデルを解析してフィールド情報を抽出するモジュール
"""

from typing import Any, get_args, get_origin
from datetime import date
from enum import Enum
from pydantic import BaseModel
from pydantic.fields import FieldInfo

from .field_types import SelectOption


class FieldType(Enum):
    """フィールドタイプの列挙型"""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    SELECT = "select"
    CHECKBOX = "checkbox"


class ParsedField:
    """解析されたフィールド情報を保持するクラス"""

    def __init__(
        self,
        name: str,
        field_type: FieldType,
        required: bool = True,
        title: str | None = None,
        description: str | None = None,
        default: Any = None,
        min_length: int | None = None,
        max_length: int | None = None,
        ge: float | None = None,
        le: float | None = None,
        gt: float | None = None,
        lt: float | None = None,
        pattern: str | None = None,
        options: list[SelectOption] | None = None,
        placeholder: str | None = None,
    ):
        self.name = name
        self.field_type = field_type
        self.required = required
        self.title = title or name.replace("_", " ").title()
        self.description = description
        self.default = default
        self.min_length = min_length
        self.max_length = max_length
        self.ge = ge
        self.le = le
        self.gt = gt
        self.lt = lt
        self.pattern = pattern
        self.options = options or []
        self.placeholder = placeholder


class ModelParser:
    """Pydanticモデルを解析するクラス"""

    @classmethod
    def parse(cls, model: type[BaseModel]) -> list[ParsedField]:
        """Pydanticモデルからフィールド情報を抽出"""
        fields: list[ParsedField] = []

        for field_name, field_info in model.model_fields.items():
            parsed = cls._parse_field(field_name, field_info)
            fields.append(parsed)

        return fields

    @classmethod
    def _parse_field(cls, name: str, field_info: FieldInfo) -> ParsedField:
        """個別のフィールドを解析"""
        annotation = field_info.annotation
        field_type = cls._detect_field_type(annotation, field_info)
        required = field_info.is_required()

        # メタデータから制約を抽出
        constraints = cls._extract_constraints(field_info)

        # 選択肢の抽出
        options = cls._extract_options(annotation, field_info)

        # プレースホルダーの抽出
        placeholder = cls._extract_placeholder(field_info)

        return ParsedField(
            name=name,
            field_type=field_type,
            required=required,
            title=field_info.title,
            description=field_info.description,
            default=field_info.default if not field_info.is_required() else None,
            options=options,
            placeholder=placeholder,
            **constraints,
        )

    @classmethod
    def _detect_field_type(cls, annotation: Any, field_info: FieldInfo) -> FieldType:
        """型アノテーションからフィールドタイプを判定"""
        from typing import Literal, Annotated, Union
        from types import UnionType

        original_annotation = annotation

        # Annotatedの場合のみ、内部の型を取得
        origin = get_origin(annotation)
        if origin is Annotated:
            args = get_args(annotation)
            if args:
                annotation = args[0]
                # 再度originを更新
                origin = get_origin(annotation)

        # Union型（T | None など）の場合、Noneでない型を取得
        if origin is Union or isinstance(annotation, UnionType):
            args = get_args(annotation)
            non_none_args = [a for a in args if a is not type(None)]
            if non_none_args:
                annotation = non_none_args[0]
                origin = get_origin(annotation)

        # Literal型の検出（選択肢として扱う）
        if origin is Literal:
            return FieldType.SELECT

        # SelectFieldの検出
        if hasattr(annotation, "_select_field") or hasattr(annotation, "_options"):
            return FieldType.SELECT

        # 基本型の判定
        if annotation is bool:
            return FieldType.CHECKBOX
        if annotation is int:
            return FieldType.INTEGER
        if annotation is float:
            return FieldType.FLOAT
        if annotation is date:
            return FieldType.DATE
        if annotation is str:
            return FieldType.STRING

        # デフォルトは文字列
        return FieldType.STRING

    @classmethod
    def _extract_constraints(cls, field_info: FieldInfo) -> dict[str, Any]:
        """フィールドの制約を抽出"""
        constraints: dict[str, Any] = {}

        # メタデータから制約を取得
        for meta in field_info.metadata:
            if hasattr(meta, "min_length"):
                constraints["min_length"] = meta.min_length
            if hasattr(meta, "max_length"):
                constraints["max_length"] = meta.max_length
            if hasattr(meta, "ge"):
                constraints["ge"] = meta.ge
            if hasattr(meta, "le"):
                constraints["le"] = meta.le
            if hasattr(meta, "gt"):
                constraints["gt"] = meta.gt
            if hasattr(meta, "lt"):
                constraints["lt"] = meta.lt
            if hasattr(meta, "pattern"):
                constraints["pattern"] = meta.pattern

        return constraints

    @classmethod
    def _extract_options(
        cls, annotation: Any, field_info: FieldInfo
    ) -> list[SelectOption]:
        """選択肢を抽出"""
        from typing import Literal, Annotated

        options: list[SelectOption] = []

        # Annotatedの場合のみ、内部の型を取得
        origin = get_origin(annotation)
        if origin is Annotated:
            args = get_args(annotation)
            if args:
                annotation = args[0]
                origin = get_origin(annotation)

        if hasattr(annotation, "_options"):
            return list(annotation._options)

        # Literal型から抽出
        if origin is Literal:
            args = get_args(annotation)
            for arg in args:
                options.append(SelectOption(str(arg), str(arg)))

        return options

    @classmethod
    def _extract_placeholder(cls, field_info: FieldInfo) -> str | None:
        """プレースホルダーを抽出"""
        # json_schema_extraからプレースホルダーを取得
        if field_info.json_schema_extra:
            if isinstance(field_info.json_schema_extra, dict):
                return field_info.json_schema_extra.get("placeholder")
        return None
