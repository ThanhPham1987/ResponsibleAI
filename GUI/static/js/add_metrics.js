'use strict';

var metric_file = "output/metric_list.json";
var explanation_file = "/Flask-Admin-Dashboard/static/output/metric_info.json";


var whitelist = []; // contains all metrics whose category is checked
var blacklist = []; // contains which metrics were X'd out
var metrics; // global variable contains all metrics on screen
var graphs = {}; // list of all graphs
var matrices = {};
var bool_charts = {}
var dict_charts = {}
var metric_info;
var model_info;
var tags = {}
var data_types = []
var use_date= true;
var page_ready = false;


$(document).ready(function() {
        setInterval("check_data()", 1000); // call every 10 seconds
});

function check_data() {
    if(page_ready){
       fetch('/updateMetrics').then(function (response) {
            return response.json();
        }).then(function(result){
            if (result){
                redoMetrics();
            }
        });
    }
}



// loads metrics. Contains lists of metrics, and metric tags.
function loadMetrics(category) {
    page_ready = false
    fetch('/getMetricList').then(function (response) {
        return response.json();
    }).then(function(text){
        metrics = text
        loadExplanations(text, category);
    });
}


function loadExplanations(metrics, category) {
    fetch('/getMetricInfo').then(function (response) {
        return response.json();
    }).then(function(text){
        metric_info = text;
        load_model_info(metrics, text, category);
    });
}


// Loads explanations.
function load_model_info(metrics, explanations, category) {
    fetch('/getModelInfo').then(function (response) {
        return response.json();
    }).then(function(text){
        model_info = text;
        load_data(metrics, explanations, category);
    });
}

// Queries Data
function load_data(metrics, data, category) {
    var date1 = document.getElementById("startDate").value;
    var date2 = document.getElementById("endDate").value;
    return fetch('/getData/' + date1 + '/' + date2)
        .then(function (response) {
            return response.json();
        }).then(function (text) {
            callAllFunctions(metrics, data, text, category);
        });
}

// Use collected data to create metrics, boxes and white list metrics by category
function callAllFunctions(metrics, data, df_json, category) {
    createMetrics(metrics, data, df_json, category);
    createBoxes(metrics, category);
    createWhiteList(metrics, category);
    page_ready = true
}


// Create graphs
function createMetrics(metrics, explanations, data, category) {
    var list = metrics[category.toLowerCase()];
    if (list==null)
        return
    for (var i = 0; i < list.length; i++) {
        if(metric_info[list[i]]["type"] == "numeric"){
            addChart(list[i], explanations, data, category, "");
        }
        else if(metric_info[list[i]]["type"] == "vector"){
            if(list[i].indexOf("_avg") >= 0)
                addChart(list[i], explanations, data, category, "-single")
            else if (! (list[i]+"_avg" in metric_info)){
                res = stringToMatrix(data, list[i])
                if (!Array.isArray(res[0]))
                    res = [res]
                addTable(list[i], explanations, res, category)
            }
        }
        else if(metric_info[list[i]]["type"] == "matrix"){
            var res = stringToMatrix(data, list[i])
            addTable(list[i], explanations, res, category)
        }
        else if(metric_info[list[i]]["type"] == "boolean"){
            addBoolChart(list[i], explanations, data, category, "");
        }
        else if(metric_info[list[i]]["type"] == "vector-dict"){
            addVectorDict(list[i], explanations, data, category, "");
        }
    }
}


function addVectorDict(metric_name, explanations, data, category, name_extension){
    var curData = data[data.length -1][metric_name]
    var features = model_info['features']
    var result = {}
    for(var i = 0; i<curData.length; i++){
        if(curData[i] != null){
            var table = dict_to_table(curData[i]);
            addTable(metric_name, explanations, table, category, features[i], String(i));
        }
    }
}


function dict_to_table(dict){
    var result = [[], []]
    for(var key in dict){
        result[0].push(key)
        result[1].push(dict[key])
    }
    return result
}


function stringToMatrix(data, name){
    var result = []
    if (data.length >= 1)
        result = data[data.length-1][name];
    return result
}

function addTags(metric_name){
    for (var i = 0; i < metric_info[metric_name]["tags"].length; i++){
        if (tags[metric_info[metric_name]["tags"][i]] == null)
            tags[metric_info[metric_name]["tags"][i]] = [];
        tags[metric_info[metric_name]["tags"][i]].push(metric_name);
    }
    // console.log(metric_info[metric_name])
    if (data_types[metric_info[metric_name]["type"]] == null){
        data_types[metric_info[metric_name]["type"]] = []
    }
    data_types[metric_info[metric_name]["type"]].push(metric_name)
}


function addChart(metric_name, explanations, data, category, name_extension){
    addTags(metric_name)
    // console.log(metric_name)
    var body = document.getElementById('metric_row');
    var newDiv = document.createElement('div');
    newDiv.setAttribute("class", category.toLowerCase() + 'Metric Metric col-sm-6 chart-container main-panel');
    newDiv.setAttribute("id", metric_name + "_chart");
    var writing = document.createElement('p');
    writing.innerHTML = metric_info[metric_name]["display_name"];
    writing.setAttribute("class", "chartHeader");
    var writing2 = document.createElement('p');
    if (typeof(data[data.length-1][metric_name + name_extension]) == 'number')
        writing2.innerHTML = data[data.length -1][ metric_name + name_extension].toFixed(3);
    else
        writing2.innerHTML = "Null"
    writing2.setAttribute("class", "chartValue");
    writing2.setAttribute("id", metric_name + "LastValue");
    var img = document.createElement('img');
    img.setAttribute("title", explanations[metric_name]["explanation"]);
    img.setAttribute("src", "/static/img/questionMark.png");
    img.setAttribute("alt", "Learn more about " + metric_name);
    img.setAttribute("class", "learnMore");
    var link = document.createElement('a')
    link.setAttribute('href', '/learnMore/'+metric_name)
    link.setAttribute('class', 'learnMoreLink')
    var logo = document.createElement('i')
    logo.setAttribute('class', 'fa fa-external-link fa-lg')
    link.appendChild(logo)
    newDiv.appendChild(link)

    newDiv.appendChild(img);
    newDiv.appendChild(writing);
    newDiv.appendChild(writing2);

    var removeBtn = document.createElement("button");
    removeBtn.innerHTML  = "X";
    removeBtn.setAttribute("class", "removeChart");
    removeBtn.setAttribute("style", "display:none");
    removeBtn.setAttribute("onclick", "blackList('" + metric_name + "')");
    newDiv.appendChild(removeBtn);

    var chart = document.createElement('div');
    chart.setAttribute("class", "overflow_table")
    chart.id = metric_name;
    chart.setAttribute("class", "morris-chart chartScalerSmall");
    newDiv.appendChild(chart);
    body.appendChild(newDiv);

    var result = createData(data, metric_name + name_extension)
    var chart_data = result[0]
    var chart_descriptions = result[1]
    var myValues  = {
        element: metric_name,
        data: chart_data,
        xkey: 'year',
        descriptions: chart_descriptions,
        ykey: metric_name,
        hideHover: true,
        smooth: false,
        lineColors: ['#000000'],
        pointFillColors: ['#000000'],
        ykeys: ['value'],
        labels: ['Value'],
        hoverCallback: function (index, options, content, row) {
                var description = options.descriptions[index];
                return content + "\nDescription: " + description;}

    }
    if(metric_info[metric_name]["has_range"]){
        if(metric_info[metric_name]["range"][0] != null){
            myValues['ymin'] = Number(metric_info[metric_name]["range"][0])
        }
        if(metric_info[metric_name]["range"][1] != null){
            myValues['ymax'] = Number(metric_info[metric_name]["range"][1])
        }
        myValues['yLabelFormat'] = function(y){return y.toFixed(2);}
    }
    myValues['parseTime'] = true

    var morrisLine = new Morris.Line(myValues)
    graphs[metric_name] = morrisLine;
}


function addBoolChart(metric_name, explanations, data, category, name_extension){
    addTags(metric_name)
    // console.log(metric_name)
    var body = document.getElementById('metric_row');
    var newDiv = document.createElement('div');
    newDiv.setAttribute("class", category.toLowerCase() + 'Metric Metric col-sm-6 chart-container main-panel');
    newDiv.setAttribute("id", metric_name + "_chart");
    var writing = document.createElement('p');
    writing.innerHTML = metric_info[metric_name]["display_name"];
    writing.setAttribute("class", "chartHeader");
    var writing2 = document.createElement('p');
    if(data[data.length-1][metric_name + name_extension] == null)
        writing2.innerHTML = "Null"
    else
        writing2.innerHTML = data[data.length -1][ metric_name + name_extension];
    writing2.setAttribute("class", "chartValue");
    writing2.setAttribute("id", metric_name + "LastValue");

    var img = document.createElement('img');
    img.setAttribute("title", explanations[metric_name]["explanation"]);
    img.setAttribute("src", "/static/img/questionMark.png");
    img.setAttribute("alt", "Learn more about " + metric_name);
    img.setAttribute("class", "learnMore");
    var link = document.createElement('a')
    link.setAttribute('href', '/learnMore/'+metric_name)
    link.setAttribute('class', 'learnMoreLink')
    var logo = document.createElement('i')
    logo.setAttribute('class', 'fa fa-external-link fa-lg')
    link.appendChild(logo)
    newDiv.appendChild(link)

    newDiv.appendChild(img);
    newDiv.appendChild(writing);
    newDiv.appendChild(writing2);

    var removeBtn = document.createElement("button");
    removeBtn.innerHTML  = "X";
    removeBtn.setAttribute("class", "removeChart");
    removeBtn.setAttribute("style", "display:none");
    removeBtn.setAttribute("onclick", "blackList('" + metric_name + "')");
    newDiv.appendChild(removeBtn);

    var chart = document.createElement('div');
    chart.setAttribute("class", "overflow_table")
    chart.id = metric_name;
    chart.setAttribute("class", "morris-chart chartScalerSmall");
    newDiv.appendChild(chart);
    body.appendChild(newDiv);

    var result = createBoolData(data, metric_name + name_extension)
    var chart_data = result[0]
    var chart_descriptions = result[1]
    var myValues  = {
        element: metric_name,
        data: chart_data,
        xkey: 'year',
        descriptions: chart_descriptions,
        ykey: metric_name,
        hideHover: true,
        smooth: false,
        lineColors: ['#000000'],
        pointFillColors: ['#000000'],
        ykeys: ['value'],
        labels: ['Value'],
        hoverCallback: function (index, options, content, row) {
                var description = options.descriptions[index];
                return content + "\nDescription: " + description;}
    }
    myValues['parseTime'] = true
    var morrisLine = new Morris.Line(myValues)
    bool_charts[metric_name] = morrisLine;
}


function addTable(metric_name, explanations, data_array, category, optionalName="", optionalNumber=""){
    addTags(metric_name)
    var body = document.getElementById('metric_row');
    var newDiv = document.createElement('div');
    newDiv.setAttribute("class", category.toLowerCase() + 'Metric Metric col-sm-6 chart-container main-panel');
        if(optionalNumber!="")
        optionalNumber = "|"+optionalNumber;
    newDiv.setAttribute("id", metric_name + "_chart"+optionalNumber);
    var writing = document.createElement('p');
    writing.innerHTML = metric_info[metric_name]["display_name"]
    if(optionalName != "")
        writing.innerHTML += " - " + optionalName
    writing.setAttribute("class", "chartHeader");
    var img = document.createElement('img');
    img.setAttribute("title", explanations[metric_name]["explanation"]);
    img.setAttribute("src", "/static/img/questionMark.png");
    img.setAttribute("alt", "Learn more about " + metric_name);
    img.setAttribute("class", "learnMore");
    newDiv.appendChild(img);
    newDiv.appendChild(writing);

    var removeBtn = document.createElement("button");
    removeBtn.innerHTML  = "X";
    removeBtn.setAttribute("class", "removeChart");
    removeBtn.setAttribute("style", "display:none");
    removeBtn.setAttribute("onclick", "blackList('" + metric_name + "')");
    newDiv.appendChild(removeBtn);

    var link = document.createElement('a')
    link.setAttribute('href', '/learnMore/'+metric_name)
    link.setAttribute('class', 'learnMoreLink')
    var logo = document.createElement('i')
    logo.setAttribute('class', 'fa fa-external-link fa-lg')
    link.appendChild(logo)
    newDiv.appendChild(link)

    var chart = document.createElement('div');
    chart.id = metric_name;
    newDiv.appendChild(chart);
    body.appendChild(newDiv);

    var table = generateTableFromArray(data_array)
    chart.appendChild(table);
    matrices[metric_name] = chart;
}


function generateTableFromArray(data_array, is_float=false){
    var table = document.createElement('table');
    table.setAttribute('class', 'displayMatrix')
    if(data_array == null)
        return table
    var tableBody = document.createElement('tbody');
    tableBody.setAttribute('class', 'displayMatrix');
    for(var r = 0; r < data_array.length; r++){
        var row = document.createElement('tr');
        row.setAttribute('class', 'displayMatrix')
        for(var c = 0; c < data_array[r].length; c++){
            var col = document.createElement('td');
            col.setAttribute('class', 'displayMatrix')
            if(typeof data_array[r][c] == 'string' || data_array[r][c] instanceof String || Number.isInteger(data_array[r][c]))
                col.appendChild(document.createTextNode(data_array[r][c]));
            else
                col.appendChild(document.createTextNode(data_array[r][c].toFixed(2)));
            row.appendChild(col);
        }
        tableBody.appendChild(row);
    }
    table.appendChild(tableBody);
    return table
}


// Used to create the data for the morris chart
function createBoolData(data, key) {
    var ret = [];
    var descriptions = []
    for (var i = 0; i < data.length; i++) {
        if(data[i][key] != null && !isNaN(data[i][key]) && isFinite(data[i][key])){
            var value = 0
                if(data[i][key])
                    value = 1
            if(use_date){
                ret.push({
                    year: data[i]["metadata > date"],
                    value: value
                });
            }
            else{
                ret.push({
                    year: String(i),
                    value: value
                });
            }
            descriptions.push(data[i]["metadata > description"])
        }
    }
    return [ret, descriptions];
}



// Used to create the data for the morris chart
function createData(data, key) {
    var ret = [];
    var descriptions = []
    for (var i = 0; i < data.length; i++) {
        if(data[i][key] != null && !isNaN(data[i][key]) && isFinite(data[i][key])){
            if(use_date){
                ret.push({
                    year: data[i]["metadata > date"],
                    value: data[i][key]
                });
            }
            else{
                ret.push({
                    year: data[i]["metadata > description"],
                    value: data[i][key]
                });
            }
            /*
            else{
                ret.push({
                    year: String(i),
                    value: data[i][key]
                });
            }
            */
            descriptions.push(data[i]["metadata > description"])
        }
    }
    return [ret, descriptions];
}

// Create the category searching of metrics
function createBoxes(metrics, category) {
    var body = document.getElementById('tag_selection');
    var list = tags
    var topBox = document.createElement("input");
    topBox.setAttribute("type", "checkbox");
    topBox.setAttribute("id", category + "_mainBox");
    topBox.setAttribute("value", true);
    topBox.setAttribute("name", category + "_mainBox");
    topBox.setAttribute("class", "selectorBox");
    topBox.setAttribute("class", "parentBox");
    topBox.setAttribute("checked", true);
    topBox.setAttribute("onclick", "checkChlidren(this, '" + category.toString().toLowerCase() + "')");
    var topLabel = document.createElement("label");
    topLabel.setAttribute("for", category + "_mainBox");
    topLabel.innerHTML = category;
    var topBr = document.createElement("br");
    body.appendChild(topBox);
    body.appendChild(topLabel);
    body.appendChild(topBr);
    for (var i in tags) {
        if (i == category.toLowerCase())
            continue;
        var newBox = document.createElement("input");
        newBox.setAttribute("type", "checkbox");
        newBox.setAttribute("id", i);
        newBox.setAttribute("value", true);
        newBox.setAttribute("name", i);
        newBox.setAttribute("class", "selectorBox");
        newBox.setAttribute("class", category.toString().toLowerCase() + "Box" + " innerBox");
        newBox.setAttribute("checked", true);
        newBox.setAttribute("onclick", "checkParent(this, '" + category + "')");
        var label = document.createElement("label");
        label.setAttribute("for", i + category.toString().toLowerCase());
        label.innerHTML = i;
        var br = document.createElement("br")
        body.appendChild(newBox);
        body.appendChild(label);
        body.appendChild(br);
    }

    body = document.getElementById("datatype_selection")
    for (var i in data_types) {
        var newBox = document.createElement("input");
        newBox.setAttribute("type", "checkbox");
        newBox.setAttribute("id", i);
        newBox.setAttribute("value", true);
        newBox.setAttribute("name", i);
        newBox.setAttribute("class", "selectorBox");
        newBox.setAttribute("class", i + "_Box");
        newBox.setAttribute("checked", true);
        newBox.setAttribute("onclick", "updateDatatypes('" + category +"')");
        var label = document.createElement("label");
        label.setAttribute("for", i);
        label.innerHTML = i;
        var br = document.createElement("br")
        body.appendChild(newBox);
        body.appendChild(label);
        body.appendChild(br);
    }
    var button = document.createElement("button");
    button.setAttribute("class", "selectorButton");
    button.innerHTML = "Done";
    button.setAttribute("onclick", "doneEdit('" + category + "');")
    document.getElementById("selector").appendChild(button);
}

// white list metrics depending on what is checked in the categories
function createWhiteList(metrics, category) {
    for (var i in tags)
        for (var j = 0; j<tags[i].length; j++){
            whitelist.push(tags[i][j]);
        }
}

// Used to display the edit view menu
function displayMenu(classtype) {
    document.getElementById("selector").style.display = "";
    var list = document.getElementsByClassName("removeChart");
    for (var i = 0; i < list.length; i++)
        list[i].style.display = "";
}

// Removes a metric when its X is pressed
function blackList(name) {
    blacklist.push(name);
    document.getElementById(name + "_chart").style.display = "none";
}

// Hides the selector menu
function doneEdit(classtype) {
    document.getElementById("selector").style.display = "none";
    var list = document.getElementsByClassName("removeChart");
    for (var i = 0; i < list.length; i++)
        list[i].style.display = "none";
}

// Generates the white list (what metrics should be shown, based on category) by looking at the checked boxes
function generateWhiteList() {
    whitelist = [];
    data_types = []
    var datatypeBox = document.getElementById("datatype_selection")
    var boxes = datatypeBox.getElementsByTagName("input")
    for (var i = 0; i<boxes.length; i++){
        if (boxes[i].checked){
            data_types.push(boxes[i].id.toString())
        }
    }

    var boxes = document.getElementById("tag_selection").getElementsByTagName("input");
    for (var i = 0; i < boxes.length; i++) {
        if (boxes[i].checked) {
            var id = boxes[i].id.toString();
            if(id.indexOf("_mainBox") == -1){
                var list = tags[id];
                for (var j = 0; j < list.length; j++) {
                    if(data_types.includes(metric_info[list[j]]["type"])){
                        whitelist.push(list[j]);
                    }
                }
            }
        }
    }
    displayWhiteList()
}





// Display the white listed metrics
function displayWhiteList() {
    var row = document.getElementById("metric_row");
    var divs = row.getElementsByClassName("Metric");
    for (var i = 0; i < divs.length; i++) {
        var div = divs[i].getElementsByTagName("div")[0];
        if (whitelist.includes(div.id) && !blacklist.includes(div.id)) {
            divs[i].style.display = "";
        }
        else {
            divs[i].style.display = "none";
        }
    }
}

// Reload the metrics once the times to query for are changed
function redoMetrics() {
    var date1 = document.getElementById("startDate").value;
    var date2 = document.getElementById("endDate").value;
    page_ready = false;
    return fetch('/getData/' + date1 + '/' + date2)
        .then(function (response) {
            return response.json();
        }).then(function (text) {
            redoMetrics2(text)
            page_ready = true
        });
}


// Fill graphs with new data
function redoMetrics2(data) {
    for (var type in graphs) {
        var ext = "";
        if(metric_info[type]["type"] == "vector")
            ext = "-single"
        var result = createData(data, type + ext);
        var new_data = result[0]
        var newExplanations = result[1]
        graphs[type]['options'].parseTime = use_date
        graphs[type].setData(new_data);
        graphs[type].options.descriptions = newExplanations

        var writing = document.getElementById(type + "LastValue");
        if(new_data.length >= 1)
            writing.innerHTML = new_data[new_data.length - 1]["value"].toFixed(3);
        else
            writing.innerHTML = "Null"
    }
    for (var type in bool_charts){
        var writing2 = document.getElementById(type + "LastValue");
        if(data.length == 0 || data[data.length-1][type] == null){
            writing2.innerHTML = "Null"
        }
        else{
            writing2.innerHTML = data[data.length -1][type];
        }
        var result = createBoolData(data, type + ext);
        var new_data = result[0]
        var newExplanations = result[1]
        bool_charts[type].options.parseTime = use_date
        bool_charts[type].setData(new_data);
        bool_charts[type].options.descriptions = newExplanations
    }
    for (var type in matrices){
        if(metric_info[type]['type'] == 'matrix' || metric_info[type]['type'] == 'vector'){
            var chart = document.getElementById(type + "_chart")
            var hiddenText = chart.id.substring(0, chart.id.indexOf("_chart"))
            var internalDiv = chart.getElementsByTagName("div")[0]
            var table = internalDiv.getElementsByTagName("table")[0]
            table.remove()
            var res = stringToMatrix(data, hiddenText)
            if (!Array.isArray(res[0]))
                        res = [res]
            var table = generateTableFromArray(res)
            internalDiv.appendChild(table);
        }
        if(metric_info[type]['type'] == 'vector-dict'){
            var curData = []
            if (data.length >= 1){
                curData = data[data.length -1][type]
            }
            var features = model_info['features']
            var result = {}
            for(var i = 0; i<features.length; i++){
                var chart = document.getElementById(type + "_chart" + "|" + String(i))
                if(chart != null){
                    var hiddenText = chart.id.substring(0, chart.id.indexOf("_chart"))
                    var internalDiv = chart.getElementsByTagName("div")[0]
                    var table = internalDiv.getElementsByTagName("table")[0]
                    table.remove()
                    var table_data = dict_to_table(curData[i]);
                    table_data = generateTableFromArray(table_data)
                    internalDiv.appendChild(table_data);
                }
                else if(curData.length != 0 && curData[type] != null){  // Add elements which may have previously been null
                    addVectorDict(type, metric_info, data, metric_info[type]["category"], "");
                }
            }
        }
    }
}


// Checks child status of boxes once parent boxes are checked in metric selector
function checkChlidren(check, type) {
    if ($(check).is(':checked')) {
        blacklist = [];
        var all = $("." + type + "Box").map(function () {
            this.checked = true;
        }).get();
    }
    else {
        var all = $("." + type + "Box").map(function () {
            this.checked = false;
        }).get();
    }
    generateWhiteList(type);
}

// Checks parent status in checkboxes, once all child checks are unchecked, or one is checked.
function checkParent(check, type) {
    var count = 0;
    if ($(check).is(':checked')) {
        blacklist = [];
        var all = $("#" + type + "_mainBox").map(function () {
            this.checked = true;
        }).get();
    }
    else {
        var swap = false;
        var items = document.getElementsByClassName(type.toString().toLowerCase() + "Box");
        for (var i = 0; i < items.length; i++) {
            swap = items[i].checked;
            if (swap)
                break
        }
        if (!swap)
            document.getElementById(type + "_mainBox").checked = false;
    }
    generateWhiteList(type);
}


// Checks parent status in checkboxes, once all child checks are unchecked, or one is checked.
function updateDatatypes(type) {
    generateWhiteList(type);
}


// Searches available metrics, changes display based on search results.
function search() {
    var input, filter, row, divs, i, text;
    input = document.getElementById("myInput");
    filter = input.value.toLowerCase();
    row = document.getElementById("metric_row");
    divs = row.getElementsByTagName("div");

    var mustInclude = [];
    for (var i in tags) {
        if (i.toLowerCase().indexOf(filter) > -1) {
            for(var j = 0; j<tags[i].length; j++) {
                mustInclude.push(tags[i][j]);
            }
        }
    }
    for (var i = 0; i < divs.length; i++) {
        var p = divs[i].getElementsByClassName("chartHeader")[0];
        var hiddenDiv = divs[i].getElementsByTagName("div")[0];
        if (p && hiddenDiv) {
            var text = p.innerText;
            var hiddenText = hiddenDiv.id;
            if ((text.toLowerCase().indexOf(filter) > -1 || mustInclude.includes(hiddenText)) && whitelist.includes(hiddenText) && !blacklist.includes(hiddenText)) {
                divs[i].style.display = "";
            } else {
                divs[i].style.display = "none";
            }
        }
    }
}

function date_slider(){
    var slider = document.getElementById('slider_input')
    use_date = !slider.checked;
    redoMetrics()
}

function view_slider(){
    var slider = document.getElementById('view_input')
    use_date = !slider.checked;
    var style = ""
    var svg_style = ""
    var header_style = ""
    var text_display = ""
    var chart_scaler = ""
    if(!slider.checked){
        style = 'width: 32%; margin-left: 1%; margin-top: 2%;   fill: black; height: 290px;'
        header_style = "text-align: center; font-size: 25px; margin-top: 10px; margin-bottom: 0px; color: black;"
        svg_style = "width:100%;"
        text_display = "display:block; margin-left:0px; text-align: center; font-size: 25px; margin-top: 5px; margin-bottom: 0px; color: black;"
        chart_scaler = "height:60%;"
    }
    var row = document.getElementById("metric_row");
    var boxes = row.getElementsByClassName("Metric");
    for(var i = 0; i<boxes.length; i++){
        boxes[i].setAttribute("style", style);
        var svgs = boxes[i].getElementsByTagName("svg")
        if(svgs.length > 0)
            svgs[0].setAttribute("width", "100%")

        var text = boxes[i].getElementsByClassName("chartValue")
        if(text.length > 0)
            text[0].setAttribute("style", text_display)

        var graph = boxes[i].getElementsByClassName("morris-chart")
        if(graph.length > 0)
            graph[0].setAttribute("style", chart_scaler)
    }
    var texts = row.getElementsByClassName("chartHeader");
    for(var i = 0; i<texts.length; i++){
        texts[i].setAttribute("style", header_style);
    }

    for(var chart in graphs){
        if(document.getElementById(chart+"LastValue").innerHTML != "Null")
                graphs[chart].redraw()
    }
    for(var chart in bool_charts){
        if(document.getElementById(chart+"LastValue").innerHTML != "Null"){
            bool_charts[chart].redraw()
        }
    }
}


