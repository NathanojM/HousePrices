from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd

# Load and preprocess the data
table = pd.read_csv('price.csv')
table["Date"] = pd.to_datetime(table["Date"])
table["Street"] = table["Street"].str.replace("  ", " ")
table["last word"] = table["Street"].str.split().str[-1]
table = table[table["Price"] > 100]
freq = table["last word"].value_counts()
table = table.join(freq, on="last word", rsuffix="_count")
table.loc[table["count"] < 50, "last word"] = "OTHER"
table["last word"] = table["last word"].astype(str)
table["first word"] = table["Street"].astype(str).str.split(" ").str[:-1].str.join(" ")

#get letter data
def get_letter_data(letter):
    temp_table = table.copy()
    temp_table[letter] = temp_table["first word"].str.count(letter)
    averaged = temp_table[[letter, "Price"]].groupby(letter).agg(["median", "count","min","max"]).reset_index()
    averaged.columns = [letter, "Median", "Count","Min","Max"]
    return averaged

# get suffix data
def get_data(sortby):
    grouped = table[['last word', 'Price']].groupby('last word').agg(['count', 'mean', 'min', 'max', 'std', 'median'])
    grouped = grouped.reset_index()
    grouped.columns = ["last word", "count", "mean", "min", "max", "std", "median"]
    grouped = grouped[grouped["last word"] != "nan"]

    if sortby == "alphabetical":
        grouped = grouped.sort_values(by="last word", ascending=True)
    else:
        grouped = grouped.sort_values(by=sortby, ascending=False)

    grouped["maxdiff"] = grouped["max"] - grouped["median"]
    grouped["mindiff"] = grouped["median"] - grouped["min"]
    return grouped


app = Dash(__name__)
server = app.server
# Layout
app.layout = html.Div([
    html.H1('House Prices by Category of Street Name', style={'textAlign': 'center'}),

    html.Div([
        dcc.Dropdown(id='sort-dropdown', value="max", style={'width': '300px', 'margin': 'auto'},
                     options=[
                {'label': 'Median', 'value': 'median'},
                {'label': 'Max', 'value': 'max'},
                {'label': 'Min', 'value': 'min'},
                {'label': 'Alphabetical (A-Z)', 'value': 'alphabetical'},
                {'label': 'Popularity', 'value': 'count'}])]),
    dcc.Graph(id='suffix-graph'),

    html.Div([
        dcc.Dropdown(id='letter-dropdown', value="A", style={'width': '300px', 'margin': 'auto'},
                     options=[{'label': chr(c), 'value': chr(c)} for c in range(ord('A'), ord('Z')+1)])]),
    dcc.Graph(id='letter-graph')])



@callback(Output('suffix-graph', 'figure'),Input('sort-dropdown', 'value'))

def update_suffix_graph(sortby):
    grouped = get_data(sortby)
    fig = px.scatter(grouped, x="median", y="last word", error_x="maxdiff", error_x_minus="mindiff",height=4000, width=1000, log_x=True)
    fig.update_xaxes(title_text="Log Price (£)")
    fig.add_trace(px.bar(grouped, x="count", y="last word", orientation='h', opacity=0.2, color_discrete_sequence=["grey"]).data[0])
    fig.update_layout(xaxis_side="top")
    return fig

@callback(Output('letter-graph', 'figure'),Input('letter-dropdown', 'value'))

def update_letter_graph(letter):
    averaged = get_letter_data(letter)
    fig = px.scatter(averaged, x=letter, y="Median", error_y="Max",error_y_minus="Min",log_y=True,height=1000,
                     title=f"Price Median vs Count of '{letter}' in Prefix")
    
    
    return fig

# Run app
if __name__ == '__main__':
    app.run(debug=True)
