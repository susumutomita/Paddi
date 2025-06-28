#!/bin/bash
set -e

# 色付きの出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# バナー表示
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🚀 Paddi Demo Environment Deployment${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 引数処理
ENVIRONMENT="${1:-demo}"
AUTO_APPROVE="${2:-}"

# ディレクトリ移動
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/../environments/$ENVIRONMENT"

echo -e "${YELLOW}📁 環境: $ENVIRONMENT${NC}"
echo -e "${YELLOW}📍 作業ディレクトリ: $(pwd)${NC}"
echo ""

# terraform.tfvarsの存在確認
if [ ! -f "terraform.tfvars" ]; then
    echo -e "${RED}❌ エラー: terraform.tfvars が見つかりません${NC}"
    echo -e "${YELLOW}💡 ヒント: terraform.tfvars.example をコピーして設定してください:${NC}"
    echo -e "   cp terraform.tfvars.example terraform.tfvars"
    echo -e "   vim terraform.tfvars  # project_id を設定"
    exit 1
fi

# プロジェクトID取得
PROJECT_ID=$(grep -E '^project_id\s*=' terraform.tfvars | sed 's/.*=\s*"\(.*\)"/\1/')
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ エラー: project_id が設定されていません${NC}"
    exit 1
fi

echo -e "${GREEN}✅ プロジェクトID: $PROJECT_ID${NC}"
echo ""

# gcloud認証確認
echo -e "${BLUE}🔐 認証状態を確認中...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" > /dev/null 2>&1; then
    echo -e "${RED}❌ エラー: gcloud認証が必要です${NC}"
    echo -e "${YELLOW}以下のコマンドを実行してください:${NC}"
    echo -e "   gcloud auth login"
    echo -e "   gcloud config set project $PROJECT_ID"
    exit 1
fi

# プロジェクト設定
gcloud config set project "$PROJECT_ID" 2>/dev/null

# 必要なAPIを有効化
echo -e "${BLUE}🔧 必要なAPIを有効化中...${NC}"
APIS=(
    "compute.googleapis.com"
    "storage.googleapis.com"
    "iam.googleapis.com"
    "aiplatform.googleapis.com"
    "cloudscheduler.googleapis.com"
    "pubsub.googleapis.com"
    "securitycenter.googleapis.com"
)

for api in "${APIS[@]}"; do
    echo -n "  - $api ... "
    if gcloud services enable "$api" --project="$PROJECT_ID" 2>/dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}スキップ${NC}"
    fi
done
echo ""

# Terraform初期化
echo -e "${BLUE}🔄 Terraformを初期化中...${NC}"
terraform init -upgrade

# Terraform計画
echo -e "${BLUE}📋 実行計画を作成中...${NC}"
terraform plan -out=tfplan

# 確認
if [ "$AUTO_APPROVE" != "-auto-approve" ]; then
    echo ""
    echo -e "${YELLOW}⚠️  上記のリソースが作成されます。続行しますか？${NC}"
    echo -e "${YELLOW}   (yes/no):${NC} \c"
    read -r response
    if [[ ! "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        echo -e "${RED}❌ デプロイをキャンセルしました${NC}"
        rm -f tfplan
        exit 1
    fi
fi

# Terraform適用
echo ""
echo -e "${BLUE}🚀 リソースを作成中...${NC}"
START_TIME=$(date +%s)
terraform apply tfplan
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# 結果表示
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ デモ環境構築完了！（所要時間: ${DURATION}秒）${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 出力値取得
echo -e "${BLUE}📊 環境情報:${NC}"
echo -e "  プロジェクトID: $(terraform output -raw project_id)"
echo -e "  Paddiサービスアカウント: $(terraform output -raw paddi_sa_email)"
echo -e "  公開バケットURL: $(terraform output -raw public_bucket_url)"
echo ""

# 環境変数設定
echo -e "${BLUE}🔧 環境変数を設定:${NC}"
export PROJECT_ID=$(terraform output -raw project_id)
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/paddi-sa-key.json"

echo "export PROJECT_ID=$PROJECT_ID"
echo "export GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS"
echo ""

# Paddi実行方法
echo -e "${YELLOW}🔍 Paddiで脆弱性をスキャン:${NC}"
echo -e "   cd $(dirname $(dirname $(dirname $SCRIPT_DIR)))"
echo -e "   python main.py audit --project-id $PROJECT_ID"
echo ""

echo -e "${YELLOW}🗑️  環境を削除する場合:${NC}"
echo -e "   cd $SCRIPT_DIR/../environments/$ENVIRONMENT"
echo -e "   terraform destroy -auto-approve"
echo ""

# 脆弱性サマリー表示
if [ -f "vulnerability-summary.json" ]; then
    echo -e "${RED}⚠️  作成された脆弱性（デモ用）:${NC}"
    jq -r '.iam_vulnerabilities[] | "  - \(.type): \(.description)"' vulnerability-summary.json
    jq -r '.storage_vulnerabilities[] | "  - \(.type): \(.description)"' vulnerability-summary.json
fi

# クリーンアップ
rm -f tfplan

echo ""
echo -e "${GREEN}👍 準備完了！ハッカソンでのデモをお楽しみください！${NC}"