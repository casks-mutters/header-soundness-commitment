# app.py
import os
import sys
import time
import argparse
from web3 import Web3

# Defaults (override via CLI flags)
DEFAULT_RPC1 = os.getenv("RPC_URL", "https://mainnet.infura.io/v3/your_api_key")
DEFAULT_RPC2 = os.getenv("RPC_URL_2")  # optional second provider

NETWORKS = {
    1: "Ethereum Mainnet",
    11155111: "Sepolia Testnet",
    10: "Optimism",
    137: "Polygon",
    42161: "Arbitrum One",
}

def network_name(cid: int) -> str:
    return NETWORKS.get(cid, f"Unknown (chain ID {cid})")

def w3_connect(url: str) -> Web3:
    w3 = Web3(Web3.HTTPProvider(url, request_kwargs={"timeout": 30}))
    if not w3.is_connected():
        print(f"❌ RPC connection failed: {url}")
        sys.exit(1)
    return w3

def parse_block_arg(arg: str):
    if arg.lower() in ("latest", "finalized", "safe", "pending"):
        return arg.lower()
    return int(arg, 0)

def header_commitment(chain_id: int, header) -> str:
    """
    Build a commitment over essential header fields (Aztec/rollup-style soundness idea):
    keccak(
      chainId[8] || number[8] || hash[32] || parentHash[32] ||
      stateRoot[32] || receiptsRoot[32] || transactionsRoot[32] || timestamp[8]
    )
    """
    num = int(header.number)
    ts = int(header.timestamp)
    fields = (
        chain_id.to_bytes(8, "big") +
        num.to_bytes(8, "big") +
        bytes.fromhex(header.hash.hex()[2:]) +
        bytes.fromhex(header.parentHash.hex()[2:]) +
        bytes.fromhex(header.stateRoot.hex()[2:]) +
        bytes.fromhex(header.receiptsRoot.hex()[2:]) +
        bytes.fromhex(header.transactionsRoot.hex()[2:]) +
        ts.to_bytes(8, "big")
    )
    return "0x" + Web3.keccak(fields).hex()

def fetch_header_bundle(w3: Web3, block_id):
    header = w3.eth.get_block(block_id)
    bundle = {
        "chain_id": w3.eth.chain_id,
        "network": network_name(w3.eth.chain_id),
        "number": int(header.number),
        "timestamp": int(header.timestamp),
        "hash": header.hash.hex(),
        "parentHash": header.parentHash.hex(),
        "stateRoot": header.stateRoot.hex(),
        "receiptsRoot": header.receiptsRoot.hex(),
        "transactionsRoot": header.transactionsRoot.hex(),
    }
    bundle["commitment"] = header_commitment(bundle["chain_id"], header)
    return bundle

def print_bundle(label: str, b: dict):
    print(f"— {label} —")
    print(f"🌐 Network: {b['network']} (chainId {b['chain_id']})")
    print(f"🔢 Block: {b['number']}  ⏱️ {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(b['timestamp']))} UTC")
    print(f"🔗 Hash: {b['hash']}")
    print(f"↩️  Parent: {b['parentHash']}")
    print(f"🌳 stateRoot: {b['stateRoot']}")
    print(f"🧾 receiptsRoot: {b['receiptsRoot']}")
    print(f"📦 txRoot: {b['transactionsRoot']}")
    print(f"🧩 Header Commitment: {b['commitment']}")

def compare(a: dict, b: dict):
    print("— Cross-check —")
    same_chain = a["chain_id"] == b["chain_id"]
    same_num = a["number"] == b["number"]
    same_hash = a["hash"] == b["hash"]
    same_parent = a["parentHash"] == b["parentHash"]
    same_state = a["stateRoot"] == b["stateRoot"]
    same_receipts = a["receiptsRoot"] == b["receiptsRoot"]
    same_txroot = a["transactionsRoot"] == b["transactionsRoot"]
    same_commit = a["commitment"] == b["commitment"]

    print(f"Chain IDs match:       {'✅' if same_chain else '❌'}")
    print(f"Block numbers match:   {'✅' if same_num else '❌'}")
    print(f"Block hashes match:    {'✅' if same_hash else '❌'}")
    print(f"Parent hashes match:   {'✅' if same_parent else '❌'}")
    print(f"stateRoot matches:     {'✅' if same_state else '❌'}")
    print(f"receiptsRoot matches:  {'✅' if same_receipts else '❌'}")
    print(f"txRoot matches:        {'✅' if same_txroot else '❌'}")
    print(f"Commitments match:     {'✅' if same_commit else '❌'}")

    if all([same_chain, same_num, same_hash, same_parent, same_state, same_receipts, same_txroot, same_commit]):
        print("🔒 Soundness confirmed across providers.")
    else:
        print("⚠️  Inconsistency detected — check providers, block tag, or try again.")

def parse_args():
    p = argparse.ArgumentParser(description="Header soundness: compare block header commitments across RPCs.")
    p.add_argument("--rpc1", default=DEFAULT_RPC1, help="Primary RPC URL (default from RPC_URL env or Infura template)")
    p.add_argument("--rpc2", default=DEFAULT_RPC2, help="Secondary RPC URL for cross-check (optional; env RPC_URL_2)")
    p.add_argument("--block", default="latest", help="Block tag or number (latest|finalized|safe|pending or int)")
    return p.parse_args()

def main():
    args = parse_args()
    if not args.rpc1:
        print("❌ Missing --rpc1 or RPC_URL env.")
        sys.exit(1)

    try:
        block_id = parse_block_arg(args.block)
    except Exception:
        print("❌ Invalid --block value. Use a number or one of latest|finalized|safe|pending.")
        sys.exit(1)

    t0 = time.time()
    w3a = w3_connect(args.rpc1)
    primary = fetch_header_bundle(w3a, block_id)
    print_bundle("PRIMARY", primary)

    if args.rpc2:
        w3b = w3_connect(args.rpc2)
        # If tag is "latest/safe/finalized", resolve number on each provider independently
        b_id = primary["number"] if isinstance(block_id, int) else block_id
        secondary = fetch_header_bundle(w3b, b_id)
        print_bundle("SECONDARY", secondary)
        compare(primary, secondary)

    print(f"⏱️  Elapsed: {time.time() - t0:.2f}s")

if __name__ == "__main__":
    main()
