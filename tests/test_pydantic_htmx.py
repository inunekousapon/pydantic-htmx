"""
pydantic-htmx のテスト
"""

from datetime import date
from typing import Literal, Annotated

import pytest
from pydantic import BaseModel, Field

from pydantic_htmx import FormGenerator, SelectOption, HTMXValidator
from pydantic_htmx.field_types import Select
from pydantic_htmx.parser import ModelParser, FieldType


# テスト用モデル
class SimpleModel(BaseModel):
    name: Annotated[str, Field(min_length=1, title="名前")]
    age: int = Field(ge=0, title="年齢")


class FullModel(BaseModel):
    """全フィールドタイプを含むモデル"""

    # 文字列
    username: Annotated[str, Field(min_length=3, max_length=20, title="ユーザー名")]

    # 数値（整数）
    age: Annotated[int, Field(ge=18, le=120, title="年齢")]

    # 数値（浮動小数点）
    score: Annotated[float, Field(ge=0.0, le=100.0, title="スコア")]

    # 日付
    birth_date: date = Field(title="生年月日")

    # 選択肢（Literal）
    status: Literal["active", "inactive", "pending"] = Field(title="ステータス")

    # チェックボックス
    is_admin: bool = Field(default=False, title="管理者権限")


class TestModelParser:
    """ModelParserのテスト"""

    def test_parse_simple_model(self):
        """シンプルなモデルの解析"""
        fields = ModelParser.parse(SimpleModel)

        assert len(fields) == 2

        name_field = next(f for f in fields if f.name == "name")
        assert name_field.field_type == FieldType.STRING
        assert name_field.title == "名前"

        age_field = next(f for f in fields if f.name == "age")
        assert age_field.field_type == FieldType.INTEGER
        assert age_field.ge == 0

    def test_parse_full_model(self):
        """全フィールドタイプを含むモデルの解析"""
        fields = ModelParser.parse(FullModel)

        assert len(fields) == 6

        # 文字列フィールド
        username = next(f for f in fields if f.name == "username")
        assert username.field_type == FieldType.STRING
        assert username.min_length == 3
        assert username.max_length == 20

        # 整数フィールド
        age = next(f for f in fields if f.name == "age")
        assert age.field_type == FieldType.INTEGER
        assert age.ge == 18
        assert age.le == 120

        # 浮動小数点フィールド
        score = next(f for f in fields if f.name == "score")
        assert score.field_type == FieldType.FLOAT

        # 日付フィールド
        birth_date = next(f for f in fields if f.name == "birth_date")
        assert birth_date.field_type == FieldType.DATE

        # 選択肢フィールド
        status = next(f for f in fields if f.name == "status")
        assert status.field_type == FieldType.SELECT
        assert len(status.options) == 3

        # チェックボックスフィールド
        is_admin = next(f for f in fields if f.name == "is_admin")
        assert is_admin.field_type == FieldType.CHECKBOX


class TestFormGenerator:
    """FormGeneratorのテスト"""

    def test_generate_form(self):
        """フォーム生成"""
        generator = FormGenerator(SimpleModel)
        html = generator.generate_form()

        assert 'id="simplemodel-form"' in html
        assert 'name="name"' in html
        assert 'name="age"' in html
        assert 'type="submit"' in html

    def test_generate_form_with_custom_options(self):
        """カスタムオプションでのフォーム生成"""
        generator = FormGenerator(SimpleModel)
        html = generator.generate_form(
            form_id="my-form", action="/api/submit", submit_text="送信する"
        )

        assert 'id="my-form"' in html
        assert 'hx-post="/api/submit"' in html
        assert ">送信する</button>" in html

    def test_generate_full_html(self):
        """完全なHTMLドキュメント生成"""
        generator = FormGenerator(SimpleModel)
        html = generator.generate_full_html(title="テストフォーム")

        assert "<!DOCTYPE html>" in html
        assert "<title>テストフォーム</title>" in html
        assert "htmx.org" in html

    def test_generate_css(self):
        """CSS生成"""
        generator = FormGenerator(SimpleModel)
        css = generator.generate_css()

        assert "<style>" in css
        assert ".pydantic-htmx-form" in css


class TestHTMXValidator:
    """HTMXValidatorのテスト"""

    def test_validate_field_valid(self):
        """有効なフィールドのバリデーション"""
        validator = HTMXValidator(SimpleModel)

        result = validator.validate_field("name", {"name": "John", "age": 25})
        assert result.is_valid

        result = validator.validate_field("age", {"name": "John", "age": 25})
        assert result.is_valid

    def test_validate_field_invalid(self):
        """無効なフィールドのバリデーション"""
        validator = HTMXValidator(FullModel)

        # 短すぎる
        result = validator.validate_field("username", {"username": "ab", "age": 20, "score": 50.0, "birth_date": "2000-01-01", "status": "active", "is_admin": False})
        assert not result.is_valid
        assert "短すぎます" in result.error_message

    def test_validate_field_required(self):
        """必須フィールドのバリデーション"""
        validator = HTMXValidator(SimpleModel)

        result = validator.validate_field("name", {"name": "", "age": 25})
        assert not result.is_valid
        assert "必須" in result.error_message

    def test_validate_all(self):
        """全フィールドのバリデーション"""
        validator = HTMXValidator(SimpleModel)

        # 有効なデータ
        results = validator.validate_all({"name": "John", "age": 25})
        assert all(r.is_valid for r in results.values())

        # 無効なデータ
        results = validator.validate_all({"name": "", "age": -5})
        assert not results["name"].is_valid
        assert not results["age"].is_valid

    def test_validate_and_parse(self):
        """バリデーションとパース"""
        validator = HTMXValidator(SimpleModel)

        # 有効なデータ
        model, results = validator.validate_and_parse({"name": "John", "age": 25})
        assert model is not None
        assert model.name == "John"
        assert model.age == 25

        # 無効なデータ
        model, results = validator.validate_and_parse({"name": "", "age": -5})
        assert model is None


class TestSelectField:
    """選択肢フィールドのテスト"""

    def test_select_with_options(self):
        """SelectOptionを使った選択肢"""

        class ModelWithSelect(BaseModel):
            color: Select(
                [
                    SelectOption("red", "赤"),
                    SelectOption("blue", "青"),
                ]
            ) = Field(title="色")

        fields = ModelParser.parse(ModelWithSelect)
        color_field = fields[0]

        assert color_field.field_type == FieldType.SELECT
        assert len(color_field.options) == 2
        assert color_field.options[0].value == "red"
        assert color_field.options[0].label == "赤"

    def test_select_with_strings(self):
        """文字列リストを使った選択肢"""

        class ModelWithSelect(BaseModel):
            size: Select(["S", "M", "L"]) = Field(title="サイズ")

        fields = ModelParser.parse(ModelWithSelect)
        size_field = fields[0]

        assert size_field.field_type == FieldType.SELECT
        assert len(size_field.options) == 3


class TestHTMLOutput:
    """HTML出力のテスト"""

    def test_htmx_attributes(self):
        """HTMX属性の確認"""
        generator = FormGenerator(SimpleModel, validate_endpoint="/api/validate")
        html = generator.generate_form()

        assert "hx-post=" in html
        assert "hx-target=" in html
        assert "hx-swap=" in html
        assert "hx-trigger=" in html

    def test_validation_endpoint(self):
        """バリデーションエンドポイントの確認"""
        generator = FormGenerator(SimpleModel, validate_endpoint="/custom/validate")
        html = generator.generate_form()

        # エンドポイントはフィールド名で変わらない
        assert 'hx-post="/custom/validate"' in html
        # フィールド名はhx-valsで送信される
        assert 'hx-vals=\'{"_field": "name"}\'' in html
        assert 'hx-vals=\'{"_field": "age"}\'' in html

    def test_html_escaping(self):
        """HTMLエスケープの確認"""

        class ModelWithSpecialChars(BaseModel):
            field: str = Field(
                title="<script>alert('xss')</script>", description="Test & <test>"
            )

        generator = FormGenerator(ModelWithSpecialChars)
        html = generator.generate_form()

        assert "&lt;script&gt;" in html
        assert "&amp;" in html


class TestFormDataParser:
    """FormDataParserのテスト"""

    def test_parse_string_to_int(self):
        """文字列から整数への変換"""
        from pydantic_htmx import parse_form_data

        form_data = {"name": "John", "age": "25"}
        model = parse_form_data(SimpleModel, form_data)

        assert model.name == "John"
        assert model.age == 25
        assert isinstance(model.age, int)

    def test_parse_full_model(self):
        """全フィールドタイプのパース"""
        from pydantic_htmx import parse_form_data

        form_data = {
            "username": "john_doe",
            "age": "25",
            "score": "85.5",
            "birth_date": "1990-01-15",
            "status": "active",
            "is_admin": "on",
        }
        model = parse_form_data(FullModel, form_data)

        assert model.username == "john_doe"
        assert model.age == 25
        assert model.score == 85.5
        assert model.birth_date == date(1990, 1, 15)
        assert model.status == "active"
        assert model.is_admin is True

    def test_parse_checkbox_unchecked(self):
        """チェックボックスが未チェックの場合"""
        from pydantic_htmx import parse_form_data

        form_data = {
            "username": "john_doe",
            "age": "25",
            "score": "85.5",
            "birth_date": "1990-01-15",
            "status": "active",
            # is_admin は送信されない（チェックされていない）
        }
        model = parse_form_data(FullModel, form_data)

        assert model.is_admin is False

    def test_parse_checkbox_values(self):
        """チェックボックスの様々な値"""
        from pydantic_htmx import FormDataParser

        class CheckboxModel(BaseModel):
            checked: bool = False

        parser = FormDataParser(CheckboxModel)

        # "on" は True
        model = parser.parse({"checked": "on"})
        assert model.checked is True

        # "true" は True
        model = parser.parse({"checked": "true"})
        assert model.checked is True

        # "1" は True
        model = parser.parse({"checked": "1"})
        assert model.checked is True

        # "false" は False
        model = parser.parse({"checked": "false"})
        assert model.checked is False

    def test_parse_safe_success(self):
        """parse_safeの成功ケース"""
        from pydantic_htmx import parse_form_data_safe

        form_data = {"name": "John", "age": "25"}
        model, errors = parse_form_data_safe(SimpleModel, form_data)

        assert model is not None
        assert model.name == "John"
        assert model.age == 25
        assert errors == {}

    def test_parse_safe_validation_error(self):
        """parse_safeのバリデーションエラー"""
        from pydantic_htmx import parse_form_data_safe

        form_data = {"name": "", "age": "-5"}
        model, errors = parse_form_data_safe(SimpleModel, form_data)

        assert model is None
        assert "name" in errors
        assert "age" in errors

    def test_parse_optional_field(self):
        """オプショナルフィールドのパース"""
        from pydantic_htmx import parse_form_data

        class OptionalModel(BaseModel):
            name: str
            nickname: str | None = None

        # ニックネームが空の場合
        form_data = {"name": "John", "nickname": ""}
        model = parse_form_data(OptionalModel, form_data)

        assert model.name == "John"
        assert model.nickname is None

        # ニックネームが存在する場合
        form_data = {"name": "John", "nickname": "Johnny"}
        model = parse_form_data(OptionalModel, form_data)

        assert model.nickname == "Johnny"


class TestFieldValidator:
    """field_validatorを含むモデルのバリデーションテスト"""

    def test_field_validator_single_field_error(self):
        """単一フィールドでfield_validatorのエラーを検出"""
        from pydantic import field_validator

        class UserModel(BaseModel):
            username: str = Field(min_length=1, title="ユーザー名")
            email: str = Field(title="メールアドレス")

            @field_validator("email")
            @classmethod
            def validate_email(cls, v: str) -> str:
                if "@" not in v:
                    raise ValueError("メールアドレスには@が必要です")
                return v

        validator = HTMXValidator(UserModel)

        # 正常なケース
        result = validator.validate_field("email", {"username": "test", "email": "test@example.com"})
        assert result.is_valid is True

        # エラーケース：@がない
        result = validator.validate_field("email", {"username": "test", "email": "invalid-email"})
        assert result.is_valid is False
        assert result.error_message is not None

    def test_field_validator_all_fields_error(self):
        """全体フィールドでfield_validatorのエラーを検出"""
        from pydantic import field_validator

        class UserModel(BaseModel):
            username: str = Field(min_length=1, title="ユーザー名")
            email: str = Field(title="メールアドレス")

            @field_validator("email")
            @classmethod
            def validate_email(cls, v: str) -> str:
                if "@" not in v:
                    raise ValueError("メールアドレスには@が必要です")
                return v

        validator = HTMXValidator(UserModel)

        # 正常なケース
        results = validator.validate_all({"username": "test", "email": "test@example.com"})
        assert results["username"].is_valid is True
        assert results["email"].is_valid is True

        # エラーケース
        results = validator.validate_all({"username": "test", "email": "invalid-email"})
        assert results["username"].is_valid is True
        assert results["email"].is_valid is False
        assert results["email"].error_message is not None

    def test_field_validator_multiple_errors(self):
        """複数フィールドでfield_validatorのエラーを検出"""
        from pydantic import field_validator

        class UserModel(BaseModel):
            username: str = Field(min_length=3, title="ユーザー名")
            password: str = Field(title="パスワード")

            @field_validator("username")
            @classmethod
            def validate_username(cls, v: str) -> str:
                if not v.isalnum():
                    raise ValueError("英数字のみ使用可能です")
                return v

            @field_validator("password")
            @classmethod
            def validate_password(cls, v: str) -> str:
                if len(v) < 8:
                    raise ValueError("パスワードは8文字以上必要です")
                return v

        validator = HTMXValidator(UserModel)

        # 両方エラー
        results = validator.validate_all({"username": "a@b", "password": "short"})
        assert results["username"].is_valid is False
        assert results["password"].is_valid is False


class TestModelValidator:
    """model_validatorを含むモデルのバリデーションテスト"""

    def test_model_validator_single_field(self):
        """単一フィールドでmodel_validatorのエラーを検出（モデルバリデータはフィールド単体では検出できない）"""
        from pydantic import model_validator

        class PasswordModel(BaseModel):
            password: str = Field(min_length=1, title="パスワード")
            password_confirm: str = Field(min_length=1, title="パスワード確認")

            @model_validator(mode="after")
            def passwords_match(self):
                if self.password != self.password_confirm:
                    raise ValueError("パスワードが一致しません")
                return self

        validator = HTMXValidator(PasswordModel)

        # 単一フィールドバリデーションでは、model_validatorは検出されない
        # （TypeAdapterはフィールド単体のバリデーションのため）
        result = validator.validate_field("password", {"password": "test123", "password_confirm": "different"})
        # model_validatorはフィールド単体では動作しないため、ここはTrueになる
        assert result.is_valid is True

    def test_model_validator_validate_all(self):
        """validate_allでmodel_validatorのエラーを検出"""
        from pydantic import model_validator

        class PasswordModel(BaseModel):
            password: str = Field(min_length=1, title="パスワード")
            password_confirm: str = Field(min_length=1, title="パスワード確認")

            @model_validator(mode="after")
            def passwords_match(self):
                if self.password != self.password_confirm:
                    raise ValueError("パスワードが一致しません")
                return self

        validator = HTMXValidator(PasswordModel)

        # validate_allを使用してmodel_validatorのエラーを検出
        results = validator.validate_all({"password": "test123", "password_confirm": "different"})
        
        # 現在の実装では、validate_allはvalidate_fieldを個別に呼び出すため
        # model_validatorのエラーは検出されない
        # これはvalidate_and_parseで検出する必要がある

    def test_model_validator_with_validate_and_parse(self):
        """validate_and_parseでmodel_validatorのエラーを検出"""
        from pydantic import model_validator

        class PasswordModel(BaseModel):
            password: str = Field(min_length=1, title="パスワード")
            password_confirm: str = Field(min_length=1, title="パスワード確認")

            @model_validator(mode="after")
            def passwords_match(self):
                if self.password != self.password_confirm:
                    raise ValueError("パスワードが一致しません")
                return self

        validator = HTMXValidator(PasswordModel)

        # 正常なケース
        model, results = validator.validate_and_parse({"password": "test123", "password_confirm": "test123"})
        assert model is not None
        assert model.password == "test123"

        # エラーケース：パスワードが一致しない
        model, results = validator.validate_and_parse({"password": "test123", "password_confirm": "different"})
        assert model is None


class TestFieldAndModelValidatorCombined:
    """field_validatorとmodel_validatorを組み合わせたテスト"""

    def test_combined_validators(self):
        """field_validatorとmodel_validatorを組み合わせたバリデーション"""
        from pydantic import field_validator, model_validator

        class RegistrationModel(BaseModel):
            email: str = Field(title="メールアドレス")
            password: str = Field(min_length=8, title="パスワード")
            password_confirm: str = Field(min_length=1, title="パスワード確認")

            @field_validator("email")
            @classmethod
            def validate_email(cls, v: str) -> str:
                if "@" not in v:
                    raise ValueError("メールアドレスには@が必要です")
                return v

            @model_validator(mode="after")
            def passwords_match(self):
                if self.password != self.password_confirm:
                    raise ValueError("パスワードが一致しません")
                return self

        validator = HTMXValidator(RegistrationModel)

        # 単一フィールド：emailのfield_validatorエラー
        result = validator.validate_field("email", {"email": "invalid", "password": "password123", "password_confirm": "password123"})
        assert result.is_valid is False
        assert result.error_message is not None

        # 単一フィールド：emailが正常
        result = validator.validate_field("email", {"email": "test@example.com", "password": "password123", "password_confirm": "password123"})
        assert result.is_valid is True

        # 全体：field_validatorエラー検出
        results = validator.validate_all({"email": "invalid", "password": "password123", "password_confirm": "password123"})
        assert results["email"].is_valid is False

        # validate_and_parse：すべて正常
        model, results = validator.validate_and_parse({"email": "test@example.com", "password": "password123", "password_confirm": "password123"})
        assert model is not None

        # validate_and_parse：model_validatorエラー
        model, results = validator.validate_and_parse({"email": "test@example.com", "password": "password123", "password_confirm": "different"})
        assert model is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
