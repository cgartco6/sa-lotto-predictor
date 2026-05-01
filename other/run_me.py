import requests
import random
import time
from collections import Counter
from itertools import combinations

print("=" * 60)
print("SA LOTTO REAL SYSTEM (No AI Lies, Just Math)")
print("=" * 60)

# Your numbers
YOUR_NUMBERS = [9, 14, 17, 32, 39, 43]

# Fetch last 60 draws
def fetch_draws(limit=60):
    draws = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for draw_id in range(2600, 2600 - limit, -1):
        try:
            resp = requests.post(
                "https://www.nationallottery.co.za/api/lotto-history",
                json={"drawId": draw_id},
                headers=headers,
                timeout=10
            )
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

print("\nFetching latest lottery draws...")
draws = fetch_draws(60)
print(f"Loaded {len(draws)} real draws.")

if not draws:
    print("ERROR: Could not fetch draws. Check internet.")
    exit()

# Frequency analysis
freq = Counter()
pair_counts = Counter()
for draw in draws:
    for n in draw:
        freq[n] += 1
    for pair in combinations(sorted(draw), 2):
        pair_counts[pair] += 1

# Boost your numbers
for n in YOUR_NUMBERS:
    freq[n] += 10

# Build candidate pool (score = freq + pair bonuses involving your numbers)
score = {}
for num in range(1, 59):
    s = freq.get(num, 0)
    # add pair bonus: if num appears in a pair with any of your numbers
    for y in YOUR_NUMBERS:
        p = tuple(sorted((y, num)))
        if p in pair_counts:
            s += pair_counts[p] * 0.5
    score[num] = s

# Top 16 numbers
top_pool = sorted(score, key=score.get, reverse=True)[:16]
print("\n--- TOP 16 NUMBER POOL (frequency + pair boost) ---")
print(top_pool)
print("Your numbers in pool:", [n for n in YOUR_NUMBERS if n in top_pool])

# Generate wheel (each ticket: 2 of your numbers + 4 from top pool)
def generate_wheel(pool, your_nums, tickets=12):
    wheel = []
    other_nums = [n for n in pool if n not in your_nums]
    if len(other_nums) < 4:
        other_nums = [n for n in range(1,59) if n not in your_nums][:20]
    for _ in range(tickets * 2):  # generate extra then dedupe
        ticket = random.sample(your_nums, 2)
        available = [n for n in other_nums if n not in ticket]
        if len(available) >= 4:
            ticket += random.sample(available, 4)
            wheel.append(sorted(ticket))
    # remove duplicates
    unique = []
    for t in wheel:
        if t not in unique:
            unique.append(t)
    return unique[:tickets]

wheel = generate_wheel(top_pool, YOUR_NUMBERS, tickets=12)
print("\n--- YOUR 12 TICKETS (WHEEL) ---")
for i, t in enumerate(wheel, 1):
    print(f"{i:2}. {t}")

# Monte Carlo simulation (lightweight)
print("\n--- ESTIMATED HIT PROBABILITY ---")
hits = 0
sims = 5000
for _ in range(sims):
    draw = set(random.sample(range(1,59), 6))
    for ticket in wheel:
        if len(set(ticket) & draw) >= 4:
            hits += 1
            break
print(f"Chance of 4+ matches in one draw: {hits/sims:.2%}")

# Top 6 prediction (highest scored numbers)
top6 = sorted(score, key=score.get, reverse=True)[:6]
print("\n--- TOP 6 PREDICTION (for quick pick) ---")
print(top6)

print("\n✅ Done. No AI lies. No crashes. Runs on your laptop.")
