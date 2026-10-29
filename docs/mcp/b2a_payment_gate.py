#!/usr/bin/env python3
# coding: utf-8
"""
B2A (Business-to-Agent / Agent-to-Agent) Micropayment & Quota Gate (b2a_payment_gate.py)

Implements deterministic free-tier quota evaluation and HTTP 402 Payment Required challenges
for machine-to-machine settlement without pre-KYC or identity registration:
1. L402 (Lightning Network HTTP 402 Protocol):
   - Issues an HMAC-signed Macaroon bound to a SHA-256 payment_hash and BOLT11 invoice challenge.
   - Unlocks execution when the caller supplies `L402 <macaroon>:<preimage_hex>` where
     `SHA256(bytes.fromhex(preimage_hex)) == payment_hash`.
2. x402 (EVM / Base / Arbitrum USDC HTTP 402 Protocol):
   - Issues a deterministic x402 payment payload specifying recipient contract/wallet, chainId,
     token contract (USDC), atomic amount, and challenge_id.
   - Unlocks execution when the caller supplies a valid `x402 <challenge_id>:<receipt_token>`.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from typing import Any

GATE_VERSION = "1.2.0"

# Deterministic secret key for local / stateless challenge signing (overridable via env)
_DEFAULT_GATE_SECRET = os.environ.get(
    "MM_B2A_GATE_SECRET",
    "awai-mm-b2a-l402-x402-deterministic-gate-key-2026",
).encode("utf-8")

# Free-tier limits for zero-auth instant execution
# Note: High-frequency hook tools (`repair_and_validate_structured_data`, `exact_decimal_and_crypto_unit_math`)
# are 100% free with generous limits to maximize daily autonomous agent inflow.
FREE_TIER_LIMITS: dict[str, dict[str, int]] = {
    "repair_and_validate_structured_data": {
        "max_input_chars": 250_000,
        "price_sats": 0,
        "price_usdc_atomic": 0,
    },
    "exact_decimal_and_crypto_unit_math": {
        "max_operations": 1_000,
        "price_sats": 0,
        "price_usdc_atomic": 0,
    },
    "subset_sum_reconcile": {
        "max_total_items": 25,
        "price_sats": 210,
        "price_usdc_atomic": 150_000,  # 0.15 USDC (6 decimals)
    },
    "stochastic_inventory_cashflow_solve": {
        "max_monte_carlo_paths": 500,
        "price_sats": 350,
        "price_usdc_atomic": 250_000,  # 0.25 USDC
    },
    "audit_smart_contract_invariants": {
        "max_source_lines": 250,
        "price_sats": 500,
        "price_usdc_atomic": 350_000,  # 0.35 USDC
    },
    "inspect_csv_integrity": {
        "max_csv_rows": 200,
        "price_sats": 150,
        "price_usdc_atomic": 100_000,  # 0.10 USDC
    },
}


def _derive_challenge_preimage(challenge_id: str, secret: bytes = _DEFAULT_GATE_SECRET) -> bytes:
    """Derive a deterministic 32-byte preimage for a given challenge_id."""
    return hmac.new(secret, f"l402-preimage:{challenge_id}".encode("utf-8"), hashlib.sha256).digest()


def derive_test_preimage_hex(challenge_id: str) -> str:
    """Helper for unit tests and local deterministic settlement verification."""
    return _derive_challenge_preimage(challenge_id).hex()


def derive_test_x402_receipt(challenge_id: str, secret: bytes = _DEFAULT_GATE_SECRET) -> str:
    """Helper for verifying x402 receipt signature in automated test suites."""
    return hmac.new(secret, f"x402-receipt:{challenge_id}".encode("utf-8"), hashlib.sha256).hexdigest()


def issue_402_challenge(tool_name: str, usage_metric: str, usage_value: int, limit_value: int) -> dict[str, Any]:
    """
    Generate a machine-readable HTTP 402 Payment Required challenge supporting both
    L402 (Lightning Network Macaroon + Preimage) and x402 (USDC on Base/Arbitrum).
    """
    spec = FREE_TIER_LIMITS.get(tool_name) or {
        "price_sats": 250,
        "price_usdc_atomic": 200_000,
    }
    sats = int(spec.get("price_sats", 250))
    usdc_atomic = int(spec.get("price_usdc_atomic", 200_000))
    usdc_decimal = f"{usdc_atomic / 1_000_000:.2f}"

    raw_seed = f"{tool_name}:{usage_metric}:{usage_value}:{limit_value}:{sats}"
    challenge_id = "chk_" + hashlib.sha256(raw_seed.encode("utf-8")).hexdigest()[:16]

    preimage_bytes = _derive_challenge_preimage(challenge_id)
    payment_hash = hashlib.sha256(preimage_bytes).hexdigest()

    macaroon_payload = {
        "v": 1,
        "cid": challenge_id,
        "tool": tool_name,
        "sats": sats,
        "phash": payment_hash,
    }
    macaroon_json = json.dumps(macaroon_payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    macaroon_sig = hmac.new(_DEFAULT_GATE_SECRET, macaroon_json, hashlib.sha256).hexdigest()
    macaroon_token = base64.urlsafe_b64encode(macaroon_json).decode("ascii").rstrip("=") + "." + macaroon_sig

    bolt11_sim = f"lnbc{sats * 10}n1p{payment_hash[:28]}"
    www_auth = f'L402 macaroon="{macaroon_token}", invoice="{bolt11_sim}"'

    return {
        "http_status": 402,
        "status": "payment_required",
        "code": "HTTP_402_PAYMENT_REQUIRED",
        "tool": tool_name,
        "quota_exceeded": {
            "metric": usage_metric,
            "requested": usage_value,
            "free_tier_limit": limit_value,
        },
        "message": (
            f"HTTP 402 Payment Required: '{tool_name}' request size ({usage_metric}={usage_value}) "
            f"exceeds free trial quota ({limit_value}). Supply an L402 or x402 payment proof to unlock."
        ),
        "headers": {
            "WWW-Authenticate": www_auth,
            "X-Payment-Protocols": "L402, x402",
        },
        "challenges": {
            "l402_lightning": {
                "protocol": "L402",
                "network": "bitcoin-lightning",
                "challenge_id": challenge_id,
                "amount_sats": sats,
                "payment_hash": payment_hash,
                "macaroon": macaroon_token,
                "invoice": bolt11_sim,
                "authorization_header_format": "L402 <macaroon>:<preimage_hex>",
            },
            "x402_usdc": {
                "protocol": "x402",
                "network": "base-mainnet",
                "chain_id": 8453,
                "asset": "USDC",
                "token_contract": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
                "amount_usdc": usdc_decimal,
                "amount_atomic": usdc_atomic,
                "challenge_id": challenge_id,
                "authorization_header_format": "x402 <challenge_id>:<receipt_token>",
            },
        },
    }


def verify_payment_proof(proof: str | dict[str, Any] | None) -> dict[str, Any]:
    """
    Verify an L402 (`L402 <macaroon>:<preimage_hex>`) or x402 (`x402 <challenge_id>:<receipt>`) proof.
    """
    if not proof:
        return {"valid": False, "reason": "missing_payment_proof"}

    if isinstance(proof, dict):
        proto = str(proof.get("protocol") or "").upper()
        if proto == "L402":
            mac = str(proof.get("macaroon") or "")
            pre = str(proof.get("preimage") or "")
            proof = f"L402 {mac}:{pre}"
        elif proto == "X402":
            cid = str(proof.get("challenge_id") or "")
            rec = str(proof.get("receipt_token") or proof.get("receipt") or "")
            proof = f"x402 {cid}:{rec}"
        else:
            return {"valid": False, "reason": "unsupported_proof_object"}

    raw = str(proof).strip()
    if raw.upper().startswith("L402 "):
        token_part = raw[5:].strip()
        if ":" not in token_part:
            return {"valid": False, "reason": "malformed_l402_token"}
        macaroon_token, preimage_hex = token_part.split(":", 1)
        if "." not in macaroon_token:
            return {"valid": False, "reason": "malformed_macaroon"}
        b64_part, sig_part = macaroon_token.rsplit(".", 1)
        pad = "=" * ((4 - len(b64_part) % 4) % 4)
        try:
            mac_bytes = base64.urlsafe_b64decode((b64_part + pad).encode("ascii"))
            expected_sig = hmac.new(_DEFAULT_GATE_SECRET, mac_bytes, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(sig_part, expected_sig):
                return {"valid": False, "reason": "invalid_macaroon_signature"}
            mac_obj = json.loads(mac_bytes.decode("utf-8"))
            pre_bytes = bytes.fromhex(preimage_hex.strip())
            computed_phash = hashlib.sha256(pre_bytes).hexdigest()
            if not hmac.compare_digest(computed_phash, str(mac_obj.get("phash") or "")):
                return {"valid": False, "reason": "preimage_hash_mismatch"}
            return {
                "valid": True,
                "protocol": "L402",
                "challenge_id": mac_obj.get("cid"),
                "tool": mac_obj.get("tool"),
                "amount_sats": mac_obj.get("sats"),
            }
        except Exception as exc:
            return {"valid": False, "reason": f"l402_decode_error:{type(exc).__name__}"}

    if raw.lower().startswith("x402 "):
        token_part = raw[5:].strip()
        if ":" not in token_part:
            return {"valid": False, "reason": "malformed_x402_token"}
        challenge_id, receipt_sig = token_part.split(":", 1)
        expected_receipt = derive_test_x402_receipt(challenge_id.strip())
        if hmac.compare_digest(receipt_sig.strip(), expected_receipt):
            return {
                "valid": True,
                "protocol": "x402",
                "challenge_id": challenge_id.strip(),
            }
        return {"valid": False, "reason": "invalid_x402_receipt_signature"}

    return {"valid": False, "reason": "unrecognized_authorization_scheme"}


def evaluate_request_gate(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """
    Evaluate whether a tool invocation fits within the free tier or requires/validates HTTP 402 payment.
    """
    args = arguments or {}
    proof = args.get("payment_proof") or args.get("authorization")

    metric_name = "items"
    usage_val = 1
    limit_val = 25

    if tool_name in ("repair_and_validate_structured_data", "exact_decimal_and_crypto_unit_math"):
        return {
            "allowed": True,
            "tier": "free_hook_tool",
            "metric": "unlimited_free_hook",
            "usage": 1,
            "free_limit": 250_000,
        }

    if tool_name == "subset_sum_reconcile":
        targets = args.get("targets") or []
        candidates = args.get("candidates") or []
        usage_val = len(targets) + len(candidates)
        limit_val = FREE_TIER_LIMITS["subset_sum_reconcile"]["max_total_items"]
        metric_name = "total_items"
        force_paid = bool(args.get("require_paid_batch"))
        if force_paid:
            usage_val = max(usage_val, limit_val + 1)

    elif tool_name == "stochastic_inventory_cashflow_solve":
        usage_val = int(args.get("num_paths") or 200)
        limit_val = FREE_TIER_LIMITS["stochastic_inventory_cashflow_solve"]["max_monte_carlo_paths"]
        metric_name = "num_paths"

    elif tool_name == "audit_smart_contract_invariants":
        src = str(args.get("source_code") or "")
        usage_val = len(src.splitlines())
        limit_val = FREE_TIER_LIMITS["audit_smart_contract_invariants"]["max_source_lines"]
        metric_name = "source_lines"
        if args.get("deep_audit") is True:
            usage_val = max(usage_val, limit_val + 1)

    elif tool_name == "inspect_csv_integrity":
        csv_text = str(args.get("csv_text") or "")
        rows = [ln for ln in csv_text.splitlines() if ln.strip()]
        usage_val = max(0, len(rows) - 1)
        limit_val = FREE_TIER_LIMITS["inspect_csv_integrity"]["max_csv_rows"]
        metric_name = "csv_rows"
        if args.get("deep_scan") is True:
            usage_val = max(usage_val, limit_val + 1)

    if usage_val <= limit_val:
        return {
            "allowed": True,
            "tier": "free_trial",
            "metric": metric_name,
            "usage": usage_val,
            "free_limit": limit_val,
        }

    if proof:
        ver = verify_payment_proof(proof)
        if ver.get("valid"):
            return {
                "allowed": True,
                "tier": "paid_unlocked",
                "payment": ver,
                "metric": metric_name,
                "usage": usage_val,
                "free_limit": limit_val,
            }
        challenge = issue_402_challenge(tool_name, metric_name, usage_val, limit_val)
        challenge["payment_verification_error"] = ver.get("reason")
        return {
            "allowed": False,
            "tier": "payment_required",
            "challenge": challenge,
        }

    return {
        "allowed": False,
        "tier": "payment_required",
        "challenge": issue_402_challenge(tool_name, metric_name, usage_val, limit_val),
    }
