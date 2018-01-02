from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///golazo.db'
db = SQLAlchemy(app)

leagues = ["premierleague", "laligafootball", "bundesligafootball", "serieafootball", "ligue1football"]
fullname = {
    "premierleague": "Premier League",
    "laligafootball": "La Liga",
    "bundesligafootball": "Bundesliga",
    "serieafootball": "Serie A",
    "ligue1football": "Ligue 1"
}

def parse_team(team):
    if team is None:
        return None
    result = {}
    result["rank"] = int(team[0])
    result["name"] = team[1]
    result["gp"] = int(team[2])
    result["win"] = int(team[3])
    result["draw"] = int(team[4])
    result["loss"] = int(team[5])
    result["goalsfor"] = int(team[6])
    result["goalsagainst"] = int(team[7])
    result["goaldif"] = int(team[8])
    result["pts"] = int(team[9])
    #result["results"] = team[10]
    return result

def fetch_table(request):
    page_source = request.text
    parser = BeautifulSoup(page_source, "html.parser")
    standings = parser.find_all(class_="table--football")[0]
    rows = standings.find_all("tr", {"class": ["", "table-row--divider"]})
    teams = [team.get_text().split("\n") for team in rows]
    parsed_teams = []
    for i, team in enumerate(teams):
        #Get rid of empty strings
        data = []
        results = []
        for col in team:
            if col is '': continue
            if len(data) < 10:
                data.append(col)
            else:
                results.append(col)
        data.append(results)
        parsed_teams.append(parse_team(data, ))
    return parsed_teams

def get_table(league):
    r = requests.get("https://www.theguardian.com/football/{}/table".format(league))
    teams = fetch_table(r)
    for team in teams:
        team["league"] = league
    return teams

def update_all():
    for league in leagues:
        update_standings(league)

def update_standings(league):
    teams = get_table(league)
    for team in teams:
        query = db.session.query(Standing).filter_by(league=league, name=team["name"])
        if query.count() == 0:
            row = Standing(**team)
            db.session.add(row)
        else:
            query.update(team)
    db.session.commit()

def query_standings(league):
    standings = db.session.query(Standing).filter_by(league=league).order_by(Standing.rank)
    return standings

class Standing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    fullname = db.Column(db.String())
    league = db.Column(db.String())
    rank = db.Column(db.Integer)
    gp = db.Column(db.Integer)
    win = db.Column(db.Integer)
    draw = db.Column(db.Integer)
    loss = db.Column(db.Integer)
    goalsfor = db.Column(db.Integer)
    goalsagainst = db.Column(db.Integer)
    goaldif = db.Column(db.Integer)
    pts = db.Column(db.Integer)

    def __repr__(self):
        return '<Team {} in League {}'.format(self.name, self.league)

@app.route('/')
def hello_world():
    standings = []
    for team in leagues:
        data = {}
        data["name"] = fullname[team]
        data["data"] = query_standings(team)
        standings.append(data)
    return render_template("layout.html", standings=standings)