import math


DEFAULT_MATCH = {

    "home": {
        "name": "Arsenal",
        "position": 2,
        "xg": 2.10,
        "xga": 0.85,
        "scored": 2.40,
        "conceded": 0.60,
        "form": 13,
        "h2h": 1.80
    },

    "away": {
        "name": "Newcastle",
        "position": 8,
        "xg": 1.20,
        "xga": 1.60,
        "scored": 1.00,
        "conceded": 1.80,
        "form": 7,
        "h2h": 0.60
    }
}


class FootballModel:

    def __init__(
        self,
        league_avg_goals=2.75,
        total_teams=20,
        home_adv=1.15,
        away_factor=0.85,
        weather=1.0
    ):

        self.baseline = league_avg_goals / 2
        self.total_teams = total_teams

        self.home_adv = home_adv
        self.away_factor = away_factor
        self.weather = weather


    @staticmethod
    def poisson(lam, k):

        return (
            lam ** k
            * math.exp(-lam)
            / math.factorial(k)
        )


    @staticmethod
    def blend(xg, actual):

        return (
            0.60 * xg
            + 0.40 * actual
        )


    def predict(self, home, away):

        # ----------------------------------------------
        # BLENDED PERFORMANCE
        # ----------------------------------------------

        home_attack = self.blend(
            home["xg"],
            home["scored"]
        )

        home_defense = self.blend(
            home["xga"],
            home["conceded"]
        )

        away_attack = self.blend(
            away["xg"],
            away["scored"]
        )

        away_defense = self.blend(
            away["xga"],
            away["conceded"]
        )


        # ----------------------------------------------
        # RELATIVE STRENGTH
        # ----------------------------------------------

        home_base = (
            (home_attack / self.baseline)
            * (away_defense / self.baseline)
            * self.baseline
            * self.home_adv
        )

        away_base = (
            (away_attack / self.baseline)
            * (home_defense / self.baseline)
            * self.baseline
            * self.away_factor
        )


        # ----------------------------------------------
        # FORM
        # ----------------------------------------------

        home_form = (
            home["form"] / 15
        ) * home_base

        away_form = (
            away["form"] / 15
        ) * away_base


        # ----------------------------------------------
        # POSITION
        # ----------------------------------------------

        home_position = (
            1
            + (
                away["position"]
                - home["position"]
            ) / self.total_teams
        ) * home_base

        away_position = (
            1
            + (
                home["position"]
                - away["position"]
            ) / self.total_teams
        ) * away_base


        # ----------------------------------------------
        # FINAL EXPECTED GOALS
        # ----------------------------------------------

        home_lambda = (

            0.35 * home_base

            + 0.40 * home_form

            + 0.15 * home["h2h"]

            + 0.10 * home_position

        ) * self.weather


        away_lambda = (

            0.35 * away_base

            + 0.40 * away_form

            + 0.15 * away["h2h"]

            + 0.10 * away_position

        ) * self.weather


        # ----------------------------------------------
        # SCORE MATRIX
        # ----------------------------------------------

        max_goals = 12

        matrix = [

            [

                self.poisson(home_lambda, i)
                * self.poisson(away_lambda, j)

                for j in range(max_goals)

            ]

            for i in range(max_goals)
        ]


        markets = {}


        # ----------------------------------------------
        # 1X2
        # ----------------------------------------------

        markets["home_win"] = sum(

            matrix[i][j]

            for i in range(max_goals)

            for j in range(max_goals)

            if i > j
        )


        markets["draw"] = sum(

            matrix[i][i]

            for i in range(max_goals)
        )


        markets["away_win"] = sum(

            matrix[i][j]

            for i in range(max_goals)

            for j in range(max_goals)

            if i < j
        )


        # ----------------------------------------------
        # TOTAL GOALS
        # ----------------------------------------------

        for threshold, key in [

            (1, "15"),
            (2, "25"),
            (3, "35")

        ]:

            under = sum(

                matrix[i][j]

                for i in range(max_goals)

                for j in range(max_goals)

                if i + j <= threshold
            )

            markets["under_" + key] = under
            markets["over_" + key] = 1 - under


        # ----------------------------------------------
        # BTTS
        # ----------------------------------------------

        btts_no = (

            sum(
                matrix[i][0]
                for i in range(max_goals)
            )

            +

            sum(
                matrix[0][j]
                for j in range(max_goals)
            )

            -

            matrix[0][0]
        )


        markets["btts_no"] = btts_no
        markets["btts_yes"] = 1 - btts_no


        # ----------------------------------------------
        # TEAM GOALS
        # ----------------------------------------------

        markets["home_over_05"] = (
            1 - self.poisson(home_lambda, 0)
        )

        markets["home_over_15"] = (

            1
            - self.poisson(home_lambda, 0)
            - self.poisson(home_lambda, 1)
        )


        markets["away_over_05"] = (
            1 - self.poisson(away_lambda, 0)
        )

        markets["away_over_15"] = (

            1
            - self.poisson(away_lambda, 0)
            - self.poisson(away_lambda, 1)
        )


        # ----------------------------------------------
        # MOST LIKELY SCORELINES
        # ----------------------------------------------

        scorelines = sorted(

            (

                (i, j, matrix[i][j])

                for i in range(max_goals)

                for j in range(max_goals)

            ),

            key=lambda x: x[2],

            reverse=True
        )


        # ----------------------------------------------
        # VARIANCE WARNING
        # ----------------------------------------------

        warning = (

            abs(
                home["xg"] * 5
                - home["scored"] * 5
            ) > 3

            or

            abs(
                away["xg"] * 5
                - away["scored"] * 5
            ) > 3
        )


        return {

            "lambda_home": home_lambda,

            "lambda_away": away_lambda,

            "markets": markets,

            "scorelines": scorelines,

            "warning": warning
        }