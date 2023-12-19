# strava-github-profile

spotify-github-profile  
Create Strava most recent card on your github profile

Running on Vercel serverless function, store data in MongoDB (store only access_token, refresh_token, token_expired_timestamp)

## Table of Contents

Connect And Grant Permission  
Example  
Running for development locally  
Setting up Vercel  
Setting up MongoDB  
Setting up Strava dev  
Running locally  
How to Contribute  
Features in Progress  
Credit

## Connect And Grant Permission

- Click `Connect with Strava` button below to grant permission

[![Connect with Strava](img/btn-strava.png)](http://www.strava.com/oauth/authorize?client_id=117383&response_type=code&redirect_uri=http://localhost/exchange_token&approval_prompt=force&scope=activity:read_all)

## User flow

![user flow](docs/[strava-github-profile]%20user%20flow.png)

## Image Generation flow

![Image generation flow](docs/[strava-github-profile]%20Image%20generation%20flow.png)
