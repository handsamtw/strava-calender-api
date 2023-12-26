import requests
from datetime import datetime, timedelta
import os
from html2image import Html2Image
import numpy as np
import pandas as pd
import io

import calmap
import matplotlib

import matplotlib.pyplot as plt

matplotlib.use("agg")


def get_all_activities(token):
    payload = {}
    headers = {"Authorization": f"Bearer {token}"}
    activities = []
    per_page = 200
    required_columns = ["name", "distance", "moving_time", "type", "start_date_local"]
    for page_num in range(1, 10):
        print(f"Page: {page_num}")
        response = requests.request(
            "GET",
            f"https://www.strava.com/api/v3/activities?page={page_num}&per_page={per_page}",
            headers=headers,
            data=payload,
        )
        if response.status_code != 200:
            print(response.status_code, response.content)
            break
        else:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                for activity in result:
                    selected_data = {col: activity[col] for col in required_columns}
                    activities.append(selected_data)
                if len(result) < 200:
                    print("We have fetched all the data. Yaho")
                    break
            else:
                print("No valid result")
                break

    return activities


def summarize_activity(activities, sport_type=None):
    ACTIVITY_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
    valid_sport_type = ["Run", "Ride", "Walk"]
    # Convert to DataFrame
    df = pd.DataFrame(activities)

    # Convert 'start_date_local' to datetime and set it as the index
    df["start_date_local"] = pd.to_datetime(
        df["start_date_local"], format=ACTIVITY_FORMAT
    )
    df.set_index("start_date_local", inplace=True)

    if sport_type is not None and sport_type in valid_sport_type:
        df = df[df["type"] == sport_type]

    # Group by date and calculate the sum for each day
    daily_summary = df.resample("D").agg({"moving_time": "sum", "distance": "sum"})
    daily_summary.rename(columns={"moving_time": "time"}, inplace=True)
    # clip all outliers to make visualization more intuitive
    outlier_std = 3
    for col in daily_summary.columns:
        max_val = int(
            np.mean(daily_summary[col]) + outlier_std * np.std(daily_summary[col])
        )
        daily_summary[col].clip(0, max_val, inplace=True)

    return daily_summary


def plot_heatmap(
    daily_summary, out_file="example_calander.png", type="time", cmap="Reds"
):
    # if type not in ["time", "distance"]:
    #     print("type must be time or distance")
    #     return
    # if cmap not in CMAP:
    #     print(
    #         f"{cmap} is not one of the color theme. Please use one of the follow {CMAP}"
    #     )
    #     return

    fig, ax = calmap.calendarplot(
        daily_summary[type],
        # daylabels="MTWTFSS",
        daylabels=["M", "TU", "W", "TH", "F", "SA", "SU"],
        cmap=cmap,
        linewidth=1,
        linecolor="white",
        fig_kws=dict(figsize=(8, 5)),
    )

    with io.BytesIO() as buffer:  # use buffer memory
        # plt.savefig(buffer, format="png")
        fig.savefig(buffer, format="png")
        buffer.seek(0)
        image_data = buffer.getvalue()
        return image_data


#     # Save plot

#     # fig.savefig(out_file, dpi=600)
#     # with open(out_file, "rb") as file:
#     #     image_data = file.read()
#     #     return image_data


# # if the token hasn't expire, will return the same token
# def refresh_access_token(refresh_token):
#     url = REFRESH_TOKEN_URL
#     refresh_data = {
#         "client_id": os.getenv("CLIENT_ID"),
#         "client_secret": os.getenv("CLIENT_SECRET"),
#         "grant_type": "refresh_token",
#         "refresh_token": refresh_token,
#     }
#     response = requests.post(url, data=refresh_data)
#     if response.status_code == 200:
#         return response.json()

#     else:
#         return Response("Failed to retrieve data.", status_code=response.status_code)


# def expire_in_n_minutes(expire_timestamp, minutes=30):
#     # Convert expiration timestamp to a datetime object
#     expire_datetime = datetime.utcfromtimestamp(expire_timestamp)

#     # Get the current time
#     current_datetime = datetime.utcnow()

#     # Calculate the time difference
#     time_difference = expire_datetime - current_datetime

#     # Check if the expiration is within 30 minutes from the current time
#     return time_difference <= timedelta(minutes=minutes)


# def get_most_recent_activity_id(access_token):
#     url = f"{ACTIVITIES_URL}?per_page=1&page=1"
#     headers = {"Authorization": f"Bearer {access_token}"}

#     response = requests.get(url, headers=headers)

#     if response.status_code == 200:
#         data = response.json()
#         if isinstance(data, list) and len(data) > 0 and "id" in data[0]:
#             return data[0]["id"]

#         else:
#             print(f"Check response type")
#             return None
#     else:
#         print(f"Failed to retrieve data. Status code: {response.status_code}")
#         return None


# def request_token(code):
#     url = "https://www.strava.com/oauth/token"

#     payload = {
#         "client_id": os.getenv("CLIENT_ID"),
#         "client_secret": os.getenv("CLIENT_SECRET"),
#         "code": code,
#         "grant_type": "authorization_code",
#     }
#     files = []
#     headers = {}

#     response = requests.request("POST", url, headers=headers, data=payload, files=files)
#     print(response.json())
#     if response.status_code == 200:
#         data = response.json()
#         return {
#             "access_token": data["access_token"],
#             "refresh_token": data["refresh_token"],
#             "expires_at": data["expires_at"],
#         }

#     else:
#         return "Error!!!"


# def html_to_activity_image(activity_id):
#     output_path = "/tmp"
#     hti = Html2Image(output_path=output_path)

#     html_content = (
#         "<div class='strava-embed-placeholder' data-embed-type='activity' data-embed-id="
#         + str(activity_id)
#         + " data-style='standard'></div><script src='https://strava-embeds.com/embed.js'></script>"
#     )

#     hti.screenshot(html_str=html_content, save_as="my_image.png")
#     with open(f"{output_path}/my_image.png", "rb") as file:
#         image_data = file.read()
#         return image_data


# """
# Calendar heatmaps from Pandas time series data.

# Plot Pandas time series data sampled by day in a heatmap per calendar year,
# similar to GitHub's contributions calendar.
# """


# _pandas_18 = StrictVersion(pd.__version__) >= StrictVersion("0.18")


# def yearplot(
#     data,
#     year=None,
#     how="sum",
#     vmin=None,
#     vmax=None,
#     cmap="Reds",
#     fillcolor="whitesmoke",
#     linewidth=1,
#     linecolor=None,
#     daylabels=calendar.day_abbr[:],
#     dayticks=True,
#     monthlabels=calendar.month_abbr[1:],
#     monthticks=True,
#     monthly_border=False,
#     ax=None,
#     **kwargs,
# ):
#     """
#     Plot one year from a timeseries as a calendar heatmap.

#     Parameters
#     ----------
#     data : Series
#         Data for the plot. Must be indexed by a DatetimeIndex.
#     year : integer
#         Only data indexed by this year will be plotted. If `None`, the first
#         year for which there is data will be plotted.
#     how : string
#         Method for resampling data by day. If `None`, assume data is already
#         sampled by day and don't resample. Otherwise, this is passed to Pandas
#         `Series.resample` (pandas < 0.18) or `pandas.agg` (pandas >= 0.18).
#     vmin : float
#         Min Values to anchor the colormap. If `None`, min and max are used after
#         resampling data by day.
#     vmax : float
#         Max Values to anchor the colormap. If `None`, min and max are used after
#         resampling data by day.
#     cmap : matplotlib colormap name or object
#         The mapping from data values to color space.
#     fillcolor : matplotlib color
#         Color to use for days without data.
#     linewidth : float
#         Width of the lines that will divide each day.
#     linecolor : color
#         Color of the lines that will divide each day. If `None`, the axes
#         background color is used, or 'white' if it is transparent.
#     daylabels : list
#         Strings to use as labels for days, must be of length 7.
#     dayticks : list or int or bool
#         If `True`, label all days. If `False`, don't label days. If a list,
#         only label days with these indices. If an integer, label every n day.
#     monthlabels : list
#         Strings to use as labels for months, must be of length 12.
#     monthticks : list or int or bool
#         If `True`, label all months. If `False`, don't label months. If a
#         list, only label months with these indices. If an integer, label every
#         n month.
#     monthly_border : bool
#         Draw black border for each month. Default: False.
#     ax : matplotlib Axes
#         Axes in which to draw the plot, otherwise use the currently-active
#         Axes.
#     kwargs : other keyword arguments
#         All other keyword arguments are passed to matplotlib `ax.pcolormesh`.

#     Returns
#     -------
#     ax : matplotlib Axes
#         Axes object with the calendar heatmap.

#     Examples
#     --------

#     By default, `yearplot` plots the first year and sums the values per day:

#     .. plot::
#         :context: close-figs

#         calmap.yearplot(events)

#     We can choose which year is plotted with the `year` keyword argment:

#     .. plot::
#         :context: close-figs

#         calmap.yearplot(events, year=2015)

#     The appearance can be changed by using another colormap. Here we also use
#     a darker fill color for days without data and remove the lines:

#     .. plot::
#         :context: close-figs

#         calmap.yearplot(events, cmap='YlGn', fillcolor='grey',
#                         linewidth=0)

#     The axis tick labels can look a bit crowded. We can ask to draw only every
#     nth label, or explicitely supply the label indices. The labels themselves
#     can also be customized:

#     .. plot::
#         :context: close-figs

#         calmap.yearplot(events, monthticks=3, daylabels='MTWTFSS',
#                         dayticks=[0, 2, 4, 6])

#     """
#     if year is None:
#         year = data.index.sort_values()[0].year

#     if how is None:
#         # Assume already sampled by day.
#         by_day = data
#     else:
#         # Sample by day.
#         if _pandas_18:
#             by_day = data.groupby(level=0).agg(how).squeeze()
#         else:
#             by_day = data.resample("D", how=how)

#     # Min and max per day.
#     if vmin is None:
#         vmin = by_day.min()
#     if vmax is None:
#         vmax = by_day.max()

#     if ax is None:
#         ax = plt.gca()

#     if linecolor is None:
#         # Unfortunately, linecolor cannot be transparent, as it is drawn on
#         # top of the heatmap cells. Therefore it is only possible to mimic
#         # transparent lines by setting them to the axes background color. This
#         # of course won't work when the axes itself has a transparent
#         # background so in that case we default to white which will usually be
#         # the figure or canvas background color.
#         linecolor = ax.get_facecolor()
#         if ColorConverter().to_rgba(linecolor)[-1] == 0:
#             linecolor = "white"

#     # Filter on year.
#     by_day = by_day[str(year)]

#     # Add missing days.
#     by_day = by_day.reindex(
#         pd.date_range(start=str(year), end=str(year + 1), freq="D")[:-1]
#     )

#     # Create data frame we can pivot later.
#     by_day = pd.DataFrame(
#         {
#             "data": by_day,
#             "fill": 1,
#             "day": by_day.index.dayofweek,
#             "week": by_day.index.isocalendar().week,
#         }
#     )

#     # There may be some days assigned to previous year's last week or
#     # next year's first week. We create new week numbers for them so
#     # the ordering stays intact and week/day pairs unique.
#     by_day.loc[(by_day.index.month == 1) & (by_day.week > 50), "week"] = 0
#     by_day.loc[(by_day.index.month == 12) & (by_day.week < 10), "week"] = (
#         by_day.week.max() + 1
#     )

#     # Pivot data on day and week and mask NaN days. (we can also mask the days with 0 counts)
#     plot_data = by_day.pivot(index="day", columns="week", values="data").values[::-1]
#     plot_data = np.ma.masked_where(np.isnan(plot_data), plot_data)

#     # Do the same for all days of the year, not just those we have data for.
#     fill_data = by_day.pivot(index="day", columns="week", values="fill").values[::-1]
#     fill_data = np.ma.masked_where(np.isnan(fill_data), fill_data)

#     # Draw background of heatmap for all days of the year with fillcolor.
#     ax.pcolormesh(fill_data, vmin=0, vmax=1, cmap=ListedColormap([fillcolor]))

#     # Draw heatmap.
#     kwargs["linewidth"] = linewidth
#     kwargs["edgecolors"] = linecolor
#     ax.pcolormesh(plot_data, vmin=vmin, vmax=vmax, cmap=cmap, **kwargs)

#     # Limit heatmap to our data.
#     ax.set(xlim=(0, plot_data.shape[1]), ylim=(0, plot_data.shape[0]))

#     # Square cells.
#     ax.set_aspect("equal")

#     # Remove spines and ticks.
#     for side in ("top", "right", "left", "bottom"):
#         ax.spines[side].set_visible(False)
#     ax.xaxis.set_tick_params(which="both", length=0)
#     ax.yaxis.set_tick_params(which="both", length=0)

#     # Get indices for monthlabels.
#     if monthticks is True:
#         monthticks = range(len(monthlabels))
#     elif monthticks is False:
#         monthticks = []
#     elif isinstance(monthticks, int):
#         monthticks = range(len(monthlabels))[monthticks // 2 :: monthticks]

#     # Get indices for daylabels.
#     if dayticks is True:
#         dayticks = range(len(daylabels))
#     elif dayticks is False:
#         dayticks = []
#     elif isinstance(dayticks, int):
#         dayticks = range(len(daylabels))[dayticks // 2 :: dayticks]

#     ax.set_xlabel("")
#     timestamps = []

#     # Month borders
#     xticks, labels = [], []
#     for month in range(1, 13):
#         first = datetime.datetime(year, month, 1)
#         last = first + relativedelta(months=1, days=-1)
#         # Monday on top
#         y0 = 6 - first.weekday()
#         y1 = 6 - last.weekday()
#         start = datetime.datetime(year, 1, 1).weekday()
#         x0 = (int(first.strftime("%j")) + start - 1) // 7
#         x1 = (int(last.strftime("%j")) + start - 1) // 7
#         P = [
#             (x0, y0 + 1),
#             (x0, 0),
#             (x1, 0),
#             (x1, y1),
#             (x1 + 1, y1),
#             (x1 + 1, 7),
#             (x0 + 1, 7),
#             (x0 + 1, y0 + 1),
#         ]

#         xticks.append(x0 + (x1 - x0 + 1) / 2)
#         labels.append(first.strftime("%b"))
#         if monthly_border:
#             poly = Polygon(
#                 P,
#                 edgecolor="black",
#                 facecolor="None",
#                 linewidth=1,
#                 zorder=20,
#                 clip_on=False,
#             )
#             ax.add_artist(poly)

#     ax.set_xticks(xticks)
#     ax.set_xticklabels(labels)
#     ax.set_ylabel("")
#     ax.yaxis.set_ticks_position("right")
#     ax.set_yticks([6 - i + 0.5 for i in dayticks])
#     ax.set_yticklabels(
#         [daylabels[i] for i in dayticks], rotation="horizontal", va="center"
#     )

#     return ax


# def calendarplot(
#     data,
#     how="sum",
#     yearlabels=True,
#     yearascending=True,
#     ncols=1,
#     yearlabel_kws=None,
#     subplot_kws=None,
#     gridspec_kws=None,
#     fig_kws=None,
#     fig_suptitle=None,
#     vmin=None,
#     vmax=None,
#     **kwargs,
# ):
#     """
#     Plot a timeseries as a calendar heatmap.

#     Parameters
#     ----------
#     data : Series
#         Data for the plot. Must be indexed by a DatetimeIndex.
#     how : string
#         Method for resampling data by day. If `None`, assume data is already
#         sampled by day and don't resample. Otherwise, this is passed to Pandas
#         `Series.resample`.
#     yearlabels : bool
#        Whether or not to draw the year for each subplot.
#     yearascending : bool
#        Sort the calendar in ascending or descending order.
#     ncols: int
#         Number of columns passed to `subplots` call.
#     yearlabel_kws : dict
#        Keyword arguments passed to the matplotlib `set_ylabel` call which is
#        used to draw the year for each subplot.
#     subplot_kws : dict
#         Keyword arguments passed to the matplotlib `add_subplot` call used to
#         create each subplot.
#     gridspec_kws : dict
#         Keyword arguments passed to the matplotlib `GridSpec` constructor used
#         to create the grid the subplots are placed on.
#     fig_kws : dict
#         Keyword arguments passed to the matplotlib `figure` call.
#     fig_suptitle : string
#         Title for the entire figure..
#     vmin : float
#         Min Values to anchor the colormap. If `None`, min and max are used after
#         resampling data by day.
#     vmax : float
#         Max Values to anchor the colormap. If `None`, min and max are used after
#         resampling data by day.
#     kwargs : other keyword arguments
#         All other keyword arguments are passed to `yearplot`.

#     Returns
#     -------
#     fig, axes : matplotlib Figure and Axes
#         Tuple where `fig` is the matplotlib Figure object `axes` is an array
#         of matplotlib Axes objects with the calendar heatmaps, one per year.

#     Examples
#     --------

#     With `calendarplot` we can plot several years in one figure:

#     .. plot::
#         :context: close-figs

#         calmap.calendarplot(events)

#     """
#     yearlabel_kws = yearlabel_kws or {}
#     subplot_kws = subplot_kws or {}
#     gridspec_kws = gridspec_kws or {}
#     fig_kws = fig_kws or {}

#     years = np.unique(data.index.year)
#     if not yearascending:
#         years = years[::-1]

#     if ncols == 1:
#         nrows = len(years)
#     else:
#         import math

#         nrows = math.ceil(len(years) / ncols)

#     fig, axes = plt.subplots(
#         nrows=nrows,
#         ncols=ncols,
#         squeeze=False,
#         subplot_kw=subplot_kws,
#         gridspec_kw=gridspec_kws,
#         **fig_kws,
#     )
#     axes = axes.flatten()
#     plt.suptitle(fig_suptitle)
#     # We explicitely resample by day only once. This is an optimization.
#     if how is None:
#         by_day = data
#     else:
#         if _pandas_18:
#             by_day = data.groupby(level=0).agg(how).squeeze()
#         else:
#             by_day = data.resample("D", how=how)

#     ylabel_kws = dict(
#         fontsize=32,
#         color=kwargs.get("fillcolor", "whitesmoke"),
#         fontweight="bold",
#         fontname="Arial",
#         ha="center",
#     )
#     ylabel_kws.update(yearlabel_kws)

#     max_weeks = 0

#     for year, ax in zip(years, axes):
#         yearplot(by_day, year=year, how=None, ax=ax, **kwargs)
#         max_weeks = max(max_weeks, ax.get_xlim()[1])

#         if yearlabels:
#             ax.set_ylabel(str(year), **ylabel_kws)

#     # If we have multiple columns, make sure any extra axes are removed
#     if ncols != 1:
#         for ax in axes[len(years) :]:
#             ax.set_axis_off()

#     # In a leap year it might happen that we have 54 weeks (e.g., 2012).
#     # Here we make sure the width is consistent over all years.
#     for ax in axes:
#         ax.set_xlim(0, max_weeks)

#     # Make the axes look good.
#     plt.tight_layout()

#     return fig, axes
