---
name: crypto-tracing
description: Trace cryptocurrency wallets across BTC, ETH (and EVM chains), TRX, SOL. Identifies exchange deposits (subpoena-able choke points), tags via WalletExplorer / Chainabuse, screens against OFAC sanctions, follows funds to mixers / cash-out.
---

# Crypto Tracing Skill

The operational playbook for `financial-tracer` subagent. Built around free public APIs; paid feeds (Etherscan keyed, Blockchair Pro) optional.

## Coverage

| Chain | Explorer (preferred) | Fallback | Tagging |
| --- | --- | --- | --- |
| BTC | mempool.space + blockchair.com/bitcoin | btc.com | walletexplorer.com (best clustering) |
| ETH | etherscan.io (key) | blockchair.com/ethereum | etherscan tags + Chainabuse |
| EVM (BSC/Polygon/Arbitrum/Optimism/Base) | <chain>scan.com (key) | blockchair.com | Chainabuse |
| TRX (USDT-TRC20) | tronscan.org | blockchair.com/tron | Chainabuse (heavy use for scams) |
| SOL | solscan.io | solana.fm | manual |
| XMR | — | — | non-attributable; flag as trail-broken |

## Per-wallet workflow

### 1. Activity sketch
```bash
# BTC
curl -s "https://api.blockchair.com/bitcoin/dashboards/address/${ADDR}"  | jq .
# ETH
curl -s "https://api.etherscan.io/api?module=account&action=txlist&address=${ADDR}&apikey=${ETHERSCAN_API_KEY}" | jq .
# TRX
curl -s "https://apilist.tronscanapi.com/api/transaction?address=${ADDR}&limit=200" | jq .
```
Capture: balance, tx count, first-seen, last-seen, top-N counterparties by volume.

### 2. Tag known entities
```bash
# Walletexplorer (BTC) — exchange / mixer / service tagging
curl -s "https://www.walletexplorer.com/api/1/address?address=${ADDR}&caller=hunter"
# Chainabuse — community-reported scam wallets, all chains
curl -s "https://www.chainabuse.com/api/v0/reports?address=${ADDR}"
# OFAC SDN screen via world-intel-mcp
# (call mcp__world-intel__intel_sanctions_search with the address)
```

### 3. Follow the money
For each top counterparty (by volume), recurse one hop. Stop at:
- An exchange deposit — this is a **subpoena-able choke point**. Record the deposit tx-hash, exchange name, date. **This is the most important artifact for a scam-attribution case.**
- A known mixer (Tornado Cash, Wasabi CoinJoin, Samourai Whirlpool) — trail broken. Mark as `mixed`.
- A peeled chain that appears to be self-shuffling — keep going one more hop only.

### 4. Cluster siblings
- **BTC common-input heuristic** — all inputs in one tx are typically controlled by one entity. Use this to cluster wallets.
- **EVM nonce sequence** — same nonce-jump pattern from a deposit address suggests script / same operator.
- **Withdrawal-pattern fingerprint** — withdrawal amounts and timings from an exchange across N wallets are an identity signal.

## Sanctions / regulatory hits

- OFAC SDN: any wallet on the list → funds were sanctioned-actor-touched. Notify the user this elevates the case (banks/exchanges have mandatory reporting).
- Chainabuse ≥ 5 reports → community-confirmed scam.
- Tornado Cash (post-2022 OFAC) → sanctioned mixer, additional reporting weight.

## Output

Per wallet, return:
- Activity sketch with EV-IDs.
- Tags (walletexplorer / chainabuse / OFAC).
- Hop-by-hop money trail (max-depth as scope).
- The **subpoena-able choke point(s)** — explicit, named, with tx-hash and date.
- Recommendations: who to contact (exchange compliance, IC3 if US, Action Fraud if UK, national CERT), with a templated email body.

## Known gaps

- This skill does not cover wire-fraud bank tracing — that requires LE engagement.
- Privacy chains (XMR) and privacy mixers break the trail. Mark and stop.
- DEX swap pivots (Uniswap / Curve LP movements) — limited public attribution.
