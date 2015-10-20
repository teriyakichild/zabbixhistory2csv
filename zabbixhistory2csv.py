import argparse
import getpass
import sys
import time
import json
import csv

from pyzabbix import ZabbixAPI

def get_zapi(host, user, password, verify):
    zapi = ZabbixAPI(host)
    # Whether or not to verify the SSL certificate
    zapi.session.verify = verify
    zapi.login(user, password)
    return zapi


def get_history(zapi, itemid, time_from, time_till):
    # The zabbix api call for history.get requires that we know the item's data type.
    # We can get this through a call to the zabbix api since we have the itemid.
    items = zapi.item.get(itemids=itemid, output=['value_type'])
    ret = []

    # The only successful outcome would be a list with one item. If we get more or less,
    # we should assume that the item doesn't exist.
    if len(items) == 1:
        value_type = items[0]['value_type']
    else:
        raise Exception('Item not found')

    # max minutes we'll look behind (to account for zabbix hitting its memory limit)
    max_mins = 120
    max_secs = max_mins * 60

    # time_till = now
    # time_from = start time
    # Make call to zabbix API for history
    while time_till > time_from:
        if time_till - time_from > max_secs:
            ret += zapi.history.get(itemids=itemid,
                                    time_from=time_from,
                                    time_till=time_from + max_secs,
                                    history=value_type,
                                    sortfield='clock',
                                    output='extend'
                                )
            time_from = time_from + max_secs 
        else:
            ret += zapi.history.get(itemids=itemid,
                                    time_from=time_from,
                                    time_till=time_till,
                                    history=value_type,
                                    sortfield='clock',
                                    output='extend'
                                )
            break
    return ret

def write_csv(objects, output_file, ):
    # Open the output_file and instanstiate the csv.writer object
    f = csv.writer(open(output_file, "wb+"))
    
    # Write the top line of the output_file which descibes the columns
    f.writerow(objects[0].keys())

    # For each object, write a row to the csv file.
    for o in objects:
        row = []
        for key in o.keys():
            row.append(o[key])
        f.writerow(row)

def build_parsers():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description='zabbixhistory2csv')
    parser.add_argument("-V", "--verify",
                        default='True',
                        choices=['True', 'False'],
                        help="Verify SSL (True, False)")
    parser.add_argument("-H", "--host",
                        dest='host',
                        required=True,
                        help="Zabbix API host"
                        "example: https://zabbixhost.example.com/zabbix")
    parser.add_argument("-u", "--user",
                        default=getpass.getuser(),
                        help="Zabbix API user")
    parser.add_argument("-m", "--minutes-ago",
                        default='60',
                        help='How many minutes worth of history should'
                              'be returned going back in time from right now')
    parser.add_argument("-o", "--output-file",
                        default='output.csv',
                        help="Output file in csv format\nDefault: output.csv")
    parser.add_argument("-i", "--itemid",
                        required=True,
                        help="The zabbix item that we will use in our history.get api call.")

    return parser

if __name__ == '__main__':
    # Load argparse and parse arguments
    parser = build_parsers()
    args = parser.parse_args(sys.argv[1:])

    # Generate parameters for get_zapi function
    seconds_ago = int(args.minutes_ago) * 60
    now = int(time.time())
    password = getpass.getpass()

    # Generate the zapi object so we can pass it to the get_history function
    zapi = get_zapi(args.host, args.user, password, eval(args.verify))

    # generate the list of history objects returned from zabbix api.
    results = get_history(zapi, args.itemid, (now - seconds_ago), now)

    # Write the results to file in csv format
    write_csv(results, args.output_file)
    print('Writing {0} minutes worth of history to {1}'.format(args.minutes_ago, args.output_file))
