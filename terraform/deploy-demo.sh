#!/bin/bash
# 簡易デプロイラッパー
chmod +x terraform/scripts/deploy.sh
exec terraform/scripts/deploy.sh demo "$@"