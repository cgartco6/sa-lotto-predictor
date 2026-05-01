import random
import requests
import time
from collections import Counter
from itertools import combinations
from datetime import datetime

def print_time():
    print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

# ----- 1. LIGHTWEIGHT SCRAPE (last ~30 draws) -----
def fetch_recent_draws(game="Lotto", limit=30):
    headers = {"User-Agent": "Mozilla/5.0"}
    draws = []
    draws_fetched = 0
    for draw_id in range(2500, 2000, -1):
        if draws_fetched >= limit:
            break
        try:
            resp = requests.post("https://www.nationallottery.co.za/api/lotto-history",
                                json={"drawId": draw_id}, headers=headers, timeout=10)
            if resp.status_code != 200:
                continue
            data = resp.json()
            numbers_str = data.get("winningNumbers")
            if numbers_str:
                numbers = [int(x) for x in numbers_str.split(",")]
                if len(numbers) == 6:
                    draws.append(numbers)
                    draws_fetched += 1
            time.sleep(0.2)
        except:
            continue
    return draws

print_time()
print("Fetching recent draws...")
lotto_draws = fetch_recent_draws("Lotto", limit=30)

if not lotto_draws:
    # fallback hardcoded list if API fails
    lotto_draws = [
        [3,9,15,32,36,49], [12,27,32,41,49,58], [12,29,31,37,40,47],
        [5,17,38,44,47,2], [6,10,13,24,26,2], [1,5,8,22,35,48],
        [4,11,19,28,34,56], [7,14,21,30,44,51], [2,13,25,38,42,55],
        [9,18,24,33,41,53], [10,16,22,29,39,59], [5,12,20,31,40,50]
    ]

print(f"Loaded {len(lotto_draws)} recent draws.")

# ----- 2. FREQUENCY + PAIR ANALYSIS with BOOSTS for your numbers -----
your_numbers = [9, 14, 17, 32, 39, 43]
freq = Counter()
pair_count = Counter()

for draw in lotto_draws:
    for num in draw:
        freq[num] += 1
    for pair in combinations(sorted(draw), 2):
        pair_count[pair] += 1

for num in your_numbers:
    freq[num] += 8   # boost your numbers in frequency

# combine freq and pair bonus for pool selection
candidate_score = {}
for num in range(1, 59):
    score = freq.get(num, 0)
    # bonus for pairs that include your numbers
    for your_num in your_numbers:
        if your_num < num:
            p = (your_num, num)
        elif your_num > num:
            p = (num, your_num)
        else:
            continue
        if p in pair_count:
            score += pair_count[p] * 0.3
    candidate_score[num] = score

# get top 18 numbers (wider pool for wheel construction)
top_numbers = sorted(candidate_score, key=candidate_score.get, reverse=True)[:18]
top_numbers = [n for n in top_numbers if 1 <= n <= 58]

print("\n--- TOP POOL (18 numbers) ---")
print(top_numbers)
print("Your numbers in pool:", [n for n in your_numbers if n in top_numbers])

# ----- 3. GENERATE ABBREVIATED WHEEL (12 tickets) -----
def build_wheel(pool, main_numbers, lines=12):
    """Each line: 2 from your numbers, 4 from rest of pool, no duplicates."""
    wheel = []
    other_pool = [n for n in pool if n not in main_numbers]
    if len(other_pool) < 4:
        # fallback: add more numbers back
        other_pool = [n for n in pool if n not in main_numbers] * 2
    for _ in range(lines):
        line = random.sample(main_numbers, 2)
        remaining = [n for n in other_pool if n not in line]
        line += random.sample(remaining, 4)
        wheel.append(sorted(line))
    # deduplicate
    unique_wheel = []
    for t in wheel:
        if t not in unique_wheel:
            unique_wheel.append(t)
    return unique_wheel

wheel = build_wheel(top_numbers, your_numbers, lines=15)

print("\n--- YOUR WHEEL (12 votes) ---")
for i, t in enumerate(wheel, 1):
    print(f"{i:2}. {t}")

# ----- 4. FAST MONTE CARLO SIMULATION (lightweight) -----
print("\n--- QUICK HIT PROBABILITY ---")
hit_count = 0
simulations = 3000
for _ in range(simulations):
    draw = set(random.sample(range(1, 59), 6))
    for ticket in wheel:
        if len(set(ticket) & draw) >= 4:
            hit_count += 1
            break
print(f"Probability of ≥4 matches (3,000 simulated draws): {hit_count/simulations:.2%}")

# ----- 5. TOP 6 PREDICTION -----
# highest combined freq +/- pair bonus
pred_6 = sorted(candidate_score, key=candidate_score.get, reverse=True)[:6]
print("\n--- TOP 6 PREDICTED NUMBERS (highest freq + pair weight) ---")
print(pred_6)

print("\n--- DONE. Good luck, for real. ---")
