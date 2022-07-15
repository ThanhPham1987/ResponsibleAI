import logging
import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, html, State
from server import app, redisUtil
from dash import dcc, ALL
from display_types import get_display
import metric_view_functions as mvf
logger = logging.getLogger(__name__)

requirements = []
prefix = "indiv_"


def populate_display_obj(group, metric):
    d = {"x": [], "y": [], "tag": [], "metric": [], "text": []}
    dataset = redisUtil.get_current_dataset()
    metric_values = redisUtil.get_metric_values()
    metric_type = redisUtil.get_metric_info()
    type = metric_type[group][metric]["type"]
    display_obj = get_display(metric, type, redisUtil)
    for i, data in enumerate(metric_values):
        data = data[dataset]
        display_obj.append(data[group][metric], data["metadata"]["tag"])
    return display_obj, display_obj.requires_tag_chooser


def get_grouped_radio_buttons():
    groups = mvf.get_nonempty_groups(requirements)
    metric_info = redisUtil.get_metric_info()

    return html.Div([
            html.Details([
                html.Summary([html.P([metric_info[group]['meta']['display_name']],
                                     style={"display": "inline-block", "margin-bottom": "0px"})]),
                dcc.RadioItems(
                    id={"type": prefix+"child-checkbox", "group": group},
                    options=[
                        {"label": metric_info[group][i]['display_name'], "value": i} for i in mvf.get_valid_metrics(group, requirements)
                    ],
                    value=[],
                    labelStyle={"display": "block"},
                    inputStyle={"margin-right": "5px"},
                    style={"padding-left": "40px"}
                )]) for group in groups], style={"margin-left": "35%"})


def get_search_and_selection_interface():
    groups = []
    for g in redisUtil.get_metric_info():
        groups.append(g)

    return html.Div(
        dbc.Form([
            dcc.Tabs([
                dcc.Tab(label='Metric Selector', children=[
                    dbc.Row([
                        dbc.Col([get_grouped_radio_buttons()], style={"position": "relative"}),
                        dbc.Col([mvf.get_reset_button(prefix)], style={"position": "relative"}),
                    ], style={"width": "100%", "margin-top": "20px"}),
                ], selected_style=mvf.get_selection_tab_selected_style(), style=mvf.get_selection_tab_style()),
                dcc.Tab(label='Metric Search', children=[
                    dbc.Row([
                        dbc.Col([
                            dcc.Dropdown(mvf.get_search_options(requirements), id=prefix+'metric_search',
                                         value=None, placeholder="Search Metrics"),
                        ], style={"position": "relative"}),
                        dbc.Col([mvf.get_reset_button(prefix)], style={"position": "relative"})
                    ], style={"width": "100%", "margin-top": "20px"}),
                ], selected_style=mvf.get_selection_tab_selected_style(), style=mvf.get_selection_tab_style()),
            ]),
            dbc.Row([dbc.Col([
                html.Br(),
                dbc.Label("Select Tag", html_for="select_metric_tag"),
                dcc.Dropdown([], id=prefix+'select_metric_tag', value=None, placeholder="Select a tag",
                             persistence=True, persistence_type='session')], id=prefix+"select_metric_tag_col",
                style={"display": 'none'})],
                id=prefix+"tag_selector_row")
        ], style=mvf.get_selection_form_style()),
        style=mvf.get_selection_div_style()
    )


def get_single_metric_display():
    return mvf.get_display(prefix, get_search_and_selection_interface())


def get_metric_info_display(group, metric, metric_info):
    return [html.Div([
        html.H3(metric_info[group][metric]['display_name'], style={"text-align": "center"}),
        html.Br(),
        html.P(metric_info[group][metric]['explanation'], style={'whiteSpace': 'pre-wrap', "text-align": "center"}),
        html.P("Citation: \n" + metric_info[group][metric]['citation'], style={'whiteSpace': 'pre-wrap'})],
        style={"background-color": "rgb(240,250,255)", "width": "70%", "border": "solid",
               "border-color": "silver", "border-radius": "5px", "padding": "10px 50px 10px 50px",
               "display": "block", "margin-left": "auto", "margin-right": "auto", "margin-top": "50px"}
    )]


@app.callback(
    Output(prefix+'legend_data', 'data'),
    Output({'type': prefix+'child-checkbox', 'group': ALL}, 'value'),
    Output(prefix+'metric_search', 'value'),
    Input({'type': prefix+'child-checkbox', 'group': ALL}, 'value'),
    Input(prefix+'reset_graph', "n_clicks"),
    Input(prefix+'metric_search', 'value'),
    State({'type': prefix+'child-checkbox', 'group': ALL}, 'options'),
    State({'type': prefix+'child-checkbox', 'group': ALL}, 'value'),
    State({'type': prefix+'child-checkbox', 'group': ALL}, 'id'),
    State(prefix+'legend_data', 'data'),
    prevent_initial_call=True
)
def update_metric_choice(c_selected, reset_button, metric_search, c_options, c_val, c_ids, options):
    ctx = dash.callback_context.triggered[0]["prop_id"]
    print("CONTEXT: ", ctx)
    ids = [c_ids[i]['group'] for i in range(len(c_ids))]
    if ctx == prefix+'reset_graph.n_clicks':
        to_c_val = [[] for _ in range(len(c_val))]
        return "", to_c_val, None
    if ctx == prefix + 'metric_search.value':
        if metric_search is None:
            return options, c_val, metric_search
        else:
            vals = metric_search.split(" | ")
            metric_name = vals[1] + ',' + vals[0]
            metric = vals[0]
            group = vals[1]
            parent_index = ids.index(group)
            print("metric_name: ", metric_name)
            if metric_name != options:
                options = metric_name
                c_val = [[] for _ in range(len(c_val))]
                c_val[parent_index] = metric
            return options, c_val, metric_search
    group = mvf.get_group_from_ctx(ctx)
    parent_index = ids.index(group)
    if "\"type\":\"" + prefix +"child-checkbox" in ctx:
        metric = c_val[parent_index]
        options = group + "," + c_val[parent_index]
        c_val = [[] for _ in range(len(c_val))]
        c_val[parent_index] = metric
        print("options: ", options)
        return options, c_val, None
    return options, c_val, None


@app.callback(
    Output(prefix+'graph_cnt', 'children'),
    Output(prefix+'select_metric_tag_col', 'style'),
    Output(prefix+'select_metric_tag', 'options'),
    Output(prefix+'select_metric_tag', 'value'),
    Output(prefix+'metric_info', 'children'),
    Input(prefix+'interval-component', 'n_intervals'),
    Input(prefix+'legend_data', 'data'),
    Input(prefix+'select_metric_tag', 'value'),
    State(prefix+'graph_cnt', 'children'),
    State(prefix+'select_metric_tag_col', 'style'),
    State(prefix+'select_metric_tag', 'options'),
    State(prefix+'select_metric_tag', 'value'),
    State(prefix+'metric_info', 'children')
)
def update_display(n, options, tag_selection, old_graph, old_style, old_children, old_tag_selection, old_info):
    ctx = dash.callback_context
    is_new_data, is_time_update, is_new_tag = mvf.get_graph_update_purpose(ctx, prefix)
    style = {"display": 'none'}
    metric_info = redisUtil.get_metric_info()

    if is_time_update:
        if redisUtil.has_update("metric_graph", reset=True):
            logger.info("new data")
            redisUtil._subscribers["metric_graph"] = False
            is_new_data = True

    if is_new_data:
        print("New data")
        if options == "" or options is None:
            return [], style, old_children, old_tag_selection, []
        k, v = options.split(',')
        print(k, v)
        print('---------------------------')
        display_obj, needs_chooser = populate_display_obj(k, v)
        children = []
        selection = None
        if needs_chooser:
            style = {"display": 'block'}
            children = display_obj.get_tags()
            selection = children[-1]
        return display_obj.to_display(), style, children, selection, get_metric_info_display(k, v, metric_info)

    elif is_new_tag:
        print("New tag selected")
        k, v = options.split(',')
        display_obj, _ = populate_display_obj(k, v)
        tags = display_obj.get_tags()
        return display_obj.display_tag_num(tags.index(tag_selection)), old_style, old_children, tag_selection, old_info

    return old_graph, old_style, old_children, old_tag_selection, old_info