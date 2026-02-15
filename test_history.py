from scheduler import generate_schedule
import sys
import pandas as pd

def test_history_and_night_balance():
    print(">>> Testing History and Night Balance <<<", flush=True)
    
    employees = [
        {"name": "Agent A", "sex": "M"},
        {"name": "Agent B", "sex": "M"},
        {"name": "Agent C", "sex": "M"},
        {"name": "Agent D", "sex": "M"},
        {"name": "Agent E", "sex": "M"},
        {"name": "Agent F", "sex": "M"},
        {"name": "Mme Mliyani", "sex": "F"}
    ]
    
    # Historique : Agent A a fini par une Nuit (D-1)
    # On va vérifier si le 1er du mois il peut travailler le Matin (Interdit: Nuit -> Matin)
    history = {
        "Agent A": ["REP", "REP", "NIGHT"],
        "Agent B": ["DAY", "DAY", "DAY"], # A fait 3 jours de suite, peut en faire qu'un de plus max
    }
    
    year = 2026
    month = 2 # Février 2026
    
    try:
        df = generate_schedule(year, month, employees, {}, {"history": history})
        if df is not None:
            print("SUCCESS: Schedule generated.", flush=True)
            
            # 1. Vérif Agent A (Transition Nuit -> Matin au 1er jour)
            first_day_matin = df.iloc[0]["Matin"]
            if "Agent A" in first_day_matin:
                print("ERROR: Agent A assigned to Matin on Day 1 after NIGHT on D-1")
            else:
                print("OK: Agent A transition respected.")

            # 2. Vérif Agent B (Sequence max 4)
            # Puisque Agent B a fait 3 jours (D-3, D-2, D-1), il ne peut travailler que le jour 1 max.
            b_work_days = []
            for i, row in df.iterrows():
                if "Agent B" in row["Matin"] or "Agent B" in row["Nuit"]:
                    b_work_days.append(row["Jour"])
            
            # Si travaille jour 1 et 2 -> Erreur (3+2=5)
            if 1 in b_work_days and 2 in b_work_days:
                print("ERROR: Agent B working 5 consecutive days (3 from history + 2 current)")
            else:
                print("OK: Agent B sequence limit respected.")

            # 3. Vérif Écart Nuits
            nights = {}
            for name in [e["name"] for e in employees if e["sex"]=="M"]:
                nights[name] = sum(1 for row in df["Nuit"] if name in row)
            
            max_n = max(nights.values())
            min_n = min(nights.values())
            print(f"Night counts: {nights}")
            if max_n - min_n > 2:
                print(f"ERROR: Night imbalance too high ({max_n - min_n})")
            else:
                print(f"OK: Night balance respected (écart={max_n - min_n})")

        else:
            print("FAILURE: No solution found.")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_history_and_night_balance()
