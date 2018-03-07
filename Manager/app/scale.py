from flask import render_template, redirect, url_for, request
from app import webapp

import boto3
import time
from threading import *

from app import config
from app import workerpool
from app import monitor

scale_is_on = True
general_error = ''


@webapp.route('/config', methods=['GET'])
# Return Config Scale Policy Page
def scale_page():
    return render_template("scale.html", title="Auto Scale Configuration")


@webapp.route('/config_scale_policy', methods=['POST'])
# Define scale policy
def start_scale_policy():
    print("======Enabling Scale Policy......======")
    global scale_is_on
    # Enable scale_is_on
    scale_is_on = True
    # Retrieve data from page

    print("======Gathering parameters......======")
    if request.form.get('up_threshold').isdigit() is False or \
            request.form.get('down_threshold').isdigit() is False or \
            request.form.get('expand_ratio').isdigit() is False or \
            request.form.get('shrink_ratio').isdigit() is False:
        return render_template("scale.html", title="Auto Scale Configuration",
                               error_msg="Error! All inputs should be integers")

    upper_limit = int(request.form.get('up_threshold'))
    lower_limit = int(request.form.get('down_threshold'))
    expand_ratio = int(request.form.get('expand_ratio'))
    shrink_ratio = int(request.form.get('shrink_ratio'))

    print("======Starting execution......======")
    # Set the parameters and run policy execution after 10s
    # Create a separate thread to deal policy execution
    thread = Thread(target=execute_policy, args=(upper_limit, lower_limit, expand_ratio, shrink_ratio))
    thread.start()

    print("======Scale Policy Started......======")
    return redirect(url_for('worker_list'))


def execute_policy(up_threshold, down_threshold, expand_ratio, shrink_ratio):
    print("======Running policy execution======")
    global scale_is_on
    print("Scale is on: " + str(scale_is_on))
    while scale_is_on:
        cpu_average = monitor.cpu_average_usage()
        # Check for expand
        if cpu_average > up_threshold:
            print("======Expanding worker pool======")
            expend_worker_pool(expand_ratio)

        # Check for shrink
        if cpu_average < down_threshold:
            print("======Shrinking worker pool======")
            shrink_worker_pool(shrink_ratio)

        # Auto scale policy runs once per minute (60 seconds)
        # If you wish to increase/decrease policy checking period
        # Please modify the number inside sleep()
        print("======Sleeping......======")
        time.sleep(60)

    print("======Policy execution inactive======")


@webapp.route('/disable_scale_policy', methods=['POST'])
# Disable scale_is_on so execute_policy will stop checking
def stop_scale_policy():
    print("======Disabling Scale Policy......======")
    # Simply disable scale_is_on so "execute_policy" will escape the loop
    global scale_is_on
    scale_is_on = False
    print("======Scale Policy Turned Off......======")
    return redirect(url_for('worker_list'))


# Expand worker pool by certain ratio
# Note: maximum size of worker pool is fixed at 20 as a protection mechanism
def expend_worker_pool(ratio):
    # Check current worker pool size
    workerpool_size = workerpool.worker_pool_size()
    count = 0

    # Cet number of workers that need to be created
    if workerpool_size * ratio >= 20:
        need_workers = 20 - workerpool_size

    else:
        need_workers = (ratio - 1) * workerpool_size

    while count < need_workers:
        workerpool.create_a_worker()
        count += 1

    print("======Successfully created " + str(need_workers) + "new workers.======")
    print("======There are " + str(need_workers + workerpool_size) + "workers in total======")


# Shrink worker pool by certain ratio
# Note: There is at least one worker, meaning minimum size of worker pool is one
def shrink_worker_pool(ratio):
    # Check current worker pool size
    workerpool_size = workerpool.worker_pool_size()
    count = 0

    # Get number of workers that need to be terminated
    if workerpool_size == 1:
        print("======There is only 1 worker left!======")
        return

    elif int(workerpool_size / ratio) <= 1:
        need_remove_workers = workerpool_size - 1

    else:
        need_remove_workers = int(workerpool_size - workerpool_size / ratio)

    while count < need_remove_workers:
        workerpool.terminate_a_worker()
        count += 1
    print("======Successfully removed " + str(need_remove_workers) + "workers.======")
    print("======There are " + str(workerpool_size - need_remove_workers) + "workers in total======")
