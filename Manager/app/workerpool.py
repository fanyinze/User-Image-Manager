from flask import render_template, redirect, url_for, request, g
from app import webapp

import os
import mysql.connector
import boto3
from app import config
from app.config import db_config
from app import userdata


@webapp.route('/manage/create_worker', methods=['POST'])
# Start a new EC2 instance
def manual_create():
    # Check current worker pool size
    workerpool_size = worker_pool_size()
    if workerpool_size >= 20:
        print("======Maximum reached! Workers cannot be more than 20!======")
        return redirect(url_for('worker_list'))
    create_a_worker()
    return redirect(url_for('worker_list'))


@webapp.route('/manage/delete_worker', methods=['POST'])
# Terminate a EC2 instance
# Note: cannot manually destroy worker if there is only one worker left
def manual_destroy():
    # Check current worker pool size
    workerpool_size = worker_pool_size()

    # Get number of workers that need to be terminated
    if workerpool_size == 1:
        print("======There is only 1 worker left!======")
        return redirect(url_for('worker_list'))
    terminate_a_worker()
    return redirect(url_for('worker_list'))


@webapp.route('/manage/clear_database', methods=['POST'])
# Delete all data on managerUI database and S3
def delete_all_data():
    os.system("sudo service mysql stop")
    os.system("sudo service mysql start")
    # Clear all tables in ec2 database
    print("======Cleaning Database...======")
    cnx = get_db()
    cursor = cnx.cursor()

    query = "SET FOREIGN_KEY_CHECKS = 0;"
    cursor.execute(query, )

    query = "TRUNCATE user;"
    cursor.execute(query, )

    query = "TRUNCATE photo;"
    cursor.execute(query, )

    query = "TRUNCATE type;"
    cursor.execute(query, )

    query = "TRUNCATE transformation;"
    cursor.execute(query, )

    query = "SET FOREIGN_KEY_CHECKS = 1;"
    cursor.execute(query, )

    query = "INSERT INTO type (id, label) VALUES (1, 'original');"
    cursor.execute(query, )

    query = "INSERT INTO type (id, label) VALUES (2, 'thumbnail');"
    cursor.execute(query, )

    query = "INSERT INTO type (id, label) VALUES (3, 'trans1');"
    cursor.execute(query, )

    query = "INSERT INTO type (id, label) VALUES (4, 'trans2');"
    cursor.execute(query, )

    query = "INSERT INTO type (id, label) VALUES (5, 'trans3');"
    cursor.execute(query, )

    cnx.commit()
    print("======Done!======")

    # Delete all files (images) on S3
    print("======Cleaning S3...======")
    s3 = boto3.resource('s3')
    bucket = s3.Bucket('ece1779cca2')
    for key in bucket.objects.all():
        key.delete()
    print("======Done!======")
    return redirect(url_for('worker_list'))


# ================== Helper Functions ==================
def create_a_worker():
    print("======Creating new worker instance======")
    ec2 = boto3.resource('ec2')
    new_instance = ec2.create_instances(
        ImageId=config.ami_id,
        InstanceType='t2.small',
        KeyName='keys here',
        MaxCount=1,
        MinCount=1,
        Monitoring={
            'Enabled': True
        },
        SecurityGroupIds=[
            'sg-xxxxxxxx',
        ],
        SubnetId='subnet-xxxxxxxx',
        UserData=userdata.UserData,
        IamInstanceProfile={
            'Arn': '#add IAM Role id with AmazonS3FullAccess here#'
        }
    )
    register_new_worker(new_instance[0].id)
    print("======Successfully created and registered a new worker======")


def terminate_a_worker():
    print("======Terminating worker instance======")
    ec2 = boto3.resource('ec2')
    worker_id = deregister_one_worker()
    ec2.instances.filter(InstanceIds=[worker_id, ]).terminate()
    print("======Successfully deregistered and terminated a worker======")


def worker_pool_size():
    client = boto3.client('elb')
    # Describe all load balancers
    response = client.describe_load_balancers(
        LoadBalancerNames=[
            'name of elb',
        ]
    )
    # Get list of all registered workers' instance id
    workers = response['LoadBalancerDescriptions'][0]['Instances']
    num_worker = len(workers)
    return num_worker


# Register new worker (ec2 instance) into ELB
def register_new_worker(instance_id):
    print("======Registering new worker======")
    client = boto3.client('elb')
    client.register_instances_with_load_balancer(
        LoadBalancerName='ece1779lb',
        Instances=[
            {
                'InstanceId': instance_id
            },
        ]
    )
    print("======Registration finished======")


# De-register worker from ELB
def deregister_one_worker():
    print("======Deregistering...======")
    client = boto3.client('elb')
    response = client.describe_load_balancers(
        LoadBalancerNames=[
            'ece1779lb',
        ],
    )

    workers = response['LoadBalancerDescriptions'][0]['Instances']
    print("Worker ID =" + workers[0]['InstanceId'])
    client.deregister_instances_from_load_balancer(
        LoadBalancerName='ece1779lb',
        Instances=[
            {
                'InstanceId': workers[0]['InstanceId']
            },
        ]
    )
    print("======Deregistration finished======")
    return workers[0]['InstanceId']


# ================== Database Function ==================
def connect_to_database():
    return mysql.connector.connect(user=db_config['user'],
                                   password=db_config['password'],
                                   host=db_config['host'],
                                   database=db_config['database'])


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = connect_to_database()
    return db


@webapp.teardown_appcontext
def teardown_db(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()




