"""
カスタムフィールドタイプの定義
選択肢、チェックボックス、日付などの特殊なフィールドタイプを定義
"""

from typing import Annotated, Any, Sequence
from dataclasses import dataclass
from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema


@dataclass
class SelectOption:
    """選択肢のオプションを定義するクラス"""

    value: str
    label: str

    def __init__(self, value: str, label: str | None = None):
        self.value = value
        self.label = label if label is not None else value


class SelectField:
    """選択肢フィールドのマーカークラス"""

    def __init__(self, options: Sequence[SelectOption | str]):
        self.options: list[SelectOption] = []
        for opt in options:
            if isinstance(opt, str):
                self.options.append(SelectOption(opt, opt))
            else:
                self.options.append(opt)

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.str_schema()


class CheckboxField:
    """チェックボックスフィールドのマーカークラス"""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.bool_schema()


class DateField:
    """日付フィールドのマーカークラス"""

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:
        return core_schema.date_schema()


def Select(options: Sequence[SelectOption | str]) -> type:
    """選択肢フィールドを作成するファクトリ関数"""
    field = SelectField(options)

    class SelectType(str):
        _select_field = field
        _options = field.options

        @classmethod
        def __get_pydantic_core_schema__(
            cls, source_type: Any, handler: GetCoreSchemaHandler
        ) -> CoreSchema:
            return core_schema.str_schema()

    return SelectType


def Checkbox() -> type:
    """チェックボックスフィールドを作成するファクトリ関数"""

    class CheckboxType:
        @classmethod
        def __get_pydantic_core_schema__(
            cls, source_type: Any, handler: GetCoreSchemaHandler
        ) -> CoreSchema:
            return core_schema.bool_schema()

    return CheckboxType


def Date() -> type:
    """日付フィールドを作成するファクトリ関数"""
    from datetime import date as date_type

    class DateType(date_type):
        @classmethod
        def __get_pydantic_core_schema__(
            cls, source_type: Any, handler: GetCoreSchemaHandler
        ) -> CoreSchema:
            return core_schema.date_schema()

    return DateType
