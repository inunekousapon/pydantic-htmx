"""
pydantic-htmx の使用例
"""

from datetime import date
from typing import Literal, Annotated

from pydantic import BaseModel, Field

from pydantic_htmx import (
    FormGenerator,
    SelectOption,
    parse_form_data,
    parse_form_data_safe,
)
from pydantic_htmx.field_types import Select


# 基本的なモデル定義
class UserRegistration(BaseModel):
    """ユーザー登録フォーム"""

    username: Annotated[
        str,
        Field(
            min_length=3,
            max_length=20,
            title="ユーザー名",
            description="3〜20文字で入力してください",
        ),
    ]

    email: Annotated[
        str,
        Field(
            pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$",
            title="メールアドレス",
            description="有効なメールアドレスを入力してください",
        ),
    ]

    age: Annotated[
        int,
        Field(ge=18, le=120, title="年齢", description="18歳以上である必要があります"),
    ]

    # Literal型を使った選択肢
    gender: Literal["male", "female", "other"] = Field(
        title="性別", description="性別を選択してください"
    )

    # 日付フィールド
    birth_date: date = Field(title="生年月日", description="生年月日を入力してください")

    # チェックボックス
    agree_terms: bool = Field(
        default=False,
        title="利用規約に同意する",
        description="利用規約を読んで同意してください",
    )


# カスタム選択肢を使ったモデル
class ProductOrder(BaseModel):
    """商品注文フォーム"""

    product_name: str = Field(title="商品名", min_length=1)

    quantity: Annotated[
        int, Field(ge=1, le=100, title="数量", description="1〜100個まで注文できます")
    ]

    # Select関数を使った選択肢
    size: Select(
        [
            SelectOption("S", "Sサイズ"),
            SelectOption("M", "Mサイズ"),
            SelectOption("L", "Lサイズ"),
            SelectOption("XL", "XLサイズ"),
        ]
    ) = Field(title="サイズ")

    color: Select(["red", "blue", "green", "black", "white"]) = Field(
        title="色", description="お好みの色を選択してください"
    )

    price: Annotated[float, Field(ge=0, title="価格", description="税込価格")]

    gift_wrap: bool = Field(
        default=False,
        title="ギフトラッピング",
        description="ギフト用にラッピングしますか？",
    )

    delivery_date: date | None = Field(
        default=None,
        title="配達希望日",
        description="希望する配達日を選択してください（任意）",
    )


def main():
    """使用例のデモ"""

    # ユーザー登録フォームの生成
    print("=" * 60)
    print("ユーザー登録フォーム")
    print("=" * 60)

    user_form = FormGenerator(UserRegistration, validate_endpoint="/api/validate/user")

    # フォームHTMLを生成
    html = user_form.generate_form(action="/api/register", submit_text="登録する")
    print(html)
    print()

    # バリデーションのデモ
    print("=" * 60)
    print("バリデーションテスト")
    print("=" * 60)

    validator = user_form.get_validator()

    # 有効なデータ
    result = validator.validate_field("username", "john_doe")
    print(f"username='john_doe': {result.to_html()}")

    # 無効なデータ（短すぎる）
    result = validator.validate_field("username", "ab")
    print(f"username='ab': {result.to_html()}")

    # 年齢の検証
    result = validator.validate_field("age", 25)
    print(f"age=25: {result.to_html()}")

    result = validator.validate_field("age", 15)
    print(f"age=15: {result.to_html()}")

    print()

    # 商品注文フォームの生成
    print("=" * 60)
    print("商品注文フォーム")
    print("=" * 60)

    order_form = FormGenerator(ProductOrder, validate_endpoint="/api/validate/order")

    # 完全なHTMLドキュメントを生成
    full_html = order_form.generate_full_html(
        title="商品注文", action="/api/order", submit_text="注文する"
    )

    # ファイルに保存
    with open("order_form.html", "w", encoding="utf-8") as f:
        f.write(full_html)

    print("order_form.html に保存しました")
    print()

    # フィールド情報の表示
    print("=" * 60)
    print("フィールド情報")
    print("=" * 60)

    for field in order_form.get_fields():
        print(f"- {field.name}: {field.field_type.value}")
        print(f"  Title: {field.title}")
        print(f"  Required: {field.required}")
        if field.options:
            print(f"  Options: {[(o.value, o.label) for o in field.options]}")
        print()

    # POSTリクエストからPydanticモデルへの変換デモ
    print("=" * 60)
    print("フォームデータのパース（POSTリクエスト処理）")
    print("=" * 60)

    # 模擬的なフォームデータ（実際のWebフレームワークでは request.form 等から取得）
    form_data = {
        "username": "john_doe",
        "email": "john@example.com",
        "age": "25",  # 文字列で送信される
        "gender": "male",
        "birth_date": "1998-05-15",  # ISO形式の日付文字列
        "agree_terms": "on",  # チェックボックスがチェックされた場合
    }

    print(f"フォームデータ: {form_data}")
    print()

    # 方法1: parse_form_data を使用（例外がスローされる可能性あり）
    try:
        user = parse_form_data(UserRegistration, form_data)
        print("parse_form_data 成功:")
        print(f"  username: {user.username} (type: {type(user.username).__name__})")
        print(f"  email: {user.email}")
        print(f"  age: {user.age} (type: {type(user.age).__name__})")
        print(f"  gender: {user.gender}")
        print(
            f"  birth_date: {user.birth_date} (type: {type(user.birth_date).__name__})"
        )
        print(
            f"  agree_terms: {user.agree_terms} (type: {type(user.agree_terms).__name__})"
        )
    except Exception as e:
        print(f"エラー: {e}")
    print()

    # 方法2: parse_form_data_safe を使用（エラーを辞書で返す）
    print("parse_form_data_safe でバリデーションエラーを確認:")
    invalid_form_data = {
        "username": "ab",  # 短すぎる
        "email": "invalid-email",  # 不正な形式
        "age": "15",  # 18未満
        "gender": "male",
        "birth_date": "1998-05-15",
        # agree_terms は送信されない（チェックされていない）
    }
    print(f"フォームデータ: {invalid_form_data}")

    user, errors = parse_form_data_safe(UserRegistration, invalid_form_data)
    if user:
        print(f"成功: {user}")
    else:
        print("バリデーションエラー:")
        for field_name, error_msg in errors.items():
            print(f"  {field_name}: {error_msg}")


if __name__ == "__main__":
    main()
