import argparse
import getpass
import sys
import time
import json
import csv

from pyzabbix import ZabbixAPI

def get_zapi(host, user, password, verify):
    zapi = ZabbixAPI(host)
    zapi.session.verify = verify
    zapi.login(user, password)
    return zapi


def get_history(zapi, itemid, time_from, time_till):
    items = zapi.item.get(itemids=itemid, output=['value_type'])
    if len(items) == 1:
        value_type = items[0]['value_type']
    else:
        raise Exception('Item not foudn')
    ret = zapi.history.get(itemids=itemid,
                            time_from=time_from,
                            time_till=time_till,
                            history=value_type,
                            sortfield='clock',
                            output='extend'
                        )
    return ret

def write_csv(objects, output_file, ):
    f = csv.writer(open(output_file, "wb+"))
    f.writerow(objects[9].keys())

    for o in objects:
        row = []
        for key in o.keys():
            row.append(o[key])
        f.writerow(row)

def build_parsers():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description='zabbixhistory2csv')
    parser.add_argument("-V", "--verify",
                        default='true',
                        help="Verify SSL (True, False, or Path to CACert)")
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
    parser = build_parsers()
    args = parser.parse_args(sys.argv[1:])
    seconds_ago = int(args.minutes_ago) * 60
    now = int(time.time())
    password = getpass.getpass()
    zapi = get_zapi(args.host, args.user, password, eval(args.verify))
    results = get_history(zapi, args.itemid, (now - seconds_ago), now)
    print('Writing {0} minutes worth of history to {1}'.format(args.minutes_ago, args.output_file))
    write_csv(results, args.output_file)
