import streamlit as st
from prediction_engine import FootballModel, DEFAULT_MATCH

st.set_page_config(
    page_title="Football Value Model",
    page_icon="⚽",
    layout="wide"
)

st.markdown("""
<style>
.block-container {
    max-width: 1150px;
    padding-top: 1.4rem;
}

div.stButton > button {
    width: 100%;
    height: 3.2rem;
    font-weight: 700;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

st.title("⚽ Football Value Model")
st.caption(
    "Independent model • xG + actual goals + form + H2H + "
    "Poisson + bookmaker value"
)

# ==========================================================
# MODEL SETTINGS
# ==========================================================

with st.sidebar:
    st.header("⚙️ Model Settings")

    league_avg = st.number_input(
        "League average total goals",
        min_value=0.50,
        max_value=6.00,
        value=2.75,
        step=0.01
    )

    total_teams = st.number_input(
        "League teams",
        min_value=2,
        max_value=40,
        value=20
    )

    home_adv = st.number_input(
        "Home advantage",
        min_value=0.50,
        max_value=2.00,
        value=1.15,
        step=0.01
    )

    away_factor = st.number_input(
        "Away factor",
        min_value=0.50,
        max_value=1.50,
        value=0.85,
        step=0.01
    )

    weather = st.number_input(
        "Weather modifier",
        min_value=0.50,
        max_value=1.50,
        value=1.00,
        step=0.01
    )


# ==========================================================
# TEAM INPUT
# ==========================================================

def team_input(prefix, title, defaults):

    st.subheader(title)

    col1, col2 = st.columns(2)

    name = col1.text_input(
        "Team",
        defaults["name"],
        key=prefix + "name"
    )

    position = col2.number_input(
        "League position",
        min_value=1,
        max_value=40,
        value=defaults["position"],
        key=prefix + "position"
    )

    col1, col2, col3 = st.columns(3)

    xg = col1.number_input(
        "xG / match",
        min_value=0.0,
        max_value=10.0,
        value=defaults["xg"],
        step=0.01,
        key=prefix + "xg"
    )

    xga = col2.number_input(
        "xGA / match",
        min_value=0.0,
        max_value=10.0,
        value=defaults["xga"],
        step=0.01,
        key=prefix + "xga"
    )

    scored = col3.number_input(
        "Goals scored / match",
        min_value=0.0,
        max_value=10.0,
        value=defaults["scored"],
        step=0.01,
        key=prefix + "scored"
    )

    col1, col2, col3 = st.columns(3)

    conceded = col1.number_input(
        "Goals conceded / match",
        min_value=0.0,
        max_value=10.0,
        value=defaults["conceded"],
        step=0.01,
        key=prefix + "conceded"
    )

    form = col2.number_input(
        "Last-5 points",
        min_value=0,
        max_value=15,
        value=defaults["form"],
        key=prefix + "form"
    )

    h2h = col3.number_input(
        "H2H goals scored avg",
        min_value=0.0,
        max_value=10.0,
        value=defaults["h2h"],
        step=0.01,
        key=prefix + "h2h"
    )

    return {
        "name": name,
        "position": position,
        "xg": xg,
        "xga": xga,
        "scored": scored,
        "conceded": conceded,
        "form": form,
        "h2h": h2h
    }


# ==========================================================
# HOME / AWAY
# ==========================================================

left, right = st.columns(2)

with left:
    home = team_input(
        "home_",
        "🏠 Home Team",
        DEFAULT_MATCH["home"]
    )

with right:
    away = team_input(
        "away_",
        "✈️ Away Team",
        DEFAULT_MATCH["away"]
    )


st.divider()


# ==========================================================
# BOOKMAKER ODDS
# ==========================================================

st.subheader("💰 Bookmaker Prices")

st.caption(
    "Enter up to three bookmaker prices. "
    "The highest valid price is automatically selected."
)

market_definitions = [

    ("home_win", "1X2 — Home Win"),
    ("draw", "1X2 — Draw"),
    ("away_win", "1X2 — Away Win"),

    ("over_15", "Goals — Over 1.5"),
    ("under_15", "Goals — Under 1.5"),

    ("over_25", "Goals — Over 2.5"),
    ("under_25", "Goals — Under 2.5"),

    ("over_35", "Goals — Over 3.5"),
    ("under_35", "Goals — Under 3.5"),

    ("btts_yes", "BTTS — Yes"),
    ("btts_no", "BTTS — No"),

    ("home_over_05", "Home Goals — Over 0.5"),
    ("away_over_05", "Away Goals — Over 0.5")
]


bookmaker_odds = {}

for market_id, market_name in market_definitions:

    st.markdown(f"**{market_name}**")

    col1, col2, col3 = st.columns(3)

    bookmaker_odds[market_id] = {}

    for column, bookmaker in zip(
        (col1, col2, col3),
        ("Book A", "Book B", "Book C")
    ):

        price = column.number_input(
            bookmaker,
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=0.01,
            key=f"{market_id}_{bookmaker}"
        )

        bookmaker_odds[market_id][bookmaker] = (
            price if price > 1.0 else None
        )


# ==========================================================
# RUN MODEL
# ==========================================================

if st.button("🔮 RUN MODEL", type="primary"):

    model = FootballModel(
        league_avg_goals=league_avg,
        total_teams=total_teams,
        home_adv=home_adv,
        away_factor=away_factor,
        weather=weather
    )

    result = model.predict(home, away)

    st.success("Prediction completed")


    # ------------------------------------------------------
    # EXPECTED GOALS
    # ------------------------------------------------------

    col1, col2, col3 = st.columns(3)

    col1.metric(
        home["name"],
        f'{result["lambda_home"]:.2f} goals'
    )

    col2.metric(
        "Expected Total",
        f'{result["lambda_home"] + result["lambda_away"]:.2f}'
    )

    col3.metric(
        away["name"],
        f'{result["lambda_away"]:.2f} goals'
    )


    if result["warning"]:

        st.warning(
            "⚠️ Large xG vs actual-goal gap detected. "
            "Model confidence should be reduced."
        )


    # ------------------------------------------------------
    # CORE MARKETS
    # ------------------------------------------------------

    st.subheader("🎯 Core Predictions")

    core_markets = [

        ("Home Win", "home_win"),
        ("Draw", "draw"),
        ("Away Win", "away_win"),

        ("Over 2.5", "over_25"),
        ("Under 2.5", "under_25"),

        ("BTTS Yes", "btts_yes"),
        ("BTTS No", "btts_no")
    ]

    columns = st.columns(4)

    for i, (label, market_id) in enumerate(core_markets):

        probability = result["markets"][market_id]

        columns[i % 4].metric(
            label,
            f"{probability * 100:.1f}%",
            f"Fair {1 / probability:.2f}"
        )


    # ------------------------------------------------------
    # MARKET TABLE
    # ------------------------------------------------------

    st.subheader("📊 Market Assessment")

    rows = []

    for market_id, market_name in market_definitions:

        probability = result["markets"][market_id]

        prices = [
            (price, bookmaker)
            for bookmaker, price
            in bookmaker_odds[market_id].items()
            if price
        ]

        best = max(prices) if prices else None

        fair_odds = 1 / probability

        if best:

            best_price, bookmaker = best

            edge = probability - (1 / best_price)

            ev = (probability * best_price) - 1

            if edge >= 0.03 and ev >= 0.03:
                rating = "VALUE"

            elif edge >= 0.01:
                rating = "WATCH"

            else:
                rating = "NO VALUE"

        else:

            best_price = None
            bookmaker = None
            edge = None
            ev = None

            rating = "NO BET"


        rows.append({

            "Market": market_name,

            "Model %":
                f"{probability * 100:.1f}%",

            "Fair Odds":
                f"{fair_odds:.2f}",

            "Best Odds":
                f"{best_price:.2f}"
                if best_price else "—",

            "Bookmaker":
                bookmaker or "—",

            "Edge":
                f"{edge * 100:+.1f}%"
                if edge is not None else "—",

            "EV":
                f"{ev * 100:+.1f}%"
                if ev is not None else "—",

            "Rating":
                rating
        })


    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True
    )


    # ------------------------------------------------------
    # SCORELINES
    # ------------------------------------------------------

    st.subheader("🔢 Most Likely Scorelines")

    score_rows = []

    for home_goals, away_goals, probability in result["scorelines"][:10]:

        score_rows.append({

            "Score":
                f"{home_goals}-{away_goals}",

            "Probability":
                f"{probability * 100:.2f}%"
        })


    st.dataframe(
        score_rows,
        use_container_width=True,
        hide_index=True
    )


    # ------------------------------------------------------
    # TEAM GOALS
    # ------------------------------------------------------

    st.subheader("📈 Team Goals")

    st.write(
        f"**{home['name']}** — "
        f"Over 0.5: "
        f"{result['markets']['home_over_05'] * 100:.1f}%"
    )

    st.write(
        f"**{away['name']}** — "
        f"Over 0.5: "
        f"{result['markets']['away_over_05'] * 100:.1f}%"
    )


    # ------------------------------------------------------
    # VALUE FINDER
    # ------------------------------------------------------

    st.subheader("💎 Best Value")

    values = []

    for market_id, market_name in market_definitions:

        probability = result["markets"][market_id]

        for bookmaker, price in bookmaker_odds[market_id].items():

            if price:

                edge = probability - (1 / price)

                ev = probability * price - 1

                if edge >= 0.03 and ev >= 0.03:

                    values.append(
                        (
                            ev,
                            market_name,
                            bookmaker,
                            price,
                            1 / probability,
                            edge
                        )
                    )


    values.sort(reverse=True)


    if values:

        for (
            ev,
            market_name,
            bookmaker,
            price,
            fair,
            edge
        ) in values[:5]:

            st.success(
                f"**{market_name}** · "
                f"{bookmaker} @ {price:.2f} · "
                f"Fair {fair:.2f} · "
                f"Edge +{edge * 100:.1f}% · "
                f"EV +{ev * 100:.1f}%"
            )

    else:

        st.info(
            "No market meets the current value threshold."
        )


st.caption(
    "Independent analytical model. "
    "Estimates are not guarantees of match outcomes."
)