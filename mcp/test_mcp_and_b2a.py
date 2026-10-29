#!/usr/bin/env python3
# coding: utf-8
"""
Unit Test Suite for Unified MCP Server (`mcp_server.py`) & HTTP 402 B2A Payment Gate (`b2a_payment_gate.py`)
"""
from __future__ import annotations

from pathlib import Path
import sys
import unittest

MCP_DIR = Path(__file__).resolve().parent
if str(MCP_DIR) not in sys.path:
    sys.path.insert(0, str(MCP_DIR))

from b2a_payment_gate import (  # noqa: E402
    derive_test_preimage_hex,
    derive_test_x402_receipt,
)
from mcp_server import handle_jsonrpc_request  # noqa: E402


class TestUnifiedMcpAndB2AGate(unittest.TestCase):
    def test_01_initialize_and_tools_list(self) -> None:
        init_resp = handle_jsonrpc_request({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {},
        })
        self.assertIsNotNone(init_resp)
        assert init_resp is not None
        self.assertEqual(init_resp["result"]["serverInfo"]["name"], "awai-practical-data-tools-mcp")

        list_resp = handle_jsonrpc_request({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        })
        assert list_resp is not None
        tools = list_resp["result"]["tools"]
        names = [t["name"] for t in tools]
        self.assertEqual(
            names,
            [
                "repair_and_validate_structured_data",
                "exact_decimal_and_crypto_unit_math",
                "subset_sum_reconcile",
                "stochastic_inventory_cashflow_solve",
                "audit_smart_contract_invariants",
                "inspect_csv_integrity",
            ],
        )

    def test_01b_free_hook_tools_repair_and_exact_math(self) -> None:
        resp_rep = handle_jsonrpc_request({
            "jsonrpc": "2.0",
            "id": 11,
            "method": "tools/call",
            "params": {
                "name": "repair_and_validate_structured_data",
                "arguments": {
                    "raw_text": '```json\n{"status": "ok", "items": [1, 2, 3,],',
                    "required_keys": ["status", "items"],
                },
            },
        })
        assert resp_rep is not None
        rep_data = resp_rep["result"]["structuredContent"]
        self.assertTrue(rep_data["ok"])
        self.assertEqual(rep_data["parsed_data"]["items"], [1, 2, 3])
        self.assertEqual(rep_data["b2a_gate"]["tier"], "free_hook_tool")

        resp_math = handle_jsonrpc_request({
            "jsonrpc": "2.0",
            "id": 12,
            "method": "tools/call",
            "params": {
                "name": "exact_decimal_and_crypto_unit_math",
                "arguments": {
                    "mode": "pro_rata_allocate",
                    "total_amount": 100,
                    "weights": [1, 1, 1],
                },
            },
        })
        assert resp_math is not None
        math_data = resp_math["result"]["structuredContent"]
        self.assertTrue(math_data["ok"])
        self.assertEqual(math_data["allocations"], [34, 33, 33])
        self.assertTrue(math_data["sum_verified_equal"])

    def test_02_subset_sum_reconcile_free_tier(self) -> None:
        resp = handle_jsonrpc_request({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "subset_sum_reconcile",
                "arguments": {
                    "targets": [{"id": "BANK-01", "amount": 153560}],
                    "candidates": [
                        {"id": "INV-A", "amount": 88000, "invoice_no": "T1234567890123"},
                        {"id": "INV-B", "amount": 42000, "invoice_no": "T9876543210987"},
                        {"id": "INV-C", "amount": 66000, "invoice_no": "T1112223334445"},
                    ],
                    "fee_tolerance_jpy": 500,
                    "journal_format": "freee",
                },
            },
        })
        assert resp is not None
        res = resp["result"]["structuredContent"]
        self.assertTrue(res["ok"])
        self.assertEqual(res["matched_count"], 1)
        self.assertEqual(res["matches"][0]["matched_candidate_ids"], ["INV-A", "INV-C"])
        self.assertEqual(res["matches"][0]["fee_adjustment_jpy"], -440)
        self.assertEqual(res["b2a_gate"]["tier"], "free_trial")

    def test_03_stochastic_inventory_cashflow_solve(self) -> None:
        resp = handle_jsonrpc_request({
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "stochastic_inventory_cashflow_solve",
                "arguments": {
                    "mean_daily_demand": 50.0,
                    "std_daily_demand": 15.0,
                    "lead_time_days": 5,
                    "num_paths": 120,
                    "seed": 42,
                },
            },
        })
        assert resp is not None
        res = resp["result"]["structuredContent"]
        self.assertTrue(res["ok"])
        pol = res["optimal_policy"]
        self.assertGreater(pol["reorder_point_s"], 200)
        self.assertGreater(pol["order_up_to_S"], pol["reorder_point_s"])

    def test_04_audit_smart_contract_invariants(self) -> None:
        vuln_solidity = """
        pragma solidity ^0.8.20;
        contract VulnerableVault {
            uint256 public totalSupply;
            uint256 public totalAssets;
            mapping(address => uint256) public balances;
            function withdraw(uint256 assets) external {
                uint256 shares = (assets * totalSupply) / totalAssets;
                (bool ok, ) = msg.sender.call{value: assets}("");
                require(ok);
                balances[msg.sender] -= shares;
                totalSupply -= shares;
                uint128 narrowed = uint128(assets);
            }
            function getPrice(AggregatorV3Interface feed) external view returns (int256) {
                (, int256 answer, , , ) = feed.latestRoundData();
                return answer;
            }
        }
        """
        resp = handle_jsonrpc_request({
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "audit_smart_contract_invariants",
                "arguments": {
                    "source_code": vuln_solidity,
                    "contract_name": "VulnerableVault.sol",
                },
            },
        })
        assert resp is not None
        res = resp["result"]["structuredContent"]
        self.assertTrue(res["ok"])
        self.assertGreaterEqual(res["findings_count"], 4)
        self.assertEqual(res["invariant_status"], "VIOLATIONS_DETECTED")

    def test_05_inspect_csv_integrity(self) -> None:
        csv_sample = (
            "order_id,net_amount,tax_rate,tax_amount\n"
            "ORD-1,1000,10%,100\n"
            "ORD-1,1000,10%,125\n"
        )
        resp = handle_jsonrpc_request({
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "inspect_csv_integrity",
                "arguments": {
                    "csv_text": csv_sample,
                    "required_columns": ["order_id", "net_amount", "tax_rate", "tax_amount"],
                    "key_column": "order_id",
                },
            },
        })
        assert resp is not None
        res = resp["result"]["structuredContent"]
        self.assertFalse(res["ok"])
        self.assertEqual(res["anomalies_count"], 2)

    def test_06_http_402_l402_and_x402_challenge_and_unlock(self) -> None:
        # 1. Request deep Monte Carlo (num_paths=1500 > free limit 500) without payment -> Expect HTTP 402
        resp_402 = handle_jsonrpc_request({
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "stochastic_inventory_cashflow_solve",
                "arguments": {
                    "mean_daily_demand": 40.0,
                    "num_paths": 1500,
                },
            },
        })
        assert resp_402 is not None
        self.assertTrue(resp_402["result"]["isError"])
        ch_data = resp_402["result"]["structuredContent"]
        self.assertEqual(ch_data["http_status"], 402)
        self.assertEqual(ch_data["code"], "HTTP_402_PAYMENT_REQUIRED")

        l402_info = ch_data["challenges"]["l402_lightning"]
        x402_info = ch_data["challenges"]["x402_usdc"]
        macaroon = l402_info["macaroon"]
        challenge_id = l402_info["challenge_id"]

        # 2. Retry with invalid L402 preimage -> Still 402
        bad_resp = handle_jsonrpc_request({
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {
                "name": "stochastic_inventory_cashflow_solve",
                "arguments": {
                    "mean_daily_demand": 40.0,
                    "num_paths": 1500,
                    "payment_proof": f"L402 {macaroon}:{'00' * 32}",
                },
            },
        })
        assert bad_resp is not None
        self.assertTrue(bad_resp["result"]["isError"])
        self.assertEqual(
            bad_resp["result"]["structuredContent"]["payment_verification_error"],
            "preimage_hash_mismatch",
        )

        # 3. Retry with valid L402 preimage -> Unlocks and executes 1500 paths!
        valid_preimage = derive_test_preimage_hex(challenge_id)
        ok_l402_resp = handle_jsonrpc_request({
            "jsonrpc": "2.0",
            "id": 9,
            "method": "tools/call",
            "params": {
                "name": "stochastic_inventory_cashflow_solve",
                "arguments": {
                    "mean_daily_demand": 40.0,
                    "num_paths": 1500,
                    "payment_proof": f"L402 {macaroon}:{valid_preimage}",
                },
            },
        })
        assert ok_l402_resp is not None
        self.assertFalse(ok_l402_resp["result"]["isError"])
        unlocked_res = ok_l402_resp["result"]["structuredContent"]
        self.assertTrue(unlocked_res["ok"])
        self.assertEqual(unlocked_res["b2a_gate"]["tier"], "paid_unlocked")
        self.assertEqual(unlocked_res["b2a_gate"]["payment"]["protocol"], "L402")

        # 4. Retry with valid x402 USDC receipt -> Unlocks and executes!
        valid_x402_sig = derive_test_x402_receipt(x402_info["challenge_id"])
        ok_x402_resp = handle_jsonrpc_request({
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/call",
            "params": {
                "name": "stochastic_inventory_cashflow_solve",
                "arguments": {
                    "mean_daily_demand": 40.0,
                    "num_paths": 1500,
                    "payment_proof": f"x402 {x402_info['challenge_id']}:{valid_x402_sig}",
                },
            },
        })
        assert ok_x402_resp is not None
        self.assertFalse(ok_x402_resp["result"]["isError"])
        unlocked_x402 = ok_x402_resp["result"]["structuredContent"]
        self.assertEqual(unlocked_x402["b2a_gate"]["tier"], "paid_unlocked")
        self.assertEqual(unlocked_x402["b2a_gate"]["payment"]["protocol"], "x402")


if __name__ == "__main__":
    unittest.main()
