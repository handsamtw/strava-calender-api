import os

PREFIX_URL = "https://www.strava.com/api/v3"
ACTIVITIES_URL = os.path.join(PREFIX_URL, "activities")
REFRESH_TOKEN_URL = os.path.join(PREFIX_URL, "oauth/token")
CMAP = {
    "Reds": "Reds",
    "Oranges": "Oranges",
    "BuGn": "BuGn",
    "Greens": "Greens",
    "PuBu": "PuBu",
    "RdPu": "RdPu",
    "twilight": "twilight",
}
FRONTEND_DEV_URL = "https://localhost:4200"
FRONTEND_PROD_URL = "https://strava-github-profile.vercel.app"
