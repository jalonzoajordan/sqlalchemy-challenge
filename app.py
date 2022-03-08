#Now that you have completed your initial analysis, design a Flask API based on the queries that you have just developed.
import numpy as np
from pandas import to_datetime

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

import datetime as dt

from flask import Flask, jsonify

app = Flask(__name__)


#Connect to the database with SQLAlchemy
engine = create_engine("sqlite:///hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)
#save table references
measurement = Base.classes.measurement
stations = Base.classes.station

#Use Flask to create your routes.
#HomePage
@app.route("/")
def homePage():
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br>"
        f"/api/v1.0/tobs<br>"
        f"/api/v1.0/start (replace start with start date using dashes(-))<br>"
        f"/api/v1.0/start/end (replace start and end with date using dashes(-))<br>"
    )

#Precipitation Dictionary
@app.route("/api/v1.0/precipitation")
def precipitationData():
    #create a session
    session = Session(engine)
    #query the columns and close session
    results = session.query(measurement.date,measurement.prcp).all()
    session.close()
    #create dictionary from result and add to list
    prcp_result = []
    for date,prcp in results:
        prcp_dict = {}
        prcp_dict["date"] = date
        prcp_dict["precipitation"] = prcp
        prcp_result.append(prcp_dict)
    #output to json
    return jsonify(prcp_result)

#Stations Dictionary
@app.route("/api/v1.0/stations")
def stationData():
    #create a session
    session = Session(engine)
    #query the columns and close session
    results = session.query(stations.station,stations.name).distinct().all()
    session.close()
    #create dictionary from result and add to list
    stat_result = []
    for station,name in results:
        stat_dict = {}
        stat_dict["station_id"] = station
        stat_dict["station_name"] = name
        stat_result.append(stat_dict)
    #output list to json
    return jsonify(stat_result)


#Temperature Dictionary
@app.route("/api/v1.0/tobs")
def tempLastYear():
    #create a session
    session = Session(engine)
    #query for most active station
    activityQuery = engine.execute("SELECT station AS 'Station_id', count(*) AS 'Count' FROM measurement GROUP BY station ORDER BY Count desc").fetchall()
    activeStation = activityQuery[0][0]
    #get station name from stations table
    activeStationNameQuery = session.query(stations.name).filter(stations.station == activeStation).all()
    activeStationName = activeStationNameQuery[0][0]
    #query for date range (1 year before last record)
    newDateQuery = engine.execute('SELECT date FROM measurement ORDER BY date DESC LIMIT 1').fetchall()
    newDate = dt.datetime.strptime(newDateQuery[0][0],"%Y-%m-%d")
    oldDate = newDate - dt.timedelta(days=365)
    #query for results and close session
    results = session.query(measurement.date,measurement.tobs).filter(measurement.station == activeStation, measurement.date > oldDate, measurement.date < newDate).all()
    #create dictionary from result and add to list
    temp_result = []
    for date,temp in results:
        temp_dict = {}
        temp_dict['station_id'] = activeStation
        temp_dict['station_name'] = activeStationName
        temp_dict['date'] = date
        temp_dict['temperature'] = temp
        temp_result.append(temp_dict)
    #output list to json
    return jsonify(temp_result)


#Temperature Observations for date ranges
@app.route("/api/v1.0/<startDate>")
def tempStart(startDate):
    #create a session
    session = Session(engine)
    #query for most active station
    activityQuery = engine.execute("SELECT station AS 'Station_id', count(*) AS 'Count' FROM measurement GROUP BY station ORDER BY Count desc").fetchall()
    activeStation = activityQuery[0][0]
    #get station name from stations table
    activeStationNameQuery = session.query(stations.name).filter(stations.station == activeStation).all()
    activeStationName = activeStationNameQuery[0][0]
    #query for date range (all after date range)
    #convert startdate to date
    try:
        start = dt.datetime.strptime(startDate,"%m-%d-%y") 
    except:
        try:
            start = dt.datetime.strptime(startDate,"%y-%m-%d")
        except:
            try:
                start = dt.datetime.strptime(startDate,'%m-%d-%Y')
            except:
                start = dt.datetime.strptime(startDate, '%Y-%m-%d')
    #run the queries
    tmin = session.query(func.min(measurement.tobs)).filter(measurement.station == activeStation, measurement.date > start).scalar()
    tavg = session.query(func.avg(measurement.tobs)).filter(measurement.station == activeStation, measurement.date > start).scalar()
    tmax = session.query(func.max(measurement.tobs)).filter(measurement.station == activeStation, measurement.date > start).scalar()
    #add found values to list and jsonify
    temp_result = [{'date': start,'station_id': activeStation, 'station_name': activeStationName, 'TMIN': tmin, 'TAVG': tavg, 'TMAX': tmax}]
    return jsonify(temp_result)


@app.route("/api/v1.0/<startDate>/<endDate>")
def tempRange(startDate,endDate):
    #create a session
    session = Session(engine)
    #query for most active station
    activityQuery = engine.execute("SELECT station AS 'Station_id', count(*) AS 'Count' FROM measurement GROUP BY station ORDER BY Count desc").fetchall()
    activeStation = activityQuery[0][0]
    #get station name from stations table
    activeStationNameQuery = session.query(stations.name).filter(stations.station == activeStation).all()
    activeStationName = activeStationNameQuery[0][0]
    #query for date range (all after date range)
    #convert startdate to date
    try:
        start = dt.datetime.strptime(startDate,"%m-%d-%y") 
    except:
        try:
            start = dt.datetime.strptime(startDate,"%y-%m-%d")
        except:
            try:
                start = dt.datetime.strptime(startDate,'%m-%d-%Y')
            except:
                start = dt.datetime.strptime(startDate, '%Y-%m-%d')
    #convert enddate to date
    try:
        end = dt.datetime.strptime(endDate,"%m-%d-%y") 
    except:
        try:
            end = dt.datetime.strptime(endDate,"%y-%m-%d")
        except:
            try:
                end = dt.datetime.strptime(endDate,'%m-%d-%Y')
            except:
                end = dt.datetime.strptime(endDate, '%Y-%m-%d')
    #run the queries
    tmin = session.query(func.min(measurement.tobs)).filter(measurement.station == activeStation, measurement.date > start, measurement.date < end).scalar()
    tavg = session.query(func.avg(measurement.tobs)).filter(measurement.station == activeStation, measurement.date > start, measurement.date < end).scalar()
    tmax = session.query(func.max(measurement.tobs)).filter(measurement.station == activeStation, measurement.date > start, measurement.date < end).scalar()
    #add found values to list and jsonify
    temp_result = [{'start_date': start, 'end_date': end,'station_id': activeStation, 'station_name': activeStationName, 'TMIN': tmin, 'TAVG': tavg, 'TMAX': tmax}]
    return jsonify(temp_result)

if __name__ == "__main__":
    app.run(debug=True)