#!/usr/bin/env python
PROGRAM_NAME = "cg-wan-capacity-graph.py"
PROGRAM_DESCRIPTION = """
CloudGenix WAN Capacity Graph
---------------------------------------
This program displays an ASCII graph of the PCM or WAN Capacity metrics for a given time period going back
an arbitrary amount of days.

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


"""
from cloudgenix import API, jd
import os
import sys
import argparse
from math import cos
from math import pi
from fuzzywuzzy import fuzz
from asciichartpy import plot
import asciichartpy
from datetime import datetime, timedelta


global_vars = {}

CLIARGS = {}
cgx_session = API()              #Instantiate a new CG API Session for AUTH

def parse_arguments():
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=PROGRAM_DESCRIPTION
            )
    parser.add_argument('--token', '-t', metavar='"MYTOKEN"', type=str, 
                    help='specify an authtoken to use for CloudGenix authentication')
    parser.add_argument('--authtokenfile', '-f', metavar='"MYTOKENFILE.TXT"', type=str, 
                    help='a file containing the authtoken')
    parser.add_argument('--site-name', '-s', metavar='SiteName', type=str, 
                    help='The site to run the site health check for', required=True)
    parser.add_argument('--period', '-p', metavar='period', type=int, 
                    help='The period of time (in hours) for the resulting graph. Default 24', default=24)
    parser.add_argument('--days', '-d', metavar='days', type=int, 
                    help='The period of time (in hours) for the resulting graph. Default 2', default=2)
    parser.add_argument('--graphheight', '-g', metavar='graph_height', type=int, 
                    help='The height of the graph to be displayed', default=15)
                    
    args = parser.parse_args()
    CLIARGS.update(vars(args)) ##ASSIGN ARGUMENTS to our DICT

def authenticate():
    print("AUTHENTICATING...")
    user_email = None
    user_password = None
    
    ##First attempt to use an AuthTOKEN if defined
    if CLIARGS['token']:                    #Check if AuthToken is in the CLI ARG
        CLOUDGENIX_AUTH_TOKEN = CLIARGS['token']
        print("    ","Authenticating using Auth-Token in from CLI ARGS")
    elif CLIARGS['authtokenfile']:          #Next: Check if an AuthToken file is used
        tokenfile = open(CLIARGS['authtokenfile'])
        CLOUDGENIX_AUTH_TOKEN = tokenfile.read().strip()
        print("    ","Authenticating using Auth-token from file",CLIARGS['authtokenfile'])
    elif "X_AUTH_TOKEN" in os.environ:              #Next: Check if an AuthToken is defined in the OS as X_AUTH_TOKEN
        CLOUDGENIX_AUTH_TOKEN = os.environ.get('X_AUTH_TOKEN')
        print("    ","Authenticating using environment variable X_AUTH_TOKEN")
    elif "AUTH_TOKEN" in os.environ:                #Next: Check if an AuthToken is defined in the OS as AUTH_TOKEN
        CLOUDGENIX_AUTH_TOKEN = os.environ.get('AUTH_TOKEN')
        print("    ","Authenticating using environment variable AUTH_TOKEN")
    else:                                           #Next: If we are not using an AUTH TOKEN, set it to NULL        
        CLOUDGENIX_AUTH_TOKEN = None
        print("    ","Authenticating using interactive login")
    ##ATTEMPT AUTHENTICATION
    if CLOUDGENIX_AUTH_TOKEN:
        cgx_session.interactive.use_token(CLOUDGENIX_AUTH_TOKEN)
        if cgx_session.tenant_id is None:
            print("    ","ERROR: AUTH_TOKEN login failure, please check token.")
            sys.exit()
    else:
        while cgx_session.tenant_id is None:
            cgx_session.interactive.login(user_email, user_password)
            # clear after one failed login, force relogin.
            if not cgx_session.tenant_id:
                user_email = None
                user_password = None            
    print("    ","SUCCESS: Authentication Complete")


def match_site():
    print_array = []
    global CLIARGS, global_vars
    
    search_site = CLIARGS['site_name']
    search_ratio = 0
    
    resp = cgx_session.get.sites()
    if resp.cgx_status:
        tenant_name = resp.cgx_content.get("name", None)
        print("TENANT NAME:",tenant_name)
        site_list = resp.cgx_content.get("items", None)    #EVENT_LIST contains an list of all returned events
        for site in site_list:                            #Loop through each EVENT in the EVENT_LIST
            check_ratio = fuzz.ratio(search_site.lower(),site['name'].lower())
            if (check_ratio > search_ratio ):
                site_id = site['id']
                site_name = site['name']
                
                search_ratio = check_ratio
                site_dict = site
    else:
        logout()
        print("ERROR: API Call failure when enumerating SITES in tenant! Exiting!")
        sys.exit((jd(resp)))
    print("I think you meant this SITE:")
    print("     Site Name: " , site_dict['name'])
    print("       Site ID: " , site_dict['id'])
    print("   Description: "  , site_dict["description"])
 
    global_vars['site_id'] = site_id
    global_vars['site_name'] = site_name
    global_vars['site_dict'] = site_dict
    
    return True
    

def go():
    global CLIARGS, global_vars
    site_id = global_vars['site_id']
    
    ####CODE GOES BELOW HERE#########
    days_ago = CLIARGS['days'] ###How many days ago to look
    statistics_period = CLIARGS['period']
    hours_ago = days_ago * 24  
    today = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    #start_time = str((datetime.today() - timedelta(hours=hours_ago)).isoformat())
    #end_time = str((datetime.today() - timedelta(hours=(hours_ago-statistics_period))).isoformat())
    start_time = str((today - timedelta(hours=hours_ago)).isoformat())
    end_time = str((today - timedelta(hours=(hours_ago-statistics_period))).isoformat())

    topology_filter = '{"type":"basenet","nodes":["' +  site_id + '"]}'
    resp = cgx_session.post.topology(topology_filter)
    phy_link_array = []
    link_count = 0
    print("LINKS at SITE",global_vars['site_name'])
    if resp.cgx_status:
        topology_list = resp.cgx_content.get("links", None)
        for links in topology_list:
            if ((links['type'] == 'internet-stub') ):
                link_count += 1
                print(str(link_count) + ") " + str(links['network']))
                phy_link_array.append(links)
                ###path_id in LINKS is path in JSON
    
    if len(phy_link_array) == 1:
        global_vars['link'] = phy_link_array[0]
        print("Only one Physical Link found at site. Implicitly selecting LINK 1 above...")
        
    elif len(phy_link_array) > 1:
        user_input = 0
        while not (0 < user_input <= len(phy_link_array)):
            user_input = int(input("Please Select the Physical link above (1 - " + str(len(phy_link_array)) + "):"))
        global_vars['link'] = phy_link_array[user_input]
    else:
        print("Error! No Physical Interfaces at site found!")
        return False
    print("")
    global_vars['path_id'] = global_vars['link']['path_id'] 
    path_id = global_vars['path_id']

    json_request = '{"start_time":"' + start_time + 'Z","end_time":"' + end_time + 'Z","interval":"5min","view":{"summary":false,"individual":"direction"},"filter":{"site":["' + site_id + '"],"path":["' + path_id + '"]},"metrics":[{"name":"PathCapacity","statistics":["average"],"unit":"Mbps"}]}'
    print("Displaying Graphs for Time Period from",start_time, " ---- ", end_time)
    bw_capacity_result = cgx_session.post.metrics_monitor(json_request)
    cgx_bw_results = bw_capacity_result.cgx_content.get("metrics")
    
    bw_metrics = {}
    bw_metrics['egress'] = []
    bw_metrics['ingress'] = []
    direction = ""
    for directions in cgx_bw_results[0]['series']:
        if directions['view']['direction'] == "Ingress":
            direction = 'ingress'
        if directions['view']['direction'] == "Egress":
            direction = 'egress'
        for datapoint in directions['data'][0]['datapoints']:
            if datapoint['value'] is not None:
                bw_metrics[direction].append(datapoint['value'])
            
    ascii_chart_config = {}
    ascii_chart_config['height'] = CLIARGS['graphheight'] #Default 15
    ascii_chart_config['min'] = 10
    hrow = [0] * len(bw_metrics['egress'])
    print("")
    print("EGRESS BANDWIDTH STATISTICS from", days_ago, "days ago for",statistics_period,"hour period at site", global_vars['site_name'], "for interface",global_vars['link']['network'])
    print(plot([bw_metrics['egress']] ,ascii_chart_config))
    print(plot(hrow))
    print("")
    hrow = [0] * len(bw_metrics['ingress'])
    print("INGRESS BANDWIDTH STATISTICS from", days_ago, "days ago for",statistics_period,"hour period at site", global_vars['site_name'], "for interface",global_vars['link']['network'])
    print(plot([bw_metrics['ingress']] ,ascii_chart_config))
    print(plot(hrow))
    
  
def logout():
    print("Logging out")
    cgx_session.get.logout()

if __name__ == "__main__":
    parse_arguments()
    authenticate()
    if (match_site()):
        go()
    logout()

