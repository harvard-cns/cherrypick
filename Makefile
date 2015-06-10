lint:
	pylint cloudbench

clean:
	find . -iname *pyc | xargs rm

azure_key:
	cd config && openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout cloud.key -out cloud.pem
	chmod 600 ./config/cloud.key
