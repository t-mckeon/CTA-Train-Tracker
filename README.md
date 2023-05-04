# CTA-Train-Tracker
Dash-backed web application displaying locations and arrival times of CTA trains.
Link: http://whereismytrainat.com

<img width="1507" alt="dash_display_screenshot" src="https://user-images.githubusercontent.com/105253832/236321514-7102c0ea-b9a1-4e0a-bff4-8168067d46ba.png">


## Process

Major components of gathering data and displaying the dashboard:

1) Receiving CTA train-tracker API
2) Parsing API data and transforming into dataframes to be importing into BigQuery
3) Managing BigQuery tables and setting up data loads
4) Building out dash app which takes BigQuery data as inputs
5) Setting up VM in Google Cloud Platform to host data load and dash app
6) Setting up Google Domain and Obtaining SSL Certificate for safe internet traffic
