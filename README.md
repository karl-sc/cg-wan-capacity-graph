# cg-wan-capacity-graph
This program displays an ASCII graph of the PCM or WAN Capacity metrics for a given time period going back an arbitrary amount of days.

USAGE:
  -h, --help            show this help message and exit
  --token "MYTOKEN", -t "MYTOKEN"
                        specify an authtoken to use for CloudGenix
                        authentication
  --authtokenfile "MYTOKENFILE.TXT", -f "MYTOKENFILE.TXT"
                        a file containing the authtoken
  --site-name SiteName, -s SiteName
                        The site to run the site health check for
  --period period, -p period
                        The period of time (in hours) for the resulting graph.
                        Default 24
  --days days, -d days  The period of time (in hours) for the resulting graph.
                        Default 2

EXAMPLES:

    Show 24-hours worth PCM data for my New York Branch from 3 days ago using my auth token file
        cg-wan-capacity-graph.py --authtokenfile ~/token-karl-demopod1.txt --site-name "york" -p 24 -d 3

    Show 8-hours worth PCM data for my Chicago Branch from 5 days ago. Authentication will be handled interactively.
        cg-wan-capacity-graph.py --site-name chicago --period 8 --days 5

    Show 4-hours worth PCM data for my Chicago Branch from 5 days ago. Force the graph height to be smaller at 5. 
        cg-wan-capacity-graph.py --site-name chicago --period 8 --days 5

NOTES:
    ASCII charts have limitations on display. Excessively large graphs may format incorrectly on small terminal windows 
    based on your Terminal width and height. To overcome this, select a shorter time period or increase your terminal 
    size. You may also reduce the graph height with the height option.

