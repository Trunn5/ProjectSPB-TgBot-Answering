docker-build:
	docker build . -t tgbot-answering

docker-run:
	docker run --name sherlok tgbot-answering

docker-start:
	docker start sherlok

docker-bash:
	docker exec -it sherlok bash
	