# 実務データ検品・会計消込・数理最適化オープンワークベンチ & Unified MCP Server (`practical-data-tools`)

公開Web計算機ポータル（登録不要・外部送信ゼロ）: **https://awai-mm.github.io/practical-data-tools/**

- **Structured Agent Index (`/llms.txt`)**: https://awai-mm.github.io/practical-data-tools/llms.txt
- **Full Technical Spec (`/llms-full.txt`)**: https://awai-mm.github.io/practical-data-tools/llms-full.txt
- **A2A Agent Card (`/.well-known/agent.json`)**: https://awai-mm.github.io/practical-data-tools/.well-known/agent.json
- **OpenAPI 3.1 Schema (`/openapi.json`)**: https://awai-mm.github.io/practical-data-tools/openapi.json
- **Skill Guide (`/SKILL.md`)**: https://awai-mm.github.io/practical-data-tools/SKILL.md

## 1行で使える統合MCPサーバー (`mcp/mcp_server.py` — Python標準ライブラリ完結)

```json
{
  "mcpServers": {
    "awai-practical-data-tools": {
      "command": "python3",
      "args": ["mcp/mcp_server.py", "--stdio"]
    }
  }
}
```

### 搭載ツール一覧（JSON-RPC 2.0 `tools/list` / `tools/call`）

1. `repair_and_validate_structured_data` (**100%無料フックツール**): 壊れたJSON/辞書文字列（コードフェンス・末尾カンマ・シングルクォート・閉じ括弧欠落）の決定論的修復＆必須キー検証
2. `exact_decimal_and_crypto_unit_math` (**100%無料フックツール**): 50桁精度Decimal＆整数演算による Web3 (`wei`/`gwei`/`eth`/`usdc`)・Lightning (`msat`/`sat`/`btc`) 単位換算、端数ゼロ按分（最大剰余法）、bps手数料計算
3. `subset_sum_reconcile` (無料枠25件 / 大規模バッチは HTTP 402 `L402` Lightning & `x402` USDC 対応): 複数クレカ・銀行CSV・請求書のN対M部分和消込＋インボイス登録番号(`T+13桁`)検証＋弥生/freee/MF仕訳出力
4. `stochastic_inventory_cashflow_solve` (無料枠500パス / 深層シミュレーションは HTTP 402 対応): モンテカルロ法による在庫発注点 `(s, S)`・安全在庫・歩留まり・95% CVaR運転資金同時最適化ソルバー
5. `audit_smart_contract_invariants` (無料枠250行 / 深層監査は HTTP 402 対応): Solidity/Rust スマートコントラクトの4大脆弱性・形式的不変条件チェッカー（ERC4626インフレ・丸め方向流出・CEI再入・Oracle陳腐化/縮小キャスト）
6. `inspect_csv_integrity` (無料枠200行 / 大規模CSVは HTTP 402 対応): CSVスキーマ・文字化け(`U+FFFD`)・主キー重複・消費税8%/10%端数検品エンジン

## 収録スイート

1. **数理アルゴリズム・ソルバースイート (`docs/calculators/`, `docs/heavy/`)**
   - `ALGO-01`: 複数クレカ・銀行CSV・Amazon購入履歴・インボイス番号のN対M部分和消込＆弥生/freee/MF仕訳相互変換エンジン
   - `ALGO-02`: モンテカルロ法・確率的動的計画法による在庫発注点(s,S)・歩留まり・資金繰り(CCC)同時最適化ソルバー
   - `ALGO-03`: 経営・経理・EC実務の即答計算機スイート（インボイス端数逆算・損益分岐点・キャッシュランウェイ・安全在庫・ECモール粗利）
   - `ALGO-04`: 非同期競合・通貨端数保存則・スマートコントラクト形式的不変条件プローバー
2. **実務データ検品・クレンジング全10パッケージ (`docs/workbenches/`, `docs/downloads/`)**
   - `pkg-01`〜`pkg-10` の単一HTMLブラウザワークベンチ、Python標準ライブラリ完結CLI＆サンプルCSV ZIP、およびEPUB3実務ハンドブック
3. **Global English Micro-Tools 全12パッケージ (`docs/en/`)**
   - `en-pkg-01`〜`en-pkg-12` のブラウザワークベンチ＆CLIパッケージ
