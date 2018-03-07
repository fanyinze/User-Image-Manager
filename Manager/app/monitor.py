from flask import render_template, redirect, url_for, request
from app import webapp

import boto3
from datetime import datetime, timedelta
from operator import itemgetter


@webapp.route('/monitoring', methods=['GET'])
# Display an HTML list of all workers (ec2 instances)
def worker_list():
    # Check S3
    # print("======Check if S3 exists......======")
    # check_s3()

    # Get list of all registered workers' instance id
    print("======Gathering Instance info from AWS ELB......======")
    workers = get_workers()
    num_worker = len(workers)

    # Get cpu usage of workers
    print("======Getting CPU Usage Data......======")
    cpu_stats_lists = get_cpu_stats()

    # Get Average usage of workers
    print("======Calculating CPU Average......======")
    cpu_average = cpu_average_usage()

    return render_template("list.html", title="Worker Pool Monitoring", instances=workers,
                           num_worker=num_worker, CPU_avg=cpu_average, cpu_stats_lists=cpu_stats_lists)


# ================== Helper Functions ==================
# Get workers:
def get_workers():
    client = boto3.client('elb')

    # Describe all load balancers
    response = client.describe_load_balancers(
        LoadBalancerNames=[
            'ece1779lb',
        ]
    )

    # Get list of all registered workers' instance id
    workers = response['LoadBalancerDescriptions'][0]['Instances']
    return workers


# Get CPU status
def get_cpu_stats():
    # Get list of all registered workers' instance id
    workers = get_workers()

    cpu_stats_lists = []
    for worker in workers:
        # Display details about a specific instance.
        worker_id = worker['InstanceId']
        cloud_client = boto3.client('cloudwatch')
        metric_name = 'CPUUtilization'

        namespace = 'AWS/EC2'
        statistic = 'Average'  # could be Sum,Maximum,Minimum,SampleCount,Average

        cpu = cloud_client.get_metric_statistics(
            Period=1 * 60,
            StartTime=datetime.utcnow() - timedelta(seconds=60 * 60),
            EndTime=datetime.utcnow() - timedelta(seconds=0 * 60),
            MetricName=metric_name,
            Namespace=namespace,  # Unit='Percent',
            Statistics=[statistic],
            Dimensions=[{'Name': 'InstanceId', 'Value': worker_id}]
        )

        cpu_stats = []

        for point in cpu['Datapoints']:
            hour = point['Timestamp'].hour
            minute = point['Timestamp'].minute
            time = hour + minute / 60
            cpu_stats.append([time, point['Average']])

        cpu_stats = sorted(cpu_stats, key=itemgetter(0))
        cpu_stats_lists.append(cpu_stats)

    return cpu_stats_lists


# Get average usage of workers cpu workload.
def cpu_average_usage():
    cpu_stats_lists = get_cpu_stats()
    cpu_usage = []

    for cpu_stat in cpu_stats_lists:
        # Ignore those newly created instance(s) that has no CPU data
        if cpu_stat:
            cpu_usage.append(cpu_stat[len(cpu_stat)-1][1])
    cpu_avg = (sum(cpu_usage))/len(cpu_stats_lists)
    return cpu_avg


# Check if S3 for storing image exists, create one if not.
def check_s3():
    s3 = boto3.resource('s3')
    all_buckets = s3.buckets.all()
    if not s3.Bucket('ece1779cca2') in all_buckets:
        s3 = boto3.client('s3')
        s3.create_bucket(Bucket='ece1779cca2')
        print("======S3 created======")
    else:
        print("======Target S3 already exists======")
