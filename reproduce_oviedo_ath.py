
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from src.logic.poisson_engine import PoissonEngine
from src.logic.value_engine import ValueEngine
from src.logic.external_analyst import ExternalAnalyst
from src.data.mock_provider import MockDataProvider
from src.models.base import Match, MatchConditions

def simulate():
    provider = MockDataProvider()
    poisson = PoissonEngine()
    value_eng = ValueEngine()
    analyst = ExternalAnalyst()

    # 1. Get Team Data
    home_name = "Real Oviedo"
    away_name = "Athletic Club"
    
    home_team = provider.get_team_data(home_name)
    away_team = provider.get_team_data(away_name)

    # 2. Estimate Lambdas
    # Assume neutral BPA and standard league avg
    h_lambda, a_lambda = poisson.estimate_lambdas(home_team, away_team)
    
    # 3. Calculate Probabilities
    prob_h, prob_d, prob_a = poisson.calculate_match_probabilities(h_lambda, a_lambda)
    
    # 4. Predict Score
    matrix = poisson.predict_score_matrix(h_lambda, a_lambda)
    best_score = max(matrix, key=matrix.get)

    # 5. External Analysis
    dummy_match = Match(
        id="sim_1",
        home_team=home_team,
        away_team=away_team,
        date=datetime.now(),
        kickoff_time="21:00",
        competition="La Liga",
        conditions=None,
        referee=None
    )
    analysis = analyst.analyze_match(dummy_match)
    stats_markets = analyst.calculate_stat_markets(dummy_match, 0.5, 0.5)

    # 6. Value Betting (Hypothetical Odds)
    # 1: 3.20, X: 3.40, 2: 2.10
    market_odds = {"1": 4.10, "X": 3.40, "2": 1.95} # Oviedo as underdog
    
    # We need a PredictionResult mock or real one
    from src.models.base import PredictionResult
    pred = PredictionResult(
        match_id="sim_1",
        bpa_home=0.5,
        bpa_away=0.5,
        win_prob_home=prob_h,
        draw_prob=prob_d,
        win_prob_away=prob_a,
        total_goals_expected=h_lambda + a_lambda,
        both_teams_to_score_prob=0.55, # Dummy estimate
        score_prediction=best_score,
        confidence_score=0.75
    )
    
    opps = value_eng.find_opportunities(pred, market_odds)

    print(f"--- SIMULATION: {home_name} vs {away_name} ---")
    print(f"Ratings: {home_name} (6.9) | {away_name} (7.9)")
    print(f"Lambdas: Home {h_lambda} | Away {a_lambda}")
    print(f"Probabilities: 1:{prob_h:.2f} | X:{prob_d:.2f} | 2:{prob_a:.2f}")
    print(f"Predicted Score: {best_score}")
    print(f"\nStats Markets:")
    for k, v in stats_markets.items():
        print(f" - {k}: {v}")
    
    print(f"\nValue Opportunities:")
    for o in opps:
        print(f" - Market {o['market']}: Prob {o['ia_prob']:.2f} | Odds {o['odds']} | EV {o['value_pct']}% | Kelly {o['suggested_stake_pct']}%")

if __name__ == "__main__":
    simulate()
