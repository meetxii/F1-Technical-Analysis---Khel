import os

import matplotlib.pyplot as plt
import pandas as pd
import requests
import streamlit as st
from google import genai

OPENF1_URL = "https://api.openf1.org/v1"
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.7-flash")


def openf1_frame(endpoint, session_key, driver_number=None):
    """Download one OpenF1 endpoint and return an empty table if unavailable."""
    parameters = {"session_key": session_key}
    if driver_number is not None:
        parameters["driver_number"] = int(driver_number)

    try:
        response = requests.get(
            f"{OPENF1_URL}/{endpoint}",
            params=parameters,
            timeout=40,
        )
        response.raise_for_status()
        data = response.json()

        if isinstance(data, list):
            return pd.DataFrame(data)
        return pd.DataFrame([data])

    except requests.RequestException:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def f1_race_sessions(year):
    try:
        response = requests.get(
            f"{OPENF1_URL}/sessions",
            params={"year": year, "session_name": "Race"},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return []


@st.cache_data(ttl=3600)
def f1_race_bundle(session_key):
    """Load the broad data set for one race."""
    endpoints = [
        "laps",
        "stints",
        "pit",
        "race_control",
        "session_result",
        "drivers",
        "overtakes",
        "weather",
    ]
    return {
        endpoint: openf1_frame(endpoint, session_key)
        for endpoint in endpoints
    }


@st.cache_data(ttl=3600)
def f1_driver_trace(session_key, driver_number):
    """Load detailed data only for the driver selected by the user."""
    return {
        "location": openf1_frame("location", session_key, driver_number),
        "car_data": openf1_frame("car_data", session_key, driver_number),
        "position": openf1_frame("position", session_key, driver_number),
        "team_radio": openf1_frame("team_radio", session_key, driver_number),
    }


def gemini_f1_summary(facts):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Gemini key is missing from .env."

    prompt = f"""
You are Khel, an evidence-first Formula 1 analyst.

Write 4 brief bullets using ONLY the facts below.
Separate confirmed facts from interpretation.
Never claim the cause of a crash, retirement, or technical failure unless the
facts explicitly state it. If it is not stated, write that the cause is unknown.

FACTS:
{facts}
"""

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )
        return response.text or "Gemini returned no summary."
    except Exception as error:
        return f"Gemini summary unavailable: {error}"


def driver_information(drivers, laps):
    """Create readable driver names such as 'VER (#1)'."""
    result = {}

    if not drivers.empty and "driver_number" in drivers.columns:
        for _, row in drivers.iterrows():
            number = int(row["driver_number"])
            name = row.get("name_acronym") or row.get("full_name") or f"Driver {number}"
            team = row.get("team_name") or "Unknown team"
            result[number] = f"{name} (#{number}) — {team}"

    if "driver_number" in laps.columns:
        for number in laps["driver_number"].dropna().unique():
            number = int(number)
            result.setdefault(number, f"Driver #{number}")

    return dict(sorted(result.items()))


def technical_metrics(car_data):
    if car_data.empty:
        return {}

    metrics = {}

    if "speed" in car_data.columns:
        metrics["Top speed (km/h)"] = round(car_data["speed"].max(), 1)
        metrics["Average speed (km/h)"] = round(car_data["speed"].mean(), 1)

    if "throttle" in car_data.columns:
        metrics["Average throttle (%)"] = round(car_data["throttle"].mean(), 1)

    if "brake" in car_data.columns:
        metrics["Braking samples (%)"] = round((car_data["brake"] > 0).mean() * 100, 1)

    if "drs" in car_data.columns:
        metrics["DRS-on samples (%)"] = round(
            car_data["drs"].isin([10, 12, 14]).mean() * 100,
            1,
        )

    return metrics


def plot_racing_line(location, driver_label, title_suffix):
    if location.empty or not {"x", "y"}.issubset(location.columns):
        st.info("Racing-line coordinates are unavailable for this selection.")
        return

    trace = location.dropna(subset=["x", "y"]).iloc[::5]
    if trace.empty:
        st.info("No usable racing-line coordinates were returned.")
        return

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot(trace["x"], trace["y"], linewidth=1.2)
    ax.scatter(trace["x"].iloc[0], trace["y"].iloc[0], s=35, label="Start")
    ax.set_title(f"Racing-line trace — {driver_label}{title_suffix}")
    ax.set_xlabel("Track X coordinate")
    ax.set_ylabel("Track Y coordinate")
    ax.set_aspect("equal", adjustable="box")
    ax.grid(alpha=0.25)
    ax.legend()
    st.pyplot(fig)

def plot_telemetry(car_data, driver_label):
    """Show a readable race overview by grouping telemetry into 20-second blocks."""
    required = {"date", "speed", "throttle", "brake"}

    if car_data.empty or not required.issubset(car_data.columns):
        st.info("Speed, throttle, and brake telemetry are unavailable for this driver.")
        return

    telemetry = car_data.copy()
    telemetry["date"] = pd.to_datetime(
        telemetry["date"],
        utc=True,
        format="mixed",
    )
    telemetry = telemetry.sort_values("date")

    if len(telemetry) < 2:
        st.info("Not enough telemetry samples were returned.")
        return

    telemetry["seconds"] = (
        telemetry["date"] - telemetry["date"].iloc[0]
    ).dt.total_seconds()

    telemetry["block"] = (telemetry["seconds"] // 20).astype(int)

    overview = (
        telemetry.groupby("block")
        .agg(
            seconds=("seconds", "mean"),
            speed=("speed", "median"),
            throttle=("throttle", "mean"),
            brake_applied=("brake", "mean"),
        )
        .reset_index(drop=True)
    )

    overview["minutes"] = overview["seconds"] / 60

    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)

    axes[0].plot(
        overview["minutes"],
        overview["speed"],
        color="#2a6fbb",
        linewidth=2,
        label="Median speed",
    )
    axes[0].set_title(f"Race telemetry overview — {driver_label}")
    axes[0].set_ylabel("Speed (km/h)")
    axes[0].grid(alpha=0.25)
    axes[0].legend()

    axes[1].plot(
        overview["minutes"],
        overview["throttle"],
        color="#2a9d5b",
        linewidth=2,
        label="Average throttle",
    )
    axes[1].plot(
        overview["minutes"],
        overview["brake_applied"],
        color="#d1495b",
        linewidth=2,
        label="Brake applied",
    )
    axes[1].set_xlabel("Minutes from first telemetry sample")
    axes[1].set_ylabel("Driver input (%)")
    axes[1].set_ylim(-5, 105)
    axes[1].grid(alpha=0.25)
    axes[1].legend()

    plt.tight_layout()
    st.pyplot(fig)

def plot_position(position_data, driver_label):
    if position_data.empty or not {"date", "position"}.issubset(position_data.columns):
        st.info("Position-trace data is unavailable for this driver.")
        return

    positions = position_data.copy()
    positions["date"] = pd.to_datetime(positions["date"], utc=True, format="mixed")
    positions = positions.sort_values("date")

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.step(positions["date"], positions["position"], where="post")
    ax.invert_yaxis()
    ax.set_title(f"Track position over time — {driver_label}")
    ax.set_xlabel("Race time")
    ax.set_ylabel("Position (1 is leader)")
    ax.grid(alpha=0.25)
    st.pyplot(fig)


def show_f1_technical():
    st.header("🏎️ F1 technical analysis")
    st.caption(
        "Evidence only: track coordinates, telemetry, tyres, pit stops, "
        "positions, overtakes, race control, weather, and available radio links."
    )

    year = st.number_input(
        "Choose a season year",
        min_value=2023,
        max_value=2030,
        value=2025,
        step=1,
    )

    sessions = f1_race_sessions(year)
    if not sessions:
        st.warning("No F1 race sessions were found for that year.")
        return

    race_options = {}
    for race in sessions:
        circuit = (
            race.get("circuit_short_name")
            or race.get("location")
            or race.get("country_name")
            or "Unknown circuit"
        )
        label = f'{circuit} — {race.get("date_start", "")[:10]}'
        race_options[f"{label} (session {race['session_key']})"] = race["session_key"]

    selected_race = st.selectbox("Choose a race", list(race_options.keys()))

    session_key = race_options[selected_race]

    if st.button("Load technical F1 data"):
        st.session_state["loaded_f1_session"] = session_key

    if st.session_state.get("loaded_f1_session") != session_key:
        st.info("Choose a race, then click 'Load technical F1 data'.")
        return

    with st.spinner("Downloading F1 timing, telemetry, and event data..."):
        bundle = f1_race_bundle(session_key)

    laps = bundle["laps"]
    stints = bundle["stints"]
    pits = bundle["pit"]
    race_control = bundle["race_control"]
    results = bundle["session_result"]
    drivers = bundle["drivers"]
    overtakes = bundle["overtakes"]
    weather = bundle["weather"]

    if laps.empty:
        st.warning("This race has no usable lap data.")
        return

    driver_labels = driver_information(drivers, laps)
    if not driver_labels:
        st.warning("No drivers were returned for this race.")
        return

    # Classification
    st.subheader("Final classification")
    if not results.empty:
        display_results = results.copy()

        if not drivers.empty and "driver_number" in drivers.columns:
            driver_columns = [
                column for column in ["driver_number", "name_acronym", "team_name"]
                if column in drivers.columns
            ]
            display_results = display_results.merge(
                drivers[driver_columns],
                on="driver_number",
                how="left",
            )

        wanted_columns = [
            column for column in [
                "position", "name_acronym", "team_name", "driver_number",
                "number_of_laps", "gap_to_leader", "dnf", "dns", "dsq",
            ]
            if column in display_results.columns
        ]
        st.dataframe(
            display_results[wanted_columns].sort_values("position"),
            use_container_width=True,
        )

    # Race incidents and race control
    st.subheader("Race-control and incident timeline")
    if race_control.empty:
        st.info("No race-control messages were returned for this session.")
        incident_rows = pd.DataFrame()
    else:
        control_columns = [
            column for column in [
                "date", "category", "flag", "lap_number", "driver_number",
                "scope", "sector", "message",
            ]
            if column in race_control.columns
        ]
        incident_rows = race_control[control_columns].copy()

        if "date" in incident_rows.columns:
            incident_rows = incident_rows.sort_values("date")

        st.dataframe(incident_rows, use_container_width=True)

        text_columns = [
            column for column in ["category", "flag", "message"]
            if column in race_control.columns
        ]
        combined_text = race_control[text_columns].fillna("").astype(str).agg(" ".join, axis=1)
        incident_words = "ACCIDENT|COLLISION|CRASH|STOPPED|RED FLAG|SAFETY CAR"
        possible_incidents = race_control[
            combined_text.str.contains(incident_words, case=False, regex=True)
        ]

        if possible_incidents.empty:
            st.info(
                "No crash-specific race-control message was found. "
                "This does not prove that no incident occurred."
            )
        else:
            st.warning(
                "Incident-related messages are shown above. Khel will not assign "
                "blame or a mechanical cause unless a source explicitly states it."
            )

    # Weather
    st.subheader("Weather evidence")
    weather_columns = [
        column for column in [
            "date", "air_temperature", "track_temperature", "humidity",
            "rainfall", "wind_speed", "wind_direction",
        ]
        if column in weather.columns
    ]
    if weather_columns:
        st.dataframe(weather[weather_columns].iloc[::5], use_container_width=True)
    else:
        st.info("No weather data was returned.")

    # Driver deep dive
    st.subheader("Driver technical deep dive")
    selected_driver = st.selectbox(
        "Choose a driver",
        options=list(driver_labels.keys()),
        format_func=lambda number: driver_labels[number],
    )
    driver_label = driver_labels[selected_driver]

    with st.spinner("Downloading the selected driver’s trace and telemetry..."):
        trace = f1_driver_trace(session_key, selected_driver)

    location = trace["location"]
    car_data = trace["car_data"]
    position_data = trace["position"]
    radio = trace["team_radio"]

    selected_laps = laps[laps["driver_number"] == selected_driver].copy()
    selected_laps = selected_laps.dropna(subset=["lap_number"]).sort_values("lap_number")

    racing_line_choice = st.selectbox(
        "Racing-line view",
        ["Whole race"] + [f"Lap {int(value)}" for value in selected_laps["lap_number"]],
    )

    trace_for_chart = location.copy()
    title_suffix = ""

    if racing_line_choice != "Whole race" and not location.empty and "date" in location.columns:
        lap_number = int(racing_line_choice.replace("Lap ", ""))
        lap_index = selected_laps.index[selected_laps["lap_number"] == lap_number][0]
        start_time = pd.to_datetime(selected_laps.loc[lap_index, "date_start"], utc=True, format="mixed")

        later_laps = selected_laps[selected_laps["lap_number"] > lap_number]
        if not later_laps.empty:
            end_time = pd.to_datetime(later_laps.iloc[0]["date_start"], utc=True, format="mixed")
        else:
            end_time = start_time + pd.Timedelta(minutes=3)

        trace_for_chart["date"] = pd.to_datetime(trace_for_chart["date"], utc=True, format="mixed")
        trace_for_chart = trace_for_chart[
            (trace_for_chart["date"] >= start_time)
            & (trace_for_chart["date"] < end_time)
        ]
        title_suffix = f" — lap {lap_number}"

    plot_racing_line(trace_for_chart, driver_label, title_suffix)

    metrics = technical_metrics(car_data)
    if metrics:
        st.subheader("Telemetry metrics")
        metric_columns = st.columns(len(metrics))
        for column, (name, value) in zip(metric_columns, metrics.items()):
            column.metric(name, value)

    plot_telemetry(car_data, driver_label)
    plot_position(position_data, driver_label)

    st.subheader("Lap, tyre, pit, and overtake evidence")

    if not selected_laps.empty:
        lap_columns = [
            column for column in [
                "lap_number", "lap_duration", "duration_sector_1",
                "duration_sector_2", "duration_sector_3", "is_pit_out_lap",
            ]
            if column in selected_laps.columns
        ]
        st.dataframe(selected_laps[lap_columns], use_container_width=True)

    driver_stints = stints[stints["driver_number"] == selected_driver] if not stints.empty else pd.DataFrame()
    if not driver_stints.empty:
        stint_columns = [
            column for column in [
                "stint_number", "compound", "lap_start", "lap_end", "tyre_age_at_start"
            ]
            if column in driver_stints.columns
        ]
        st.caption("Tyre stints")
        st.dataframe(driver_stints[stint_columns], use_container_width=True)

    driver_pits = pits[pits["driver_number"] == selected_driver] if not pits.empty else pd.DataFrame()
    if not driver_pits.empty:
        pit_columns = [
            column for column in [
                "lap_number", "lane_duration", "stop_duration", "date"
            ]
            if column in driver_pits.columns
        ]
        st.caption("Pit stops")
        st.dataframe(driver_pits[pit_columns], use_container_width=True)

    if not overtakes.empty:
        involved_overtakes = overtakes[
            (overtakes["overtaking_driver_number"] == selected_driver)
            | (overtakes["overtaken_driver_number"] == selected_driver)
        ]
        if not involved_overtakes.empty:
            st.caption("Overtakes involving this driver")
            st.dataframe(involved_overtakes, use_container_width=True)

    st.subheader("Team-radio recordings")
    if not radio.empty and "recording_url" in radio.columns:
        for _, item in radio.iterrows():
            st.link_button(
                f'Open radio recording — {item.get("date", "time unknown")}',
                item["recording_url"],
            )
    else:
        st.info("No team-radio recording links were returned for this driver.")

    # Evidence-based AI summary
    fastest_lap = (
        selected_laps["lap_duration"].min()
        if "lap_duration" in selected_laps.columns else None
    )
    dnf_status = "unknown"
    if not results.empty and "driver_number" in results.columns:
        result_row = results[results["driver_number"] == selected_driver]
        if not result_row.empty and "dnf" in result_row.columns:
            dnf_status = str(bool(result_row.iloc[0]["dnf"]))

    race_messages = []
    if not incident_rows.empty and "message" in incident_rows.columns:
        race_messages = incident_rows["message"].dropna().astype(str).head(12).tolist()

    facts = (
        f"Race: {selected_race}. "
        f"Selected driver: {driver_label}. "
        f"Fastest recorded lap: {fastest_lap}. "
        f"DNF field: {dnf_status}. "
        f"Telemetry metrics: {metrics}. "
        f"Pit-stop records: {len(driver_pits)}. "
        f"Tyre-stint records: {len(driver_stints)}. "
        f"Race-control messages: {race_messages}. "
        "Telemetry alone cannot confirm the cause of a crash or mechanical failure."
    )

    st.subheader("Khel’s evidence-based technical brief")
    st.write(gemini_f1_summary(facts))