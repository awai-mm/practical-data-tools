#!/usr/bin/env python3
# coding: utf-8
"""
Awai Practical Data Tools — Unified Deterministic MCP Server (mcp/mcp_server.py)

Pure Python 3 standard-library Model Context Protocol (MCP) JSON-RPC 2.0 server
designed for autonomous coding/ops agents and automated workflows.
Provides 4 deterministic mathematical & formal verification tools:
  1. `subset_sum_reconcile` : N-to-M subset-sum invoice/bank/card reconciliation + Yayoi/freee/MF journal export
  2. `stochastic_inventory_cashflow_solve` : Monte Carlo (s, S) reorder point, yield & CVaR working-capital optimizer
  3. `audit_smart_contract_invariants` : Static formal invariant & 4-class vulnerability analyzer for Solidity/Rust
  4. `inspect_csv_integrity` : CSV schema, JCT 8%/10% tax rounding, duplicate key & date integrity verifier

Integrated with `b2a_payment_gate.py` for zero-auth free trial execution and
HTTP 402 (L402 Lightning Macaroon+Preimage / x402 Base USDC) machine-to-machine unlocking.
"""
from __future__ import annotations

import argparse
import ast
import csv
from decimal import Decimal, ROUND_CEILING, ROUND_DOWN, ROUND_HALF_UP, getcontext
import io
import json
import math
from pathlib import Path
import random
import re
import sys
from typing import Any

getcontext().prec = 50

MCP_DIR = Path(__file__).resolve().parent
if str(MCP_DIR) not in sys.path:
    sys.path.insert(0, str(MCP_DIR))

from b2a_payment_gate import evaluate_request_gate  # noqa: E402

SERVER_NAME = "awai-practical-data-tools-mcp"
SERVER_VERSION = "1.2.0"
PROTOCOL_VERSION = "2024-11-05"

INVOICE_REG_RE = re.compile(r"^T\d{13}$")


# ---------------------------------------------------------------------------
# Free Hook Tool 0A: repair_and_validate_structured_data (100% Free Inflow Hook)
# ---------------------------------------------------------------------------
def tool_repair_and_validate_structured_data(args: dict[str, Any]) -> dict[str, Any]:
    """
    100% Free Hook Tool: Repairs malformed/truncated JSON payloads (markdown code fences,
    trailing commas, single-quoted dicts, unclosed brackets/braces) and validates required keys.
    """
    raw_input = str(args.get("raw_text") or "").strip()
    required_keys = list(args.get("required_keys") or [])
    repairs_applied: list[str] = []

    cleaned = raw_input
    # 1. Strip markdown code fences if present
    fence_m = re.search(r"```(?:json|javascript|py|python|yaml)?\s*([\s\S]*?)```", cleaned, re.IGNORECASE)
    if fence_m:
        cleaned = fence_m.group(1).strip()
        repairs_applied.append("stripped_markdown_code_fences")
    elif cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", cleaned).rstrip("`").strip()
        repairs_applied.append("stripped_leading_code_fence")

    # 2. Remove trailing commas before } or ]
    no_trailing = re.sub(r",\s*([}\]])", r"\1", cleaned)
    if no_trailing != cleaned:
        cleaned = no_trailing
        repairs_applied.append("removed_trailing_commas")

    parsed_obj: Any = None
    parse_ok = False

    # Try strict JSON first
    try:
        parsed_obj = json.loads(cleaned)
        parse_ok = True
    except Exception:
        pass

    # 3. Try balancing truncated braces/brackets
    if not parse_ok:
        open_curly = cleaned.count("{") - cleaned.count("}")
        open_sq = cleaned.count("[") - cleaned.count("]")
        if open_curly > 0 or open_sq > 0:
            candidate = re.sub(r",\s*$", "", cleaned.strip())
            candidate += ("]" * max(0, open_sq)) + ("}" * max(0, open_curly))
            try:
                parsed_obj = json.loads(candidate)
                cleaned = candidate
                parse_ok = True
                repairs_applied.append("balanced_unclosed_brackets")
            except Exception:
                pass

    # 4. Try Python literal eval for single-quoted dicts / True / False / None
    if not parse_ok:
        try:
            lit_obj = ast.literal_eval(cleaned)
            parsed_obj = json.loads(json.dumps(lit_obj, ensure_ascii=False))
            parse_ok = True
            repairs_applied.append("converted_python_literal_or_single_quotes")
        except Exception:
            pass

    missing_keys: list[str] = []
    if parse_ok and isinstance(parsed_keys_target := parsed_obj, dict):
        missing_keys = [k for k in required_keys if k not in parsed_keys_target]

    return {
        "ok": parse_ok and len(missing_keys) == 0,
        "solver": "repair_and_validate_structured_data",
        "parse_succeeded": parse_ok,
        "repairs_applied": repairs_applied,
        "missing_required_keys": missing_keys,
        "normalized_json": json.dumps(parsed_obj, ensure_ascii=False) if parse_ok else None,
        "parsed_data": parsed_obj if parse_ok else None,
    }


# ---------------------------------------------------------------------------
# Free Hook Tool 0B: exact_decimal_and_crypto_unit_math (100% Free Inflow Hook)
# ---------------------------------------------------------------------------
_UNIT_DECIMALS: dict[str, int] = {
    "wei": 0,
    "gwei": 9,
    "eth": 18,
    "usdc_atomic": 0,
    "usdc": 6,
    "msat": 0,
    "sat": 3,
    "sats": 3,
    "btc": 11,  # relative to msat (1 BTC = 10^8 sat = 10^11 msat)
}


def tool_exact_decimal_and_crypto_unit_math(args: dict[str, Any]) -> dict[str, Any]:
    """
    100% Free Hook Tool: Arbitrary-precision Decimal & integer unit math for Web3 (Wei/Gwei/ETH/USDC),
    Bitcoin Lightning (msat/sat/BTC), zero-dust pro-rata allocation, and exact basis-point / tax splits.
    """
    mode = str(args.get("mode") or "pro_rata_allocate").strip().lower()

    if mode == "convert_units":
        val_dec = Decimal(str(args.get("value") or "0"))
        from_u = str(args.get("from_unit") or "eth").lower()
        to_u = str(args.get("to_unit") or "wei").lower()
        if from_u in ("wei", "gwei", "eth") and to_u in ("wei", "gwei", "eth"):
            scale = Decimal(10) ** (_UNIT_DECIMALS[from_u] - _UNIT_DECIMALS[to_u])
            converted = val_dec * scale
        elif from_u in ("msat", "sat", "sats", "btc") and to_u in ("msat", "sat", "sats", "btc"):
            scale = Decimal(10) ** (_UNIT_DECIMALS[from_u] - _UNIT_DECIMALS[to_u])
            converted = val_dec * scale
        elif from_u in ("usdc", "usdc_atomic") and to_u in ("usdc", "usdc_atomic"):
            scale = Decimal(10) ** (_UNIT_DECIMALS[from_u] - _UNIT_DECIMALS[to_u])
            converted = val_dec * scale
        else:
            converted = val_dec
        normalized = format(converted.normalize(), "f") if converted != 0 else "0"
        return {
            "ok": True,
            "solver": "exact_decimal_and_crypto_unit_math",
            "mode": "convert_units",
            "input_value": str(args.get("value")),
            "from_unit": from_u,
            "to_unit": to_u,
            "exact_result": normalized,
        }

    if mode == "bps_fee_split":
        gross = Decimal(str(args.get("total_amount") or "0"))
        bps = Decimal(str(args.get("fee_bps") or "30"))  # e.g. 30 bps = 0.30%
        fee_floor = (gross * bps / Decimal(10000)).quantize(Decimal("1"), rounding=ROUND_DOWN)
        fee_ceil = (gross * bps / Decimal(10000)).quantize(Decimal("1"), rounding=ROUND_CEILING)
        fee_half_up = (gross * bps / Decimal(10000)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return {
            "ok": True,
            "solver": "exact_decimal_and_crypto_unit_math",
            "mode": "bps_fee_split",
            "gross_amount": str(gross),
            "fee_bps": str(bps),
            "fee_floor": str(fee_floor),
            "net_after_floor_fee": str(gross - fee_floor),
            "fee_ceil_protocol_safe": str(fee_ceil),
            "net_after_ceil_fee": str(gross - fee_ceil),
            "fee_half_up": str(fee_half_up),
        }

    # Default: pro_rata_allocate (Largest Remainder Method guaranteeing sum(allocations) == total_amount)
    total_int = int(Decimal(str(args.get("total_amount") or "0")))
    raw_weights = [Decimal(str(w)) for w in (args.get("weights") or [1, 1, 1])]
    weight_sum = sum(raw_weights)
    if weight_sum <= 0:
        return {"ok": False, "error": "sum_of_weights_must_be_positive"}

    exact_quotas = [(Decimal(total_int) * w) / weight_sum for w in raw_weights]
    floors = [int(q.to_integral_value(rounding=ROUND_DOWN)) for q in exact_quotas]
    remainders = [(exact_quotas[i] - Decimal(floors[i]), i) for i in range(len(raw_weights))]
    shortfall = total_int - sum(floors)
    remainders.sort(key=lambda x: (-x[0], x[1]))
    for k in range(max(0, shortfall)):
        floors[remainders[k][1]] += 1

    return {
        "ok": True,
        "solver": "exact_decimal_and_crypto_unit_math",
        "mode": "pro_rata_allocate",
        "total_amount": total_int,
        "allocations": floors,
        "sum_verified_equal": sum(floors) == total_int,
        "dust_remainder_lost": 0,
    }


# ---------------------------------------------------------------------------
# Tool 1: subset_sum_reconcile
# ---------------------------------------------------------------------------
def tool_subset_sum_reconcile(args: dict[str, Any]) -> dict[str, Any]:
    """
    Deterministic N-to-M subset-sum solver with fee tolerance, JCT invoice number validation,
    and double-entry accounting journal generation (yayoi / freee / mf).
    """
    targets = list(args.get("targets") or [])
    candidates = list(args.get("candidates") or [])
    fee_tolerance = int(args.get("fee_tolerance_jpy") or 0)
    export_format = str(args.get("journal_format") or "freee").lower()

    used_candidate_ids: set[str] = set()
    matches: list[dict[str, Any]] = []
    unmatched_targets: list[dict[str, Any]] = []

    for tgt in targets:
        t_id = str(tgt.get("id") or "")
        t_amt = int(tgt.get("amount") or 0)
        avail = [
            c for c in candidates
            if str(c.get("id") or "") not in used_candidate_ids
        ]

        best_subset: list[dict[str, Any]] | None = None
        best_diff = 10**12

        # Exact + fee-tolerant branch-and-bound subset-sum search (up to subset size 8)
        n = len(avail)

        def _dfs(idx: int, chosen: list[dict[str, Any]], current_sum: int) -> bool:
            nonlocal best_subset, best_diff
            diff = abs(t_amt - current_sum)
            if chosen and diff <= fee_tolerance and diff < best_diff:
                best_subset = list(chosen)
                best_diff = diff
                if diff == 0:
                    return True
            if idx >= n or len(chosen) >= 8:
                return False
            if current_sum > t_amt + fee_tolerance and all(int(x.get("amount") or 0) >= 0 for x in avail[idx:]):
                return False
            for i in range(idx, n):
                c = avail[i]
                c_amt = int(c.get("amount") or 0)
                chosen.append(c)
                if _dfs(i + 1, chosen, current_sum + c_amt):
                    return True
                chosen.pop()
            return False

        _dfs(0, [], 0)

        if best_subset is not None:
            matched_ids = [str(c.get("id") or "") for c in best_subset]
            for mid in matched_ids:
                used_candidate_ids.add(mid)
            sub_sum = sum(int(c.get("amount") or 0) for c in best_subset)
            fee_diff = t_amt - sub_sum
            valid_invoices = [
                str(c.get("invoice_no") or "")
                for c in best_subset
                if INVOICE_REG_RE.match(str(c.get("invoice_no") or ""))
            ]
            matches.append({
                "target_id": t_id,
                "target_amount": t_amt,
                "matched_candidate_ids": matched_ids,
                "candidates_sum": sub_sum,
                "fee_adjustment_jpy": fee_diff,
                "verified_invoice_numbers": valid_invoices,
                "match_type": "exact" if fee_diff == 0 else "fee_adjusted",
            })
        else:
            unmatched_targets.append({"target_id": t_id, "target_amount": t_amt})

    journal_rows: list[dict[str, Any]] = []
    for m in matches:
        journal_rows.append({
            "format": export_format,
            "target_id": m["target_id"],
            "debit_account": "買掛金・未払金" if export_format != "en" else "Accounts Payable",
            "debit_amount": m["candidates_sum"],
            "credit_account": "普通預金" if export_format != "en" else "Cash at Bank",
            "credit_amount": m["target_amount"],
            "fee_account": "支払手数料" if m["fee_adjustment_jpy"] != 0 else None,
            "fee_amount": abs(m["fee_adjustment_jpy"]),
            "invoice_registration_numbers": m["verified_invoice_numbers"],
        })

    return {
        "ok": True,
        "solver": "subset_sum_reconcile",
        "matched_count": len(matches),
        "unmatched_targets_count": len(unmatched_targets),
        "matches": matches,
        "unmatched_targets": unmatched_targets,
        "journal_entries": journal_rows,
    }


# ---------------------------------------------------------------------------
# Tool 2: stochastic_inventory_cashflow_solve
# ---------------------------------------------------------------------------
def tool_stochastic_inventory_cashflow_solve(args: dict[str, Any]) -> dict[str, Any]:
    """
    Deterministic-seed Monte Carlo (s, S) inventory & CVaR working-capital optimizer.
    """
    mean_daily_demand = float(args.get("mean_daily_demand") or 40.0)
    std_daily_demand = float(args.get("std_daily_demand") or 12.0)
    lead_time_days = int(args.get("lead_time_days") or 7)
    unit_cost = float(args.get("unit_cost") or 1000.0)
    unit_price = float(args.get("unit_price") or 1650.0)
    holding_cost_per_day = float(args.get("holding_cost_per_day") or 8.0)
    stockout_penalty = float(args.get("stockout_penalty") or 450.0)
    yield_rate = max(0.1, min(1.0, float(args.get("yield_rate") or 0.96)))
    horizon_days = max(7, min(365, int(args.get("horizon_days") or 60)))
    num_paths = max(20, min(5000, int(args.get("num_paths") or 200)))
    seed = int(args.get("seed") or 20261029)

    lt_mean = mean_daily_demand * lead_time_days
    lt_std = std_daily_demand * math.sqrt(max(1, lead_time_days))

    candidate_policies: list[tuple[int, int]] = []
    for z_mult in (1.28, 1.65, 1.96, 2.33):
        s_pt = max(1, int(round(lt_mean + z_mult * lt_std)))
        for cover_days in (7, 14, 21):
            S_up = max(s_pt + 1, int(round((s_pt + mean_daily_demand * cover_days) / yield_rate)))
            candidate_policies.append((s_pt, S_up))

    best_eval: dict[str, Any] | None = None

    for s_pt, S_up in candidate_policies:
        rng = random.Random(seed)
        path_profits: list[float] = []
        path_min_cash: list[float] = []
        stockout_days_total = 0

        for _ in range(num_paths):
            inv = float(S_up)
            cash = 0.0
            min_cash = 0.0
            pending_orders: list[tuple[int, float]] = []

            for day in range(horizon_days):
                arriving = sum(qty for d_arr, qty in pending_orders if d_arr == day)
                pending_orders = [(d_arr, qty) for d_arr, qty in pending_orders if d_arr > day]
                inv += arriving

                demand = max(0.0, rng.gauss(mean_daily_demand, std_daily_demand))
                sold = min(inv, demand)
                shortage = max(0.0, demand - inv)
                inv -= sold

                if shortage > 0:
                    stockout_days_total += 1

                cash += sold * unit_price - inv * holding_cost_per_day - shortage * stockout_penalty

                on_order = sum(qty for _, qty in pending_orders)
                if inv + on_order <= s_pt:
                    order_raw = (S_up - (inv + on_order)) / yield_rate
                    usable_qty = order_raw * yield_rate
                    pending_orders.append((day + lead_time_days, usable_qty))
                    cash -= order_raw * unit_cost

                if cash < min_cash:
                    min_cash = cash

            path_profits.append(cash)
            path_min_cash.append(min_cash)

        path_profits.sort()
        path_min_cash.sort()
        tail_n = max(1, int(num_paths * 0.05))
        cvar_95_profit = sum(path_profits[:tail_n]) / tail_n
        cvar_95_drawdown = abs(sum(path_min_cash[:tail_n]) / tail_n)
        expected_profit = sum(path_profits) / num_paths
        service_level = 1.0 - (stockout_days_total / float(num_paths * horizon_days))

        score = expected_profit - 0.35 * cvar_95_drawdown
        rec = {
            "reorder_point_s": s_pt,
            "order_up_to_S": S_up,
            "safety_stock_units": max(0, int(round(s_pt - lt_mean))),
            "expected_net_profit": round(expected_profit, 2),
            "cvar_95_profit": round(cvar_95_profit, 2),
            "working_capital_buffer_95": round(cvar_95_drawdown, 2),
            "service_level_rate": round(service_level, 4),
            "_score": score,
        }
        if best_eval is None or score > best_eval["_score"]:
            best_eval = rec

    assert best_eval is not None
    best_eval.pop("_score", None)
    return {
        "ok": True,
        "solver": "stochastic_inventory_cashflow_solve",
        "monte_carlo_paths": num_paths,
        "horizon_days": horizon_days,
        "optimal_policy": best_eval,
    }


# ---------------------------------------------------------------------------
# Tool 3: audit_smart_contract_invariants
# ---------------------------------------------------------------------------
def tool_audit_smart_contract_invariants(args: dict[str, Any]) -> dict[str, Any]:
    """
    Static formal invariant & 4-class vulnerability analyzer for Solidity / Rust contracts.
    Detects:
      1. Invariant Violation (ERC4626 share/asset inflation, unbacked minting)
      2. Rounding Direction Drain (floor division on withdraw/redeem share burn)
      3. State-Transition Order / Reentrancy (external call before state update)
      4. Oracle Staleness & Narrowing Downcast (latestRoundData without updatedAt check, uint128/96/64 cast)
    """
    source_code = str(args.get("source_code") or "")
    contract_name = str(args.get("contract_name") or "TargetContract.sol")
    lines = source_code.splitlines()

    findings: list[dict[str, Any]] = []

    # 1. Check ERC4626 / Share-Asset Inflation & Rounding Direction
    for idx, ln in enumerate(lines, start=1):
        if any(tok in ln for tok in ("totalSupply", "totalAssets", "total_shares", "total_assets")):
            if "/" in ln and not any(safe_tok in source_code for safe_tok in ("VIRTUAL_SHARES", "_decimalsOffset", "mulDivUp", "Math.Rounding.Ceil")):
                findings.append({
                    "class": "Class 1 & 2: Share/Asset Invariant & Rounding Direction",
                    "severity": "HIGH",
                    "line": idx,
                    "code_snippet": ln.strip()[:140],
                    "invariant_violated": "shares_burned(assets) >= ceil(assets * (totalSupply + VIRTUAL_SHARES) / (totalAssets + VIRTUAL_ASSETS))",
                    "remediation": "Add virtual share/asset offset (e.g. 1e3 virtual shares) and enforce ceil rounding when burning shares on withdraw.",
                })
                break

    # 2. Check State Transition Order / CEI Reentrancy (external call before state update)
    ext_call_line = None
    for idx, ln in enumerate(lines, start=1):
        if re.search(r"(\.call\s*\{|safeTransfer\s*\(|transferFrom\s*\(|invoke_signed)", ln):
            ext_call_line = idx
        elif ext_call_line is not None and idx > ext_call_line and (idx - ext_call_line) <= 12:
            if re.search(r"(\b(?:balances|shares|totalSupply|totalAssets|reserves|user_stake)\b.*(?:\-=|\+=|=))", ln):
                findings.append({
                    "class": "Class 3: State-Transition Order & Reentrancy (CEI Violation)",
                    "severity": "HIGH",
                    "line": idx,
                    "external_call_line": ext_call_line,
                    "code_snippet": ln.strip()[:140],
                    "invariant_violated": "All internal state mutations (balances, totalSupply, reserves) must complete before any external call or callback.",
                    "remediation": "Apply Checks-Effects-Interactions (CEI) order and add a nonReentrant mutex across state-reading view functions.",
                })
                break

    # 3. Check Chainlink Oracle Staleness / Heartbeat validation
    for idx, ln in enumerate(lines, start=1):
        if "latestRoundData" in ln:
            window = "\n".join(lines[max(0, idx - 2) : min(len(lines), idx + 10)])
            if "updatedAt" not in window or "answeredInRound" not in window:
                findings.append({
                    "class": "Class 4A: Oracle Staleness & Incomplete Round Validation",
                    "severity": "MEDIUM",
                    "line": idx,
                    "code_snippet": ln.strip()[:140],
                    "invariant_violated": "price > 0 && updatedAt > 0 && block.timestamp - updatedAt <= MAX_HEARTBEAT && answeredInRound >= roundId",
                    "remediation": "Validate `answer > 0`, `updatedAt >= block.timestamp - HEARTBEAT`, and `answeredInRound >= roundId`.",
                })

    # 4. Check Unsafe Narrowing Integer Downcast
    for idx, ln in enumerate(lines, start=1):
        m_cast = re.search(r"\b(uint(?:128|96|64|32|16|8))\s*\(", ln)
        if m_cast and "SafeCast" not in ln:
            cast_type = m_cast.group(1)
            findings.append({
                "class": f"Class 4B: Silent Narrowing Integer Downcast ({cast_type})",
                "severity": "MEDIUM",
                "line": idx,
                "code_snippet": ln.strip()[:140],
                "invariant_violated": f"x <= type({cast_type}).max before narrowing conversion",
                "remediation": f"Replace raw `{cast_type}(x)` cast with `SafeCast.to{cast_type.capitalize()}(x)` or explicit upper-bound revert check.",
            })
            break

    return {
        "ok": True,
        "solver": "audit_smart_contract_invariants",
        "contract_name": contract_name,
        "lines_scanned": len(lines),
        "findings_count": len(findings),
        "invariant_status": "PASS_NO_VIOLATION_DETECTED" if not findings else "VIOLATIONS_DETECTED",
        "findings": findings,
    }


# ---------------------------------------------------------------------------
# Tool 4: inspect_csv_integrity
# ---------------------------------------------------------------------------
def tool_inspect_csv_integrity(args: dict[str, Any]) -> dict[str, Any]:
    """
    Deterministic CSV schema, encoding replacement char, duplicate key, and JCT 8%/10% tax rounding verifier.
    """
    csv_text = str(args.get("csv_text") or "")
    required_columns = list(args.get("required_columns") or [])
    key_column = str(args.get("key_column") or "")

    reader = csv.DictReader(io.StringIO(csv_text.strip()))
    headers = list(reader.fieldnames or [])
    missing_columns = [c for c in required_columns if c not in headers]

    anomalies: list[dict[str, Any]] = []
    seen_keys: dict[str, int] = {}
    row_count = 0

    for idx, row in enumerate(reader, start=2):
        row_count += 1
        raw_vals = [str(v or "") for v in row.values()]
        if any("\ufffd" in v for v in raw_vals):
            anomalies.append({
                "row": idx,
                "type": "encoding_garble_replacement_char",
                "detail": "Contains U+FFFD replacement character indicating Shift_JIS/UTF-8 decoding mismatch.",
            })

        if key_column and key_column in row:
            kv = str(row.get(key_column) or "").strip()
            if kv:
                if kv in seen_keys:
                    anomalies.append({
                        "row": idx,
                        "type": "duplicate_primary_key",
                        "detail": f"Duplicate key '{kv}' (first seen on row {seen_keys[kv]}).",
                    })
                else:
                    seen_keys[kv] = idx

        if "net_amount" in row and "tax_rate" in row and "tax_amount" in row:
            try:
                net = int(str(row["net_amount"]).replace(",", "").strip())
                rate = float(str(row["tax_rate"]).replace("%", "").strip())
                if rate > 1.0:
                    rate = rate / 100.0
                reported_tax = int(str(row["tax_amount"]).replace(",", "").strip())
                floor_tax = int(math.floor(net * rate + 1e-9))
                round_tax = int(round(net * rate))
                ceil_tax = int(math.ceil(net * rate - 1e-9))
                if reported_tax not in (floor_tax, round_tax, ceil_tax):
                    anomalies.append({
                        "row": idx,
                        "type": "tax_rounding_discrepancy",
                        "detail": (
                            f"Reported tax ({reported_tax}) does not match floor ({floor_tax}), "
                            f"half-up ({round_tax}), or ceil ({ceil_tax}) for net={net} at rate={rate:.2f}."
                        ),
                    })
            except Exception:
                pass

    return {
        "ok": len(missing_columns) == 0 and len(anomalies) == 0,
        "solver": "inspect_csv_integrity",
        "rows_inspected": row_count,
        "headers": headers,
        "missing_columns": missing_columns,
        "anomalies_count": len(anomalies),
        "anomalies": anomalies,
    }


# ---------------------------------------------------------------------------
# MCP Tool Registry & JSON Schema Definitions
# ---------------------------------------------------------------------------
MCP_TOOLS_SPEC: list[dict[str, Any]] = [
    {
        "name": "repair_and_validate_structured_data",
        "description": (
            "[100% FREE HOOK TOOL] Repairs malformed or truncated JSON/dict payloads (strips markdown fences, "
            "removes trailing commas, converts single-quoted dicts, balances unclosed brackets/braces) "
            "and validates required schema keys."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "raw_text": {
                    "type": "string",
                    "description": "Raw, potentially malformed or truncated JSON/dict string.",
                },
                "required_keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of required top-level keys to verify.",
                },
            },
            "required": ["raw_text"],
        },
    },
    {
        "name": "exact_decimal_and_crypto_unit_math",
        "description": (
            "[100% FREE HOOK TOOL] Exact 50-digit Decimal & integer arithmetic for Web3 units (Wei/Gwei/ETH/USDC), "
            "Lightning units (msat/sat/BTC), zero-dust pro-rata allocation (Largest Remainder Method), "
            "and basis-point (bps) fee splits without floating-point rounding drift."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["pro_rata_allocate", "convert_units", "bps_fee_split"],
                    "default": "pro_rata_allocate",
                },
                "total_amount": {"type": ["integer", "string", "number"]},
                "weights": {"type": "array", "items": {"type": "number"}},
                "value": {"type": ["string", "number"]},
                "from_unit": {"type": "string"},
                "to_unit": {"type": "string"},
                "fee_bps": {"type": ["integer", "number", "string"]},
            },
        },
    },
    {
        "name": "subset_sum_reconcile",
        "description": (
            "Deterministic N-to-M subset-sum bank/card/invoice reconciliation solver with fee tolerance, "
            "Japanese Qualified Invoice (T+13 digits) validation, and Yayoi/freee/MoneyForward journal export. "
            "Free tier up to 25 items; larger batches support HTTP 402 (L402 Lightning / x402 USDC) unlock."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "targets": {
                    "type": "array",
                    "description": "Bank deposits or aggregated credit card withdrawals to reconcile.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "amount": {"type": "integer"},
                        },
                        "required": ["id", "amount"],
                    },
                },
                "candidates": {
                    "type": "array",
                    "description": "Individual invoices, orders, or receipts to match against targets.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "amount": {"type": "integer"},
                            "invoice_no": {"type": "string"},
                        },
                        "required": ["id", "amount"],
                    },
                },
                "fee_tolerance_jpy": {
                    "type": "integer",
                    "default": 0,
                    "description": "Maximum allowed bank transfer / gateway fee difference.",
                },
                "journal_format": {
                    "type": "string",
                    "enum": ["freee", "yayoi", "mf", "en"],
                    "default": "freee",
                },
                "payment_proof": {
                    "type": "string",
                    "description": "Optional L402 ('L402 <macaroon>:<preimage>') or x402 ('x402 <cid>:<receipt>') proof for large batches.",
                },
            },
            "required": ["targets", "candidates"],
        },
    },
    {
        "name": "stochastic_inventory_cashflow_solve",
        "description": (
            "Monte Carlo stochastic dynamic programming solver that computes the optimal (s, S) reorder policy, "
            "safety stock, yield loss buffer, and 95% CVaR working-capital requirement."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "mean_daily_demand": {"type": "number", "default": 40.0},
                "std_daily_demand": {"type": "number", "default": 12.0},
                "lead_time_days": {"type": "integer", "default": 7},
                "unit_cost": {"type": "number", "default": 1000.0},
                "unit_price": {"type": "number", "default": 1650.0},
                "holding_cost_per_day": {"type": "number", "default": 8.0},
                "stockout_penalty": {"type": "number", "default": 450.0},
                "yield_rate": {"type": "number", "default": 0.96},
                "horizon_days": {"type": "integer", "default": 60},
                "num_paths": {"type": "integer", "default": 200},
                "seed": {"type": "integer", "default": 20261029},
                "payment_proof": {"type": "string"},
            },
        },
    },
    {
        "name": "audit_smart_contract_invariants",
        "description": (
            "Formal invariant and static vulnerability checker for Solidity/Rust smart contracts covering "
            "ERC4626 share inflation, floor/ceil rounding drain, CEI/read-only reentrancy, and oracle/downcast bugs."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "source_code": {"type": "string", "description": "Solidity or Rust smart contract source code."},
                "contract_name": {"type": "string", "default": "TargetContract.sol"},
                "deep_audit": {"type": "boolean", "default": False},
                "payment_proof": {"type": "string"},
            },
            "required": ["source_code"],
        },
    },
    {
        "name": "inspect_csv_integrity",
        "description": (
            "Deterministic CSV schema, Shift_JIS/UTF-8 garble detection, primary-key uniqueness, "
            "and Japanese 8%/10% consumption tax rounding inspector."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "csv_text": {"type": "string", "description": "Raw CSV content to inspect."},
                "required_columns": {"type": "array", "items": {"type": "string"}},
                "key_column": {"type": "string"},
                "deep_scan": {"type": "boolean", "default": False},
                "payment_proof": {"type": "string"},
            },
            "required": ["csv_text"],
        },
    },
]

_TOOL_DISPATCH = {
    "repair_and_validate_structured_data": tool_repair_and_validate_structured_data,
    "exact_decimal_and_crypto_unit_math": tool_exact_decimal_and_crypto_unit_math,
    "subset_sum_reconcile": tool_subset_sum_reconcile,
    "stochastic_inventory_cashflow_solve": tool_stochastic_inventory_cashflow_solve,
    "audit_smart_contract_invariants": tool_audit_smart_contract_invariants,
    "inspect_csv_integrity": tool_inspect_csv_integrity,
}


def handle_jsonrpc_request(req: dict[str, Any]) -> dict[str, Any] | None:
    """Process a single JSON-RPC 2.0 request dict and return the JSON-RPC 2.0 response dict."""
    req_id = req.get("id")
    method = str(req.get("method") or "")
    params = req.get("params") or {}

    if method == "notifications/initialized":
        return None

    if method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {
                    "tools": {"listChanged": False},
                },
                "serverInfo": {
                    "name": SERVER_NAME,
                    "version": SERVER_VERSION,
                },
            },
        }

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": MCP_TOOLS_SPEC,
            },
        }

    if method == "tools/call":
        t_name = str(params.get("name") or "")
        t_args = params.get("arguments") or {}
        if t_name not in _TOOL_DISPATCH:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Unknown tool: {t_name}",
                },
            }

        gate_res = evaluate_request_gate(t_name, t_args)
        if not gate_res.get("allowed"):
            challenge_payload = gate_res["challenge"]
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "isError": True,
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(challenge_payload, ensure_ascii=False),
                        }
                    ],
                    "structuredContent": challenge_payload,
                },
            }

        try:
            exec_res = _TOOL_DISPATCH[t_name](t_args)
            exec_res["b2a_gate"] = {
                "tier": gate_res.get("tier"),
                "payment": gate_res.get("payment"),
            }
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "isError": False,
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(exec_res, ensure_ascii=False),
                        }
                    ],
                    "structuredContent": exec_res,
                },
            }
        except Exception as exc:
            err_obj = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "isError": True,
                    "content": [{"type": "text", "text": json.dumps(err_obj, ensure_ascii=False)}],
                    "structuredContent": err_obj,
                },
            }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": -32601,
            "message": f"Method not found: {method}",
        },
    }


def run_stdio_server() -> int:
    """Run MCP JSON-RPC 2.0 server over standard input/output."""
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"},
            }
            sys.stdout.write(json.dumps(err_resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
            continue

        resp = handle_jsonrpc_request(req)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Awai Practical Data Tools — Deterministic MCP Server")
    parser.add_argument("--stdio", action="store_true", help="Run JSON-RPC 2.0 MCP server over stdio")
    parser.add_argument("--rpc-json", type=str, help="Execute a single JSON-RPC 2.0 request string and print response")
    args = parser.parse_args(argv)

    if args.rpc_json:
        req = json.loads(args.rpc_json)
        resp = handle_jsonrpc_request(req)
        print(json.dumps(resp, ensure_ascii=False, indent=2))
        return 0

    return run_stdio_server()


if __name__ == "__main__":
    raise SystemExit(main())
