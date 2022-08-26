import logging
from dash import dcc
import dash
from server import app, redisUtil
from dash import Input, Output, html, State
from dash.exceptions import PreventUpdate

logger = logging.getLogger(__name__)
INTERPRETATION_ANALYSIS = ["DataVisualization"]
prefix = "data_"


def get_available_options(options):
    result = [option for option in options if option in INTERPRETATION_ANALYSIS]
    return result


def get_data_summary_page():
    redisUtil.request_available_analysis()
    options = redisUtil.get_available_analysis()
    options = get_available_options(options)
    choice = options[0] if (options is not None and len(options) > 0) else None
    result = html.Div([
        html.H4("Run analysis"),
        dcc.Interval(
            id=prefix + 'interval-component',
            interval=1 * 3000,  # in milliseconds
            n_intervals=0),
        dcc.Dropdown(
            id=prefix + "analysis_selector",
            options=options,
            value=choice,
            persistence=True),
        html.Button("Run Analysis", id=prefix + "run_analysis_button", style={"margin-top": "20px"}),
        html.Div([], id=prefix + "analysis_display", style={"margin-top": "20px"})
    ], style={})
    return result


@app.callback(
    Output(prefix + 'analysis_selector', 'options'),
    Output(prefix + 'analysis_display', 'children'),
    Output(prefix + 'analysis_selector', 'value'),
    Input(prefix + 'interval-component', 'n_intervals'),
    Input(prefix + 'run_analysis_button', 'n_clicks'),
    Input(prefix + 'analysis_selector', 'value'),
    State(prefix + 'analysis_selector', 'options'),
    State(prefix + 'analysis_display', 'children'),
)
def get_analysis_updates(timer, btn, analysis_choice, analysis_choices, analysis_display):
    ctx = dash.callback_context
    is_time_update = any(prefix + 'interval-component.n_intervals' in i['prop_id'] for i in ctx.triggered)
    is_button = any(prefix + 'run_analysis_button.n_clicks' in i['prop_id'] for i in ctx.triggered)
    is_value = any(prefix + 'analysis_selector.value' == i['prop_id'] for i in ctx.triggered)
    should_update = False
    force_new_display = False

    if analysis_choices != get_available_options(redisUtil.get_available_analysis()):
        analysis_choices = get_available_options(redisUtil.get_available_analysis())
        should_update = True
    if analysis_choice is None and (analysis_choices is not None and len(analysis_choices) > 0):
        analysis_choice = analysis_choices[0]
        force_new_display = True

    if is_time_update and analysis_choice is not None:
        if redisUtil.has_analysis_update(analysis_choice, reset=True):
            print("Analysis update: ")
            analysis_display = [redisUtil.get_analysis(analysis_choice),
                                html.P(analysis_choice, style={"display": "none"})]
            return analysis_choices, analysis_display
    if is_button:
        if analysis_choice is None or analysis_choice == "":
            return analysis_choices, [html.P("Please select an analysis")]
        else:
            redisUtil.request_start_analysis(analysis_choice)
            return redisUtil.get_available_analysis(), [html.P("Requesting Analysis..")]

    # Extra condition was added because dash would not always update when changing to/from a large analysis
    if force_new_display or is_value or (analysis_choice and analysis_display==[]) \
            or ((len(analysis_display) > 1 and analysis_choice != analysis_display[1].get("props", {}).get("children", {}))):
        print("Value triggered")
        analysis_display = [redisUtil.get_analysis(analysis_choice),
                            html.P(analysis_choice, style={"display": "none"})]
        should_update = True

    if not should_update:
        raise PreventUpdate

    return analysis_choices, analysis_display, analysis_choice
