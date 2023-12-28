#!/bin/sh
while [[ $(curl -G -s -o /dev/null -w '%{http_code}' \
    --data-urlencode 'query=select 1;' questdb:9000/exec) != "200" ]]
do
    echo "Waiting for QuestDB..."
    sleep 1
done

echo "QuestDB is up!"

exec /venv/bin/python statsbot/main.py

