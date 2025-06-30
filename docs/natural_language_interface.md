# Natural Language Interface for Paddi

Paddi now supports a gemini-cli style natural language interface that allows you to interact with the security audit system using natural language commands in both Japanese and English.

## Usage

### Interactive Mode

Start the interactive natural language interface:

```bash
python main.py natural
```

Or directly launch the autonomous CLI:

```bash
python -m app.agents.autonomous_cli
```

### One-Shot Mode

Execute a single natural language command:

```bash
python main.py "GCPプロジェクト example-123 のセキュリティを監査して"
```

## Supported Commands

### Natural Language Examples

- **Japanese:**
  - `GCPプロジェクト example-123 のセキュリティを監査して`
  - `プロジェクトの構成情報を収集して`
  - `セキュリティリスクを分析して`
  - `監査レポートを作成して`

- **English:**
  - `audit security for project test-project`
  - `collect configuration data`
  - `analyze security risks`
  - `generate audit report`

### Special Commands (Interactive Mode)

- `/exit` - Exit the session
- `/clear` - Clear the screen
- `/help` - Show help information
- `/model <name>` - Switch AI model
- `/history` - Show conversation history
- `/reset` - Reset conversation context

## Features

### Context Preservation
The interface maintains conversation context, allowing you to refer to previous commands and results:

```
paddi> GCPプロジェクト my-project のセキュリティを監査して
✅ 監査が完了しました...

paddi> 詳細なレポートを作成して
✅ レポートを作成しました...
```

### Intelligent Command Parsing
The system automatically detects:
- Project IDs from natural language
- Mock vs. real data preferences
- Command intent (audit, collect, analyze, report)

### Error Handling
Clear error messages in Japanese/English when commands fail:

```
paddi> 不明なコマンド
❌ エラー: コマンドを理解できませんでした
```

## Integration with Existing CLI

The natural language interface seamlessly integrates with the existing Fire-based CLI. You can still use traditional commands:

```bash
# Traditional command
python main.py audit --project-id=example-123

# Natural language equivalent
python main.py "audit project example-123"
```

## Architecture

The natural language interface consists of:

1. **AutonomousCLI** - Main interface class
2. **NaturalLanguageParser** - Parses natural language to structured commands
3. **ConversationContext** - Maintains session state
4. **SpecialCommand** - Handles special commands like /exit, /help

The implementation follows SOLID principles with clear separation of concerns and high test coverage.