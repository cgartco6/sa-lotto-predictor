import requests
import random
import time
import sqlite3
from collections import Counter
from itertools import combinations

print("=" * 70)
print("POWERBALL PREDICTOR (No personal number anchoring)")
print("=" * 70)

YOUR_NUMBERS = [9, 14, 17, 32, 39, 43]
print(f"\nYour personal numbers (for reference only): {YOUR_NUMBERS}")
print("The predictions below are independent of these numbers.\n")

MAX_NUM = 50
MAIN_PICKS = 5
API_ENDPOINT = "https://www.nationallottery.co.za/api/powerball-history"
DB_NAME = "powerball_cache.db"

def fetch_draws(limit=120):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS draws (id INTEGER PRIMARY KEY, numbers TEXT, date TEXT, powerball INTEGER)''')
    conn.commit()
    draws = []
    powerballs = []
    headers = {"User-Agent": "Mozilla/5.0"}
    for draw_id in range(800, 800 - limit, -1):
        try:
            resp = requests.post(API_ENDPOINT, json={"drawId": draw_id}, headers=headers, timeout=10)
            if resp.status_code != 200:
                continue
            data = resp.json()
            nums_str = data.get("winningNumbers")
            pb = data.get("powerball")
            if nums_str and pb is not None:
                nums = [int(x.strip()) for x in nums_str.split(",") if x.strip()]
                if len(nums) == MAIN_PICKS:
                    draws.append(nums)
                    powerballs.append(int(pb))
                    c.execute("INSERT OR IGNORE INTO draws (numbers, date, powerball) VALUES (?, ?, ?)",
                              (str(nums), data.get("drawDate"), pb))
                    conn.commit()
            time.sleep(0.2)
        except:
            continue
        if len(draws) >= limit:
            break
    conn.close()
    if not draws:
        print("No internet. Using built-in sample draws for POWERBALL.")
        draws = [
            [5,17,38,44,47], [6,10,13,24,26], [1,5,8,22,35],
            [4,11,19,28,34], [7,14,21,30,44], [2,13,25,38,42],
            [9,18,24,33,41], [10,16,22,29,39], [3,12,20,31,40],
        ]
        powerballs = [2, 7, 13, 17, 20, 5, 11, 15, 18]  # dummy
    return draws, powerballs

def analyze(draws, top_n=18):
    freq = Counter()
    pair_count = Counter()
    for draw in draws:
        for n in draw:
            freq[n] += 1
        for pair in combinations(sorted(draw), 2):
            pair_count[pair] += 1
    score = {n: freq.get(n, 0) for n in range(1, MAX_NUM+1)}
    for pair, cnt in pair_count.items():
        score[pair[0]] += cnt * 0.15
        score[pair[1]] += cnt * 0.15
    top_numbers = sorted(score, key=score.get, reverse=True)[:top_n]
    return top_numbers, score

def analyze_powerballs(powerballs):
    pb_counter = Counter(powerballs)
    most_common = [num for num, _ in pb_counter.most_common(5)]
    return most_common

def generate_tickets(top_pool, num_tickets):
    if num_tickets > 100:
        num_tickets = 100
    tickets = []
    for _ in range(num_tickets):
        ticket = sorted(random.sample(top_pool, MAIN_PICKS))
        tickets.append(ticket)
    unique = []
    for t in tickets:
        if t not in unique:
            unique.append(t)
    return unique[:num_tickets]

def backtest(tickets, draws, recent=50):
    test = draws[-recent:] if len(draws) >= recent else draws
    wins = {3:0,4:0,5:0}
    for draw in test:
        draw_set = set(draw)
        for t in tickets:
            match = len(set(t) & draw_set)
            if match >= 3:
                wins[match] += 1
                break
    return wins, len(test)

def main():
    print("Fetching recent POWERBALL draws...")
    draws, powerballs = fetch_draws(120)
    print(f"Loaded {len(draws)} draws.\n")
    while True:
        try:
            num = int(input("How many POWERBALL lines do you want to play? (2-20): "))
            if 2 <= num <= 20:
                break
            else:
                print("Please enter between 2 and 20.")
        except:
            print("Invalid input.")
    top_pool, _ = analyze(draws, top_n=18)
    print(f"\nTop 18 main numbers for POWERBALL: {top_pool}")
    tickets = generate_tickets(top_pool, num)
    print(f"\n--- YOUR {len(tickets)} PREDICTED POWERBALL TICKETS ---")
    for i, t in enumerate(tickets, 1):
        common = set(t) & set(YOUR_NUMBERS)
        mark = "⭐" if common else "  "
        print(f"{mark} {i:2}: {t}   (Your numbers: {sorted(common) if common else 'none'})")
    # Powerball suggestions
    pb_freq = analyze_powerballs(powerballs)
    print(f"\nMost frequent Powerball numbers (1-20): {pb_freq[:5]}")
    print("Pick one Powerball number for all your lines, or choose your own.")
    wins, total = backtest(tickets, draws, recent=50)
    total_wins = sum(wins.values())
    print(f"\n--- BACKTEST ON LAST {total} POWERBALL DRAWS (main numbers only) ---")
    print(f"Draws with a win (3+ main matches): {total_wins} ({total_wins/total*100:.1f}%)")
    if wins[3]: print(f"   3 main matches: {wins[3]} times (approx R20-50 each)")
    if wins[4]: print(f"   4 main matches: {wins[4]} times (approx R300-500 each)")
    if wins[5]: print(f"   5 main matches: {wins[5]} times (big prize + Powerball needed for jackpot)")
    print("\n✅ These tickets are for Powerball & Powerball Plus (same main numbers).")
    print("Run this script again before the next Powerball draw.\n")

if __name__ == "__main__":
    main()
