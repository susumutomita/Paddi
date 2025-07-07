"""Ollama integration for security analysis."""

import json
import logging
from typing import Any, Dict, List

import requests

from app.common.models import SecurityFinding

logger = logging.getLogger(__name__)


class OllamaSecurityAnalyzer:
    """Ollamaを使用したセキュリティ分析クラス"""

    def __init__(self, model: str = "gemma3:latest", endpoint: str = "http://localhost:11434"):
        self.model = model
        self.endpoint = endpoint
        self._verify_connection()

    def _verify_connection(self) -> None:
        """Ollamaへの接続を確認"""
        try:
            response = requests.get(f"{self.endpoint}/api/tags", timeout=5)
            response.raise_for_status()

            # モデルが存在するか確認
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]

            if self.model not in model_names:
                logger.warning("Model %s not found. Attempting to pull...", self.model)
                self._pull_model()

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to connect to Ollama at {self.endpoint}: {e}") from e

    def _pull_model(self) -> None:
        """Ollamaモデルをダウンロード"""
        try:
            response = requests.post(
                f"{self.endpoint}/api/pull", json={"name": self.model}, timeout=30
            )
            response.raise_for_status()
            logger.info("Successfully pulled model: %s", self.model)
        except Exception as e:
            logger.error("Failed to pull model %s: %s", self.model, e)
            raise

    def analyze_security_risks(self, configuration: Dict[str, Any]) -> List[SecurityFinding]:
        """Ollamaを使用してセキュリティ分析を実行"""
        prompt = self._build_analysis_prompt(configuration)

        try:
            response = requests.post(
                f"{self.endpoint}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.2, "top_p": 0.8},
                },
                timeout=60,
            )
            response.raise_for_status()

            result = response.json()
            return self._parse_ollama_response(result["response"])

        except Exception as e:
            logger.error("Ollama analysis failed: %s", e)
            raise

    def _build_analysis_prompt(self, configuration: Dict[str, Any]) -> str:
        """分析用のプロンプトを構築"""
        findings = configuration.get("scc_findings", [])
        iam_policies = configuration.get("iam_policies", [])
        cloud_type = "GCP"

        prompt = f"""
あなたはクラウドセキュリティの専門家です。以下のクラウド構成情報を分析し、セキュリティリスクを特定してください。

クラウドタイプ: {cloud_type}

発見事項:
{json.dumps(findings, ensure_ascii=False, indent=2)}

IAMポリシー:
{json.dumps(iam_policies, ensure_ascii=False, indent=2)}

以下の形式でJSONレスポンスを返してください:
[
  {{
    "title": "リスクのタイトル",
    "severity": "HIGH/MEDIUM/LOW",
    "explanation": "リスクの詳細説明",
    "recommendation": "推奨される対処法"
  }}
]

重要: 必ず有効なJSONフォーマットで返答してください。
"""

        return prompt

    def _parse_ollama_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Ollamaのレスポンスをパース"""
        try:
            # レスポンスからJSON部分を抽出
            import re

            json_match = re.search(r"\[[\s\S]*\]", response_text)
            if json_match:
                json_str = json_match.group(0)
                results = json.loads(json_str)

                # 結果の検証と正規化
                findings = []
                for result in results:
                    finding = SecurityFinding(
                        title=result.get("title", "不明なリスク"),
                        severity=result.get("severity", "MEDIUM").upper(),
                        explanation=result.get("explanation", "詳細情報なし"),
                        recommendation=result.get("recommendation", "推奨事項なし"),
                    )
                    findings.append(finding)

                return findings
            logger.error("No JSON found in response: %s", response_text)
            return self._create_fallback_response()

        except json.JSONDecodeError as e:
            logger.error("Failed to parse Ollama response: %s", e)
            return self._create_fallback_response()

    def _create_fallback_response(self) -> List[Dict[str, Any]]:
        """パースエラー時のフォールバックレスポンス"""
        return [
            SecurityFinding(
                title="分析エラー",
                severity="MEDIUM",
                explanation="Ollamaからの応答を正しく解析できませんでした。",
                recommendation="ログを確認し、Ollama設定を見直してください。",
            )
        ]
