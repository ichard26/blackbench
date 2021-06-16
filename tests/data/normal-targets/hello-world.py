#!/usr/bin/env python

from datetime import datetime, date, timedelta
from pathlib import Path
import sys

import matplotlib.pyplot as plt
from matplotlib.dates import YearLocator, MonthLocator, DateFormatter
from matplotlib.ticker import AutoMinorLocator

import lib

print("[*] Importing finished")

try:
    name = Path(sys.argv[1])
except IndexError:
    name = Path("black.tgz")

issues, record = lib.load(name, minified=True)

print("[*] Data file loaded")
print("[*] Data parsing finished")

sdate = issues[1].created_at.date()
edate = datetime.utcnow().date()
delta = edate - sdate
days = [sdate + timedelta(days=i) for i in range(delta.days + 1)]

print("[*] Supporting data generation finished")


def cal_open_issues_over_time(days, issues):
    issues_per_day = []
    for day in days:
        open_ = 0
        for i in issues:
            if i.created_at.date() <= day:
                if i.closed_at is None:
                    open_ += 1
                elif i.closed_at.date() > day:
                    open_ += 1
        issues_per_day.append(open_)
    return issues_per_day


issues_noprs = lib.IssueSet([v for v in issues if not v.is_pr])
issues_withprs = issues

print("[*] Data preparation finished")

ydata_withoutprs = cal_open_issues_over_time(days, issues_noprs)
#ydata_withprs = cal_open_issues_over_time(days, issues_withprs)

print("[*] Data chrunching finished")

fig, ax = plt.subplots()
ax.plot_date(
    days, ydata_withoutprs, fmt="r-", xdate=True, label="Open issues (w/o PRs)"
)
#ax.plot_date(days, ydata_withprs, fmt="b-", xdate=True, label="Open issues (w/ PRs)")
#ax.xaxis.set_major_locator(YearLocator())
#ax.xaxis.set_minor_locator(MonthLocator())
#ax.xaxis.set_major_formatter(DateFormatter("%Y"))
ax.fmt_xdata = DateFormatter('%Y-%m-%d')  # Fix the toolbar stats for X
ax.fmt_ydata = int
ax.xaxis.set_minor_formatter(DateFormatter("%b"))
ax.yaxis.set_minor_locator(AutoMinorLocator())
ax.grid(which="major", axis="y", linestyle="--")
ax.set_xlabel("Date (UTC date/time)")
ax.set_ylabel("Number of open issues")
ax.set_title(f"The number of open issues in {record.repo.name}'s issue tracker overtime.")
ax.legend()
plt.show()
