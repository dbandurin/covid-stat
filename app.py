import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output
import pandas as pd
import numpy as np
import dateutil
import warnings
warnings.filterwarnings("ignore")

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
    data = data.query('date >="2020-02-15"')
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
    #data = data.query('date >="2020-02-15"')
    data = data.query('date >="2021-02-15"')
    return data

def loadDataUS_details(fileName, columnName, drop_pop = True): 
    data = pd.read_csv(baseURL + fileName) #.drop(['Lat', 'Long_'], axis=1) 
    data.drop(columns=['UID','iso2','iso3','code3','FIPS','Combined_Key'],inplace=True,errors='ignore')
    if drop_pop:
        data.drop(columns=['Population'],inplace=True, errors='ignore')
    data = data.groupby(['Province_State','Country_Region','Admin2','Lat', 'Long_']).sum().reset_index()                                                                                             
    data = data.melt(id_vars=['Province_State', 'Country_Region','Admin2','Lat', 'Long_'], var_name='date', value_name=columnName) \
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

#For maps
USData_pop = loadDataUS_details("time_series_covid19_deaths_US.csv", "Population", False).query('date == "Population"')

date_max = max(USData_d.date)
USData_m = USData_d.query('date == "{}"'.format(date_max))  
USData_m = pd.merge(USData_m, USData_pop[['Province/State','County','Population']], on=['Province/State','County'])
USData_m['CumDeaths/Population (%)'] = 100 * USData_m['CumDeaths'] / USData_m['Population']
USData_m['CumConfirmed/Population (%)'] = 100 * USData_m['CumConfirmed'] / USData_m['Population'] 
USData_m['text'] = USData_m['Province/State'] + ', ' + USData_m['County'] + \
            ',<br> Population ' + USData_m['Population'].astype(str) +\
            ',<br> Confirmed ' + USData_m['CumConfirmed'].astype(str) +\
            ',<br> Deaths ' +   USData_m['CumDeaths'].astype(str) +\
            ',<br> Confirmed/Population (%) ' +   USData_m['CumConfirmed/Population (%)'].astype(str) +\
            ',<br> Deaths/Population (%) ' +   USData_m['CumDeaths/Population (%)'].astype(str)
for col in ['Population','CumConfirmed','CumDeaths','CumDeaths/Population (%)','CumConfirmed/Population (%)']:
    USData_m[col] = USData_m[col].astype(float)

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

                html.Div([ html.P(id = "tot_stat", 
                          style={'textAlign': 'center','font-size': '100%', 'font-weight': 'bold'},
                          children=["init"])
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

        dcc.Tab(label='US States & Counties', 
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

                html.Div([ html.P(id = "tot_stat_us", 
                          style={'textAlign': 'center','font-size': '100%', 'font-weight': 'bold'},
                          children=["init"])
                         ]),

                dcc.Graph(
                    id="plot_new_metrics_usa",
                    config={ 'displayModeBar': False }
                ),
                dcc.Graph(
                    id="plot_cum_metrics_usa",
                    config={ 'displayModeBar': False }
                ),
                html.Div(className="six columns", children=[
                        html.Div(className="raw", children=[
                            html.H6('Cumulative Metric for Map'),
                            dcc.Dropdown(
                                id='us_map_metric',
                                options=[{'label':c, 'value':c} for c in 
                                ['Confirmed','Deaths','Confirmed/Population (%)','Deaths/Population (%)',
                                'Population']],
                                value='Confirmed'
                            ),
                            #html.H6('Bottom threshold'),
                            dcc.Input(
                                id="us_map_thresh",type='number',
                                placeholder='Bottom threshold'
                                #value=0
                                )
                        ]),
                        dcc.Graph(
                            id='us_map',
                            config={ 'displayModeBar': False }
                        )
                ])

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
        # print(metrics)
        # print(data.columns)
        # print(len(data))
    figure = go.Figure()
    if len(data)>0:
        X = data.date.apply(lambda x: str(x)[:10])
        figure = go.Figure(data=[
            go.Bar( 
                name=metric, x=X, y=data[prefix + metric],
                marker_line_color='rgb(0,0,0)', marker_line_width=1,
                marker_color={ 'Deaths':'rgb(200,30,30)', 'Recovered':'rgb(30,200,30)', 'Confirmed':'rgb(100,140,240)'}[metric]
            ) for metric in metrics
        ])
        figure.update_layout( 
                barmode='group', legend=dict(x=.05, y=0.95, font={'size':6}, bgcolor='rgba(240,240,240,0.5)'), 
                plot_bgcolor='#FFFFFF', font=tickFont, 
                xaxis = dict(tickmode = 'linear', dtick = 9)) \
            .update_xaxes( 
                title="", tickangle=-60, type='category', showgrid=True, gridcolor='#DDDDDD', 
                tickfont=tickFont, ticktext=data.dateStr, tickvals=X) \
            .update_yaxes(
                title=yaxisTitle, showgrid=True, gridcolor='#DDDDDD') 
                
    return figure

def us_map(metric, Data):
    fig = go.Figure(data=go.Scattergeo(
            #locationmode = 'USA-states',
            lon = Data['Long_'],
            lat = Data['Lat'],
            text = Data['text'],
            mode = 'markers',
            marker = dict(
                size = 4,
                opacity = 0.95,
                reversescale = True,
                autocolorscale = False,
                symbol = 'square',
                line = dict(
                    width=1,
                    color='rgba(102, 102, 102)'
                ),
                colorscale = 'Electric', #scl, #'Blues',
                color = Data[metric],
                cmin = np.percentile(Data[metric],[1])[0],
                cmax = np.percentile(Data[metric],[99.5])[0],
                colorbar_title="{}".format(metric)
            )
    ))
    fig.update_layout(
            title = 'Covid-19 US County Map, {} (Hover for status)'.format(str(date_max)[:10]),
            #geo_scope='usa'
            autosize=False,
            width=900,
            height=600,
            geo = dict(
                scope='usa',
                projection_type='albers usa',
                showland = True,
                landcolor = "rgb(250, 250, 250)",
                subunitcolor = "rgb(217, 217, 217)",
                countrycolor = "rgb(217, 217, 217)",
                countrywidth = 0.5,
                subunitwidth = 0.5
            )
    )
    return fig

@app.callback(
    Output('plot_new_metrics', 'figure'), 
    [Input('country', 'value'), Input('state', 'value'), Input('metrics', 'value')]
)
def update_plot_new_metrics(country, state, metrics):
    data = nonreactive_data(country, state)
    return barchart(data, metrics, prefix="New", yaxisTitle="New Cases per Day")

@app.callback(
    [Output('plot_cum_metrics', 'figure'), 
     Output('tot_stat', 'children')],
    [Input('country', 'value'), Input('state', 'value'), Input('metrics', 'value')]
)
def update_plot_cum_metrics(country, state, metrics):
    data = nonreactive_data(country, state)
    tot_conf, tot_d = 0,0
    if len(data)>0:
        tot_conf = data.CumConfirmed.iloc[-1]
        tot_d = data.CumDeaths.iloc[-1]
    return barchart(data, metrics, prefix="Cum", yaxisTitle="Cumulated Cases"),\
           'Total Confirmed {}, Deaths {}'.format(tot_conf,tot_d)

#USA
@app.callback(
    Output('plot_new_metrics_usa', 'figure'), 
    [Input('us_state', 'value'), Input('us_county', 'value'), Input('us_metrics', 'value')]
)
def update_plot_new_metrics_usa(us_state, us_county, us_metrics):
    data = nonreactive_data(us_state, us_county, True)
    return barchart(data, us_metrics, prefix="New", yaxisTitle="New Cases per Day")

@app.callback(
    [Output('plot_cum_metrics_usa', 'figure'), 
    Output('tot_stat_us', 'children')],
    [Input('us_state', 'value'), Input('us_county', 'value'), Input('us_metrics', 'value')]
)
def update_plot_cum_metrics_usa(us_state, us_county, us_metrics):
    data = nonreactive_data(us_state, us_county, True)
    tot_conf = data.CumConfirmed.iloc[-1]
    tot_d = data.CumDeaths.iloc[-1]
    return barchart(data, us_metrics, prefix="Cum", yaxisTitle="Cumulated Cases"),\
           'Total Confirmed {}, Deaths {}'.format(tot_conf,tot_d)

@app.callback(
    Output('us_map', 'figure'), 
    [Input('us_map_metric', 'value'), Input('us_map_thresh', 'value')]
)
def update_us_map(metric, thresh):
    if metric != 'Population':
        metric = 'Cum'+metric
    threshold = 0
    if thresh != None and thresh > 0:
        threshold = thresh
    data = USData_m[USData_m[metric]>threshold]   
    if len(data) < 2:
        data = USData_m
    return us_map(metric, data)

server = app.server

if __name__ == '__main__':
    app.run_server(host="0.0.0.0", debug=False)
