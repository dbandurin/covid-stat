import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output
import pandas as pd
import numpy as np
import dateutil

baseURL = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/"

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

tickFont = {'size':12, 'color':"rgb(30,30,30)", 'family':"Courier New, monospace"}

def loadData(fileName, columnName): 
    data = pd.read_csv(baseURL + fileName) \
             .drop(['Lat', 'Long'], axis=1) \
             .melt(id_vars=['Province/State', 'Country/Region'], var_name='date', value_name=columnName) \
             .astype({'date':'datetime64[ns]', columnName:'Int64'}, errors='ignore')
    data['Province/State'].fillna('<all>', inplace=True)
    data[columnName].fillna(0, inplace=True)
    return data

def loadDataUS(fileName, columnName): 
    data = pd.read_csv(baseURL + fileName).drop(['Lat', 'Long_'], axis=1) 
    data.drop(columns=['UID','iso2','iso3','code3','FIPS','Admin2','Combined_Key','Population'],inplace=True,
                                                                                                errors='ignore')
    data = data.groupby(['Province_State','Country_Region']).sum().reset_index()                                                                                             
    data = data.melt(id_vars=['Province_State', 'Country_Region'], var_name='date', value_name=columnName) \
             .astype({'date':'datetime64[ns]', columnName:'Int64'}, errors='ignore')
    data.rename(columns={'Province_State':'Province/State','Country_Region':'Country/Region'},inplace=True)
    data['Province/State'].fillna('<all>', inplace=True)
    data[columnName].fillna(0, inplace=True)
    return data

def loadDataUS_details(fileName, columnName): 
    data = pd.read_csv(baseURL + fileName).drop(['Lat', 'Long_'], axis=1) 
    data.drop(columns=['UID','iso2','iso3','code3','FIPS','Combined_Key','Population'],inplace=True,
                                                                                                errors='ignore')
    data = data.groupby(['Province_State','Country_Region','Admin2']).sum().reset_index()                                                                                             
    data = data.melt(id_vars=['Province_State', 'Country_Region','Admin2'], var_name='date', value_name=columnName) \
             .astype({'date':'datetime64[ns]', columnName:'Int64'}, errors='ignore')
    data.rename(columns={'Province_State':'Province/State','Country_Region':'Country/Region','Admin2':'County'},inplace=True)
    data['Province/State'].fillna('<all>', inplace=True)
    data[columnName].fillna(0, inplace=True)
    data = data.query('date >="2020-03-01"')
    return data

allData = loadData("time_series_covid19_confirmed_global.csv", "CumConfirmed") \
   .merge(loadData("time_series_covid19_deaths_global.csv", "CumDeaths")) \
   .merge(loadData("time_series_covid19_recovered_global.csv", "CumRecovered"))

USData = loadDataUS("time_series_covid19_confirmed_US.csv", "CumConfirmed") \
  .merge(loadDataUS("time_series_covid19_deaths_US.csv", "CumDeaths")) 
USData['CumRecovered'] = 0.11 * USData['CumConfirmed']

USData_d = loadDataUS_details("time_series_covid19_confirmed_US.csv", "CumConfirmed") \
  .merge(loadDataUS_details("time_series_covid19_deaths_US.csv", "CumDeaths")) 
USData_d['CumRecovered'] = 0.11 * USData['CumConfirmed']

allData = pd.concat([allData, USData]) 

countries = allData['Country/Region'].unique()
countries.sort()

US_states = USData_d['Province/State'].unique()
US_states.sort()

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(

    dcc.Tabs([
        dcc.Tab(label='World', 
                style={'width': '165%','font-size': '130%','height': '30%'},
                children=[
                html.H2('Case History of Coronavirus (COVID-19): World'),
                html.Div(className="row", children=[
                    html.Div(className="four columns", children=[
                        html.H5('Country'),
                        dcc.Dropdown(
                            id='country',
                            options=[{'label':c, 'value':c} for c in countries],
                            value='US'
                        )
                    ]),
                    html.Div(className="four columns", children=[
                        html.H5('State/Province'),
                        dcc.Dropdown(
                            id='state'
                        )
                    ]),
                    html.Div(className="four columns", children=[
                        html.H5('Selected Metrics'),
                        dcc.Checklist(
                            id='metrics',
                            options=[{'label':m, 'value':m} for m in ['Confirmed', 'Deaths', 'Recovered']],
                            value=['Confirmed', 'Deaths']
                        )
                    ])
                ]),
                dcc.Graph(
                    id="plot_new_metrics",
                    config={ 'displayModeBar': False }
                ),
                dcc.Graph(
                    id="plot_cum_metrics",
                    config={ 'displayModeBar': False }
                )
        ]),

        dcc.Tab(label='US Counties', 
        style={'width': '35%','font-size': '130%','height': '30%'},
        children=[
                html.H2('Case History of Coronavirus (COVID-19): USA'),
                html.Div(className="row", children=[
                    html.Div(className="four columns", children=[
                        html.H5('State'),
                        dcc.Dropdown(
                            id='us_state',
                            options=[{'label':c, 'value':c} for c in US_states],
                            value='Illinois'
                        )
                    ]),
                    html.Div(className="four columns", children=[
                        html.H5('County'),
                        dcc.Dropdown(
                            id='us_county'
                        )
                    ]),
                    html.Div(className="four columns", children=[
                        html.H5('Selected Metrics'),
                        dcc.Checklist(
                            id='us_metrics',
                            options=[{'label':m, 'value':m} for m in ['Confirmed', 'Deaths']],
                            value=['Confirmed', 'Deaths']
                        )
                    ])
                ]),
                dcc.Graph(
                    id="plot_new_metrics_usa",
                    config={ 'displayModeBar': False }
                ),
                dcc.Graph(
                    id="plot_cum_metrics_usa",
                    config={ 'displayModeBar': False }
                )

        ])
    ])
        
)


@app.callback(
    [Output('state', 'options'), Output('state', 'value')],
    [Input('country', 'value')]
)
def update_states(country):
    states = list(allData.loc[allData['Country/Region'] == country]['Province/State'].unique())
    states.insert(0, '<all>')
    states.sort()
    state_options = [{'label':s, 'value':s} for s in states]
    state_value = state_options[0]['value']
    return state_options, state_value

@app.callback(
    [Output('us_county', 'options'), Output('us_county', 'value')],
    [Input('us_state', 'value')]
)
def update_counties(us_state):
    counties = list(USData_d.loc[USData_d['Province/State'] == us_state]['County'].unique())
    #counties.insert(0, 'Adams')
    counties.sort()
    county_options = [{'label':s, 'value':s} for s in counties]
    county_value = county_options[0]['value']
    return county_options, county_value

def nonreactive_data(country, state, USA=False):

    if not USA:
        data = allData.loc[allData['Country/Region'] == country] \
                    .drop('Country/Region', axis=1)
        data = data.loc[data['Province/State'] == state]
    else:
        data = USData_d.loc[USData_d['Province/State'] == country] \
                    .drop('Province/State', axis=1)
        data = data.loc[data['County'] == state]

    if len(data)>0:  
        #newCases = data.select_dtypes(include='int').diff(axis = 0, periods = 1)
        if 'CumRecovered' not in data.columns:
            data['CumRecovered'] = 0
        newCases = data[['CumConfirmed',  'CumDeaths',  'CumRecovered']]#.diff(axis = 0, periods = 1)
        newCases['CumConfirmed'] = np.insert(np.diff(data['CumConfirmed']),0,0)
        newCases['CumDeaths'] = np.insert(np.diff(data['CumDeaths']),0,0)
        newCases['CumRecovered'] = np.insert(np.diff(data['CumRecovered']),0,0)
        newCases = newCases.fillna(0)
        newCases['CumConfirmed'] = newCases['CumConfirmed'].apply(lambda x: max(x,0))
        newCases['CumDeaths'] = newCases['CumDeaths'].apply(lambda x: max(x,0))
        newCases['CumRecovered'] = newCases['CumRecovered'].apply(lambda x: max(x,0))
        newCases.columns = [column.replace('Cum', 'New') for column in newCases.columns]
        data = data.join(newCases)
    data['dateStr'] = data['date'].dt.strftime('%b %d, %Y')
    return data

def barchart(data, metrics, prefix="", yaxisTitle=""):
    figure = go.Figure(data=[
        go.Bar( 
            name=metric, x=data.date, y=data[prefix + metric],
            marker_line_color='rgb(0,0,0)', marker_line_width=1,
            marker_color={ 'Deaths':'rgb(200,30,30)', 'Recovered':'rgb(30,200,30)', 'Confirmed':'rgb(100,140,240)'}[metric]
        ) for metric in metrics
    ])
    figure.update_layout( 
              barmode='group', legend=dict(x=.05, y=0.95, font={'size':15}, bgcolor='rgba(240,240,240,0.5)'), 
              plot_bgcolor='#FFFFFF', font=tickFont) \
          .update_xaxes( 
              title="", tickangle=-90, type='category', showgrid=True, gridcolor='#DDDDDD', 
              tickfont=tickFont, ticktext=data.dateStr, tickvals=data.date) \
          .update_yaxes(
              title=yaxisTitle, showgrid=True, gridcolor='#DDDDDD')
    return figure

@app.callback(
    Output('plot_new_metrics', 'figure'), 
    [Input('country', 'value'), Input('state', 'value'), Input('metrics', 'value')]
)
def update_plot_new_metrics(country, state, metrics):
    data = nonreactive_data(country, state)
    return barchart(data, metrics, prefix="New", yaxisTitle="New Cases per Day")

@app.callback(
    Output('plot_cum_metrics', 'figure'), 
    [Input('country', 'value'), Input('state', 'value'), Input('metrics', 'value')]
)
def update_plot_cum_metrics(country, state, metrics):
    data = nonreactive_data(country, state)
    return barchart(data, metrics, prefix="Cum", yaxisTitle="Cumulated Cases")

#USA
@app.callback(
    Output('plot_new_metrics_usa', 'figure'), 
    [Input('us_state', 'value'), Input('us_county', 'value'), Input('us_metrics', 'value')]
)
def update_plot_new_metrics_usa(us_state, us_county, us_metrics):
    data = nonreactive_data(us_state, us_county, True)
    return barchart(data, us_metrics, prefix="New", yaxisTitle="New Cases per Day")

@app.callback(
    Output('plot_cum_metrics_usa', 'figure'), 
    [Input('us_state', 'value'), Input('us_county', 'value'), Input('us_metrics', 'value')]
)
def update_plot_cum_metrics_usa(us_state, us_county, us_metrics):
    data = nonreactive_data(us_state, us_county, True)
    return barchart(data, us_metrics, prefix="Cum", yaxisTitle="Cumulated Cases")


server = app.server

if __name__ == '__main__':
    app.run_server(host="0.0.0.0", debug=False)
