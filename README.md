## Strava Calendar API

Strava Calendar API is the API that suppports Strava Calendar app to retrieve Strava personal data and plot the heatmap. It is implemented in Python Flask framework. To setup up locally devloping environment of this backend API, here is the todo list

- [ ] Fork the repo and clone your forked repo to local environment
- [ ] Install Python dependencies
- [ ] Setup MongoDB Atlas
- [ ] Setup Strava developer credentials
- [ ] Add .env file to the root directory
- [ ] Run locally

### Setup MongoDB Atlas

1. Login to your MongoDB Atlass portal
2. Create New Organization(optional)
3. Create New Project within the organization
4. Navigate to Database at the left sidebar and click `Build a database`

5. Choose the M0 Free version and the region that is closest to your geological location
   ![create-cluster](/assets/mongodb/create%20cluster.png)
6. When MongoDB processes your request, add Username and Password to authenticate your connection with MongoDB. In addition, add entries to your IP Access List (Only an IP address you add to your Access List will be able to connect to your project's clusters)
7. After your cluster is built up, click `connect button`, visit Drivers tab and select Python as programming language
   ![connect-cluster 1](/assets/mongodb/connect%20cluster1.png)

8. Follow the instruction you saw, copy somthing like `mongodb+srv://<Your username>:{your password}@cluster0.<cluster name>.mongodb.net/?retryWrites=true&w=majority` and replace line around 32 in api/index.py with your own credential
   ![connect-cluster 2](/assets/mongodb/connect%20cluster2.png)

9. Navigate to database tab, click `browse collection`, and create your collection
   ![create-database](/assets/mongodb/create-database.png)

10. After you create your database and collection, you might find the name mismatch between yours and mine at around line 40 in api/index.py. Change it to yours if needed.

### Setup Strava developer credential

To make request to Strava API, there're three critical credential: CLIENT_ID, CLIENT_SECRET, ACCESS_TOKEN
If you are a Strava user, you can login to your Strava account and hover to your icon at the top-right corner, click settings (or navigate to https://www.strava.com/settings/profile). At the last tab of left sidebar, there's My API application (or navigate to https://www.strava.com/settings/api). Once you create your application, Strava will grant you devloper Client ID, Client Secret, and access token, which you will use later in .env file

### Add .env file to the root directory

The .env.example serves as a template for developers to understand the required environment variables without exposing any sensitive data. By filling in your sensitive data and change the file name from `.env.example` to `.env`, the os.config can parse the data and application is expected to run in local environment

## Design documentation

### User flow

![user flow](docs/[strava-github-profile]%20user%20flow.png)

### Image Generation flow

![Image generation flow](docs/[strava-github-profile]%20Image%20generation%20flow.png)
