# pydantic-htmx

PydanticスキーマからHTMXフォームを自動生成するライブラリ

## 特徴

- 🚀 **Pydanticモデルからフォーム自動生成** - クラス定義だけでHTMLフォームを生成
- ✅ **バリデーション連動** - Pydanticのバリデーションとhtmxのリアルタイムバリデーションが完全連動
- 🎨 **多様なフィールドタイプ** - 文字列、数値、日付、選択肢、チェックボックスに対応
- 📦 **最小限の依存** - pydanticとhtmx以外の依存なし

## インストール

```bash
uv add pydantic-htmx
```

## クイックスタート

### 基本的な使い方

```python
from datetime import date
from typing import Literal, Annotated
from pydantic import BaseModel, Field
from pydantic_htmx import FormGenerator

# Pydanticモデルを定義
class UserForm(BaseModel):
    username: Annotated[str, Field(
        min_length=3,
        max_length=20,
        title="ユーザー名",
        description="3〜20文字で入力してください"
    )]
    
    email: Annotated[str, Field(
        pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$',
        title="メールアドレス"
    )]
    
    age: Annotated[int, Field(
        ge=18,
        title="年齢",
        description="18歳以上である必要があります"
    )]
    
    gender: Literal["male", "female", "other"] = Field(title="性別")
    
    birth_date: date = Field(title="生年月日")
    
    agree_terms: bool = Field(default=False, title="利用規約に同意する")

# フォームを生成
generator = FormGenerator(UserForm, validate_endpoint="/api/validate")

# HTMLを取得
html = generator.generate_form(
    action="/api/submit",
    submit_text="登録する"
)

print(html)
```

### 生成されるHTML

```html
<form id="userform-form" hx-post="/api/submit" hx-target="#response" hx-swap="innerHTML" class="pydantic-htmx-form">
  <div class="form-field" id="field-username">
    <label for="username">ユーザー名 <span class='required'>*</span></label>
    <input type="text" id="username" name="username" required minlength="3" maxlength="20"
           hx-post="/api/validate/username" hx-trigger="blur" hx-target="#username-error" hx-swap="innerHTML">
    <small class="field-description">3〜20文字で入力してください</small>
    <div class="error-message" id="username-error"></div>
  </div>
  <!-- 他のフィールド... -->
  <div class="form-actions">
    <button type="submit">登録する</button>
  </div>
</form>
```

## 対応フィールドタイプ

### 文字列 (str)

```python
username: str = Field(
    min_length=3,
    max_length=20,
    pattern=r'^[a-zA-Z0-9_]+$'
)
```

### 数値 (int, float)

```python
age: int = Field(ge=0, le=120)
price: float = Field(ge=0)
```

### 日付 (date)

```python
from datetime import date
birth_date: date = Field(title="生年月日")
```

### 選択肢 (Literal または Select)

```python
from typing import Literal

# Literalを使う方法
status: Literal["active", "inactive", "pending"] = Field(title="ステータス")

# Selectを使う方法（カスタムラベル付き）
from pydantic_htmx import SelectOption
from pydantic_htmx.field_types import Select

color: Select([
    SelectOption("red", "赤色"),
    SelectOption("blue", "青色"),
    SelectOption("green", "緑色"),
]) = Field(title="色")
```

### チェックボックス (bool)

```python
agree_terms: bool = Field(default=False, title="利用規約に同意する")
```

## バリデーション

### フィールド単位のバリデーション

```python
generator = FormGenerator(UserForm)
validator = generator.get_validator()

# 単一フィールドのバリデーション
result = validator.validate_field("username", "john_doe")
print(result.is_valid)  # True
print(result.to_html())  # <span class="valid">✓</span>

result = validator.validate_field("username", "ab")
print(result.is_valid)  # False
print(result.to_html())  # <span class="error">この値は短すぎます</span>
```

### 全フィールドのバリデーション

```python
data = {
    "username": "john_doe",
    "email": "john@example.com",
    "age": 25,
    # ...
}

results = validator.validate_all(data)
for field_name, result in results.items():
    print(f"{field_name}: {result.is_valid}")
```

### バリデーション＋パース

```python
model, results = validator.validate_and_parse(data)
if model:
    # バリデーション成功 - modelはPydanticモデルのインスタンス
    print(model.username)
else:
    # バリデーション失敗
    for field_name, result in results.items():
        if not result.is_valid:
            print(f"{field_name}: {result.error_message}")
```

## POSTリクエストからPydanticモデルへの変換

HTMXフォームから送信されたPOSTデータを直接Pydanticモデルに変換できます。

### parse_form_data を使用

```python
from pydantic_htmx import parse_form_data

# フォームから送信されたデータ（文字列の辞書）
form_data = {
    "username": "john_doe",
    "age": "25",           # 文字列として送信される
    "birth_date": "1998-05-15",  # ISO形式の日付
    "agree_terms": "on",   # チェックボックスがONの場合
}

# Pydanticモデルに変換（型は自動変換される）
user = parse_form_data(UserForm, form_data)

print(user.username)    # "john_doe"
print(user.age)         # 25 (int型)
print(user.birth_date)  # date(1998, 5, 15)
print(user.agree_terms) # True (bool型)
```

### parse_form_data_safe を使用（エラーハンドリング）

```python
from pydantic_htmx import parse_form_data_safe

form_data = {
    "username": "ab",       # 短すぎる
    "age": "15",            # 18未満
    "birth_date": "invalid",
}

user, errors = parse_form_data_safe(UserForm, form_data)

if user:
    print(f"成功: {user}")
else:
    print("バリデーションエラー:")
    for field_name, error_msg in errors.items():
        print(f"  {field_name}: {error_msg}")
    # username: この値は短すぎます
    # age: この値は18以上である必要があります
    # birth_date: 有効な日付を入力してください
```

### チェックボックスの処理

チェックボックスは未チェック時にフォームデータとして送信されません。
`parse_form_data` はこれを自動的に `False` として処理します。

```python
# チェックボックスがチェックされていない場合
form_data = {"name": "John"}  # is_admin は送信されない

user = parse_form_data(UserForm, form_data)
print(user.is_admin)  # False
```

## サーバー統合例

### FastAPIとの統合

```python
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from pydantic_htmx import FormGenerator, parse_form_data_safe

app = FastAPI()

class ContactForm(BaseModel):
    name: str = Field(min_length=1, title="お名前")
    email: str = Field(title="メールアドレス")
    message: str = Field(min_length=10, title="メッセージ")

generator = FormGenerator(ContactForm, validate_endpoint="/validate")

@app.get("/", response_class=HTMLResponse)
async def index():
    return generator.generate_full_html(
        title="お問い合わせ",
        action="/submit"
    )

@app.post("/validate/{field_name}", response_class=HTMLResponse)
async def validate_field(field_name: str, request: Request):
    form_data = await request.form()
    value = form_data.get(field_name)
    validator = generator.get_validator()
    result = validator.validate_field(field_name, value)
    return result.to_html()

@app.post("/submit", response_class=HTMLResponse)
async def submit(request: Request):
    # フォームデータを取得
    form_data = await request.form()
    form_dict = dict(form_data)
    
    # parse_form_data_safe でPydanticモデルに変換
    model, errors = parse_form_data_safe(ContactForm, form_dict)
    
    if model:
        # バリデーション成功 - modelはContactFormのインスタンス
        print(f"受信: {model.name}, {model.email}")
        return '<div class="success">送信しました！</div>'
    else:
        # バリデーション失敗
        error_html = "<ul>"
        for field_name, error_msg in errors.items():
            error_html += f"<li>{field_name}: {error_msg}</li>"
        error_html += "</ul>"
        return f'<div class="errors">{error_html}</div>'
```

## 完全なHTMLドキュメント生成

```python
html = generator.generate_full_html(
    title="ユーザー登録",
    action="/api/register",
    submit_text="登録",
    include_htmx=True  # htmx.jsのCDNリンクを含める
)

# ファイルに保存
with open("form.html", "w") as f:
    f.write(html)
```

## カスタムCSS

```python
# デフォルトのCSSを取得
css = generator.generate_css()

# 独自のスタイルを追加する場合は、CSSをカスタマイズしてください
```

## ライセンス

MIT License
