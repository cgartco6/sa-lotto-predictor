# powerball.py – Powerball main predictor
GAME_NAME = "POWERBALL"
API_URL = "https://www.nationallottery.co.za/api/powerball-history"
DB_NAME = "powerball.db"
MAX_NUM = 50
PICKS = 5
YOUR_NUMBERS = [9, 14, 17, 32, 39, 43]

print("="*70)
print(f"{GAME_NAME} PREDICTOR – Own machine")
print("="*70)
print(f"Your numbers (reference only): {YOUR_NUMBERS}\n")

GROUPS = {"G1":range(1,11),"G2":range(11,21),"G3":range(21,31),"G4":range(31,MAX_NUM+1)}
GROUP_KEYS = ["G1","G2","G3","G4"]

# The rest of the code is exactly the same as lotto.py (same functions)
# Only change: bonus ball extraction uses "powerball" instead of "bonusBall"
# We need to adjust fetch_draws accordingly.

def fetch_draws(limit=120):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS draws (id INTEGER PRIMARY KEY, numbers TEXT, date TEXT, bonus INTEGER)''')
    conn.commit()
    draws, bonuses = [], []
    headers = {"User-Agent":"Mozilla/5.0"}
    for draw_id in range(800, 800-limit, -1):
        try:
            resp = requests.post(API_URL, json={"drawId":draw_id}, headers=headers, timeout=10)
            if resp.status_code != 200: continue
            data = resp.json()
            nums_str = data.get("winningNumbers")
            bonus = data.get("powerball")   # <-- different key
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
        bonuses = [random.randint(1,20) for _ in range(20)]
    return draws, bonuses

# All other functions (group_dist, analyse, generate, backtest, main) are identical.
# Copy them from lotto.py (they work unchanged because they rely on GROUPS and PICKS).
