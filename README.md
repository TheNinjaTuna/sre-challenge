# Warpnet SRE Challenge submission
This git repo contains my submission for the Warpnet SRE challenge. The goal of this challenge was to fix and deploy a provided flask app while keeping the following principles in mind:

- Functionality
- Simplicity
- Readability
- Extensibility
- Maintainability
- Observability
- Security

Deployment needed to be arranged via two methods: deployment to a VM and to a Kubernetes cluster. The methods I have chosen will be further outlined down below.

## Changes to the app
The following changes were made to the app:

- Implemented password hashing in both the database and app.
    - Argon2 hashes were chosen, with implementation using a public library: https://pypi.org/project/argon2-cffi.
- Made it so that not all users are fetched from the database and looped through when authenticating.
    - Instead only one user with a matching username is fetched.
- Added indexing to the username column in the users table of the DB. This is considered a best practice and speeds up DB queries when looking through a large number of records.
- Implemented prepared statements when querying the database in order to sanitize user input.
- Removed passwords from app logging.
- Removed the hardcoded flask secret in favor of an enviroment variable, this enables the usage of secret management.
- Ensured DB persistence for all deployment methods. The pre-packed database is now copied to a predefined location (also defined by an enviroment variable). This is not done in case the DB is already present.

### Container image
A container image has been constructed using the dockerfile included in this project. It can be found on https://hub.docker.com/repository/docker/theninjatuna/warpnet-sre-challenge, and pulled from docker.io under theninjatuna/warpnet-sre-challenge:latest

The dockerfile is structured as follows:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# install dependencies
COPY /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy app
COPY app/ .

# create directory for SQLite DB
RUN mkdir -p /data

ENV SQLITE_DB_PATH=/data/database.db

EXPOSE 5000

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "warning", "application:app"]
```

## Deployment to VM
For VM deployment I chose to go with an Ansible playbook. This playbook can be found in the /deploymentstrategies/ansible folder.

Be mindful: this playbook targets all hosts in your ansible inventory, but this can easily be changed. 

In order for this playbook to work, the provided j2 template - called "flaskapp.service.j2" - needs to be present in the folder the playbook is run from.

It's best to run this playbook with:
``ansible-playbook -K deploy_app.yaml``

Once run it will prompt you for the target machine's root pass, and also ask you for your flask secret (twice to ensure errors are unlikely).

The playbook will then:
- Install the required APT dependencies
- Create a user with the name flaskapp
- Clone the app via a Git clone into a new directory in /opt/flaskapp
- Create a directory for the persistent database in /var/lib/flaskapp
- Install the required python dependencies in a new virtual enviroment
- Create a systemd service based on the j2 template, called flaskapp
    - This systemd service executes the flaskapp via gunicorn with two parralel workers
- Ensure the systemd service is started


### Alternate installation method
Alternatively, the app can also easily be installed on a machine with the docker engine and docker compose installed.

In the folder /deploymentstrategies/compose you can find a docker compose file which can deploy the application. A .env file with APP_SECRET also needs to
be present in the same folder. I'd recommend using the included template, renaming it to .env and replacing the secret inside with whatever you desire.

To do deploy the app, run this command in the folder with compose.yaml:
``docker compose up -d``

### Some small notes
Running the app with multiple gunicorn workers (and thus app instances) can potentially be dangerous because we're using a SQLite database. As far as I'm aware this is mainly an issue when writes to the database happen, which this app doesn't do. Yet this should still be taken into account.

I'd also recommend the usage of a more conventient secret manager (like ansible-vault) for the ansible deployment strategy, though prompting the user seemed like an easy enough alround solution.

### About my enviroment
The virtual machine I used when testing my playbook is a Ubuntu LTS 22.04 machine hosted on my own Proxmox server.

## Deployment to a cluster
For deploying the app to a cluster I chose to prepare a kustomize yaml, with all of the necessary kubernetes resources included.

To deploy the app on your cluster, download all the contents of the /deploymentstrategies/k8s folder into a folder of your choosing on a machine with kubectl installed and configured.

Before running the deployment command, it should be noted that the ingress resource present in this project is meant for the NGINX ingress controller, which I have running in my enviroment. Though it can easily be edited or subsituted for your own prefered method of ingress control. It points to "flaskapp.snowy", with snowy being my internal homelab TLD.

Once you have ommited, subsituted or edited the file, run the command:
``kubectl apply -k {folder with contents of /deploymentstrategies/k8s}``

A new namespace called "warpnet-sre-challenge" will be created, along with a deployment, service, persistent volume, persistent volume claim, secret, and ingress.

After all the resources have been created, your service should be reachable via the host you specified in your ingress file. Make sure a DNS entry exists pointing to the host running your cluster ingress.

### About my enviroment
My test deployment was made on my homelab Kubernetes cluster, which consists of three virtualized nodes (ran on a Proxmox server). I use an external DNS server (dnsmasq) and reverse proxy (Caddy) which I use to route the traffic to my cluster. 

I deployed it using ArgoCD, while pointing it at this GitHub repository. It will find the k8s folder and corresponding kustomize file.
