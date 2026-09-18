import requests
import streamlit as st
import plotly.graph_objects as go


API_URL = "http://127.0.0.1:8000"


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="NZ Transit Intelligence",
    page_icon="🚌",
    layout="wide",
)


# ============================================================
# API HELPERS
# ============================================================

@st.cache_data(ttl=300)
def get_routes():

    response = requests.get(
        f"{API_URL}/gtfs/routes",
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


@st.cache_data(ttl=300)
def get_route_stops(
    route_id: str,
    direction_id: int,
):

    response = requests.get(
        f"{API_URL}/gtfs/routes/{route_id}/stops",
        params={
            "direction_id": direction_id,
        },
        timeout=20,
    )

    response.raise_for_status()

    rows = response.json()

    unique_rows = []
    seen = set()

    for row in rows:

        key = (
            row["stop_id"],
            row["stop_sequence"],
        )

        if key not in seen:

            seen.add(key)
            unique_rows.append(row)

    return unique_rows


@st.cache_data(ttl=120)
def get_network_kpis():

    response = requests.get(
        f"{API_URL}/analytics/network-kpis",
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


@st.cache_data(ttl=120)
def get_time_period_performance():

    response = requests.get(
        f"{API_URL}/analytics/time-period-performance",
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


@st.cache_data(ttl=120)
def get_top_delayed_routes():

    response = requests.get(
        f"{API_URL}/analytics/top-delayed-routes",
        params={
            "limit": 10,
            "min_observations": 10,
        },
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


@st.cache_data(ttl=120)
def get_problem_stops():

    response = requests.get(
        f"{API_URL}/analytics/problem-stops",
        params={
            "limit": 50,
            "min_observations": 5,
        },
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# DISPLAY HELPERS
# ============================================================

def route_label(route):

    short_name = (
        route.get("route_short_name")
        or ""
    ).strip()

    long_name = (
        route.get("route_long_name")
        or ""
    ).strip()

    route_id = route["route_id"]

    if (
        short_name
        and long_name
        and short_name.lower()
        == long_name.lower()
    ):
        return short_name

    if short_name and long_name:

        return (
            f"{short_name} — "
            f"{long_name}"
        )

    if short_name:
        return short_name

    if long_name:
        return long_name

    return route_id


def analytics_route_label(route):

    short_name = (
        route.get("route_short_name")
        or ""
    ).strip()

    long_name = (
        route.get("route_long_name")
        or ""
    ).strip()

    route_id = (
        route.get("route_id")
        or "Unknown"
    )

    if (
        short_name
        and long_name
        and short_name.lower()
        == long_name.lower()
    ):
        return short_name

    if short_name and long_name:

        return (
            f"{short_name} — "
            f"{long_name}"
        )

    if short_name:
        return short_name

    if long_name:
        return long_name

    return route_id


def stop_label(stop):

    stop_name = (
        stop.get("stop_name")
        or stop["stop_id"]
    )

    sequence = stop["stop_sequence"]

    return (
        f"{sequence}. "
        f"{stop_name}"
    )


# ============================================================
# PLOTLY CHART HELPERS
# ============================================================

def create_probability_gauge(
    probability: float,
):

    figure = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=probability,
            number={
                "suffix": "%"
            },
            title={
                "text":
                    "Predicted Delay Probability"
            },
            gauge={
                "axis": {
                    "range": [
                        0,
                        100,
                    ]
                },
                "bar": {},
                "steps": [
                    {
                        "range": [
                            0,
                            25,
                        ]
                    },
                    {
                        "range": [
                            25,
                            50,
                        ]
                    },
                    {
                        "range": [
                            50,
                            75,
                        ]
                    },
                    {
                        "range": [
                            75,
                            100,
                        ]
                    },
                ],
            },
        )
    )

    figure.update_layout(
        height=300,
        margin=dict(
            l=30,
            r=30,
            t=60,
            b=20,
        ),
    )

    return figure


def create_top_routes_chart(
    routes,
):

    chart_rows = list(
        reversed(routes)
    )

    labels = [
        analytics_route_label(row)
        for row in chart_rows
    ]

    values = [
        float(
            row.get(
                "delayed_percentage",
                0,
            )
            or 0
        )
        for row in chart_rows
    ]

    observations = [
        int(
            row.get(
                "observations",
                0,
            )
            or 0
        )
        for row in chart_rows
    ]

    average_delays = [
        float(
            row.get(
                "average_delay_minutes",
                0,
            )
            or 0
        )
        for row in chart_rows
    ]

    custom_data = []

    for index in range(
        len(chart_rows)
    ):

        custom_data.append(
            [
                observations[index],
                average_delays[index],
            ]
        )

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            width=0.65,
            text=[
                f"{value:.1f}%"
                for value in values
            ],
            textposition="outside",
            customdata=custom_data,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Delayed: %{x:.2f}%<br>"
                "Observations: "
                "%{customdata[0]:,}<br>"
                "Average delay: "
                "%{customdata[1]:.2f} min"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        title="Routes with Highest Delay Rate",
        xaxis_title="Delayed Observations (%)",
        yaxis_title="Route",
        height=500,
        margin=dict(
            l=30,
            r=80,
            t=60,
            b=40,
        ),
    )

    return figure


def create_time_delay_chart(
    rows,
):

    periods = [
        row["time_period"]
        for row in rows
    ]

    delayed_percentages = [
        float(
            row.get(
                "delayed_percentage",
                0,
            )
            or 0
        )
        for row in rows
    ]

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=periods,
            y=delayed_percentages,
            text=[
                f"{value:.1f}%"
                for value
                in delayed_percentages
            ],
            textposition="auto",
        )
    )

    figure.update_layout(
        title="Delay Rate by Time Period",
        xaxis_title="Time Period",
        yaxis_title="Delayed Observations (%)",
        height=400,
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=40,
        ),
    )

    return figure


def create_average_delay_chart(
    rows,
):

    periods = [
        row["time_period"]
        for row in rows
    ]

    average_delays = [
        float(
            row.get(
                "average_delay_minutes",
                0,
            )
            or 0
        )
        for row in rows
    ]

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=periods,
            y=average_delays,
            text=[
                f"{value:.2f}"
                for value
                in average_delays
            ],
            textposition="auto",
        )
    )

    figure.update_layout(
        title="Average Delay by Time Period",
        xaxis_title="Time Period",
        yaxis_title="Average Delay (Minutes)",
        height=400,
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=40,
        ),
    )

    return figure


def create_problem_stops_chart(
    rows,
):

    top_rows = rows[:10]

    chart_rows = list(
        reversed(top_rows)
    )

    stop_names = [
        row.get(
            "stop_name",
            row.get(
                "stop_id",
                "Unknown",
            ),
        )
        for row in chart_rows
    ]

    delayed_percentages = [
        float(
            row.get(
                "delayed_percentage",
                0,
            )
            or 0
        )
        for row in chart_rows
    ]

    observations = [
        int(
            row.get(
                "observations",
                0,
            )
            or 0
        )
        for row in chart_rows
    ]

    average_delays = [
        float(
            row.get(
                "average_delay_minutes",
                0,
            )
            or 0
        )
        for row in chart_rows
    ]

    maximum_delays = [
        float(
            row.get(
                "maximum_delay_minutes",
                0,
            )
            or 0
        )
        for row in chart_rows
    ]

    custom_data = []

    for index in range(
        len(chart_rows)
    ):

        custom_data.append(
            [
                observations[index],
                average_delays[index],
                maximum_delays[index],
            ]
        )

    figure = go.Figure()

    figure.add_trace(
        go.Bar(
            x=delayed_percentages,
            y=stop_names,
            orientation="h",
            width=0.65,
            text=[
                f"{value:.1f}%"
                for value
                in delayed_percentages
            ],
            textposition="outside",
            customdata=custom_data,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Delayed: %{x:.2f}%<br>"
                "Observations: "
                "%{customdata[0]:,}<br>"
                "Average delay: "
                "%{customdata[1]:.2f} min<br>"
                "Maximum delay: "
                "%{customdata[2]:.2f} min"
                "<extra></extra>"
            ),
        )
    )

    figure.update_layout(
        title="Stops with Highest Delay Rate",
        xaxis_title="Delayed Observations (%)",
        yaxis_title="Stop",
        height=520,
        margin=dict(
            l=40,
            r=80,
            t=60,
            b=40,
        ),
    )

    return figure


# ============================================================
# PROBLEM STOPS MAP
# FIXED FOR NEW PLOTLY:
# go.Scattermap instead of go.Scattermapbox
# ============================================================

def create_problem_stops_map(
    rows,
):

    valid_rows = []

    for row in rows:

        if (
            row.get("stop_lat")
            is not None
            and row.get("stop_lon")
            is not None
        ):

            valid_rows.append(row)


    if not valid_rows:

        return None


    latitudes = [
        float(
            row["stop_lat"]
        )
        for row in valid_rows
    ]

    longitudes = [
        float(
            row["stop_lon"]
        )
        for row in valid_rows
    ]

    delayed_percentages = [
        float(
            row.get(
                "delayed_percentage",
                0,
            )
            or 0
        )
        for row in valid_rows
    ]


    marker_sizes = []

    for value in delayed_percentages:

        marker_size = (
            10
            + value * 0.35
        )

        marker_size = max(
            10,
            marker_size,
        )

        marker_size = min(
            30,
            marker_size,
        )

        marker_sizes.append(
            marker_size
        )


    hover_text = []

    for row in valid_rows:

        stop_name = row.get(
            "stop_name",
            row.get(
                "stop_id",
                "Unknown",
            ),
        )

        observations = int(
            row.get(
                "observations",
                0,
            )
            or 0
        )

        delayed = float(
            row.get(
                "delayed_percentage",
                0,
            )
            or 0
        )

        average_delay = float(
            row.get(
                "average_delay_minutes",
                0,
            )
            or 0
        )

        maximum_delay = float(
            row.get(
                "maximum_delay_minutes",
                0,
            )
            or 0
        )

        hover_text.append(
            (
                f"<b>{stop_name}</b><br>"
                f"Stop ID: "
                f"{row.get('stop_id', '')}<br>"
                f"Observations: "
                f"{observations:,}<br>"
                f"Delayed: "
                f"{delayed:.2f}%<br>"
                f"Average delay: "
                f"{average_delay:.2f} min<br>"
                f"Maximum delay: "
                f"{maximum_delay:.2f} min"
            )
        )


    centre_lat = (
        sum(latitudes)
        / len(latitudes)
    )

    centre_lon = (
        sum(longitudes)
        / len(longitudes)
    )


    figure = go.Figure()

    figure.add_trace(
        go.Scattermap(
            lat=latitudes,
            lon=longitudes,
            mode="markers",

            marker={
                "size":
                    marker_sizes,

                "color":
                    delayed_percentages,

                "colorscale":
                    "YlOrRd",

                "showscale":
                    True,

                "colorbar": {
                    "title": {
                        "text":
                            "Delay %"
                    }
                },

                "opacity":
                    0.80,
            },

            text=hover_text,

            hovertemplate=(
                "%{text}"
                "<extra></extra>"
            ),
        )
    )


    figure.update_layout(

        title=(
            "Geographic Distribution "
            "of Problem Stops"
        ),

        map={
            "style":
                "open-street-map",

            "center": {
                "lat":
                    centre_lat,

                "lon":
                    centre_lon,
            },

            "zoom":
                9,
        },

        height=600,

        margin=dict(
            l=0,
            r=0,
            t=60,
            b=0,
        ),
    )


    return figure


# ============================================================
# TITLE
# ============================================================

st.title(
    "🚌 NZ Transit Intelligence"
)

st.caption(
    "Auckland Transport delay prediction "
    "and transit analytics"
)


# ============================================================
# API HEALTH
# ============================================================

api_connected = False

try:

    health_response = requests.get(
        f"{API_URL}/health",
        timeout=5,
    )

    if (
        health_response.status_code
        == 200
    ):

        api_connected = True

except requests.RequestException:

    api_connected = False


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header(
    "Journey Details"
)


if api_connected:

    st.sidebar.success(
        "Prediction API connected"
    )

else:

    st.sidebar.error(
        "Prediction API is not running"
    )


# ============================================================
# LOAD ROUTES
# ============================================================

routes = []

if api_connected:

    try:

        routes = get_routes()

    except requests.RequestException as error:

        st.error(
            "Could not load GTFS routes."
        )

        st.code(
            str(error)
        )


# ============================================================
# ROUTE / STOP SELECTION
# ============================================================

selected_route = None
selected_stop = None

route_id = None
stop_id = None
stop_sequence = None

direction_id = 0


if routes:

    selected_route = (
        st.sidebar.selectbox(
            "Route",
            options=routes,
            format_func=route_label,
        )
    )

    route_id = selected_route[
        "route_id"
    ]


    direction_id = (
        st.sidebar.selectbox(
            "Direction",
            options=[
                0,
                1,
            ],
            format_func=lambda value: (
                f"Direction {value}"
            ),
        )
    )


    try:

        stops = get_route_stops(
            route_id,
            direction_id,
        )

    except requests.RequestException as error:

        stops = []

        st.sidebar.error(
            "Could not load stops."
        )

        st.sidebar.code(
            str(error)
        )


    if stops:

        selected_stop = (
            st.sidebar.selectbox(
                "Stop",
                options=stops,
                format_func=stop_label,
            )
        )

        stop_id = selected_stop[
            "stop_id"
        ]

        stop_sequence = int(
            selected_stop[
                "stop_sequence"
            ]
        )

        st.sidebar.caption(
            f"Stop ID: {stop_id}"
        )

        st.sidebar.caption(
            f"Stop sequence: "
            f"{stop_sequence}"
        )

    else:

        st.sidebar.warning(
            "No stops found for this "
            "route and direction."
        )


# ============================================================
# HOUR OF DAY
# ============================================================

local_hour = st.sidebar.slider(
    "Hour of Day",
    min_value=0,
    max_value=23,
    value=17,
)


# ============================================================
# DAY
# ============================================================

day_number = (
    st.sidebar.selectbox(
        "Day",
        options=[
            1,
            2,
            3,
            4,
            5,
            6,
            7,
        ],
        format_func=lambda day: {
            1: "Monday",
            2: "Tuesday",
            3: "Wednesday",
            4: "Thursday",
            5: "Friday",
            6: "Saturday",
            7: "Sunday",
        }[day],
    )
)


# ============================================================
# DELAY PREDICTION
# ============================================================

st.subheader(
    "Delay Prediction"
)

st.write(
    "Select a real Auckland Transport route, "
    "stop, direction and journey time to "
    "generate a machine-learning prediction."
)


predict_disabled = (
    not api_connected
    or selected_route is None
    or selected_stop is None
)


if st.button(
    "Predict Delay",
    type="primary",
    use_container_width=True,
    disabled=predict_disabled,
):

    payload = {
        "route_id":
            route_id,

        "stop_id":
            stop_id,

        "stop_sequence":
            stop_sequence,

        "direction_id":
            int(direction_id),

        "local_hour":
            int(local_hour),

        "day_number":
            int(day_number),
    }

    try:

        response = requests.post(
            f"{API_URL}/predict-delay",
            json=payload,
            timeout=15,
        )

        if (
            response.status_code
            == 200
        ):

            result = response.json()

            probability = float(
                result[
                    "delay_probability_percent"
                ]
            )

            risk = result[
                "risk_level"
            ]

            delayed = result[
                "delayed"
            ]

            time_period = result[
                "time_period"
            ]

            is_weekend = result[
                "is_weekend"
            ]


            # ================================================
            # PREDICTION KPI CARDS
            # ================================================

            col1, col2, col3, col4 = (
                st.columns(4)
            )

            col1.metric(
                "Delay Probability",
                f"{probability:.2f}%",
            )

            col2.metric(
                "Risk Level",
                risk,
            )

            col3.metric(
                "Prediction",
                (
                    "Delayed"
                    if delayed
                    else "Not Delayed"
                ),
            )

            col4.metric(
                "Time Period",
                time_period,
            )


            # ================================================
            # PROBABILITY GAUGE
            # ================================================

            st.plotly_chart(
                create_probability_gauge(
                    probability
                ),
                use_container_width=True,
            )


            # ================================================
            # PREDICTION MESSAGE
            # ================================================

            if delayed:

                st.error(
                    "⚠️ This journey is predicted "
                    "to be delayed."
                )

            else:

                st.success(
                    "✅ This journey is currently "
                    "predicted as not delayed."
                )


            # ================================================
            # JOURNEY SUMMARY
            # ================================================

            st.subheader(
                "Journey Summary"
            )

            summary_col1, summary_col2 = (
                st.columns(2)
            )

            summary_col1.write(
                f"**Route:** "
                f"{route_label(selected_route)}"
            )

            summary_col1.write(
                f"**Stop:** "
                f"{selected_stop['stop_name']}"
            )

            summary_col1.write(
                f"**Stop Sequence:** "
                f"{stop_sequence}"
            )

            summary_col2.write(
                f"**Direction:** "
                f"{direction_id}"
            )

            summary_col2.write(
                f"**Hour:** "
                f"{local_hour}:00"
            )

            summary_col2.write(
                f"**Weekend:** "
                f"{'Yes' if is_weekend else 'No'}"
            )

        else:

            st.error(
                "Prediction request failed."
            )

            st.code(
                response.text
            )

    except requests.RequestException as error:

        st.error(
            "Could not connect to "
            "the prediction API."
        )

        st.code(
            str(error)
        )


# ============================================================
# TRANSIT NETWORK ANALYTICS
# ============================================================

st.divider()

st.header(
    "Transit Network Analytics"
)

st.caption(
    "Performance statistics calculated from "
    "Auckland Transport realtime observations."
)


# ============================================================
# NETWORK OVERVIEW
# ============================================================

if api_connected:

    try:

        network_kpis = (
            get_network_kpis()
        )

        if network_kpis:

            st.subheader(
                "Network Overview"
            )

            kpi1, kpi2, kpi3, kpi4 = (
                st.columns(4)
            )

            kpi1.metric(
                "Observations",
                f"{int(network_kpis.get('total_observations', 0) or 0):,}",
            )

            kpi2.metric(
                "Unique Trips",
                f"{int(network_kpis.get('unique_trips', 0) or 0):,}",
            )

            kpi3.metric(
                "Routes Observed",
                f"{int(network_kpis.get('routes_observed', 0) or 0):,}",
            )

            kpi4.metric(
                "Stops Observed",
                f"{int(network_kpis.get('stops_observed', 0) or 0):,}",
            )


            kpi5, kpi6, kpi7, kpi8 = (
                st.columns(4)
            )

            average_delay = float(
                network_kpis.get(
                    "average_delay_minutes",
                    0,
                )
                or 0
            )

            median_delay = float(
                network_kpis.get(
                    "median_delay_minutes",
                    0,
                )
                or 0
            )

            delayed_percentage = float(
                network_kpis.get(
                    "delayed_percentage",
                    0,
                )
                or 0
            )

            on_time_percentage = float(
                network_kpis.get(
                    "on_time_percentage",
                    0,
                )
                or 0
            )

            kpi5.metric(
                "Average Delay",
                f"{average_delay:.2f} min",
            )

            kpi6.metric(
                "Median Delay",
                f"{median_delay:.2f} min",
            )

            kpi7.metric(
                "Delayed",
                f"{delayed_percentage:.2f}%",
            )

            kpi8.metric(
                "On Time",
                f"{on_time_percentage:.2f}%",
            )

    except requests.RequestException as error:

        st.warning(
            "Network analytics could not "
            "be loaded."
        )

        st.code(
            str(error)
        )


# ============================================================
# TOP DELAYED ROUTES
# ============================================================

st.divider()

st.subheader(
    "Routes with Highest Delay Rate"
)

try:

    delayed_routes = (
        get_top_delayed_routes()
    )

    if delayed_routes:

        st.plotly_chart(
            create_top_routes_chart(
                delayed_routes
            ),
            use_container_width=True,
        )

        with st.expander(
            "View route performance data"
        ):

            route_table = []

            for row in delayed_routes:

                route_table.append(
                    {
                        "Route":
                            analytics_route_label(
                                row
                            ),

                        "Observations":
                            int(
                                row.get(
                                    "observations",
                                    0,
                                )
                                or 0
                            ),

                        "Delay Observations":
                            int(
                                row.get(
                                    "delay_observations",
                                    0,
                                )
                                or 0
                            ),

                        "Average Delay (min)":
                            round(
                                float(
                                    row.get(
                                        "average_delay_minutes",
                                        0,
                                    )
                                    or 0
                                ),
                                2,
                            ),

                        "Delayed %":
                            round(
                                float(
                                    row.get(
                                        "delayed_percentage",
                                        0,
                                    )
                                    or 0
                                ),
                                2,
                            ),

                        "On Time %":
                            round(
                                float(
                                    row.get(
                                        "on_time_percentage",
                                        0,
                                    )
                                    or 0
                                ),
                                2,
                            ),
                    }
                )

            st.dataframe(
                route_table,
                use_container_width=True,
                hide_index=True,
            )

    else:

        st.info(
            "No route analytics available."
        )

except requests.RequestException as error:

    st.warning(
        "Route performance analytics "
        "could not be loaded."
    )

    st.code(
        str(error)
    )


# ============================================================
# TIME PERIOD PERFORMANCE
# ============================================================

st.divider()

st.subheader(
    "Performance by Time Period"
)

try:

    time_rows = (
        get_time_period_performance()
    )

    if time_rows:

        chart_col1, chart_col2 = (
            st.columns(2)
        )

        with chart_col1:

            st.plotly_chart(
                create_time_delay_chart(
                    time_rows
                ),
                use_container_width=True,
            )

        with chart_col2:

            st.plotly_chart(
                create_average_delay_chart(
                    time_rows
                ),
                use_container_width=True,
            )


        with st.expander(
            "View time-period data"
        ):

            time_table = []

            for row in time_rows:

                time_table.append(
                    {
                        "Time Period":
                            row.get(
                                "time_period"
                            ),

                        "Observations":
                            int(
                                row.get(
                                    "observations",
                                    0,
                                )
                                or 0
                            ),

                        "Delay Observations":
                            int(
                                row.get(
                                    "delay_observations",
                                    0,
                                )
                                or 0
                            ),

                        "Average Delay (min)":
                            round(
                                float(
                                    row.get(
                                        "average_delay_minutes",
                                        0,
                                    )
                                    or 0
                                ),
                                2,
                            ),

                        "Delayed %":
                            round(
                                float(
                                    row.get(
                                        "delayed_percentage",
                                        0,
                                    )
                                    or 0
                                ),
                                2,
                            ),
                    }
                )

            st.dataframe(
                time_table,
                use_container_width=True,
                hide_index=True,
            )

    else:

        st.info(
            "No time-period analytics available."
        )

except requests.RequestException as error:

    st.warning(
        "Time-period analytics "
        "could not be loaded."
    )

    st.code(
        str(error)
    )


# ============================================================
# PROBLEM STOPS
# ============================================================

st.divider()

st.header(
    "Problem Stops"
)

st.caption(
    "Stops with the highest observed delay rates "
    "from realtime Auckland Transport data."
)


try:

    problem_stops = (
        get_problem_stops()
    )

    if problem_stops:

        # ====================================================
        # PROBLEM STOPS BAR CHART
        # ====================================================

        st.plotly_chart(
            create_problem_stops_chart(
                problem_stops
            ),
            use_container_width=True,
        )


        # ====================================================
        # PROBLEM STOPS DATA TABLE
        # ====================================================

        with st.expander(
            "View problem stop data"
        ):

            stop_table = []

            for row in problem_stops[:20]:

                stop_table.append(
                    {
                        "Stop":
                            row.get(
                                "stop_name"
                            ),

                        "Observations":
                            int(
                                row.get(
                                    "observations",
                                    0,
                                )
                                or 0
                            ),

                        "Delay Observations":
                            int(
                                row.get(
                                    "delay_observations",
                                    0,
                                )
                                or 0
                            ),

                        "Average Delay (min)":
                            round(
                                float(
                                    row.get(
                                        "average_delay_minutes",
                                        0,
                                    )
                                    or 0
                                ),
                                2,
                            ),

                        "Maximum Delay (min)":
                            round(
                                float(
                                    row.get(
                                        "maximum_delay_minutes",
                                        0,
                                    )
                                    or 0
                                ),
                                2,
                            ),

                        "Delayed %":
                            round(
                                float(
                                    row.get(
                                        "delayed_percentage",
                                        0,
                                    )
                                    or 0
                                ),
                                2,
                            ),
                    }
                )

            st.dataframe(
                stop_table,
                use_container_width=True,
                hide_index=True,
            )


        # ====================================================
        # PROBLEM STOPS MAP
        # ====================================================

        st.subheader(
            "Problem Stops Map"
        )

        st.caption(
            "Marker size and colour represent "
            "the observed delay rate. "
            "Hover over a marker to view stop details."
        )


        try:

            map_figure = (
                create_problem_stops_map(
                    problem_stops
                )
            )

            if map_figure is not None:

                st.plotly_chart(
                    map_figure,
                    use_container_width=True,
                )

            else:

                st.info(
                    "No stop coordinates "
                    "available for map."
                )

        except Exception as error:

            st.warning(
                "Problem stops map could "
                "not be displayed."
            )

            st.code(
                str(error)
            )

    else:

        st.info(
            "No problem stop analytics "
            "available."
        )

except requests.RequestException as error:

    st.warning(
        "Problem stop analytics "
        "could not be loaded."
    )

    st.code(
        str(error)
    )


# ============================================================
# MODEL INFORMATION
# ============================================================

st.divider()

st.subheader(
    "Model Information"
)


if api_connected:

    try:

        model_response = requests.get(
            f"{API_URL}/model-info",
            timeout=5,
        )

        if (
            model_response.status_code
            == 200
        ):

            info = (
                model_response.json()
            )

            model_name = info.get(
                "model",
                "Unknown",
            )

            st.write(
                f"**Model:** {model_name}"
            )

            accuracy = (
                info.get(
                    "accuracy"
                )
                or 0
            )

            precision = (
                info.get(
                    "precision"
                )
                or 0
            )

            recall = (
                info.get(
                    "recall"
                )
                or 0
            )

            f1 = (
                info.get(
                    "f1"
                )
                or 0
            )

            roc_auc = (
                info.get(
                    "roc_auc"
                )
                or 0
            )

            pr_auc = (
                info.get(
                    "pr_auc"
                )
                or 0
            )


            model_col1, model_col2, model_col3 = (
                st.columns(3)
            )

            model_col1.metric(
                "Accuracy",
                f"{accuracy * 100:.2f}%",
            )

            model_col2.metric(
                "ROC AUC",
                f"{roc_auc:.3f}",
            )

            model_col3.metric(
                "PR AUC",
                f"{pr_auc:.3f}",
            )


            model_col4, model_col5, model_col6 = (
                st.columns(3)
            )

            model_col4.metric(
                "Precision",
                f"{precision:.3f}",
            )

            model_col5.metric(
                "Recall",
                f"{recall:.3f}",
            )

            model_col6.metric(
                "F1 Score",
                f"{f1:.3f}",
            )

    except requests.RequestException:

        st.warning(
            "Model information "
            "is unavailable."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "NZ Transit Intelligence • "
    "GTFS + Realtime Data + PostgreSQL + "
    "Analytics + Machine Learning + "
    "FastAPI + Streamlit"
)