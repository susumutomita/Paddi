#!/bin/bash
set -e

# 色付きの出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# バナー表示
echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${RED}🗑️  Paddi Demo Environment Destruction${NC}"
echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
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

# Terraformステートの存在確認
if [ ! -f "terraform.tfstate" ]; then
    echo -e "${YELLOW}⚠️  警告: terraform.tfstate が見つかりません${NC}"
    echo -e "${YELLOW}   既に環境が削除されている可能性があります${NC}"
    exit 0
fi

# 現在のリソース確認
echo -e "${BLUE}📊 削除予定のリソース:${NC}"
terraform state list 2>/dev/null || true
echo ""

# プロジェクトID取得
PROJECT_ID=$(terraform output -raw project_id 2>/dev/null || echo "不明")
echo -e "${YELLOW}🎯 プロジェクトID: $PROJECT_ID${NC}"
echo ""

# 確認
if [ "$AUTO_APPROVE" != "-auto-approve" ]; then
    echo -e "${RED}⚠️  警告: この操作はすべてのリソースを削除します！${NC}"
    echo -e "${RED}   本当に続行しますか？${NC}"
    echo -e "${RED}   'yes' と入力して確認:${NC} \c"
    read -r response
    if [ "$response" != "yes" ]; then
        echo -e "${YELLOW}❌ 削除をキャンセルしました${NC}"
        exit 1
    fi
fi

# バックアップ作成
echo -e "${BLUE}💾 状態ファイルをバックアップ中...${NC}"
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp terraform.tfstate* "$BACKUP_DIR/" 2>/dev/null || true
cp *.json "$BACKUP_DIR/" 2>/dev/null || true
echo -e "${GREEN}✅ バックアップ作成: $BACKUP_DIR${NC}"
echo ""

# Terraform destroy実行
echo -e "${RED}🗑️  リソースを削除中...${NC}"
START_TIME=$(date +%s)

if [ "$AUTO_APPROVE" == "-auto-approve" ]; then
    terraform destroy -auto-approve
else
    terraform destroy
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# クリーンアップ
echo ""
echo -e "${BLUE}🧹 ローカルファイルをクリーンアップ中...${NC}"

# 生成されたファイルを削除
rm -f paddi-sa-key.json
rm -f vulnerability-summary.json
rm -f .terraform.lock.hcl
rm -rf .terraform/

echo -e "${GREEN}✅ クリーンアップ完了${NC}"

# 結果表示
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ 環境削除完了！（所要時間: ${DURATION}秒）${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 次のステップ
echo -e "${BLUE}📝 次のステップ:${NC}"
echo -e "  - 再度デプロイする場合: ./deploy.sh $ENVIRONMENT"
echo -e "  - バックアップ確認: ls -la $BACKUP_DIR"
echo ""

echo -e "${GREEN}👍 お疲れ様でした！${NC}"