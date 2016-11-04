#!/usr/bin/env python
# Script to parse a logging file, extract the stats, and graph them
#
# Copyright (C) 2016  Kevin O'Connor <kevin@koconnor.net>
#
# This file may be distributed under the terms of the GNU GPLv3 license.
import optparse, datetime
import matplotlib.pyplot as plt, matplotlib.dates as mdates

MAXBANDWIDTH=25000.
MAXBUFFER=5.

def parse_log(logname):
    f = open(logname, 'rb')
    out = []
    for line in f:
        parts = line.split()
        if not parts or parts[0] != 'INFO:root:Stats':
            #if parts and parts[0] == 'INFO:root:shutdown:':
            #    break
            continue
        keyparts = dict(p.split('=', 1) for p in parts[2:])
        keyparts['#sampletime'] = float(parts[1][:-1])
        out.append(keyparts)
    f.close()
    return out

def plot_mcu(data, maxbw, outname):
    # Generate data for plot
    basetime = lasttime = data[0]['#sampletime']
    lastbw = float(data[0]['bytes_write']) + float(data[0]['bytes_retransmit'])
    times = []
    bwdeltas = []
    loads = []
    hostbuffers = []
    for d in data:
        st = d['#sampletime']
        timedelta = st - lasttime
        if timedelta <= 0.:
            continue
        bw = float(d['bytes_write']) + float(d['bytes_retransmit'])
        load = float(d['mcu_task_avg']) + 3*float(d['mcu_task_stddev'])
        if st - basetime < 15.:
            load = 0.
        pt = float(d['print_time'])
        hb = float(d['buffer_time'])
        if pt <= 2*MAXBUFFER or hb >= MAXBUFFER:
            hb = 0.
        else:
            hb = 100. * (MAXBUFFER - hb) / MAXBUFFER
        hostbuffers.append(hb)
        times.append(datetime.datetime.utcfromtimestamp(st))
        bwdeltas.append(100. * (bw - lastbw) / (maxbw * timedelta))
        loads.append(100. * load / .001)
        lasttime = st
        lastbw = bw

    # Build plot
    fig, ax1 = plt.subplots()
    ax1.set_title("MCU bandwidth and load utilization")
    ax1.set_xlabel('Time (UTC)')
    ax1.set_ylabel('Usage (%)')
    ax1.plot_date(times, loads, 'r', label='MCU load')
    ax1.plot_date(times, bwdeltas, 'g', label='Bandwidth')
    #ax1.plot_date(times, hostbuffers, 'c', label='Host buffer')
    ax1.legend()
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    #plt.gcf().autofmt_xdate()
    ax1.grid(True)
    plt.savefig(outname)

def main():
    usage = "%prog [options] <logfile> <outname>"
    opts = optparse.OptionParser(usage)
    options, args = opts.parse_args()
    if len(args) != 2:
        opts.error("Incorrect number of arguments")
    logname, outname = args
    data = parse_log(logname)
    if not data:
        return
    plot_mcu(data, MAXBANDWIDTH, outname)

if __name__ == '__main__':
    main()