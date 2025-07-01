# 高度なエラーハンドリングと自己修復機能

Paddiの自動エラー回復システムは、エラーを自動的に分析し、可能な限り自己修復を試みます。

## 🚀 機能概要

### 1. インテリジェントエラーハンドラー
- エラーの自動分類（API制限、権限、ネットワーク、リソースなど）
- 重要度の判定（CRITICAL、HIGH、MEDIUM、LOW）
- 根本原因の分析

### 2. 自己修復メカニズム
- 複数の回復戦略を自動的に試行
- 成功した解決策の学習と再利用
- 代替手段の提案

### 3. 特定エラーハンドラー
- **APILimitHandler**: API制限エラーの処理
- **PermissionHandler**: 権限エラーの処理とガイダンス
- **NetworkErrorHandler**: ネットワークエラーの診断
- **ResourceErrorHandler**: リソース不足の最適化

## 📋 使用方法

### 基本的な使用例

```python
from app.error_handling.decorators import with_self_healing
from app.memory.context_manager import ContextualMemory

# メモリマネージャーの初期化
memory = ContextualMemory(project_id="my-project")

# デコレーターを使用した自動回復
@with_self_healing(memory_manager=memory, max_retries=3)
async def my_function():
    # エラーが発生する可能性のある処理
    return await risky_operation()
```

### 手動でのエラーハンドリング

```python
from app.error_handling.intelligent_handler import SelfHealingSystem, ExecutionContext

healing_system = SelfHealingSystem()

async def my_operation():
    return await some_api_call()

context = ExecutionContext(operation=my_operation)

try:
    result = await my_operation()
except Exception as e:
    # 自己修復を試みる
    result = await healing_system.handle_error(e, context)
```

### 特定のエラータイプの処理

```python
from app.error_handling.specific_handlers import ErrorHandlerRegistry

registry = ErrorHandlerRegistry()

# API制限エラーの処理
error = Exception("429 Rate limit exceeded")
guidance = await registry.handle_specific_error(
    "api_limit", error, {"service": "gemini"}
)
print(guidance)
# 出力: {"action": "retry", "wait_time": 60, ...}
```

## 🔧 デコレーター

### @with_self_healing
完全な自己修復機能を追加

```python
@with_self_healing(
    memory_manager=memory,    # 学習用メモリ（オプション）
    max_retries=3,           # 最大リトライ回数
    error_types=[ValueError], # 処理するエラータイプ（Noneは全て）
    fallback=my_fallback     # 全て失敗時のフォールバック関数
)
async def protected_function():
    pass
```

### @auto_retry
シンプルな自動リトライ

```python
@auto_retry(
    max_attempts=3,
    delay=1.0,              # 初期待機時間（秒）
    backoff=2.0,            # 待機時間の増加率
    exceptions=(Exception,)  # キャッチする例外
)
async def retryable_function():
    pass
```

### @handle_specific_errors
特定のエラーに対するカスタムハンドラー

```python
def handle_api_error(e):
    return {"error": "API unavailable", "retry_later": True}

@handle_specific_errors({
    APIError: handle_api_error,
    NetworkError: lambda e: None  # エラーを無視
})
def my_function():
    pass
```

## 🎯 エラーパターンと対処法

### API制限エラー
```python
# 自動的に以下を実行:
# 1. Retry-Afterヘッダーの確認
# 2. 適切な待機時間の計算
# 3. 代替APIエンドポイントの提案
```

### 権限エラー
```python
# 自動的に生成:
# - 必要な権限の特定
# - 修正用のgcloudコマンド
# - 管理者への連絡手順
```

### ネットワークエラー
```python
# 自動診断:
# - 接続性チェック
# - プロキシ設定の確認
# - DNS問題の検出
```

### リソースエラー
```python
# 最適化戦略:
# - データの分割処理
# - メモリ/キャッシュのクリア
# - リソース使用量の監視
```

## 📊 統計情報の取得

```python
# 修復統計の取得
stats = healing_system.get_healing_statistics()
print(f"成功率: {stats['success_rate']:.1%}")
print(f"カテゴリ別: {stats['by_category']}")
```

## 🔄 既存コードへの統合

### CLIコマンドの強化

```python
from app.error_handling.integration_example import integrate_error_handling_into_cli

# CLIに自己修復機能を追加
integrate_error_handling_into_cli()
```

### カスタムコレクターの作成

```python
from app.error_handling.integration_example import ErrorAwareCollector

# エラー対応機能付きコレクター
collector = ErrorAwareCollector(project_id="my-project")
data = await collector.collect()  # 自動リトライ付き
```

## ⚙️ 設定

環境別の設定例:

```python
from app.error_handling.integration_example import get_error_handling_config

# 開発環境
config = get_error_handling_config("development")
# {"max_retries": 5, "retry_delay": 1.0, ...}

# 本番環境
config = get_error_handling_config("production")
# {"max_retries": 3, "retry_delay": 5.0, ...}
```

## 🧪 テスト

```bash
# エラーハンドリングのテストを実行
pytest app/tests/test_error_handling.py -v
```

## 📝 ベストプラクティス

1. **適切なエラータイプの選択**: 処理したいエラーのみをキャッチ
2. **フォールバックの実装**: 重要な処理には必ずフォールバックを用意
3. **ログの活用**: エラーと回復の過程を適切にログに記録
4. **学習の活用**: 同じエラーに対する過去の解決策を再利用
5. **リソースの監視**: リソース関連エラーの予防的な監視

## 🚨 注意事項

- 無限ループを防ぐため、最大リトライ回数を適切に設定
- センシティブ情報はログに含めない
- ネットワークエラーは一時的な場合が多いため、適切な待機時間を設定
- API制限は共有リソースのため、他のユーザーへの影響を考慮