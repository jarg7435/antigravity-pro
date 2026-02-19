import sys
import os

# Add the project root directory to Python path
sys.path.append(os.path.abspath(os.path.join(os.getcwd())))

from src.data.mock_provider import MockDataProvider

def test_fixes():
    provider = MockDataProvider()
    
    print("--- Testing Liga Mixta ---")
    mixta_teams = provider.get_teams_by_league("Liga Mixta (Combinada)")
    print(f"Total teams in Liga Mixta: {len(mixta_teams)}")
    if len(mixta_teams) > 50:
        print("SUCCESS: Liga Mixta returns multiple teams.")
    else:
        print(f"FAILURE: Liga Mixta only returned {len(mixta_teams)} teams.")

    print("\n--- Testing Ligue 1 (Lille) ---")
    ligue1_teams = provider.get_teams_by_league("Ligue 1")
    if "Lille" in ligue1_teams:
        print("SUCCESS: Lille found in Ligue 1.")
    else:
        print("FAILURE: Lille NOT found in Ligue 1.")
    
    print("\n--- Testing League Normalization ---")
    la_liga_teams = provider.get_teams_by_league("La Liga (España)")
    if len(la_liga_teams) > 0:
        print(f"SUCCESS: 'La Liga (España)' returned {len(la_liga_teams)} teams.")
    else:
        print("FAILURE: 'La Liga (España)' returned 0 teams.")

if __name__ == "__main__":
    test_fixes()
