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
            ],
            "PEI": [
                {
                    "url": "/testdata",
                    "icon": "fas fa-sidebar",
                    "name": "PEI Calculator",
                    "disabled": "true",
                },
                {
                    "url": "/testdata",
                    "icon": "fas fa-sidebar",
                    "name": "ER Calculator",
                    "disabled": "true",
                },
            ],
        }
    }
    return {"global_context": context}
