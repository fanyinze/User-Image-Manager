## User Image Manager - An Elastic Photo Storage Web Application
### Introduction:
User Image Manager is an AWS based elastic web application. It has two interfaces: Worker and Manager. 

Worker has one or more EC2 instances that dealing with users requests, including user accounts' registration, image uploading, and store actual image files on AWS S3. 

Manager is a stand-alone EC2 instance that monitors each worker instance's CPU utilization, increase/decrease total number of workers, evenly distributed all traffics across workers using Elastic Load Balancing, stores accounts info, and can reset both local database and S3.

### Project Specification: 
- Operating System: Windows, MacOS and Linux
- Design Languages: Python 3.5, HTML5
- Libraries and Frameworks: Flask, MySQL-Connector, Boto3, ImageMagick, Gunicorn, Bootstrap
- AWS Services: EC2, S3, Load Balancing

(*Note: All AWS credential related info (IAM Role, Group ID, Security ID, etc.) has been removed.)
