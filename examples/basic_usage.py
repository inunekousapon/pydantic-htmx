"""
pydantic-htmx の使用例
"""

from datetime import date
from typing import Literal, Annotated

from pydantic import BaseModel, Field

from pydantic_htmx import FormGenerator, SelectOption
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


if __name__ == "__main__":
    main()
