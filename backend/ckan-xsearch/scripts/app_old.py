#!python3
# -*- coding: utf-8 -*-

import csv
import logging
import os.path

from harvester import CkanHarvester


def download_csvfiles(h):
    logging.info("Downloading CSV resources.")
    csvlist = h.get_csv_resources()

    logging.info(
        "Writing resource list into 'csvlist.txt' and 'csvlist_error.txt'.")
    with open('csvlist.txt', 'w', newline='', encoding='utf-8') as f_success, \
            open('csvlist_error.txt', 'w', newline='', encoding='utf-8') as f_error:
        writer_success = csv.writer(f_success)
        writer_error = csv.writer(f_error)
        header = ['SiteName', 'PackageID', 'Title', 'URL', 'Filepath']
        writer_success.writerow(header)
        writer_error.writerow(header)
        for row in csvlist:
            if row[4] is not False:
                row[4] = os.path.relpath(row[4])
                writer_success.writerow(row)
            else:
                row[4] = ''
                writer_error.writerow(row)


if __name__ == '__main__':
    logging.basicConfig(filename='log', level=logging.DEBUG)
    h = CkanHarvester()   # Read ckan list from 'ckanlist.json'
    h.get_dataset_list()  # Prepare ckan-site's api endpoints

    # print(h.get_ckan_list())
    # h.save_ckan_list()
    logging.info("Downloading catalogs from CKAN sites.")
    h.get_package_catalog()  # Check and save to files

    # download_csvfiles(h)

    logging.info("Done.")
