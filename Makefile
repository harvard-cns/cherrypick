lint:
	pylint cloudbench

clean:
	find . -iname *pyc | xargs rm
