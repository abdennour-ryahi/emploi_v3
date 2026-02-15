# Project Constraints - Source of Truth (Updated Feb 14, 2026)

This document is the **official reference**. The algorithm prioritizes **ALWAYS finding a solution**.

## 1. Capacity & Shifts
- **Shifts**: Matin (Day), Nuit (Night).
- **Capacity**: Exactly **2 agents per shift** (4 agents/day). **[HARD]**

## 2. Hard Legal Rules
- **One shift per day**: An agent cannot work two shifts in 24h. **[HARD]**
- **Night -> Day**: No Day shift immediately following a Night shift. **[HARD]**

## 3. Worker Sequences & Robustness (Solution A)
- **Consecutive Work**: Target **4 days**.
- **Safety Valve**: If a solution is mathematically impossible (due to small team or leaves), the solver may allow a **5th day** (high penalty) to prevent crashing. **[SOFT 1000]**
- **Identical Shifts**: Avoid 3+ identical shifts in a row (J-J-J or N-N-N). **[SOFT 500]**

## 4. Mme Mliyani (Special Schedule)
- **Shifts**: Matin only. Never Nuit. Never Saturday/Sunday. **[HARD]**
- **Shifts**: Friday. **[SOFT 1]**
- **Mandatory Mon-Thu**: These 4 days are mandatory.
- **Safety Valve**: In extreme cases of team-wide rotation deadlock, the solver may skip one of these days (extremely high penalty) to ensure a team-wide plan exists. **[SOFT 2000]**

## 5. Global Fairness & Balance
- **Rule**: Minimize the gap between **Ratios** (`Total Shifts / Available Days`).
- **Target**: (MAX ratio - MIN ratio) <= 5%.
- **Male Agents Balance**: `abs(Day Shifts - Night Shifts) <= 3`. **[SOFT 400]**

## 6. Priority Order
1.  **Feasibility**: A solution **MUST** be found (using Safety Valves if needed).
2.  **Hard Rules**: Transition (Night->Day) and Capacity (2 per shift).
3.  **Fairness**: Balanced workload ratios across the whole month.
4.  **Preferences**: 4-day limit, Mixed shifts, etc.
  - *Adaptive Exception*: applied only if total monthly leaves > 40 days, sequences of **4 identical shifts** are permitted to ensure solver feasibility.

### Rest Sequences (Male Agents Only)
- **Rest Length (SOFT)**: Ideal rest period is **2–3 consecutive days**.
- **Avoid Isolated Rest (1-day Rest Between Work Days)**:
  Different penalties apply depending on surrounding shifts:
  - **N - R - J** → Strongly discouraged **[SOFT 800]**
  - **N - R - N** → Discouraged **[SOFT 500]**
  - **J - R - J** → Discouraged **[SOFT 500]**
  Where:
  - N = Night
  - J = Day (Matin)
  - R = Rest
- **Max Rest**: Avoid more than **4 consecutive rest days**
  (unless due to long leave) **[SOFT 1000]**


## 7. Fairness & Balance (SOFT)
Instead of absolute counts, the solver aims to balance **percentages (ratios)** based on agent availability (Total Days - Leave Days).

- **Total Workload Fairness (SOFT)**: Minimize gaps in the ratio `(Total Shifts / Available Days)` between agents (male and female).
- **Internal Day/Night Balance (SOFT)**: Each male agent should have a balanced number of Day and Night shifts relative to their own availability. Formula: **abs(Day Shifts - Night Shifts) <= 3** (target). This prevents agents from being stuck in one shift type while allowing the solver flexibility. The solver allows up to **4** in extreme cases with high penalties.
- **Night Shift Distribution (SOFT)**: Minimize gaps in the ratio `(Night Shifts / Available Days)` across male agents as a secondary objective.

## 6. Month-to-Month Continuity
- The solver accepts the last 3 days of the previous month (D-3, D-2, D-1) to:
  - Enforce the Night->Day transition from the last day of the old month to the first day of the new month.
  - Count consecutive work days starting from the end of the previous month.

## 7. Leave & Holiday Priority
- **Specific Agent Absences (HARD)**: Each agent (Male/Female) is unavailable on days selected in their own "Congés personnels" tab.
- **Team Holidays (HARD)**: Mme Mliyani (Sexe F) is automatically off on days marked in the "Jours Fériés MA" widget. Male agents are available on those days unless they select them as personal leave.
- **Coverage (HARD)**: Always 2 agents per shift type (Matin/Nuit).
