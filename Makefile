lint:
	pylint cloudbench

clean:
	@find . -iname *pyc -delete

azure_key:
	@cd config && openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout cloud.key -out cloud.pem
	@chmod 600 ./config/cloud.key

gcloud_key:
	@echo "Creating Google cloud keys"
	@cd config && printf "cloudbench:" > gcloud_ssh_key
	@cd config && ssh-keygen -y -f cloud.key >> gcloud_ssh_key
	@cat ./config/gcloud_ssh_key

aws_key:
	@echo "Creating AWS cloud keys"
	@cd config && openssl rsa -pubout -in cloud.key -out cloud.pub

test:
	@python -m unittest discover -s tests

prereqs:
	pip install -r requirements.txt

keys: gcloud_key aws_key
