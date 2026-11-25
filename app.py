"""Streamlit dashboard: streamlit run app.py"""
import json

import pandas as pd
import streamlit as st

from dora.metrics import summarize, weekly_trend

st.set_page_config(page_title="DORA Metrics", layout="wide")
st.title("DORA Metrics Dashboard")

src = st.sidebar.radio("Data source", ["Sample data", "Upload JSON", "GitHub releases"])
days = st.sidebar.number_input("Period (days)", 7, 365, 90)

deploys: list[dict] = []
if src == "Sample data":
    deploys = json.load(open("sample_data/deployments.json"))
elif src == "Upload JSON":
    f = st.sidebar.file_uploader("deployments.json", type="json")
    deploys = json.load(f) if f else []
else:
    repo = st.sidebar.text_input("owner/repo")
    if repo and st.sidebar.button("Fetch"):
        from dora.github_client import deployments_from_releases
        deploys = deployments_from_releases(repo)

if not deploys:
    st.info("Load some deployment data to begin.")
    st.stop()

s = summarize(deploys, int(days))
c1, c2, c3, c4 = st.columns(4)
c1.metric("Deploys / day", s["deployment_frequency_per_day"])
c2.metric("Lead time (median h)", s["lead_time_hours_median"])
c3.metric("Change failure rate", f"{(s['change_failure_rate'] or 0):.0%}")
c4.metric("MTTR (median h)", s["mttr_hours_median"])
st.caption(f"Overall band: **{s['band']}**. Use the trend, not the label, to drive decisions.")

trend = pd.DataFrame(weekly_trend(deploys)).set_index("week")
st.subheader("Weekly deployments")
st.bar_chart(trend["deployments"])
st.subheader("Weekly median lead time (hours)")
st.line_chart(trend["lead_time_hours_median"])
