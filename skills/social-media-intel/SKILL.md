---
name: social-media-intel
description: SOCMINT playbooks for Telegram, X/Twitter, Instagram, Facebook, TikTok, Discord, Reddit, LinkedIn. Public scraping only — no login-walled content, no private DMs, no auth bypass.
---

# Social Media Intelligence Skill

Pattern derived from `claude-skills-journalism/social-media-intelligence`. Public-only scraping; respect TOS.

## Telegram
- `t.me/<handle>` — profile preview.
- `t.me/s/<handle>` — last 20 messages public preview, no auth.
- `tgstat.com/<handle>` — stats / engagement / language detect.
- Channel-mention crawl: for each known related channel, search for the target string in `t.me/s/<other>` previews.

## X / Twitter
- `x.com/<handle>` — unauth limited.
- `nitter.net/<handle>` (and mirrors) — better unauth scraping when up.
- `https://web.archive.org/web/*/x.com/<handle>` and `twitter.com/<handle>` — historical state.
- Politwoops-style mirrors for deleted tweets (where applicable).

## Instagram
- `https://www.instagram.com/<handle>/` — limited unauth (often login-walled).
- Public profile JSON: `?__a=1` (rate-limited, may break).
- Wayback for historical posts.
- `imginn.com` and similar mirrors — verify content authenticity before trusting.

## Facebook
- Page transparency: `https://www.facebook.com/<page>/about_profile_transparency`. When public: page creation date, country, admin count, name-change history. **High-grade attribution data.**
- Wayback for historical state.
- Group/event listings — mostly login-walled; capture URLs only.

## TikTok
- `https://www.tiktok.com/@<handle>` — public profile + post listing (often unauth-accessible).
- Wayback.

## Discord
- `https://discord.com/invite/<code>` — server name, member count, online count.
- User-server membership requires mutuals — not unauth-accessible.

## Reddit
- `https://www.reddit.com/user/<handle>/.json?limit=100` — full public submission/comment history. **Highest-yield platform.**
- Subreddit membership pattern reveals interests.
- Karma history visible.

## LinkedIn
- Login-walled. Use Google cache + Wayback.
- Public sales-nav style profile URLs may surface in Google.

## Behavioral signals

Across every platform, capture:
- Account creation vs first-activity — large gap → purchased / stolen account.
- Posting timezone clusters — reveals operator working hours.
- Language and translation artifacts — native vs MT.
- Handle-reuse pattern — same username on N platforms (handle-correlation) is strong-but-not-conclusive.

## Evidence discipline

Every profile and quoted post → `evidence-officer` (Wayback + archive.today + screenshot + SHA-256). Posts can be edited/deleted at any time; what isn’t archived doesn’t exist.

## Refusals

- No login-bypass scraping.
- No private-DM or member-only content collection.
- No collection from accounts of obvious bystanders — limit to scope targets and direct interlocutors.
