build:
	docker buildx build --platform linux/amd64 -t longedok/statsbot .

push:
	docker push longedok/statsbot

update: build push

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

