# powerball_main.py
import requests, random, time, sqlite3
from collections import Counter
from itertools import combinations

print("=" * 70)
print("POWERBALL MAIN (Machine 1) – Separate from Plus")
print("=" * 70)

YOUR_NUMBERS = [9, 14, 17, 32, 39, 43]
print(f"Your numbers (reference): {YOUR_NUMBERS}")

MAX_NUM = 50
PICKS = 5
API_URL = "https://www.nationallottery.co.za/api/powerball-history"
DB_NAME = "pb_main.db"

MAIN_GROUPS = {"G1":range(1,11),"G2":range(11,21),"G3":range(21,31),"G4":range(31,51)}
GROUP_KEYS = ["G1","G2","G3","G4"]

def group_dist(draw):
    cnt = [0,0,0,0]
    for n in draw:
        for i,(_,r) in enumerate(MAIN_GROUPS.items()):
            if n in r: cnt[i]+=1; break
    return tuple(cnt)

def fetch_draws(limit=120):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS draws (id INTEGER PRIMARY KEY, numbers TEXT, date TEXT, bonus INTEGER)''')
    conn.commit()
    draws, bonuses = [], []
    headers = {"User-Agent": "Mozilla/5.0"}
    for draw_id in range(800, 800-limit, -1):
        try:
            resp = requests.post(API_URL, json={"drawId": draw_id}, headers=headers, timeout=10)
            if resp.status_code != 200: continue
            data = resp.json()
            nums_str = data.get("winningNumbers")
            bonus = data.get("powerball")
            if nums_str and bonus:
                nums = [int(x.strip()) for x in nums_str.split(",") if x.strip()]
                if len(nums) == PICKS:
                    draws.append(nums)
                    bonuses.append(int(bonus))
                    c.execute("INSERT INTO draws (numbers, date, bonus) VALUES (?,?,?)",
                              (str(nums), data.get("drawDate"), bonus))
                    conn.commit()
            time.sleep(0.2)
        except: continue
        if len(draws) >= limit: break
    conn.close()
    if not draws:  # fallback
        draws = [[5,17,38,44,47],[6,10,13,24,26],[1,5,8,22,35]]
        bonuses = [2,7,13]
    return draws, bonuses

def analyse(draws, bonuses):
    main_pat = Counter(group_dist(d) for d in draws).most_common(1)[0][0]
    bonus_groups = ["low" if b<=10 else "high" for b in bonuses]
    bonus_pat = Counter(bonus_groups).most_common(1)[0][0]
    return main_pat, bonus_pat

def generate(tickets, top_pool, main_pat, bonus_pat, num):
    group_nums = {g: [n for n in top_pool if n in MAIN_GROUPS[g]] for g in GROUP_KEYS}
    for i,g in enumerate(GROUP_KEYS):
        if len(group_nums[g]) < main_pat[i]:
            group_nums[g] = list(MAIN_GROUPS[g])
    for _ in range(num*2):
        t = []
        for i,g in enumerate(GROUP_KEYS):
            if main_pat[i]:
                t.extend(random.sample(group_nums[g], main_pat[i]))
        if len(t)==PICKS:
            tickets.append(sorted(t))
    unique = []
    for t in tickets:
        if t not in unique: unique.append(t)
    bonus_sug = [2,5,7,9,10] if bonus_pat=="low" else [11,13,15,17,19]
    return unique[:num], bonus_sug

def backtest(tickets, draws, recent=50):
    test = draws[-recent:]
    wins = {3:0,4:0,5:0}
    for d in test:
        ds = set(d)
        best = max((len(set(t)&ds) for t in tickets), default=0)
        if best>=3: wins[best]+=1
    return wins, len(test)

def main():
    draws, bonuses = fetch_draws(120)
    print(f"Loaded {len(draws)} Powerball MAIN draws.")
    main_pat, bonus_pat = analyse(draws, bonuses)
    print(f"Main pattern: {main_pat}")
    print(f"Bonus ball pattern: {bonus_pat} (low/high)")
    num = int(input("Lines to play (2-20): "))
    freq = Counter(); pair = Counter()
    for d in draws:
        for n in d: freq[n]+=1
        for p in combinations(sorted(d),2): pair[p]+=1
    score = {n: freq.get(n,0) for n in range(1,MAX_NUM+1)}
    for p,c in pair.items():
        score[p[0]] += c*0.15; score[p[1]] += c*0.15
    top = sorted(score, key=score.get, reverse=True)[:30]
    tickets, bonus_sug = generate([], top, main_pat, bonus_pat, num)
    print(f"\n--- YOUR {len(tickets)} POWERBALL MAIN TICKETS ---")
    for i,t in enumerate(tickets,1):
        common = set(t)&set(YOUR_NUMBERS)
        print(f"{'⭐' if common else '  '} {i:2}: {t} {common if common else ''}")
    print(f"\nSuggested Bonus (Powerball) numbers ({bonus_pat}): {bonus_sug}")
    wins, total = backtest(tickets, draws, 50)
    print(f"\nBacktest last {total} Powerball MAIN draws: wins {sum(wins.values())} ({sum(wins.values())/total*100:.1f}%)")
    for k in (3,4,5):
        if wins[k]: print(f"  {k} matches: {wins[k]}")
    print("\n✅ Run before Powerball main draw.\n")

if __name__=="__main__": main()
