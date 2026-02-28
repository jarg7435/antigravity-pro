import random
import requests
import re
from bs4 import BeautifulSoup
from src.models.base import Match, Team

class ExternalAnalyst:
    """
    Simulates the aggregation of external intelligence from:
    1. Local Press (City/Region specific) - Focused on Injuries & Signings.
    2. National Press (Country specific) - Context & Sentiment.
    3. Weather Reports.
    4. Expert Consensus.
    """
    
    # Simulation Data: Mapping Teams to Context
    # Simulation Data: Expanded European Context
    TEAM_CONTEXT = {
        # --- La Liga (Spain) ---
        "Real Madrid": {"city": "Madrid", "country": "Spain", "papers": ["Marca", "Defensa Central"]},
        "Atletico Madrid": {"city": "Madrid", "country": "Spain", "papers": ["Marca", "Mundo Deportivo"]},
        "FC Barcelona": {"city": "Barcelona", "country": "Spain", "papers": ["Sport", "Mundo Deportivo"]},
        "Athletic Club": {"city": "Bilbao", "country": "Spain", "papers": ["Deia", "El Correo"]},
        "Real Sociedad": {"city": "San Sebastian", "country": "Spain", "papers": ["Diario Vasco", "Mundo Deportivo"]},
        "Osasuna": {"city": "Pamplona", "country": "Spain", "papers": ["Diario de Navarra", "Noticias de Navarra"]},
        "Sevilla FC": {"city": "Sevilla", "country": "Spain", "papers": ["Estadio Deportivo", "Diario de Sevilla"]},
        "Real Betis": {"city": "Sevilla", "country": "Spain", "papers": ["Estadio Deportivo", "El Desmarque"]},
        "Valencia": {"city": "Valencia", "country": "Spain", "papers": ["Superdeporte", "Plaza Deportiva"]},
        "Celta": {"city": "Vigo", "country": "Spain", "papers": ["Faro de Vigo", "La Voz de Galicia"]},
        "Villarreal": {"city": "Villarreal", "country": "Spain", "papers": ["El Periódico Mediterráneo", "Marca"]},
        "Las Palmas": {"city": "Gran Canaria", "country": "Spain", "papers": ["Canarias7", "La Provincia"]},

        # --- Premier League (UK) ---
        "Manchester City": {"city": "Manchester", "country": "England", "papers": ["Manchester Evening News", "City Xtra"]},
        "Manchester Utd": {"city": "Manchester", "country": "England", "papers": ["Manchester Evening News", "United Stand"]},
        "Liverpool": {"city": "Liverpool", "country": "England", "papers": ["Liverpool Echo", "Anfield Watch"]},
        "Arsenal": {"city": "London", "country": "England", "papers": ["Football.London", "Arseblog"]},
        "Chelsea": {"city": "London", "country": "England", "papers": ["Football.London", "We Ain't Got No History"]},
        "Tottenham": {"city": "London", "country": "England", "papers": ["Football.London", "Spurs Web"]},
        "Newcastle": {"city": "Newcastle", "country": "England", "papers": ["The Chronicle", "Geordie Boot Boys"]},

        # --- Serie A (Italy) ---
        "Inter Milan": {"city": "Milan", "country": "Italy", "papers": ["Gazzetta dello Sport", "L'Interista"]},
        "AC Milan": {"city": "Milan", "country": "Italy", "papers": ["Gazzetta dello Sport", "MilanNews"]},
        "Juventus": {"city": "Turin", "country": "Italy", "papers": ["Tuttosport", "Juventibus"]},
        "Napoli": {"city": "Naples", "country": "Italy", "papers": ["Il Mattino", "TuttoNapoli"]},
        "AS Roma": {"city": "Rome", "country": "Italy", "papers": ["Corriere dello Sport", "RomaPress"]},
        "Lazio": {"city": "Rome", "country": "Italy", "papers": ["Corriere dello Sport", "La Lazio Siamo Noi"]},

        # --- Bundesliga (Germany) ---
        "Bayern Munich": {"city": "Munich", "country": "Germany", "papers": ["Kicker", "Bild Sport"]},
        "Dortmund": {"city": "Dortmund", "country": "Germany", "papers": ["Ruhr Nachrichten", "Kicker"]},
        "Leverkusen": {"city": "Leverkusen", "country": "Germany", "papers": ["Kicker", "Bild"]},

        # --- Ligue 1 (France) ---
        "PSG": {"city": "Paris", "country": "France", "papers": ["L'Equipe", "Le Parisien"]},
        "Marseille": {"city": "Marseille", "country": "France", "papers": ["La Provence", "L'Equipe"]}
    }

    def _get_context(self, team_name: str):
        # 1. Exact Match
        if team_name in self.TEAM_CONTEXT:
            return self.TEAM_CONTEXT[team_name]
            
        # 2. Smart Inference (Heuristic) for Manual Teams
        return self._infer_context_from_name(team_name)

    def _infer_context_from_name(self, name: str):
        """
        Guesses the region/press based on the team name string.
        """
        name_lower = name.lower()
        
        # Italian patterns
        if any(x in name_lower for x in ["inter", "milan", "juve", "roma", "lazio", "napoli", "calcio", "fiorentina"]):
            return {"city": "Italia (Inferido)", "country": "Italy", "papers": ["Gazzetta dello Sport", "Corriere dello Sport"]}
            
        # English patterns
        if any(x in name_lower for x in ["united", "city", "fc", "town", "albion", "wanderers", "hotspur", "villa", "palace"]):
            return {"city": "Reino Unido (Inferido)", "country": "England", "papers": ["BBC Sport", "Sky Sports News"]}
            
        # German patterns
        if any(x in name_lower for x in ["bayern", "borussia", "rb ", "leipzig", "schalke", "werder", "hamburg", "eintracht"]):
            return {"city": "Alemania (Inferido)", "country": "Germany", "papers": ["Kicker", "Bild"]}

        # Default / Spanish fallback
        return {
            "city": f"Ciudad de {name}", 
            "country": "Internacional/España", 
            "papers": [f"Diario de {name}", "Agencias Internacionales", "Marca (Global)"]
        }

    def _get_city(self, team_name): return self._get_context(team_name)["city"]
    def _get_country(self, team_name): return self._get_context(team_name)["country"]
    def _get_papers(self, team_name): return self._get_context(team_name)["papers"]

    def get_detailed_intelligence(self, match: Match) -> dict:
        """
        New method that returns both the text report and the numerical impact modifiers.
        """
        # Fetch real injuries if available
        real_injuries = {}
        try:
            from src.logic.lineup_fetcher import LineupFetcher
            from src.data.mock_provider import MockDataProvider
            fetcher = LineupFetcher(MockDataProvider())
            real_injuries = fetcher.fetch_injuries(match.competition)
        except:
            pass

        # 1. Scans with sentiment tracking
        home_news, home_impact = self._scan_and_quantify(match.home_team, real_injuries)
        away_news, away_impact = self._scan_and_quantify(match.away_team, real_injuries)
        
        # 2. Context & Weather (minimal impact usually)
        nat_context = self._scan_national_press(match.home_team)
        weather = self._analyze_weather(match)
        
        # Build Report Text
        h_papers = ', '.join(self._get_papers(match.home_team.name))
        a_papers = ', '.join(self._get_papers(match.away_team.name))
        country_name = str(self._get_country(match.home_team.name))
        
        report = f"""
        ### PRENSA LOCAL Y ENTORNO (50 min antes)
        
        **Local: {match.home_team.name} ({self._get_city(match.home_team.name)}):**
        *Fuentes Detectadas: {h_papers}*
        {home_news}
        
        **Visitante: {match.away_team.name} ({self._get_city(match.away_team.name)}):**
        *Fuentes Detectadas: {a_papers}*
        {away_news}
        
        ### CONTEXTO NACIONAL ({country_name.upper()})
        {nat_context}
        
        ### CLIMA Y CONDICIONES
        {weather}
        """.strip()

        return {
            "report": report,
            "impact": {
                "home": home_impact,
                "away": away_impact
            }
        }

    def analyze_match(self, match: Match) -> str:
        """Compatibility layer for old Predictor approach."""
        res = self.get_detailed_intelligence(match)
        return res["report"]

    def _scan_and_quantify(self, team: Team, real_injuries: dict) -> tuple:
        """
        Returns (text_report, numerical_multiplier).
        Base multiplier is 1.0 (neutral).
        """
        reports = []
        impact = 1.0
        
        # 1. Real Scraped Injuries (High Weight)
        found_real = []
        for team_name_scraped, players in real_injuries.items():
            if team.name.lower() in team_name_scraped.lower() or team_name_scraped.lower() in team.name.lower():
                for p_data in players:
                    stat = p_data.get('status', '').lower()
                    if 'out' in stat or 'baja' in stat or 'injure' in stat:
                        found_real.append(f"🚨 {p_data['player']}: {p_data['reason']} (Confirmado)")
                        impact -= 0.03 # Penalty per real injury detected in elite sources
                    elif 'doubt' in stat or 'duda' in stat:
                        found_real.append(f"⏳ {p_data['player']}: Duda por {p_data['reason']}")
                        impact -= 0.01

        # 2. Live Web News Search
        web_news, web_impact = self._search_live_news_with_sentiment(team)
        impact += web_impact
        
        if found_real or web_news:
            reports.append("INFO: Análisis de Inteligencia Real:")
            all_raw = found_real + web_news
            for item in all_raw[:6]:
                reports.append(item)
        else:
            # Fallback to team state if no live news
            bajas = [p for p in team.players if p.status.value == "Baja"]
            if bajas:
                reports.append(f"WARN: La prensa local confirma las bajas ya conocidas de {bajas[0].name}.")
                impact -= 0.02
            else:
                reports.append("OK: Sin incidencias de última hora reportadas.")

        # 3. Environment (Atmosphere)
        atmospheres = [
            ("INFO: Ambiente: 'Es una final', mucha presión en el vestuario.", -0.01),
            ("INFO: Estabilidad: Rumores de mal vestuario o impagos.", -0.04),
            ("INFO: Motivación: El club ha prometido prima por ganar.", 0.03),
            ("INFO: Táctica: Se espera un planteamiento muy atrevido.", 0.01),
            ("INFO: Entorno estable y concentrado.", 0.0)
        ]
        # Weighted random choice based on team status or just salt
        choice, mod = random.choice(atmospheres)
        reports.append(choice)
        impact += mod
        
        return "\n".join(reports), round(impact, 3)

    def _search_live_news_with_sentiment(self, team: Team) -> tuple:
        """
        Performs search and analyzes keywords for sentiment multiplier.
        """
        news_found = []
        sentiment_impact = 0.0
        
        papers = self._get_papers(team.name)
        primary_paper = papers[0] if papers else "prensa local"
        
        query = f"{team.name} {primary_paper} lesionados noticias hoy"
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        try:
            resp = requests.get(search_url, headers=headers, timeout=5)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                snippets = []
                for g in soup.find_all('div', class_=re.compile(r'VwiC3b|g|s', re.I)):
                    st_text = g.get_text()
                    if len(st_text) > 40: snippets.append(st_text)
                
                # Sentiment Scoring Rules
                neg_keywords = {
                    "baja": -0.04, "lesión": -0.03, "roja": -0.05, "quirófano": -0.06, 
                    "duda": -0.01, "crisis": -0.04, "derrota": -0.02, "problemas": -0.02
                }
                pos_keywords = {
                    "vuelve": 0.03, "recuperado": 0.03, "alta": 0.04, "listo": 0.02,
                    "motivación": 0.02, "fichaje": 0.02, "victoria": 0.01, "líder": 0.02
                }
                
                for snippet in snippets[:4]:
                    snippet_lower = snippet.lower()
                    relevance = False
                    
                    # Apply sentiment
                    for kw, val in neg_keywords.items():
                        if kw in snippet_lower:
                            sentiment_impact += val
                            relevance = True
                    for kw, val in pos_keywords.items():
                        if kw in snippet_lower:
                            sentiment_impact += val
                            relevance = True
                    
                    if relevance:
                        clean = re.sub(r'\s+', ' ', snippet).strip()
                        news_found.append(f"🔗 {clean[:140]}...")
        except:
            pass
            
        return news_found, round(sentiment_impact, 3)

    def _scan_national_press(self, team: Team) -> str:
        country = self._get_country(team.name)
        if country == "Spain":
            return "La prensa nacional (Marca/As) debate sobre la carrera por el título y la presión arbitral."
        elif country == "England":
            return "Sky Sports y BBC destacan la intensidad del calendario y su impacto en las lesiones."
        elif country == "Italy":
            return "Debate táctico en La Gazzetta sobre el 'Catenaccio' moderno y la falta de gol."
        else:
            return "Atención mediática centrada en las competiciones europeas."

    def _analyze_weather(self, match: Match) -> str:
        cond = match.conditions
        if not cond:
             return "☀️ **Clima estable**. No hay datos meteorológicos críticos."
             
        if cond.rain_mm > 5:
            return f"☔ **Lluvia intensa** ({cond.rain_mm}mm). Atención a resbalones y balones rápidos."
        elif cond.wind_kmh > 20:
             return f"💨 **Viento fuerte** ({cond.wind_kmh}km/h). Dificultad para el juego en largo."
        else:
             return "☀️ **Clima perfecto**. Sin excusas meteorológicas."

    def calculate_stat_markets(self, match: Match, bpa_home: float, bpa_away: float):
        from src.models.base import RefereeStrictness
        
        dominance = bpa_home - bpa_away # Positive if Home favors
        
        # --- Corners (Enhanced Sensitivity) ---
        # Base corners around 4-5 per team, adjusted heavily by dominance
        # If home dominates by 0.1 BPA, they get ~7 corners, away gets ~3
        corners_h = int(5.5 + (dominance * 18)) # Increased multiplier from 2 to 18
        corners_a = int(4.5 - (dominance * 12))
        
        # --- Referee Factor (Using Enum Comparison) ---
        ref_factor = 0.0
        if match.referee:
            if match.referee.strictness == RefereeStrictness.HIGH: ref_factor = 2.0
            elif match.referee.strictness == RefereeStrictness.LOW: ref_factor = -1.5
            
        cards_h = max(0, 2.0 + ref_factor + (-1.0 if dominance > 0.05 else 1.0))
        cards_a = max(0, 2.5 + ref_factor + (1.5 if dominance > 0.05 else -0.5))
        
        # --- Shots (Enhanced Sensitivity) ---
        shots_h = int(12 + (dominance * 40))
        shots_a = int(10 - (dominance * 30))
        
        # --- Shots on Target (Heuristic based on shots) ---
        # Usually ~30-40% of shots are on target
        sot_h = int(shots_h * 0.35)
        sot_a = int(shots_a * 0.35)
        
        return {
            "corners": (f"{max(2, int(corners_h-1.5))}-{int(corners_h+2)}", f"{max(1, int(corners_a-1.5))}-{int(corners_a+2)}"),
            "cards": (f"{max(0, int(cards_h-1))}-{int(cards_h+1)}", f"{max(0, int(cards_a-1))}-{int(cards_a+1)}"),
            "shots": (f"{max(4, int(shots_h-3))}-{int(shots_h+4)}", f"{max(3, int(shots_a-3))}-{int(shots_a+4)}"),
            "shots_on_target": (f"{max(1, int(sot_h-1))}-{int(sot_h+2)}", f"{max(1, int(sot_a-1))}-{int(sot_a+2)}")
        }
