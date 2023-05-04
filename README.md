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

### CTA Train Tracking API

The Chicago Transit Authority provides citizens with live-time data of the CTA Trains currently on the system, in the expressed purpose to "create interesting new applications and mash-ups that’ll help people get the information they want or need about CTA services". By going to the [CTA API Site]https://www.transitchicago.com/developers/traintracker/, and signing up for a key through the API Key Application Form, the CTA will provide an API Key likely that same day.
