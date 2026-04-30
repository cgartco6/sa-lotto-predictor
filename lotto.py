
### `lotto.py` (for Lotto main)

```python
# lotto.py – Lotto (main) predictor
import requests, random, time, sqlite3
from collections import Counter
from itertools import combinations

GAME_NAME = "LOTTO"
API_URL = "https://www.nationallottery.co.za/api/lotto-history"
DB_NAME = "lotto.db"
MAX_NUM = 58
PICKS = 6
YOUR_NUMBERS = [9, 14, 17, 32, 39, 43]

print("="*70)
print(f"{GAME_NAME} PREDICTOR – Own machine, own history")
print("="*70)
print(f"Your numbers (reference only): {YOUR_NUMBERS}\n")

GROUPS = {"G1":range(1,11),"G2":range(11,21),"G3":range(21,31),"G4":range(31,MAX_NUM+1)}
GROUP_KEYS = ["G1","G2","G3","G4"]

def group_dist(draw):
    cnt = [0,0,0,0]
    for n in draw:
        for i,(_,r) in enumerate(GROUPS.items()):
            if n in r: cnt[i]+=1; break
    return tuple(cnt)

def fetch_draws(limit=120):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS draws (id INTEGER PRIMARY KEY, numbers TEXT, date TEXT, bonus INTEGER)''')
    conn.commit()
    draws,bonuses = [],[]
    headers = {"User-Agent":"Mozilla/5.0"}
    for draw_id in range(3000, 3000-limit, -1):
        try:
            resp = requests.post(API_URL, json={"drawId":draw_id}, headers=headers, timeout=10)
            if resp.status_code != 200: continue
            data = resp.json()
            nums_str = data.get("winningNumbers")
            bonus = data.get("bonusBall")
            if nums_str and bonus is not None:
                nums = [int(x.strip()) for x in nums_str.split(",") if x.strip()]
                if len(nums) == PICKS:
                    draws.append(nums)
                    bonuses.append(int(bonus))
                    c.execute("INSERT OR IGNORE INTO draws (numbers,date,bonus) VALUES (?,?,?)",
                              (str(nums), data.get("drawDate"), bonus))
                    conn.commit()
            time.sleep(0.2)
        except:
            continue
        if len(draws) >= limit: break
    conn.close()
    if not draws:
        print("Fallback sample draws")
        draws = [random.sample(range(1,MAX_NUM+1),PICKS) for _ in range(20)]
        bonuses = [random.randint(1,MAX_NUM) for _ in range(20)]
    return draws, bonuses

def analyse(draws, bonuses):
    main = Counter(group_dist(d) for d in draws).most_common(1)[0][0]
    bonus_groups = []
    for b in bonuses:
        for i,(_,r) in enumerate(GROUPS.items()):
            if b in r: bonus_groups.append(i); break
    bonus = Counter(bonus_groups).most_common(1)[0][0]
    return main, bonus

def generate(tickets, top_pool, main_pat, bonus_pat, num):
    group_nums = {g: [n for n in top_pool if n in GROUPS[g]] for g in GROUP_KEYS}
    for i,g in enumerate(GROUP_KEYS):
        if len(group_nums[g]) < main_pat[i]:
            group_nums[g] = list(GROUPS[g])
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
    bonus_range = list(GROUPS[GROUP_KEYS[bonus_pat]])
    bonus_sug = random.sample(bonus_range, min(5,len(bonus_range)))
    return unique[:num], sorted(bonus_sug)

def backtest(tickets, draws, recent=50):
    test = draws[-recent:] if len(draws)>=recent else draws
    wins = {3:0,4:0,5:0,6:0}
    for d in test:
        ds = set(d)
        best = max((len(set(t)&ds) for t in tickets), default=0)
        if best>=3: wins[best]+=1
    return wins, len(test)

def main():
    d,b = fetch_draws(120)
    print(f"Loaded {len(d)} draws.")
    mp, bp = analyse(d,b)
    print(f"Main pattern: {mp}\nBonus group: {bp} (0=G1..3=G4)")
    try:
        num = int(input("Lines (2-20): "))
        num = max(2, min(20, num))
    except:
        num = 6
    freq = Counter(); pair = Counter()
    for dr in d:
        for n in dr: freq[n]+=1
        for p in combinations(sorted(dr),2): pair[p]+=1
    score = {n: freq.get(n,0) for n in range(1,MAX_NUM+1)}
    for p,c in pair.items():
        score[p[0]] += c*0.15
        score[p[1]] += c*0.15
    top = sorted(score, key=score.get, reverse=True)[:40]
    tickets, bsug = generate([], top, mp, bp, num)
    print(f"\n--- YOUR {len(tickets)} TICKETS ---")
    for i,t in enumerate(tickets,1):
        common = set(t) & set(YOUR_NUMBERS)
        star = "⭐" if common else "  "
        print(f"{star} {i:2}: {t}   {common if common else ''}")
    print(f"\nSuggested bonus numbers (group {GROUP_KEYS[bp]}): {bsug}")
    wins, total = backtest(tickets, d, 50)
    tw = sum(wins.values())
    print(f"\nBacktest last {total} draws: wins {tw} ({tw/total*100:.1f}%)")
    for k in (3,4,5,6):
        if wins[k]: print(f"  {k} matches: {wins[k]}")
    print(f"\n✅ Run again before next {GAME_NAME} draw.\n")

if __name__=="__main__": main()
