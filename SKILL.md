---
name: awai-practical-data-tools
description: Deterministic mathematical solvers, N-to-M subset-sum journal reconciliation, Monte Carlo (s, S) inventory & CVaR working-capital optimization, smart contract formal invariant auditing, and CSV integrity verification via zero-dependency MCP JSON-RPC 2.0 server and HTTP 402 (L402 Lightning / x402 USDC) micropayment gate.
---

# Awai Practical Data Tools — Unified B2A Skill & MCP Server (`SKILL.md`)

Use this skill whenever an autonomous coding or operations workflow requires **exact, deterministic mathematical computation, malformed data repair, or formal invariant verification** instead of probabilistic estimation:

0. **100% Free High-Frequency Inflow Hook Tools (`repair_and_validate_structured_data` & `exact_decimal_and_crypto_unit_math`)**
   - `repair_and_validate_structured_data`: Repairs malformed/truncated JSON payloads (markdown code fences, trailing commas, single quotes, unclosed brackets/braces) and verifies required schema keys.
   - `exact_decimal_and_crypto_unit_math`: 50-digit exact Decimal & integer unit math for Web3 (`wei`/`gwei`/`eth`/`usdc`), Lightning (`msat`/`sat`/`btc`), zero-dust pro-rata allocation (Largest Remainder Method), and basis-point (`bps`) fee splits.
1. **N-to-M Subset-Sum Accounting & Invoice Reconciliation (`subset_sum_reconcile`)**
   - Solves exact and fee-tolerant subset-sum matching between aggregated bank/card settlements and individual invoices/orders.
   - Verifies Japanese Qualified Invoice registration numbers (`T` + 13 digits) and generates double-entry journal rows (`freee`, `yayoi`, `mf`, `en`).
2. **Stochastic Inventory & Cashflow Optimization (`stochastic_inventory_cashflow_solve`)**
   - Runs seeded Monte Carlo simulations across demand variance, lead-time uncertainty, and yield loss to compute optimal `(s, S)` reorder points, safety stock, and 95% CVaR working-capital buffers.
3. **Smart Contract Formal Invariant & 4-Class Vulnerability Analyzer (`audit_smart_contract_invariants`)**
   - Audits Solidity (`.sol`) and Rust (`.rs`) smart contracts for:
     - Class 1: ERC4626 share/asset conservation & first-depositor inflation attacks
     - Class 2: Asymmetric floor/ceil rounding drain on withdraw/redeem
     - Class 3: State-transition order & Checks-Effects-Interactions (CEI) / read-only reentrancy
     - Class 4: Oracle staleness (`latestRoundData` heartbeat checks) & narrowing integer downcasts (`uint128`/`uint96`/`uint64`)
4. **CSV Schema, Encoding & Tax Rounding Inspector (`inspect_csv_integrity`)**
   - Detects `Shift_JIS` / `UTF-8` replacement-character corruption (`U+FFFD`), duplicate primary keys, and 8%/10% consumption tax rounding discrepancies.

---

## Quick Start (One-Line MCP Server Registration)

Requires **only Python 3.9+ standard library** (zero `pip install` dependencies).

### 1. Run via MCP `stdio` (JSON-RPC 2.0)

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

### 2. Single-Shot CLI Execution (`--rpc-json`)

```bash
python3 mcp/mcp_server.py --rpc-json '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"subset_sum_reconcile","arguments":{"targets":[{"id":"BANK-01","amount":153560}],"candidates":[{"id":"INV-A","amount":88000,"invoice_no":"T1234567890123"},{"id":"INV-C","amount":66000,"invoice_no":"T1112223334445"}],"fee_tolerance_jpy":500}}}'
```

### 3. Verify All Tools & HTTP 402 Gate

```bash
python3 mcp/test_mcp_and_b2a.py
```

---

## B2A Quota & HTTP 402 Micropayment Protocol (`L402` / `x402`)

- **Free Trial Quota (Zero Auth)**:
  - `subset_sum_reconcile`: up to `25` total items (`targets + candidates`)
  - `stochastic_inventory_cashflow_solve`: up to `500` Monte Carlo paths
  - `audit_smart_contract_invariants`: up to `250` lines of source code
  - `inspect_csv_integrity`: up to `200` CSV rows
- **Machine-to-Machine Settlement (`HTTP 402 Payment Required`)**:
  - Requests exceeding the free quota return a structured `402 Payment Required` JSON payload in `result.structuredContent` containing:
    - `challenges.l402_lightning`: Macaroon + BOLT11 invoice + SHA-256 `payment_hash` (`Authorization: L402 <macaroon>:<preimage_hex>`)
    - `challenges.x402_usdc`: Base Mainnet (`chain_id: 8453`) USDC atomic payment challenge (`Authorization: x402 <challenge_id>:<receipt_token>`)
  - Passing a valid `payment_proof` in `arguments` immediately unlocks full-batch execution with zero pre-KYC or account registration.

---

## Machine-Readable Discovery Endpoints

- **Structured Tool Index**: `https://awai-mm.github.io/practical-data-tools/llms.txt`
- **Full Technical Specification**: `https://awai-mm.github.io/practical-data-tools/llms-full.txt`
- **A2A Agent Card**: `https://awai-mm.github.io/practical-data-tools/.well-known/agent.json`
- **OpenAPI 3.1 Schema**: `https://awai-mm.github.io/practical-data-tools/openapi.json`
- **GitHub Repository**: `https://github.com/awai-mm/practical-data-tools`
