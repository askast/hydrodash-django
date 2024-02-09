def context(request):
    context_dict = {
        "navbardata": {
            "Test Data": [
                {"url": "/testdata", "icon": "fas fa-lock", "name": "Raw Test Data"},
                {
                    "url": "/testdata/reducedtestlist",
                    "icon": "fas fa-server",
                    "name": "Reduced Test Data",
                },
                {"url": "/testdata/directdatainput", "icon": "fas fa-lock", "name": "Direct Data Input"},
                {"url": "/testdata/keysightdaq", "icon": "fas fa-chart-area", "name": "Keysight DAQ Test"},
            ],
            "Data Acquisition": [
                {
                    "url": "/daq/",
                    "icon": "fas fa-tachograph-digital",
                    "name": "DAQ",
                },
                {
                    "url": "/daq/database",
                    "icon": "fas fa-database",
                    "name": "DAQ Database",
                },
            ],
            "Marketing": [
                {
                    "url": "/marketingdata/marketinglistview",
                    "icon": "fas fa-bullhorn",
                    "name": "Performance Curves",
                },
                {
                    "url": "/pump/pumplistview",
                    "icon": "fas fa-fighter-jet",
                    "name": "Pumps Listing",
                },
                {
                    "url": "/marketingdata/marketingnpshinput",
                    "icon": "fas fa-server",
                    "name": "NPSH Data",
                },
                {
                    "url": "/marketingdata/marketingmap",
                    "icon": "fas fa-chart-area",
                    "name": "Family of Curves",
                },
                {
                    "url": "/pump/marketingtestcreatorview",
                    "icon": "fas fa-magic",
                    "name": "Raw Data Creator",
                }
            ],
            "PEI": [
                {
                    "url": "/pei/ceiwizard",
                    "icon": "fas fa-hat-wizard",
                    "name": "CEI Wizard",
                },
                {
                    "url": "/pei/peicalculator",
                    "icon": "fas fa-calculator",
                    "name": "PEI Calculator",
                },
            ],
            "Design Data": [
                {
                    "icon": "fas fa-lock",
                    "name": "CFD Data",
                    "submenu": [
                        {"url": "/testdata", "name": "Raw CFD Results"},
                        {"url": "/testdata", "name": "CFD Curves"},
                        {"url": "/testdata", "name": "Edit CFD Results"},
                    ],
                },
                {
                    "url": "/testdata",
                    "icon": "far fa-file-text",
                    "name": "Curve Compare",
                    "disabled": "true",
                },
            ],
        }
    }
    return {"global_context": context_dict}
