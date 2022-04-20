from dash import html
import dash_bootstrap_components as dbc
import dash
from dash import Input, Output, State
def Iconify(txt, icon, margin="10px", style=None):

    # if style is None:
    style={ "margin-right":15 }

    return html.Div([
                    html.I(className=icon, style=style,), txt])


def dic2tbl(d,list_vertical = True):
    
     
    return dbc.Table(
        # className="model-info-table",
        children = [
        html.Thead(
            html.Tr([  html.Th(x) for x in d.keys()  ])
        ),
        
        html.Tbody(
            html.Tr([  html.Td( process_cell(x, list_vertical) ) for x in d.values()  ])
          )
        ],
        bordered=True,
        hover=True,
        responsive=True,
        striped=True,
        style={ "while-space":"pre",
                "padding-top": "12px",
                "padding-bottom": "12px"}
        )

from server import app
unique_id = [1]
full = {}

# dmy = html.Div(id = "dummy_x")

def ToStr(v, max_len = 100):
    s = str(v)
    if len(s)>max_len:
        unique_id[0]+=1
        s=s[:max_len] 
        full[s] = str(v) 
        btn = dbc.Button("...", id = { "type":str(v), "index":unique_id[0]},  
        outline=True, color="secondary", className="me-1",size="sm",
              style = {"margin-left":"5px", "width":"28px", "height":"20px", "text-align":"center buttom",  "line-height": "5px"})
        return html.Div( [s,btn, html.Div(id='dummy_x')])
    return s
@app.callback(
    Output( "dummy_x", "children"),
    Input({ "type":dash.ALL, "index": dash.ALL}, "n_clicks")
   
)
def show_full(x):
    print('---+++ : ', x)
    
    i=0
    while i<len(x) and x[i] is None:
        i+=1
    if i>=len(x): return []
    # print( i, x[i],  dash.callback_context.inputs_list[0][i])
    return dbc.Offcanvas(
            html.P(
                 dash.callback_context.inputs_list[0][i]["id"]["type"]
            ),
            id="offcanvas",
            title="Full Content",
            is_open=True,
        ),
    # if i<len(dash.callback_context.inputs):
    #     print(i, dash.callback_context.inputs[i] )
    # else:
    #     print("????", i, len(dash.callback_context.inputs) )
    # print( len(dash.callback_context.inputs_list))
    return []
def process_cell(v, list_vertical = True):
     
    if type(v) in (tuple, list):
        # return pp.pformat(v)
        if list_vertical:
            return [ dbc.Row(dbc.Col(html.Div(ToStr(x)))) for x in v] 
        else:
            return ToStr(v)   
    
    if isinstance(v,dict):
        return dic2tbl(v,list_vertical)
        # return pp.pformat(v)
        return json.dumps(v, indent=4)
    return ToStr(v)