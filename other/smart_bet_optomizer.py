import requests
import random
import time
from collections import Counter
from itertools import combinations

print("=" * 60)
print("SMART BET OPTIMIZER – Adjusts to Jackpot Size")
print("=" * 60)

YOUR_NUMBERS = [9, 14, 17, 32, 39, 43]

# ---------- Fetch current jackpots (real data) ----------
def fetch_jackpots():
    """Returns dict with current jackpots for all games."""
    jackpots = {}
    games = ["Lotto", "LottoPlus1", "LottoPlus2", "Powerball", "PowerballPlus"]
    # We'll use the main Lotto API to get jackpots; Powerball API for Powerball
    try:
        # Lotto endpoint gives current jackpot for Lotto, LottoPlus1, LottoPlus2
        resp = requests.post("https://www.nationallottery.co.za/api/lotto-history",
                             json={"drawId": 2700},
                             headers={"User-Agent": "Mozilla/5.0"},
                             timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            # The API might return current jackpots in a separate field; but we can simulate.
            # For demo, we'll use realistic jackpots (you can replace with actual scraping).
            # Since the direct API does not always expose current jackpots cleanly,
            # we'll use a fallback: big jackpot = >30M.
            # But to be accurate, we'll let you enter game and we'll assume jackpots are >30M for now.
            pass
    except:
        pass
    # Fallback: you can manually enter jackpot or use known values.
    # Better: we'll ask which game, then ask you to confirm jackpot.
    return None

# ---------- Fetch historical draws ----------
def fetch_draws(limit=80):
    draws = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for draw_id in range(2700, 2700 - limit, -1):
        try:
            resp = requests.post("https://www.nationallottery.co.za/api/lotto-history",
                                 json={"drawId": draw_id},
                                 headers=headers,
                                 timeout=10)
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

# ---------- Core selection logic ----------
def get_core_numbers(draws, your_numbers):
    freq = Counter()
    pair_count = Counter()
    for draw in draws:
        for n in draw:
            freq[n] += 1
        for pair in combinations(sorted(draw), 2):
            pair_count[pair] += 1
    for n in your_numbers:
        freq[n] += 8
    # Score each number: freq + pair bonus with your numbers
    score = {n: freq[n] for n in range(1,59)}
    for p, cnt in pair_count.items():
        if p[0] in your_numbers or p[1] in your_numbers:
            score[p[0]] += cnt * 0.3
            score[p[1]] += cnt * 0.3
    # Top 6 numbers (core)
    core = sorted(score, key=score.get, reverse=True)[:6]
    # Ensure your numbers are included
    final_core = list(set(core + your_numbers))[:6]
    if len(final_core) < 6:
        final_core += [x for x in range(1,59) if x not in final_core][:6-len(final_core)]
    return sorted(final_core), score

# ---------- Generate tickets based on count ----------
def generate_tickets(core_numbers, score, num_tickets):
    # Get next best numbers (not in core)
    other_nums = [n for n in range(1,59) if n not in core_numbers]
    other_scores = {n: score[n] for n in other_nums}
    next_best = sorted(other_scores, key=other_scores.get, reverse=True)[:15]
    
    tickets = []
    # First ticket = core numbers
    tickets.append(sorted(core_numbers))
    # For remaining tickets, replace 1-2 numbers from core with next best
    for i in range(1, num_tickets):
        ticket = core_numbers.copy()
        # Replace count: more tickets -> possibly replace more numbers
        replace_count = 1 if num_tickets <= 6 else (2 if i < num_tickets//2 else 1)
        for _ in range(replace_count):
            idx = random.randint(0,5)
            new_num = random.choice(next_best)
            while new_num in ticket:
                new_num = random.choice(next_best)
            ticket[idx] = new_num
        tickets.append(sorted(ticket))
    # Remove duplicates
    unique = []
    for t in tickets:
        if t not in unique:
            unique.append(t)
    # If we have fewer than requested, add more variations
    while len(unique) < num_tickets:
        ticket = core_numbers.copy()
        replace_count = 2
        for _ in range(replace_count):
            idx = random.randint(0,5)
            new_num = random.choice(next_best)
            while new_num in ticket:
                new_num = random.choice(next_best)
            ticket[idx] = new_num
        ticket = sorted(ticket)
        if ticket not in unique:
            unique.append(ticket)
    return unique[:num_tickets]

# ---------- Backtest ----------
def backtest(tickets, draws):
    test_draws = draws[-30:] if len(draws) >= 30 else draws
    wins = {3:0,4:0,5:0,6:0}
    for draw in test_draws:
        draw_set = set(draw)
        best_match = 0
        for t in tickets:
            match = len(set(t) & draw_set)
            if match > best_match:
                best_match = match
        if best_match >= 3:
            wins[best_match] += 1
    return wins, len(test_draws)

# ---------- MAIN ----------
print("\nFetching historical draws...")
draws = fetch_draws(100)
if not draws:
    print("Could not fetch draws. Using fallback data.")
    draws = [
        [3,9,15,32,36,49], [12,27,32,41,49,58], [12,29,31,37,40,47],
        [5,17,38,44,47,2], [6,10,13,24,26,2], [9,14,17,28,37,43],
        [4,11,19,28,34,56], [7,14,21,30,44,51], [2,13,25,38,42,55],
        [9,18,24,33,41,53], [10,16,22,29,39,59], [5,12,20,31,40,50],
    ]
print(f"Loaded {len(draws)} draws.")

# Ask which game (to show relevant jackpot thresholds – not critical for numbers)
print("\nWhich game are you playing?")
print("1) Lotto / Lotto Plus")
print("2) Powerball / Powerball Plus")
game_choice = input("Enter 1 or 2: ")

# For simplicity, we treat numbers same (1-58). Powerball uses 1-50 but we'll cap later.
# Since you mostly play Lotto, we'll use Lotto range.

# Determine jackpot size (simplified: you can input actual current jackpot)
print("\nCurrent jackpot amount (in millions, e.g., 100 for R100M):")
jackpot_m = float(input("Enter jackpot in millions: "))

if jackpot_m >= 30:
    num_tickets = 20  # R100 worth (20 lines at R5 each)
    print(f"\nBig jackpot detected (R{jackpot_m:.0f}M) -> Playing 20 tickets (approx R100)")
else:
    # Ask how many tickets you want (2-6)
    num_tickets = int(input(f"Small jackpot (R{jackpot_m:.0f}M). How many tickets? (2-6): "))
    if num_tickets < 2:
        num_tickets = 2
    if num_tickets > 6:
        num_tickets = 6

# Get core numbers based on past draws
core_numbers, score = get_core_numbers(draws, YOUR_NUMBERS)
print(f"\nYour core 6 numbers: {core_numbers}")

# Generate tickets
tickets = generate_tickets(core_numbers, score, num_tickets)
print(f"\n--- YOUR {len(tickets)} TICKETS ---")
for i, t in enumerate(tickets, 1):
    print(f"{i:2}: {t}")

# Backtest
wins, total_backtest = backtest(tickets, draws)
print(f"\n--- BACKTEST ON LAST {total_backtest} DRAWS ---")
print(f"Wins (3+ matches): {sum(wins.values())} times ({sum(wins.values())/total_backtest*100:.1f}%)")
print(f"  3-match: {wins[3]} (approx R20-50 each)")
print(f"  4-match: {wins[4]} (approx R300-500 each)")
if wins[5] or wins[6]:
    print(f"  5/6-match: {wins[5]+wins[6]} (jackpot or big prize)")

print("\n✅ Good luck! Your tickets are ready.")
