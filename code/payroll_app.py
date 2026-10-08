"""
payroll_app.py — the weekly payroll, for someone who has never opened a terminal.

Every Friday the office manager at Salt City Coffee exports the week's timesheet
from the point-of-sale system. This page turns it into a paycheck table and the
CSV the online payroll provider imports — without the manager touching pandas.

The app is mostly *assembly*: the roster is loaded from data/, the upload comes
from the page, and one call to `build_payroll` does all the work. What the page
adds is what a manager needs to trust the numbers: totals, a loud warning about
anything the pipeline could not match, the full lineage table, and the download.

Run it:  Run and Debug -> "Streamlit Run: Current File"   (see README Reference #1)
Test it: pytest tests/test_pipeline.py -k app
"""

# --- The page ---------------------------------------------------------------------
#
# No scaffolding. Every function this page needs already exists in the payroll
# package, and every widget it needs you used in Assignment 03. README Step 8 has
# the exact widgets, keys and labels; the tests in tests/test_pipeline.py -k app
# check them.
#
# The shape, in words:
#
#   title and a sentence of instructions
#   roster  <- load_employees()                      (fixed; not uploaded)
#   upload  <- st.file_uploader, key="timesheet"     (returns None until chosen)
#   if there is an upload:
#       timesheet <- load_timesheet(upload)
#       payroll   <- build_payroll(timesheet, roster)   one call does all the work
#       the pay period (payroll_date) as a subheader
#       four st.metric cards in st.columns(4) — totals are .sum() on a Series,
#           counts are len() of a boolean-indexed frame
#       st.warning naming the unmatched employee_ids, or st.success if none
#       st.dataframe(payroll) — the lineage table, raw and computed side by side
#       st.download_button, key="download": payroll_export(payroll).to_csv(index=False)
#
# What the page does NOT do: arithmetic on rows, cleaning, merging. If you find
# yourself writing a loop or an apply here, that logic belongs in the package.

import streamlit as st

from payroll import build_payroll, load_employees, load_timesheet, payroll_export

st.title("Salt City Coffee — Weekly Payroll")
st.write(
    "Upload this week's timesheet CSV from the point-of-sale system "
    "to see the payroll."
)

roster = load_employees()
upload = st.file_uploader("Timesheet CSV", type="csv", key="timesheet")

if upload is not None:
    timesheet = load_timesheet(upload)
    payroll = build_payroll(timesheet, roster)
    payroll_date = payroll["payroll_date"].iloc[0]

    st.subheader(f"Pay period: {payroll_date}")

    paid = payroll[payroll["pay_type"] != "unmatched"]
    overtime = payroll[payroll["pay_type"] == "overtime"]
    unmatched = payroll[payroll["pay_type"] == "unmatched"]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Employees paid", len(paid))
    col2.metric("Total hours", f"{payroll['hours_worked'].sum():,.2f}")
    col3.metric("Total gross pay", f"${payroll['gross_pay'].sum():,.2f}")
    col4.metric("Overtime weeks", len(overtime))

    if len(unmatched) > 0:
        ids = ", ".join(unmatched["employee_id"].astype(str))
        st.warning(f"Unmatched employee_ids (not on the roster, not exported): {ids}")
    else:
        st.success("Every employee_id was found on the roster.")

    st.dataframe(payroll)

    st.download_button(
        "Download payroll CSV",
        data=payroll_export(payroll).to_csv(index=False),
        file_name=f"payroll_{payroll_date}.csv",
        mime="text/csv",
        key="download",
    )
