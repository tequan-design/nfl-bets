# Lessons learned (durable memory)

Update every Wednesday after grading. Newest lessons first under each heading. Keep it tight.

## From the user's chat history (Oct 8 - Nov 10, 2026)
- True locks are rare: almost every verified prop priced 55-66%. The edge is taking the **lowest
  available line** (goblins / discounted / Kalshi low rungs) on players in good spots.
- Closest-to-lock props were very low thresholds (QB over 0.5 / 4.5 rush yards for mobile-ish QBs).
- Kalshi prices double as honest hit-rate estimates; Billy Bets signals were useful in Week 9.
- Live player box scores were hard to get mid-game; a screenshot from the Yahoo/ESPN app works.
- User also plays free Yahoo DFS contests (0.5 PPR, $200 cap): exclude backup QBs with inflated FPPG.

## Scorecard after seeding Weeks 8-9 (20 suggested legs, 8 hit = 40%)
- Anytime TD overs on goal-line backs/rushing QBs: 3/4. Keep using them as sprinkle legs.
- **Unders went 1/7.** Receptions unders on secondary pass-catchers (Chism, Knox) and rush-yard unders
  (Charbonnet, Love) all missed. Be skeptical of unders unless the market price is 65%+ and the role
  is shrinking for a concrete reason.
- Week 9 "plays" list (mostly -110 to -125 coin flips) went 6/14. Coin-flip legs do not belong in
  conservative entries. Only 62%+ legs go in Power/Standard entries.
- Game-level: favorites in parlays split 1/2 (Texans won, Patriots lost).
- Sample is tiny; treat these as soft priors, not rules.

## Week 10 results (graded Wed 11/18)
- TNF entry (Diggs o2.5 rec + Fields o14.5 rec yds) HIT; all 3 live 2H Kalshi plays HIT (Diggs 40+, Likely 50+/60+).
  Live halftime plays on players already near the line with heavy target share are a strength. Keep offering them.
- Kalshi favorites parlay (5 legs, 64-84% each) HIT. 70%+ legs overall: 7/8. Prediction-market favorites vs rookie/backup QBs worked.
- Sunday v2 standard-line legs: 1/6 (only Cook o91.5 hit, 157). The goblin entries they replaced would ALSO have lost
  (Core A: Maye threw 48 yds in a 35-10 loss, Warren 15, Olave 30). It was a game-script week, not just a line-level problem.
- **Game script is the biggest risk.** Warren (PIT, +3.5 dog) got 7 carries in a 38-18 loss. Avoid RB rushing overs on underdogs;
  prefer RB overs on favorites (Cook, BUF -8, hit easily).
- **Tight matchup = goblin, confirmed.** Bowers o59.5 vs SEA (#1 pass D) with a rookie QB: 18 yds. Under the mixed-line rule he'd be a goblin or skipped.
- **Dual-threat RBs: look at receiving/rush+rec too.** McCaffrey: 62 rush (missed by 0.5) but 161 rec yds. When unsure of the split,
  use rush+rec yds or the receiving line.
- Near misses: McCaffrey 62 vs 62.5, Higgins 66 vs 75.5. Half-point lines matter: when two apps differ, take the lower one.

## Week 11 results (graded Wed 11/25) + calibration
- Roughly break-even week. HIT: Power 3 (Dak 325, Javonte goblin 67, Gibbs goblin 98), Flex 5 4/5, Flex 6 5/6,
  Kalshi 7-favorite parlay (now 12/12 legs over two weeks). MISS: Power 2 (McCaffrey 49 vs 49.5), TNF, both MNF entries.
- **Calibration (76 graded legs): 70%+ legs 17/20 (85%), 62-70% 7/12, 55-62% 12/27 (44%), <55% 8/17.**
  My 55-62% estimates are too high. Treat those legs as coin flips: use them only in Flex entries or as the single
  standard leg next to goblin/Kalshi-backed 70%+ legs. Power entries need at least one 70%+ leg.
- Kalshi favorite parlays and 70%+ Kalshi-ladder goblins are the most reliable tools so far. Keep them weekly.
- McCaffrey rushing missed by 0.5 two weeks in a row (62 vs 62.5, 49 vs 49.5): his rush line is set right at his median; avoid it.
- Weather swap worked (Caleb 181 / Odunze 45 in rain). Wind game (MNF gusts 27): even a goblin on Ja'Marr Chase missed (31).
  In 25+ mph gusts, avoid all receiving overs.

## Week 11 notes
- TNF: Collins goblin would hit (58) but my Thursday "upgrade to standard 70.5" text would have missed. When a goblin leg looks
  even better on game day, keep the goblin; don't chase the upgrade on TNF.
- Trailing-team RB receiving overs are not automatic: Taylor had 6 rec yds as IND lost 26-3 (blowouts can kill the whole offense).

## Thursday Night Football
- Treat TNF results as noisy. Prior: halve stakes, favor floor props, at most one TNF leg per Power entry.

## Process notes
- Odds API free plan = 500 credits/month. Pull props once Wednesday (all games, 4 markets) and refresh
  Saturday (2 markets). Kalshi ladders and Billy Bets props are free fallbacks.

## Payout preference (user feedback, Week 10)
- User REJECTED the all-goblin Week 10 entries: 3-pick Core A paid only 1.64x, 5-pick Flex only 1.98x.
  They want conservative-ish but real multipliers: build on standard lines (2-pick ~3x, 3-pick ~5-6x,
  5-flex ~10x). Goblins only as a single anchor leg. Week 10 Sunday entries were rebuilt Fri 11/13 (v2).
- At standard lines books/Kalshi sit near 50%; pick legs where form + defense rank add the edge
  (e.g. RBs vs bottom-8 run defenses, TE with a 7/7 floor, QB vs bottom-5 pass defense in a dome).
- Refinement (user, Fri 11/13): don't make an entry all goblins OR all standard. Pick the line per leg:
  good matchup = standard or higher (demon), tight matchup = lower (goblin). Mixed entries keep a real multiplier.
