# header-soundness-commitment

## Overview
This tiny tool checks **soundness** of Ethereum block headers across RPC providers (a practice inspired by Aztec/rollup integrity checks). It computes a deterministic commitment over key header fields and optionally cross-compares two RPC endpoints. If commitments differ for the same block, something is off.

## What it commits to
- `chainId`, `number`, `hash`, `parentHash`, `stateRoot`, `receiptsRoot`, `transactionsRoot`, `timestamp`  
- Commitment: `keccak(chainId[8] || number[8] || hash[32] || parentHash[32] || stateRoot[32] || receiptsRoot[32] || transactionsRoot[32] || timestamp[8])`

## Files
- `app.py` — CLI to fetch a block header, compute the commitment, and optionally compare between two RPCs.
- `README.md` — this file.

## Requirements
- Python 3.10+
- `web3.py`
- One or two Ethereum-compatible RPC URLs (Infura, Alchemy, your node)

## Installation
1) Install dependency:
   pip install web3
2) Set RPC(s) (optional; you can also pass via CLI):
   export RPC_URL="https://mainnet.infura.io/v3/<KEY>"
   export RPC_URL_2="https://rpc.ankr.com/eth"

## Usage
Basic (single provider):
   python app.py --block latest
With explicit RPC:
   python app.py --rpc1 https://mainnet.infura.io/v3/<KEY> --block 18000000
Cross-check two providers:
   python app.py --rpc1 https://mainnet.infura.io/v3/<KEY> --rpc2 https://rpc.ankr.com/eth --block finalized

## Expected output
- Network name and chain ID
- Block number, timestamp (UTC)
- Block hash, parent hash, stateRoot, receiptsRoot, transactionsRoot
- Header commitment
- If `--rpc2` is provided: a cross-check matrix indicating whether fields/commitments match

## Notes
- For tags like `latest/safe/finalized`, each RPC may resolve to different numbers depending on their view; pass a specific number to test strict equality.
- Differences may indicate provider lag, reorgs, differing pruning/merkleization, or RPC bugs; re-run with an exact block number to diagnose.
- Works on Mainnet, Sepolia, and other EVM networks; the commitment is chain-specific.
- This is a **commitment** (soundness) demo — not a zero-knowledge proof. You can embed the same hash in a ZK circuit later to privately attest header fields.
