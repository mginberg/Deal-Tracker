
import streamlit as st
import pandas as pd
from datetime import timedelta

st.set_page_config(page_title='Agent Deal Tracker', layout='wide')

# Upload file
uploaded_file = st.file_uploader("Upload HubSpot CSV", type=["csv"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df["DATE"] = pd.to_datetime(df["DATE"], errors='coerce')
    df = df.dropna(subset=["DATE"])
    df["Submission Week"] = df["DATE"].apply(lambda x: x - timedelta(days=x.weekday()))
    df["Submission Month"] = df["DATE"].dt.strftime("%B %Y")

    # Define status categories
    PAYABLE_STATUSES = [
        "Active", "Submitted", "Approved", "Enrolled",
        "Future Active Policy", "In Progress", "Pending"
    ]
    CANCELLED_STATUSES = [
        "Cancelled", "Closed", "Denied", "Duplicate", "Early Cancellation",
        "Inactive", "Invalid Election Period", "Member Cancellation",
        "No Carrier Match", "Not Found", "Pended", "Plan Change",
        "Rejected", "Request for Information", "Unknown"
    ]

    # Read agent name from URL
    query_params = st.query_params
    selected_agent = query_params.get("agent", [None])[0]

    if not selected_agent:
        st.error("Missing agent name in URL. Use ?agent=YOUR_NAME")
    else:
        st.title(f"📊 Agent Deal Tracker – {selected_agent}")
        agent_df = df[df["CLOSER"].str.upper() == selected_agent.upper()]

        if agent_df.empty:
            st.warning(f"No deals found for '{selected_agent}'. Check spelling or data.")
        else:
            # Weekly Tracker
            st.header("📅 Weekly Tracker")
            weekly = agent_df.groupby("Submission Week")
            for week, group in weekly:
                st.subheader(f"Week of {week.strftime('%B %d, %Y')}")
                st.dataframe(group[["First Name", "Last Name", "DATE", "CARRIER", "STATUS", "Submission Month"]].sort_values("DATE"))

            # Monthly Bonus
            st.header("🏆 Monthly Bonus")
            months = sorted(agent_df["Submission Month"].unique())
            for month in months:
                current_month_df = agent_df[agent_df["Submission Month"] == month]
                good_deals = current_month_df[current_month_df["STATUS"].isin(PAYABLE_STATUSES)]
                bad_deals = current_month_df[current_month_df["STATUS"].isin(CANCELLED_STATUSES)]

                st.subheader(f"{month}")
                st.markdown("**✅ Good Deals**")
                st.dataframe(good_deals[["First Name", "Last Name", "DATE", "CARRIER", "STATUS"]])

                st.markdown("**❌ Bad Deals**")
                st.dataframe(bad_deals[["First Name", "Last Name", "DATE", "CARRIER", "STATUS"]])

                # Reinstated/Chargeback tracking
                if month != months[0]:
                    prev_month = months[months.index(month) - 1]
                    current_ids = set(current_month_df["Record ID"])
                    prior_df = agent_df[agent_df["Submission Month"] == prev_month]

                    prior_good = set(prior_df[prior_df["STATUS"].isin(PAYABLE_STATUSES)]["Record ID"])
                    prior_bad = set(prior_df[prior_df["STATUS"].isin(CANCELLED_STATUSES)]["Record ID"])

                    chargebacks = prior_good.intersection(current_ids) & set(bad_deals["Record ID"])
                    reinstatements = prior_bad.intersection(current_ids) & set(good_deals["Record ID"])

                    st.markdown("**🔁 Chargebacks (from last month)**")
                    if chargebacks:
                        st.dataframe(current_month_df[current_month_df["Record ID"].isin(chargebacks)][["First Name", "Last Name", "DATE", "CARRIER", "STATUS"]])
                    else:
                        st.write("None")

                    st.markdown("**🔄 Reinstated Deals (from last month)**")
                    if reinstatements:
                        st.dataframe(current_month_df[current_month_df["Record ID"].isin(reinstatements)][["First Name", "Last Name", "DATE", "CARRIER", "STATUS"]])
                    else:
                        st.write("None")
