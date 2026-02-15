import pandas as pd
from ortools.sat.python import cp_model
import datetime
import calendar

def generate_schedule(year, month, employees, leaves, params):
    """
    Génère un planning mensuel en respectant les contraintes métier.
    
    Args:
        year (int): Année du planning.
        month (int): Mois du planning.
        employees (list): Liste de dictionnaires {'name': str, 'sex': 'M'/'F'}.
        leaves (dict): Dict {nom_employé: [jours_de_congés]}.
        params (dict): Paramètres de contraintes (activées/désactivées).
        
    Returns:
        pd.DataFrame or None: Le planning généré ou None si aucune solution.
    """
    model = cp_model.CpModel()
    
    num_days = calendar.monthrange(year, month)[1]
    num_employees = len(employees)
    
    # Constantes pour les types de postes
    DAY = 0
    NIGHT = 1
    SHIFTS = [DAY, NIGHT]

    holidays = params.get("holidays", [])
    history = params.get("history", {})
    
    # Variables: shifts[(n, d, s)] == 1 si l'employé n travaille le jour d au poste s
    shifts = {}
    for n in range(num_employees):
        for d in range(1, num_days + 1):
            for s in SHIFTS:
                shifts[(n, d, s)] = model.NewBoolVar(f'shift_n{n}_d{d}_s{s}')

    # --- OBJECTIF & PENALITES ---
    penalties = []

    # 1. Capacité (DURE) : Dynamique selon la taille de l'équipe
    # < 6 agents -> 1 personne par poste, >= 6 agents -> 2 personnes par poste
    capacity = 1 if num_employees < 6 else 2
    for d in range(1, num_days + 1):
        for s in SHIFTS:
            model.Add(sum(shifts[(n, d, s)] for n in range(num_employees)) == capacity)

    # 2. Un employé ne peut faire qu'un seul poste par jour (DURE)
    for n in range(num_employees):
        for d in range(1, num_days + 1):
            model.Add(sum(shifts[(n, d, s)] for s in SHIFTS) <= 1)

    # --- HISTORY & TRANSITIONS ---
    history = params.get('history', {}) # {name: [shift_d-3, shift_d-2, shift_d-1]}
    # Conversion : DAY=0, NIGHT=1, REST=-1
    history_map = {"DAY": 0, "NIGHT": 1, "REP": -1}
    
    # helper functions for history-aware constraints
    def get_shift_var(n_idx, day_idx, shift_type):
        if day_idx <= 0:
            agent_name = employees[n_idx]['name']
            agent_hist = history.get(agent_name, ["REP", "REP", "REP"]) # [D-3, D-2, D-1]
            idx = 2 + day_idx
            val = agent_hist[idx] if 0 <= idx < len(agent_hist) else "REP"
            return 1 if history_map.get(val, -1) == shift_type else 0
        if day_idx > num_days:
            return 0 # On suppose repos après la fin du mois
        return shifts[(n_idx, day_idx, shift_type)]

    def is_working_var(n_idx, day_idx):
        if day_idx <= 0:
            agent_name = employees[n_idx]['name']
            agent_hist = history.get(agent_name, ["REP", "REP", "REP"])
            idx = 2 + day_idx
            val = agent_hist[idx] if 0 <= idx < len(agent_hist) else "REP"
            return 1 if history_map.get(val, -1) in [0, 1] else 0
        if day_idx > num_days:
            return 0 # Repos après la fin du mois
        return sum(shifts[(n_idx, day_idx, s)] for s in SHIFTS)

    # 3. Nuit suivie de Jour (DURE) - inclut l'historique
    for n in range(num_employees):
        for d in range(0, num_days): # d=0 check transition from D-1 (history) to D=1
            model.Add(get_shift_var(n, d, NIGHT) + get_shift_var(n, d+1, DAY) <= 1)

    # --- ADAPTIVE CONSTRAINTS LOGIC ---
    total_monthly_leaves = sum(len(leaves.get(e['name'], [])) for e in employees)
    
    # a) Hard work days consecutive (Default 4, Adaptive 5)
    max_consecutive_work = 5 if total_monthly_leaves > 31 else 4
    # b) Identical shifts consecutive (Penalty for 3+, Adaptive relaxation for 4)
    # If total_monthly_leaves > 40, we penalize 4-sequences less.

    # 4. Congés (DURE)
    for n, emp in enumerate(employees):
        emp_leaves = leaves.get(emp['name'], [])
        for d in emp_leaves:
            if 1 <= d <= num_days:
                for s in SHIFTS:
                    model.Add(shifts[(n, d, s)] == 0)

    # 5. Cas spécial : Mme Mliyani (DURE)
    holidays = params.get('holidays', [])
    for n, emp in enumerate(employees):
        if emp['sex'] == 'F':
            emp_leaves = leaves.get(emp['name'], [])
            for d in range(1, num_days + 1):
                model.Add(shifts[(n, d, NIGHT)] == 0)
                date_obj = datetime.date(year, month, d)
                wd = date_obj.weekday()
                if wd >= 5 or d in holidays:
                    model.Add(shifts[(n, d, DAY)] == 0)
                elif d not in emp_leaves:
                    if wd <= 3: # Lun-Jeu mandatory
                        # SAFETY VALVE: Mandatory Mon-Thu is now SOFT (Penalty 2000)
                        is_working = model.NewBoolVar(f'mandatory_mliyani_d{d}')
                        model.Add(shifts[(n, d, DAY)] == 1).OnlyEnforceIf(is_working)
                        model.Add(shifts[(n, d, DAY)] == 0).OnlyEnforceIf(is_working.Not())
                        penalties.append(is_working.Not() * 3000)
                    elif wd == 4: # Vendredi SOFT preference (prefer off, allow for balance)
                        # Penalize working on Friday (SOFT 1)
                        penalties.append(shifts[(n, d, DAY)] * 1)

    # 6. Équité & Balance (OBJECTIF PRINCIPAL)
    # Règle 1: Équité globale (M/F) basée sur le RATIO (Total Shifts / Available Days)
    SCALE = 1000
    ratio_vars = []
    for n, emp in enumerate(employees):
        avail_i = num_days - len(leaves.get(emp['name'], []))
        if avail_i == 0: continue
        
        m_shifts_i = sum(shifts[(n, d, DAY)] for d in range(1, num_days + 1))
        n_shifts_i = sum(shifts[(n, d, NIGHT)] for d in range(1, num_days + 1))
        total_shifts_i = m_shifts_i + n_shifts_i
        
        # Robust Division: interim variable for numerator
        num_scaled = model.NewIntVar(0, num_days * SCALE, f'num_scaled_n{n}')
        model.Add(num_scaled == total_shifts_i * SCALE)
        
        ratio_i = model.NewIntVar(0, SCALE, f'ratio_n{n}')
        model.AddDivisionEquality(ratio_i, num_scaled, avail_i)
        ratio_vars.append(ratio_i)

        # Règle 2: Équilibre INTERNE (Hommes seulement) : abs(Matin - Nuit) <= 3
        if emp['sex'] == 'M':
            diff_internal = model.NewIntVar(-num_days, num_days, f'diff_internal_n{n}')
            model.Add(diff_internal == m_shifts_i - n_shifts_i)
            abs_diff_internal = model.NewIntVar(0, num_days, f'abs_diff_internal_n{n}')
            model.AddAbsEquality(abs_diff_internal, diff_internal)
            
            # Pénalité légère par point d'écart
            penalties.append(abs_diff_internal * 10)
            
            # Pénalité moyenne si > 3
            over3_internal = model.NewBoolVar(f'over3_internal_n{n}')
            model.Add(abs_diff_internal > 3).OnlyEnforceIf(over3_internal)
            model.Add(abs_diff_internal <= 3).OnlyEnforceIf(over3_internal.Not())
            penalties.append(over3_internal * 400)

            # Très forte pénalité si > 4
            over4_internal = model.NewBoolVar(f'over4_internal_n{n}')
            model.Add(abs_diff_internal > 4).OnlyEnforceIf(over4_internal)
            model.Add(abs_diff_internal <= 4).OnlyEnforceIf(over4_internal.Not())
            penalties.append(over4_internal * 800)

    # Minimisation de l'écart de ratio (Fairness Globale)
    if len(ratio_vars) >= 2:
        max_ratio = model.NewIntVar(0, SCALE, 'max_ratio')
        min_ratio = model.NewIntVar(0, SCALE, 'min_ratio')
        model.AddMaxEquality(max_ratio, ratio_vars)
        model.AddMinEquality(min_ratio, ratio_vars)
        
        ratio_gap = model.NewIntVar(0, SCALE, 'ratio_gap')
        model.Add(ratio_gap == max_ratio - min_ratio)
        
        # Objectif : minimiser cet écart
        penalties.append(ratio_gap * 300) 


    # 8. Séquences de travail (inclut l'historique)
    for n, emp in enumerate(employees):
        # a) Max jours consécutifs TOTAL (PASSAGE EN MOLL POUR ROBUSTESSE)
        for d in range(-3, num_days - max_consecutive_work + 1):
            is_over_consecutive = model.NewBoolVar(f'over_consecutive_n{n}_d{d}')
            seq_sum = sum(is_working_var(n, d+i) for i in range(max_consecutive_work + 1))
            # Si seq_sum > limit, on active la pénalité
            model.Add(seq_sum > max_consecutive_work).OnlyEnforceIf(is_over_consecutive)
            model.Add(seq_sum <= max_consecutive_work).OnlyEnforceIf(is_over_consecutive.Not())
            penalties.append(is_over_consecutive * 1500) # Très forte pénalité
            
        # b) Éviter jours consécutifs IDENTIQUES (MOLLE Adaptatif)
        if emp['sex'] == 'M':
            # NEW: Avoid more than 2 identical shifts (3+ penalized)
            limit_same = 2
            penalty_same = 500 # Strong penalty as requested
            for d in range(-1, num_days - limit_same + 1):
                for s in SHIFTS:
                    is_over = model.NewBoolVar(f'over_same_n{n}_d{d}_s{s}')
                    model.Add(sum(get_shift_var(n, d+i, s) for i in range(limit_same + 1)) - limit_same <= is_over)
                    penalties.append(is_over * penalty_same)

        # c) Min 2 jours consécutifs (MOLLE)
        # Avoid isolated work days (1 day work between rests)
        for d in range(0, num_days + 1):
            is_iso = model.NewBoolVar(f'iso_n{n}_d{d}')
            # iso == 1 if working(d) and not working(d-1) and not working(d+1)
            model.Add(is_working_var(n, d) - is_working_var(n, d-1) - is_working_var(n, d+1) <= is_iso)
            penalties.append(is_iso * 200)

    # 9. Repos (MOLLE pour laisser de la souplesse avec les congés)
    for n in range(num_employees):
        # les repos doivent idéalement être entre 1 et 4 jours
        # On pénalise si on dépasse 4 jours de repos de suite
        for d in range(-2, num_days - 3 + 1):
            is_over_rest = model.NewBoolVar(f'over_rest_n{n}_d{d}')
            # over_rest == 1 <=> all 5 days are rest
            seq_work_5 = [is_working_var(n, d+i) for i in range(5)]
            model.Add(sum(seq_work_5) == 0).OnlyEnforceIf(is_over_rest)
            model.Add(sum(seq_work_5) >= 1).OnlyEnforceIf(is_over_rest.Not())
            penalties.append(is_over_rest * 1000) # Max Rest Penalty

        # a) Pas de repos isolé (MOLLE)
        for d in range(0, num_days):
            is_iso_r = model.NewBoolVar(f'iso_r_n{n}_d{d}')
            model.Add(is_working_var(n, d-1) + is_working_var(n, d+1 if d<num_days else -100) - is_working_var(n, d) - 1 <= is_iso_r)
            penalties.append(is_iso_r * 500) # Isolated Rest Penalty
        
        # b) Favoriser 2-3 jours de repos (MOLLE : pénalise 4)
        for d in range(-2, num_days - 3 + 1):
            is_4r = model.NewBoolVar(f'rest4_n{n}_d{d}')
            # rest4 == 1 <=> all 4 days are rest
            model.Add(sum(is_working_var(n, d+i) for i in range(4)) == 0).OnlyEnforceIf(is_4r)
            model.Add(sum(is_working_var(n, d+i) for i in range(4)) >= 1).OnlyEnforceIf(is_4r.Not())
            penalties.append(is_4r * 20)

        # # c) Nuit -> Repos -> Jour (inclut historique)
        # for d in range(0, num_days - 1):
        #     bad = model.NewBoolVar(f'bad_tr_n{n}_d{d}')
        #     model.Add(get_shift_var(n, d, NIGHT) + (1 - is_working_var(n, d+1)) + get_shift_var(n, d+2, DAY) - 2 <= bad)
        #     penalties.append(bad * 800)

        for d in range(0, num_days - 2):
            # CAS 1 : N - R - J (1000)
            bad_nrj = model.NewBoolVar(f'bad_nrj_n{n}_d{d}')
            model.Add(get_shift_var(n, d, NIGHT)+ (1 - is_working_var(n, d+1))+ get_shift_var(n, d+2, DAY)- 2 <= bad_nrj)
            penalties.append(bad_nrj * 1000)
            # CAS 2 : N - R - N (500)
            bad_nrn = model.NewBoolVar(f'bad_nrn_n{n}_d{d}')
            model.Add(get_shift_var(n, d, NIGHT)+ (1 - is_working_var(n, d+1))+ get_shift_var(n, d+2, NIGHT)- 2 <= bad_nrn)
            penalties.append(bad_nrn * 500)
            # CAS 3 : J - R - J (500)
            bad_jrj = model.NewBoolVar(f'bad_jrj_n{n}_d{d}')
            model.Add(get_shift_var(n, d, DAY)+ (1 - is_working_var(n, d+1))+ get_shift_var(n, d+2, DAY)- 2 <= bad_jrj)
            penalties.append(bad_jrj * 500)





    # --- RÉSOLUTION ---
    model.Minimize(sum(penalties))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 120.0
    status = solver.Solve(model)

    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        data = []
        for d in range(1, num_days + 1):
            m, n_lst = [], []
            for ni, emp in enumerate(employees):
                if solver.Value(shifts[(ni, d, DAY)]): m.append(emp['name'])
                if solver.Value(shifts[(ni, d, NIGHT)]): n_lst.append(emp['name'])
            data.append({"Jour": d, "Date": datetime.date(year, month, d).strftime("%d/%m/%Y"),
                         "Semaine": ["Lun","Mar","Mer","Jeu","Ven","Sam","Dim"][datetime.date(year, month, d).weekday()],
                         "Matin": ", ".join(m), "Nuit": ", ".join(n_lst)})
        return pd.DataFrame(data)
    return None
