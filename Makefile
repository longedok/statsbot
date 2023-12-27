run:
	docker compose up -d questdb
	sleep 0.5
	poetry run python3 main.py

stop:
	docker compose stop

build:
	docker buildx build --platform linux/amd64 -t longedok/statsbot .

push:
	docker push longedok/statsbot

publish: build push

deploy:
	git pull
	pass show docker-credential-helpers/docker-pass-initialized-check
	docker compose up --pull always -d

startup:
	docker compose up --pull never -d

shutdown:
	docker compose stop

ssh:
	gcloud compute ssh --zone "us-east1-b" "longedok@hobby" --project \
		"telegram-bot-303420"

logs:
	docker compose logs bot -f

glogs:
	gcloud logging read --limit 10 --order asc \
		'logName="projects/telegram-bot-303420/logs/gcplogs-docker-driver"'

updb:
	docker compose up -d questdb

