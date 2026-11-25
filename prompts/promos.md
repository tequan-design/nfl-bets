# Promo scan (daily ~3:23pm ET, plus Sat/Sun ~10:17am ET)

Goal: find promos the user can actually use on PrizePicks, Underdog, Betr, Kalshi, Polymarket, and keep
`memory/promos.md` current so picks can be built around them.

1. `git pull --rebase`.
2. Gmail search (Gmail connector `search_threads`, view THREAD_VIEW_SUMMARY), last ~26 hours:
   `(from:prizepicks OR from:underdogsports OR from:betr.app OR from:kalshi OR from:polymarket) newer_than:2d`
   Skip threads already listed in `memory/promos.md` (match by subject + date).
3. For each new promo-looking email, read it with `get_message` using messageFormat `PLAIN_TEXT`
   (never FULL_CONTENT; the HTML is huge). Extract: platform, offer (profit boost %, discount, protected
   play/insurance, deposit match %, bonus funds $, free entry), requirements (opt-in, minimum entry/trade,
   sports, max entry), and expiry (date/time ET).
4. **Keep only usable offers for this user:** existing-customer promos on NFL/any-sport picks or trades.
   **Ignore:** new-user/signup offers, refer-a-friend, casino/social casino/sportsbook-tab/spins, card packs
   ("Rips", "Packs", "Grails"), news/newsletters, login/funding receipts.
5. Update `memory/promos.md`: "Active" table (platform | offer | how to use | expires | seen) and move
   expired ones to "Expired". Note any money the user is about to lose (e.g. bonus funds expiring) at the top.
6. **Text only if actionable soon:** a profit boost/protected play/discount usable on today's or tomorrow's
   NFL slate, bonus funds expiring within 48h, or a deposit match worth >= $10 at the user's normal $50-$100
   reload. One short plain-text message (<= 400 chars), e.g.
   `PROMO: PrizePicks 40% Profit Boost (opt in, expires 11:59pm). Use it on the Power 2: ... Underdog $19 bonus expires tomorrow.`
   Suggest which of this week's picks (memory/picks.csv, open rows) to attach it to. No texts in quiet hours.
7. Commit + push `memory/promos.md` (never commit email addresses or account details).
