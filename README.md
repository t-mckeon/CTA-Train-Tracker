# CTA-Train-Tracker
Dash-backed web application displaying locations and arrival times of CTA trains.
Link: http://whereismytrainat.com

<img width="1507" alt="dash_display_screenshot" src="https://user-images.githubusercontent.com/105253832/236321514-7102c0ea-b9a1-4e0a-bff4-8168067d46ba.png">

Note: Researching the process and writing the code for this project was aided by the use of [ChatGPT](https://openai.com/blog/chatgpt)

## Process

Major components of gathering data and displaying the dashboard:

1) Receiving CTA train-tracker API
2) Parsing API data and transforming into dataframes to be importing into BigQuery
3) Managing BigQuery tables and setting up data loads
4) Building out dash app which takes BigQuery data as inputs
5) Setting up Virutal Machine in Google Cloud Platform to host data load and dash app
6) Setting up Google Domain and Obtaining SSL Certificate for safe internet traffic

### CTA Train Tracking API

The Chicago Transit Authority provides citizens with live-time data of the CTA Trains currently on the system, in the expressed purpose to "create interesting new applications and mash-ups that’ll help people get the information they want or need about CTA services". By going to the [CTA API Site](https://www.transitchicago.com/developers/traintracker/) and signing up for a key through the API Key Application Form, the CTA will provide an API Key likely that same day.

### Parsing API Data

The API imports the train location data as an XML file. To parse out the data, we use the BeautifulSoup module to clean up the XML, and the find_all() function to grab each train in the system and loop through its properties, adding the data to a pandas dataframe. 

### Managing BigQuery

Google Cloud Platform provides a data storage service called [BigQuery](https://cloud.google.com/bigquery), which can be used to house the CTA data for effectively no cost (Limits apply to storage and queueing data, but for this app's purpose we don't come near those limits). I have data uploading to two BigQuery tables in this project. One is a snapshot table that truncates (replaces) the current location data of trains, continously updating and feeding the table and figure in my dash app. The second table is an aggregate table that takes data that has been transformed into train-run oriented data - containing the times a certain train passed each station on its route. This table is currently not being used but will hopefully form the base of a predictive model that will estimate train arrival times in a later iteration of the website.

### Building out Dash App

The Dash App build followed these main steps:
  1) Creating an html script setting up the base table and figure elements for the dashboard
  2) Defining a function that grabs the CTA data from BigQuery and loads it into a dataframe
  3) Obtaining a geojson file of the lat/lon locations of the CTA train system from the [Chicago Data Portal](https://data.cityofchicago.org/browse?q=cta&sortBy=relevance) (Might have to convert a Shapfile into geojson)
  3) Defining a function that plots the traces of the Train Lines, as well as the locations of the trains currently running on the CTA system
  4) Defining a function that takes in 'route color' as an input, and outputs a table with all the trains running on that Line
  5) Defining callback functions on the app to update the dashboard every 30 seconds, including 'State' dependancies to maintain UI consistency while updates are occuring
  6) Creating 'update_on_load' function to run the app, and update it on designated interval
  
### Setting up Virutal Machine

Google Cloud Platform also provides [Virtual Machines](https://cloud.google.com/compute/docs/instances/create-start-instance), essentially allowing users to use a CPU hosted virtually by google to run programs/software without having to keep your computer on constantly. These Virtual Machines are quites cost friendly as well, depending on usage. Setting up the Virtual Machine is pretty straightforward, but to run the dash app all of the dependancies must be imported into the VM's instance as well, as well as any assets the dash app uses. Finally, we use 'tmux' to run the Data Load and Dash App python scripts, which will run even when you close out of the SSH terminal in the Virtual Machine.

NOTE: Google Cloud Platform Virtual Machines are not meant for sites with high traffic. This solution is used as I am not expecting high traffic on the site for the near future. 

### Google Domain

Purchase domain from Google Domain, setting up the DNS settings to match the external IP addres of your VM. Now when you run the dash app script with host = '0.0.0.0' (Open) through your virtual machine, the app should dislay on your purchased domain. Make sure firewall settings in your VM allow for outside traffic onto the port specified in your dash app script (such as 8050, traffic isn't allowed through port 80 in GCP VM's).



