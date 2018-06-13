"""
+------------------------------------------------------------------------------+
|                       Copyright 2017 Rockwell Collins                        |
|                             All Rights Reserved                              |
|                           Proprietary Information                            |
+------------------------------------------------------------------------------+

Utility functions for interfacing with report files
"""
import csv


__version__ = '$Rev: 254921 $'


def write_csv(csv_path, headers, data, sort_col=None, reverse=False):
    """
    Writes tabular data to a CSV file.

    :param csv_path: path to the CSV report file
    :type  csv_path: basestring
    :param headers: headers to include in the top row
    :type  headers: list[basestring] or dict{basestring:int}
    :param data: data rows to include in the report
    :type  data: list[list[basestring]]
    :param sort_col: column index to sort by
    :type  sort_col: int
    :param reverse: whether to reverse the sort
    :type  reverse: bool
    """
    if isinstance(headers, dict):
        col = headers
        headers = [''] * (max(col.values()) + 1)
        for header, idx in col.iteritems():
            headers[idx] = header

    with open(csv_path, 'wb') as f:
        writer = csv.writer(f, quotechar='"')
        if sort_col is not None:
            data = sorted(data, key=lambda r: r[sort_col], reverse=reverse)

        if headers is not None:
            data = [headers] + data

        writer.writerows(data)


def read_csv(csv_path, no_headers=False, header_row=0):
    """
    Reads tabular data from a CSV file.

    :param csv_path: path to the CSV report file
    :type  csv_path: basestring
    :param no_headers: interpret all rows as data only
    :type  no_headers: bool
    :param header_row: index of the row which contains column headers
    :type  header_row: int
    :return: map of column names to indices and data rows from the report
    :rtype: list[list[basestring]] or
            tuple(dict{basestring:int},list[list[basestring]])
    """
    with open(csv_path, 'rb') as f:
        data = [[y for y in x] for x in csv.reader(f)]

    if no_headers:
        return data

    return {
        header: col
        for col, header in enumerate(data[header_row])
    }, data[header_row+1:]
