from typing import Any
import asyncio
import httpx
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
import urllib.parse
import json


API_BASE = "pro-api.coinmarketcap.com"
API_KEY = None
DEFI_API_KEY = None


server = Server("coin-api")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    List available tools.
    Each tool specifies its arguments using JSON Schema validation.
    """
    return [
        types.Tool(
            name="listing-coins",
            description="Returns a paginated list of all active cryptocurrencies with latest market data",
            inputSchema={
                "type": "object",
                "properties": {
                    "start": {
                        "type": "integer",
                        "description": "Optionally offset the start (1-based index) of the paginated list of items to return.",
                        "minimum": 1,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Optionally specify the number of results to return.",
                        "minimum": 1,
                        "maximum": 5000,
                    },
                    "price_min": {
                        "type": "number",
                        "description": "Optionally specify a threshold of minimum USD price to filter results by.",
                        "minimum": 0,
                    },
                    "price_max": {
                        "type": "number",
                        "description": "Optionally specify a threshold of maximum USD price to filter results by.",
                        "minimum": 0,
                    },
                    "market_cap_min": {
                        "type": "number",
                        "description": "Optionally specify a threshold of minimum market cap to filter results by.",
                        "minimum": 0,
                    },
                    "market_cap_max": {
                        "type": "number",
                        "description": "Optionally specify a threshold of maximum market cap to filter results by.",
                        "minimum": 0,
                    },
                    "volume_24h_min": {
                        "type": "number",
                        "description": "Optionally specify a threshold of minimum 24 hour USD volume to filter results by.",
                        "minimum": 0,
                    },
                    "volume_24h_max": {
                        "type": "number",
                        "description": "Optionally specify a threshold of maximum 24 hour USD volume to filter results by.",
                        "minimum": 0,
                    },
                    "circulating_supply_min": {
                        "type": "number",
                        "description": "Optionally specify a threshold of minimum circulating supply to filter results by.",
                        "minimum": 0,
                    },
                    "circulating_supply_max": {
                        "type": "number",
                        "description": "Optionally specify a threshold of maximum circulating supply to filter results by.",
                        "minimum": 0,
                    },
                    "percent_change_24h_min": {
                        "type": "number",
                        "description": "Optionally specify a threshold of minimum 24 hour percent change to filter results by.",
                        "minimum": -100,
                    },
                    "percent_change_24h_max": {
                        "type": "number",
                        "description": "Optionally specify a threshold of maximum 24 hour percent change to filter results by.",
                        "minimum": -100,
                    },
                    "convert": {
                        "type": "string",
                        "description": "Optionally calculate market quotes in up to 120 currencies at once by passing a comma-separated list of cryptocurrency or fiat currency symbols.",
                    },
                    "convert_id": {
                        "type": "string",
                        "description": "Optionally calculate market quotes by CoinMarketCap ID instead of symbol.",
                    },
                    "sort": {
                        "type": "string",
                        "description": "What field to sort the list of cryptocurrencies by.",
                        "enum": [
                            "market_cap",
                            "name",
                            "symbol",
                            "date_added",
                            "market_cap_strict",
                            "price",
                            "circulating_supply",
                            "total_supply",
                            "max_supply",
                            "num_market_pairs",
                            "volume_24h",
                            "percent_change_1h",
                            "percent_change_24h",
                            "percent_change_7d",
                            "market_cap_by_total_supply_strict",
                            "volume_7d",
                            "volume_30d",
                        ],
                    },
                    "sort_dir": {
                        "type": "string",
                        "description": "The direction in which to order cryptocurrencies against the specified sort.",
                        "enum": ["asc", "desc"],
                    },
                    "cryptocurrency_type": {
                        "type": "string",
                        "description": "The type of cryptocurrency to include.",
                        "enum": ["all", "coins", "tokens"],
                    },
                    "tag": {
                        "type": "string",
                        "description": "The tag of cryptocurrency to include.",
                        "enum": ["all", "defi", "filesharing"],
                    },
                    "aux": {
                        "type": "string",
                        "description": "Optionally specify a comma-separated list of supplemental data fields to return.",
                    },

                },
                "required": [],
            },
        ),
        types.Tool(
            name="get-coin-info",
            description="Get coins' information includes details like logo, description, official website URL, social links, and links to a cryptocurrency's technical documentation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "One or more comma-separated CoinMarketCap cryptocurrency IDs. Example: \"1,2\"",
                    },
                    "slug": {
                        "type": "string",
                        "description": "Alternatively pass a comma-separated list of cryptocurrency slugs. Example: \"bitcoin,ethereum\"",
                    },
                    "symbol": {
                        "type": "string",
                        "description": "Alternatively pass one or more comma-separated cryptocurrency symbols. Example: \"BTC,ETH\"",
                    },
                    "address": {
                        "type": "string",
                        "description": "Alternatively pass in a contract address. Example: \"0xc40af1e4fecfa05ce6bab79dcd8b373d2e436c4e\"",
                    },
                    "skip_invalid": {
                        "type": "boolean",
                        "description": "Pass true to relax request validation rules. When requesting records on multiple cryptocurrencies an error is returned if any invalid cryptocurrencies are requested or a cryptocurrency does not have matching records in the requested timeframe. If set to true, invalid lookups will be skipped allowing valid cryptocurrencies to still be returned.",
                        "default": False,
                    },
                    "aux": {
                        "type": "string",
                        "description": "Optionally specify a comma-separated list of supplemental data fields to return. Pass urls,logo,description,tags,platform,date_added,notice,status to include all auxiliary fields.",
                    },
                },
                "required": [],
            }
        ),
        types.Tool(
            name="get-coin-quotes",
            description='''the latest market quote for 1 or more cryptocurrencies. Use the "convert" option to return market values in multiple fiat and cryptocurrency conversions in the same call.''',
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "One or more comma-separated cryptocurrency CoinMarketCap IDs. Example: 1,2",
                    },
                    "slug": {
                        "type": "string",
                        "description": "Alternatively pass a comma-separated list of cryptocurrency slugs. Example: \"bitcoin,ethereum\"",
                    },
                    "symbol": {
                        "type": "string",
                        "description": "Alternatively pass one or more comma-separated cryptocurrency symbols. Example: \"BTC,ETH\"",
                    },
                    "convert": {
                        "type": "string",
                        "description": "Optionally calculate market quotes in up to 120 currencies at once by passing a comma-separated list of cryptocurrency or fiat currency symbols.",
                    },
                    "convert_id": {
                        "type": "string",
                        "description": "Optionally calculate market quotes by CoinMarketCap ID instead of symbol. This option is identical to convert outside of ID format.",
                    },
                    "aux": {
                        "type": "string",
                        "description": "\"num_market_pairs,cmc_rank,date_added,tags,platform,max_supply,circulating_supply,total_supply,is_active,is_fiat\"Optionally specify a comma-separated list of supplemental data fields to return.",
                    },
                    "skip_invalid": {
                        "type": "boolean",
                        "description": "Pass true to relax request validation rules.",
                        "default": False,
                    },
                },
                "required": [],
            },
        ),
        types.Tool(
            name="get-protocols",
            description='''List all protocols along with their tvl(total value locked).''',
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "One or more comma-separated cryptocurrency CoinMarketCap IDs. Example: 1,2",
                    },
                    "slug": {
                        "type": "string",
                        "description": "Alternatively pass a comma-separated list of cryptocurrency slugs. Example: \"bitcoin,ethereum\"",
                    },
                    "symbol": {
                        "type": "string",
                        "description": "Alternatively pass one or more comma-separated cryptocurrency symbols. Example: \"BTC,ETH\"",
                    },
                    "convert": {
                        "type": "string",
                        "description": "Optionally calculate market quotes in up to 120 currencies at once by passing a comma-separated list of cryptocurrency or fiat currency symbols.",
                    },
                    "convert_id": {
                        "type": "string",
                        "description": "Optionally calculate market quotes by CoinMarketCap ID instead of symbol. This option is identical to convert outside of ID format.",
                    },
                    "aux": {
                        "type": "string",
                        "description": "\"num_market_pairs,cmc_rank,date_added,tags,platform,max_supply,circulating_supply,total_supply,is_active,is_fiat\"Optionally specify a comma-separated list of supplemental data fields to return.",
                    },
                    "skip_invalid": {
                        "type": "boolean",
                        "description": "Pass true to relax request validation rules.",
                        "default": False,
                    },
                },
                "required": [],
            },
        ),
        types.Tool(
            name="listing-protocols",
            description="Get detailed information about a specific protocol including its TVL, supported chains, and other metadata",
            inputSchema={
                "type": "object",
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "The unique identifier of the protocol",
                    },
                    "name": {
                        "type": "string",
                        "description": "The name of the protocol",
                    },
                    "symbol": {
                        "type": "string",
                        "description": "The symbol associated with the protocol",
                    },
                    "url": {
                        "type": "string",
                        "description": "The official website URL of the protocol",
                    },
                    "description": {
                        "type": "string",
                        "description": "A detailed description of the protocol",
                    },
                    "chain": {
                        "type": "string",
                        "description": "The primary chain the protocol operates on",
                    },
                    "logo": {
                        "type": "string",
                        "description": "URL to the protocol's logo image",
                    },
                    "audits": {
                        "type": "string",
                        "description": "Number of security audits performed",
                    },
                    "audit_note": {
                        "type": ["string", "null"],
                        "description": "Additional notes about protocol audits",
                    },
                    "category": {
                        "type": "string",
                        "description": "The category of the protocol (e.g., CEX, DEX, Lending)",
                    },
                    "chains": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of blockchain networks supported by the protocol",
                    },
                    "twitter": {
                        "type": "string",
                        "description": "Twitter handle of the protocol",
                    },
                    "forkedFrom": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of protocols this one was forked from",
                    },
                    "oracles": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of oracle services used by the protocol",
                    },
                    "listedAt": {
                        "type": "integer",
                        "description": "Unix timestamp when the protocol was first listed",
                    },
                    "methodology": {
                        "type": "string",
                        "description": "Description of how protocol data is collected and calculated",
                    },
                    "slug": {
                        "type": "string",
                        "description": "URL-friendly identifier for the protocol",
                    },
                    "tvl": {
                        "type": "number",
                        "description": "Total Value Locked in the protocol across all chains",
                    },
                    "chainTvls": {
                        "type": "object",
                        "description": "Breakdown of TVL by individual chains",
                        "additionalProperties": {
                            "type": "number"
                        }
                    },
                    "change_1h": {
                        "type": "number",
                        "description": "Percentage change in TVL over the last hour",
                    },
                    "change_1d": {
                        "type": "number",
                        "description": "Percentage change in TVL over the last 24 hours",
                    },
                    "change_7d": {
                        "type": "number",
                        "description": "Percentage change in TVL over the last 7 days",
                    },
                    "tokenBreakdowns": {
                        "type": "object",
                        "description": "Breakdown of protocol's token distributions",
                        "additionalProperties": {
                            "type": "object"
                        }
                    },
                    "mcap": {
                        "type": ["number", "null"],
                        "description": "Market capitalization of the protocol's token",
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="get-protocol-tvl",
            description="Fetches the Total Value Locked (TVL) for a specific protocol.",
            inputSchema={
                "type": "object",
                "properties": {
                    "protocol": {
                        "type": "string",
                        "description": "The URL-friendly identifier for the protocol.",
                    },
                },
                "required": ["protocol"],
            },
        ),
        types.Tool(
            name="get-apr",
            description="Fetches the Annual Percentage Rate for a specific protocol.",
            inputSchema={
                "type": "object",
                "properties": {
                    "liquidStakingId": {
                        "type": "string",
                        "description": "ID for liquid staking. This ID is required to get the APR for the protocol",
                    },
                },
                "required": ["liquidStakingId"],
            },
        ),
    ]


async def make_coinmarketcap_request(client: httpx.AsyncClient, url: str) -> dict[str, Any] | None:
    """Make a request to the CoinMarketCap API with proper error handling."""
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': API_KEY,
    }
    try:
        response = await client.get(url, headers=headers, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


async def make_defillama_request(client: httpx.AsyncClient, url: str) -> dict[str, Any] | None:
    """Make a request to the DeFi Llama API with proper error handling."""
    headers = {
        'accept': '*/*',
    }
    try:
        response = await client.get(url, headers=headers, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


async def make_expand_network_request(client: httpx.AsyncClient, url: str) -> dict[str, Any] | None:
    """Make a request to the Expand Network API with proper error handling."""
    headers = {
        'accept': '*/*',
        'X-API-Key': DEFI_API_KEY,

    }
    try:
        response = await client.get(url, headers=headers, timeout=10.0)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool execution requests.
    Currently supported tools:
    - listing-coins: fetches a list of all cryptocurrencies.
    - get-coin-quotes: fetches quotes for a specific cryptocurrency.
    - get-coin-info: fetches information for a specific cryptocurrency.
    - listing-protocols : fetches a list of all protocols along with their tvl. 
    - get-protocol-tvl : fetches a tvl for the particular protocol.
    - get-apr : fetches APR for the particular protocol.
    """

    if name == "listing-coins":
        request_data = {}
        if arguments is not None:
            condi_keys = [
                "start",
                "limit",
                "price_min",
                "price_max",
                "market_cap_min",
                "market_cap_max",
                "volume_24h_min",
                "volume_24h_max",
                "circulating_supply_min",
                "circulating_supply_max",
                "percent_change_24h_min",
                "percent_change_24h_max",
                "convert",
                "convert_id",
                "sort",
                "sort_dir",
                "cryptocurrency_type",
                "tag",
                "aux",
            ]

            for key in arguments.keys():
                if key in condi_keys:
                    request_data[key] = arguments[key]

        async with httpx.AsyncClient() as client:
            listing_url = f"https://{API_BASE}/v1/cryptocurrency/listings/latest?{urllib.parse.urlencode(request_data)}"

            listing_data = await make_coinmarketcap_request(client, listing_url)

            if not listing_data:
                return [types.TextContent(type="text", text="Failed to retrieve listing data")]

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(listing_data)
                )
            ]
    elif name == "get-coin-info":
        request_data = {}
        if arguments is not None:
            condi_keys = [
                "id",
                "slug",
                "symbol",
                "address",
                "skip_invalid",
                "aux",
            ]

            for key in arguments.keys():
                if key in condi_keys:
                    request_data[key] = arguments[key]

        async with httpx.AsyncClient() as client:
            coin_info_url = f"https://{API_BASE}/v2/cryptocurrency/info?{urllib.parse.urlencode(request_data)}"

            coin_info_data = await make_coinmarketcap_request(client, coin_info_url)

            if not coin_info_data:
                return [types.TextContent(type="text", text="Failed to retrieve coin info data")]

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(coin_info_data)
                )
            ]
    elif name == "get-coin-quotes":
        request_data = {}
        if arguments is not None:
            condi_keys = [
                "id",
                "slug",
                "symbol",
                "convert",
                "convert_id",
                "aux",
                "skip_invalid",
            ]

            for key in arguments.keys():
                if key in condi_keys:
                    request_data[key] = arguments[key]

        async with httpx.AsyncClient() as client:
            coin_quotes_url = f"https://{API_BASE}/v2/cryptocurrency/quotes/latest?{urllib.parse.urlencode(request_data)}"

            coin_quotes_data = await make_coinmarketcap_request(client, coin_quotes_url)

            if not coin_quotes_data:
                return [types.TextContent(type="text", text="Failed to retrieve coin quotes data")]

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(coin_quotes_data)
                )
            ]
    elif name == "listing-protocols":

        async with httpx.AsyncClient() as client:
            protocols_url = "https://api.llama.fi/protocols"

            protocols_data = await make_defillama_request(client, protocols_url)

            if not protocols_data:
                return [types.TextContent(type="text", text="Failed to retrieve protocols data")]

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(protocols_data)
                )
            ]
    elif name == "get-protocol-tvl":
        request_data = {}
        if arguments is not None:
            condi_keys = [
                "protocol",
            ]

            for key in arguments.keys():
                if key in condi_keys:
                    request_data[key] = arguments[key]

        async with httpx.AsyncClient() as client:
            protocols_url = f"https://api.llama.fi/tvl/{request_data["protocol"]}"

            protocols_data = await make_defillama_request(client, protocols_url)

            if not protocols_data:
                return [types.TextContent(type="text", text="Failed to retrieve protocols tvl data")]

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(protocols_data)
                )
            ]
    elif name == "get-apr":
        request_data = {}
        if arguments is not None:
            condi_keys = [
                "liquidStakingId",
            ]

            for key in arguments.keys():
                if key in condi_keys:
                    request_data[key] = arguments[key]

        async with httpx.AsyncClient() as client:
            protocols_url = f"https://api.expand.network/liquidstaking/getapr?liquidStakingId={request_data['liquidStakingId']}"

            protocols_data = await make_expand_network_request(client, protocols_url)

            if not protocols_data:
                return [types.TextContent(type="text", text="Failed to retrieve protocols APR data.")]

            return [
                types.TextContent(
                    type="text",
                    text=json.dumps(protocols_data)
                )
            ]
    else:
        raise ValueError(f"Unknown tool: {name}")


async def main(api_key: str, defi_api_key: str):
    global API_KEY
    API_KEY = api_key
    global DEFI_API_KEY
    DEFI_API_KEY = defi_api_key
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="coin-api",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

# This is needed if you'd like to connect to a custom client
if __name__ == "__main__":
    # get api key from coinmarketcap
    api_key = "xxxxxxx"
    asyncio.run(main(api_key))
