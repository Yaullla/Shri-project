"""No model calls; verifies real MCP discovery and execution over stdio."""
import asyncio
import sys
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport


async def main():
    root = Path(__file__).resolve().parents[1]
    transport = StdioTransport(command=sys.executable,
                               args=["-m", "radar.server"], cwd=str(root), keep_alive=False)
    async with Client(transport, mode="legacy") as client:
        names = {t.name for t in await client.list_tools()}
        expected = {"calculate_margin", "competitive_price", "source_health",
                    "inspect_snapshot", "price_history", "find_deals", "get_exchange_rates"}
        assert expected <= names, names
        result = await client.call_tool("calculate_margin", {
            "purchase_rub": 10000, "sale_rub": 20000, "shipping_rub": 1000,
            "customs_rub": 2000, "other_cost_rub": 500, "fee_percent": 12})
        assert result.data["profit_rub"] == 4100, result.data
        assert result.data["margin_percent"] == 20.5, result.data
        print(f"MCP stdio verified: {len(names)} tools; financial test passed")


if __name__ == "__main__":
    asyncio.run(main())
