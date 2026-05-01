import requests
import random
import time
from collections import Counter
from itertools import combinations

print("=" * 60)
print("SA LOTTO – FEW LINES OPTIMIZER (2–6 tickets)")
print("=" * 60)

YOUR_NUMBERS = [9, 14, 17, 32, 39, 43]

# Fetch live draws (last 80)
def fetch_draws(limit=80):
    draws = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for draw_id in range(2700, 2700 - limit, -1):
        try:
            resp = requests.post("https://www.nationallottery.co.za/api/lotto-history",
                                 json={"drawId": draw_id}, headers=headers, timeout=10)
            if resp.status_code != 200:
                continue
            data = resp.json()
            nums_str = data.get("winningNumbers")
            if nums_str:
                nums = [int(x.strip()) for x in nums_str.split(",") if x.strip()]
                if len(nums) == 6:
                    draws.append(nums)
            time.sleep(0.2)
        except:
            continue
        if len(draws) >= limit:
            break
    return draws

print("\nFetching recent draws...")
draws = fetch_draws(80)
if not draws:
    print("Using fallback data.")
    draws = [
        [3,9,15,32,36,49], [12,27,32,41,49,58], [12,29,31,37,40,47],
        [5,17,38,44,47,2], [6,10,13,24,26,2], [9,14,17,28,37,43],
        [4,11,19,28,34,56], [7,14,21,30,44,51], [2,13,25,38,42,55],
        [9,18,24,33,41,53], [10,16,22,29,39,59], [5,12,20,31,40,50],
    ]

print(f"Loaded {len(draws)} draws.")

# Frequency analysis
freq = Counter()
pair_count = Counter()
for draw in draws:
    for n in draw:
        freq[n] += 1
    for pair in combinations(sorted(draw), 2):
        pair_count[pair] += 1

# Boost your numbers
for n in YOUR_NUMBERS:
    freq[n] += 8

# Score each number: freq + weight from pairs with your numbers
score = {n: freq[n] for n in range(1,59)}
for p, cnt in pair_count.items():
    if p[0] in YOUR_NUMBERS or p[1] in YOUR_NUMBERS:
        score[p[0]] += cnt * 0.3
        score[p[1]] += cnt * 0.3

# Pick top 6 numbers (your core set)
top_numbers = sorted(score, key=score.get, reverse=True)[:6]
# Ensure your numbers are included (if any missing, add them)
core_numbers = list(set(top_numbers + YOUR_NUMBERS))[:6]

print("\n=== YOUR CORE 6 NUMBERS (play these as your main line) ===")
print(sorted(core_numbers))

# Generate small variations (2–6 tickets)
num_tickets = int(input("\nHow many tickets do you want to play? (2-6): "))
if num_tickets < 2:
    num_tickets = 2
if num_tickets > 6:
    num_tickets = 6

# Variation pool: next best numbers not in core
other_numbers = [n for n in range(1,59) if n not in core_numbers]
other_scores = {n: score[n] for n in other_numbers}
next_best = sorted(other_scores, key=other_scores.get, reverse=True)[:10]

tickets = []
# First ticket is the core numbers
tickets.append(sorted(core_numbers))

# For the rest, replace 1 or 2 numbers from core with next best ones
for i in range(1, num_tickets):
    ticket = core_numbers.copy()
    # replace 1 number (if many tickets, maybe 2 for some)
    replace_count = 1 if i <= 3 else 2
    for _ in range(replace_count):
        idx = random.randint(0,5)
        new_num = random.choice(next_best)
        while new_num in ticket:
            new_num = random.choice(next_best)
        ticket[idx] = new_num
    tickets.append(sorted(ticket))

print(f"\n--- YOUR {num_tickets} TICKETS ---")
for i, t in enumerate(tickets, 1):
    print(f"{i}: {t}")

# Quick backtest on last 30 draws (how many wins with these tickets)
test_draws = draws[-30:] if len(draws) >= 30 else draws
wins = {3:0, 4:0, 5:0, 6:0}
for draw in test_draws:
    draw_set = set(draw)
    best_match = 0
    for t in tickets:
        match = len(set(t) & draw_set)
        if match > best_match:
            best_match = match
    if best_match >= 3:
        wins[best_match] += 1

print("\n--- BACKTEST ON LAST 30 DRAWS (with your few tickets) ---")
print(f"Wins: {sum(wins.values())} draws out of {len(test_draws)} ({sum(wins.values())/len(test_draws)*100:.1f}%)")
print(f"  3 matches: {wins[3]} times (approx R20-50 each)")
print(f"  4 matches: {wins[4]} times (approx R300-500 each)")
if wins[5] or wins[6]:
    print(f"  5/6 matches: {wins[5]+wins[6]} times")

print("\n✅ Use the tickets above. Good luck.")
