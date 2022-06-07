import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html
import logging
logger = logging.getLogger(__name__)
from server import redisUtil
import dash_daq as daq
# import dash_trich_components as dtc
import numpy as np

from utils import Iconify


def card_title( t, ico, color ):
    

    style = {    }
    style={"text-align":"center"}
    return dbc.Row([
                      dbc.Col(html.H4(t)), dbc.Col(html.I(   className=ico, style={"font-size": "3em", "color":color}) ) ])

                    
def get_card( t1, t2, t3, ic, n , id, c):
    # c = "lightcyan"
    # c= "lightgoldenrodyellow"
    return dbc.Card(
    [
         
        # html.I(className=ic, style={}),
        # dbc.CardImg(src="fa-solid fa-list-check", top=True),
        dbc.CardBody(
            [
                # html.H4(t1, className="card-title", style={"text-align":"center"}),
                card_title ( t1,  ic, c),
                dbc.Row( [
                    dbc.Col( daq.Gauge(
                                color={"gradient":True,"ranges":{"red":[0,40],"yellow":[40,80],"green":[80,100]}},
                                value=100*np.mean(n),
                                label='',
                                max=100,
                                min=0,
                                size=100
                            ) ),
                    # html.Hr(),
                    dbc.Col( html.P ( "%d of total %d certificates passed"%(
                    np.sum(n), len(n) ), style={"text-align":"left","padding":"50px 0"} ) )
                ])
            ]
        ),
        
       
    ],
    style={"width": "30rem",
    "background-color":"rgb(218,226,234)",
    "margin":"20px",
    "border-radius":"10px",
    "height":"180px"
    },
    )


def get_home_page():


    certs = redisUtil.get_certificate_info()
    explain = []
    robust = []
    fair = []
    perform = []

    score_explain = []
    score_robust = []
    score_fair = []
    score_perform = []
    cert_values = redisUtil.get_certificate_values()[-1]
    
    for c in certs:
         
        for t in certs[c]["tags"]:
            if "explain" in t.lower():
                explain.append(c)
                score_explain.append( 1 if cert_values[c]["value"] else 0)
            if "robust" in t.lower():
                robust.append(c)
                score_robust.append( 1 if cert_values[c]["value"] else 0)

            if "perform" in t.lower():
                perform.append(c)
                score_perform.append( 1 if cert_values[c]["value"] else 0)

            if "fair" in t.lower():
                fair.append(c)
                score_fair.append( 1 if cert_values[c]["value"] else 0)
    
   

    gauges  =[dbc.Row(
             [
                get_card("Explainability", "success rate", "details", "fa-solid fa-person-circle-question",  score_explain,"c1", "blue"),
                get_card("Robustness", "success rate", "details", "fa-solid fa-file-shield", score_robust,"c2", "orange"),

             ] )
             ,
        dbc.Row(
             [
                get_card("Performance", "success rate", "details", "fa-solid fa-trophy", score_perform,"c3","red"),
                get_card("Fairness", "success rate", "details", "fa-solid fa-scale-balanced",  score_fair,"c4","darkgreen"),

             ] )]
    # return html.P("This is the content of the home page!")
    from certificate_page import generate_cert_table

    return html.Div([
        
        dbc.Row([
            dbc.Row(gauges), 
            dbc.Row(
                html.Div( generate_cert_table(-1,False) , style = {"margin":"20px","border-color":"silver", "border-radius":"1px", 
                "border-style":"solid","margin-top":"20px","width":"63rem"} ) )
        ] )
        

    ])
