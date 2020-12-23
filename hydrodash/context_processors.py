def context(request):
    context = {
        "navbardata": {
            "Test Data": [
                {"url": "/testdata", "icon": "fas fa-lock", "name": "Raw Test Data"},
                {
                    "url": "/testdata/reducedtestlist",
                    "icon": "fas fa-server",
                    "name": "Reduced Test Data",
                },
                {"url": "/testdata/directdatainput", "icon": "fas fa-lock", "name": "Direct Data Input"},
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
                    "url": "/pei/peiwizard",
                    "icon": "fas fa-hat-wizard",
                    "name": "PEI Wizard",
                },
                {
                    "url": "/pei/peicalculator",
                    "icon": "fas fa-calculator",
                    "name": "PEI Calculator",
                },
            ],
        }
    }
    return {"global_context": context}
