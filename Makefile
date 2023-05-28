all: boxes test

boxes:
	bash build_boxes.sh

env: env/touchfile

env/touchfile: requirements.txt
	test -d env || python -m venv env
	. env/bin/activate && pip install -r requirements.txt
	touch env/touchfile

test: env
	. env/bin/activate && bash test.sh

clean:
	-rm -r build/
	-rm -r logs/
	-find . -path "*/out/*" -delete