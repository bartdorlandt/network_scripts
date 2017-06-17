#!/usr/bin/env python3

import argparse
import xlsxwriter
import glob


def createexcel(filename):
    countrydict = dict()
    headerwidth = [17, 10, 8, 12, 9, 10]
    headerlist = ('Site;Total SW;Fine;PrefUpgrade;Replace;IOS update')

    # create the workbook
    workbook = xlsxwriter.Workbook(filename)
    header = workbook.add_format()
    header.set_bold()
    header.set_align('vcenter')
    # setting default format
    defformat = workbook.add_format()
    defformat.set_align('vcenter')
    #
    worksheet = workbook.add_worksheet('Totals ISE')
    worksheet.set_default_row(16)
    #
    col = 0
    row = 0
    for x in headerwidth:
        worksheet.set_column('{0}:{0}'.format(chr(col + ord('A'))), x)
        col += 1
    col = 0
    #
    for x in headerlist.split(';'):
        worksheet.write(row, col, x, header)
        col += 1
    #
    row += 1
    col = 0
    # Starting new tabs, for each IP address.
    for sc in sorted(sitesdict):
        col = 0
        # sites[sc] = 'Fine:   3 PrefUpgrade:   0 Replace:   0 IOS update:   0'
        scsplit = sitesdict[sc].split()
        if len(scsplit) != 9:
            worksheet.write(row, col, '{}_nothing'.format(sc), defformat)
        else:
            FI = int(scsplit[1])
            PU = int(scsplit[3])
            RE = int(scsplit[5])
            IU = int(scsplit[8])
            TO = FI + PU + RE
            # ColumnA sitecode
            worksheet.write(row, col, sc, defformat)
            # ColumnB Totals
            worksheet.write_number(row, col + 1, TO, defformat)
            # ColumnC Fine
            worksheet.write_number(row, col + 2, FI, defformat)
            # ColumnD PrefUpgrade
            worksheet.write_number(row, col + 3, PU, defformat)
            # ColumnE Replace
            worksheet.write_number(row, col + 4, RE, defformat)
            # ColumnF IOS update
            worksheet.write_number(row, col + 5, IU, defformat)
            #
            # Fill the country counting
            try:
                a, b, c, d = countrydict[sc[0:2]]
            except KeyError:
                a, b, c, d = 0, 0, 0, 0
            #
            a += FI
            b += PU
            c += RE
            d += IU
            countrydict[sc[0:2]] = (a, b, c, d)
            #
        row += 1
    col = 0
    worksheet.write(row, col, 'Totals:', header)
    col += 1
    worksheet.write_formula(
        row, col, '=SUM({0}1:{0}{1})'.format(
            chr(col + ord('A')), row), header)
    col += 1
    worksheet.write_formula(
        row, col, '=SUM({0}1:{0}{1})'.format(
            chr(col + ord('A')), row), header)
    col += 1
    worksheet.write_formula(
        row, col, '=SUM({0}1:{0}{1})'.format(
            chr(col + ord('A')), row), header)
    col += 1
    worksheet.write_formula(
        row, col, '=SUM({0}1:{0}{1})'.format(
            chr(col + ord('A')), row), header)
    col += 1
    worksheet.write_formula(
        row, col, '=SUM({0}1:{0}{1})'.format(
            chr(col + ord('A')), row), header)

    # Country summary
    row = 0
    secondcol = 7
    col = secondcol
    headerwidth = [12, 10, 8, 12, 9, 10]
    headerlist = ('Country SUM;Total SW;Fine;PrefUpgrade;Replace;IOS update')
    #
    for x in headerwidth:
        worksheet.set_column('{0}:{0}'.format(chr(col + ord('A'))), x)
        col += 1
    col = secondcol
    #
    for x in headerlist.split(';'):
        worksheet.write(row, col, x, header)
        col += 1
    col = secondcol
    row += 1
    #
    for x in sorted(countrydict):
        # ColumnA sitecode
        worksheet.write(row, col, x, defformat)
        # ColumnB Total SW
        worksheet.write_number(
            row, col + 1, countrydict[x][0] + countrydict[x][1] +
            countrydict[x][2], defformat)
        # ColumnC Fine
        worksheet.write_number(row, col + 2, countrydict[x][0], defformat)
        # ColumnD PrefUpgrade
        worksheet.write_number(row, col + 3, countrydict[x][1], defformat)
        # ColumnE Replace
        worksheet.write_number(row, col + 4, countrydict[x][2], defformat)
        # ColumnF IOS update
        worksheet.write_number(row, col + 5, countrydict[x][3], defformat)
        row += 1
    #
    # Closing the workbook, all IP's done.
    workbook.close()


# Provide switches to control this script
parser = argparse.ArgumentParser(
    add_help=True,
    description='''Converts the totals gathered by sw_showhw.py for ISE to
excel.''',
    epilog="Environment variables used: None")
parser.add_argument(
    '--dir', required=True, default=None,
    help="Provide the directory.")
parser.add_argument(
    '--ext', required=False, default='csv.txt',
    help="Provide the extension. The default extension is set to: %(default)s."
)
args = parser.parse_args()

extension = args.ext
if not extension.startswith('.'):
    extension = '.{}'.format(extension)
inputdir = args.dir
searchstring = '*{}'.format(extension)
sitesdict = dict()
filename = '{}/01.ISE_totals.xlsx'.format(inputdir)
files = (glob.glob1(inputdir, searchstring))

for x in files:
    hostname = x.split('.')[0]
    with open('{}/{}'.format(inputdir, x), 'r') as f:
        for line in f:
            if line.startswith('Fine') and line.find('PrefUpgrade') > 0:
                sitesdict[hostname] = line
            else:
                sitesdict[hostname] = 'Nothing found'

createexcel(filename)

print('Done creating the excel file.\nLocation: {}'.format(filename))
