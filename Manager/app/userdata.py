UserData = """#cloud-config
runcmd:
 - git clone https://#Username#:#Password#@bitbucket.org/#Username#/ece1779_project2_users.git /home/ubuntu/Desktop/ece1779a2
 - cd /home/ubuntu/Desktop
 - sudo chmod -R 777 ece1779a2
 - cd ece1779a2
 - source venv/bin/activate
 - ./run.sh
 - sudo ./run.sh
"""
