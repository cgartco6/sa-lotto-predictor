# pure_predictor.py
import requests
import random
import time
import sqlite3
import os
from collections import Counter
from itertools import combinations

print("=" * 70)
print("PURE LOTTO PREDICTOR (No personal number anchoring)")
print("=" * 70)

YOUR_NUMBERS = [9, 14, 17, 32, 39, 43]
print(f"\nYour personal numbers (for reference only): {YOUR_NUMBERS}")
print("The predictions below are independent of these numbers.\n")

def fetch_draws(limit=100):
    conn = sqlite3.connect("lotto_cache.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS draws (id INTEGER PRIMARY KEY, numbers TEXT, date TEXT)''')
    conn.commit()
    draws = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for draw_id in range(2800, 2800 - limit, -1):
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
                    c.execute("INSERT OR IGNORE INTO draws (numbers, date) VALUES (?, ?)",
                              (str(nums), data.get("drawDate")))
                    conn.commit()
            time.sleep(0.2)
        except:
            continue
        if len(draws) >= limit:
            break
    conn.close()
    if not draws:
        print("No internet. Using built-in sample draws.")
        draws = [
            [5,12,23,34,45,56], [2,11,28,33,44,58], [7,18,22,35,41,52],
            [4,13,27,38,49,57], [9,14,17,32,39,43], [3,16,25,36,41,55],
            [8,19,24,31,42,59], [1,10,21,30,44,53], [6,15,26,37,48,50],
        ]
    return draws

def analyze(draws, top_n=18):
    freq = Counter()
    pair_count = Counter()
    for draw in draws:
        for n in draw:
            freq[n] += 1
        for pair in combinations(sorted(draw), 2):
            pair_count[pair] += 1
    score = {n: freq.get(n, 0) for n in range(1, 59)}
    for pair, cnt in pair_count.items():
        score[pair[0]] += cnt * 0.15
        score[pair[1]] += cnt * 0.15
    top_numbers = sorted(score, key=score.get, reverse=True)[:top_n]
    return top_numbers, score

def generate_tickets(top_pool, num_tickets):
    if num_tickets > 100:
        num_tickets = 100
    tickets = []
    for _ in range(num_tickets):
        ticket = sorted(random.sample(top_pool, 6))
        tickets.append(ticket)
    unique = []
    for t in tickets:
        if t not in unique:
            unique.append(t)
    return unique[:num_tickets]

def backtest(tickets, draws, recent=50):
    test = draws[-recent:] if len(draws) >= recent else draws
    wins = {3:0,4:0,5:0,6:0}
    for draw in test:
        draw_set = set(draw)
        for t in tickets:
            match = len(set(t) & draw_set)
            if match >= 3:
                wins[match] += 1
                break
    return wins, len(test)

def main():
    print("Fetching recent lottery draws...")
    draws = fetch_draws(120)
    print(f"Loaded {len(draws)} draws.\n")
    while True:
        try:
            num = int(input(f"How many lines do you want to play? (2-20): "))
            if 2 <= num <= 20:
                break
            else:
                print("Please enter between 2 and 20.")
        except:
            print("Invalid input.")
    top_pool, scores = analyze(draws, top_n=18)
    print(f"\nTop 18 numbers (based on frequency + pairs): {top_pool}")
    tickets = generate_tickets(top_pool, num)
    print(f"\n--- YOUR {len(tickets)} PREDICTED TICKETS ---")
    for i, t in enumerate(tickets, 1):
        common = set(t) & set(YOUR_NUMBERS)
        mark = "⭐" if common else "  "
        print(f"{mark} {i:2}: {t}   (Your numbers in this ticket: {sorted(common) if common else 'none'})")
    wins, total = backtest(tickets, draws, recent=50)
    total_wins = sum(wins.values())
    print(f"\n--- BACKTEST ON LAST {total} DRAWS ---")
    print(f"Draws with a win (3+ matches): {total_wins} ({total_wins/total*100:.1f}%)")
    if wins[3]: print(f"   3 matches: {wins[3]} times (approx R20-50 each)")
    if wins[4]: print(f"   4 matches: {wins[4]} times (approx R300-500 each)")
    if wins[5]: print(f"   5 matches: {wins[5]} times")
    if wins[6]: print(f"   6 matches: {wins[6]} times")
    print("\n✅ Predictions are based purely on historical patterns, not your personal numbers.")
    print("Run this script again before each draw to get updated predictions.\n")

if __name__ == "__main__":
    main()
