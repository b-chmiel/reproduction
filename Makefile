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
	-find . -name "test_template*.sh" -type f -delete
	-find . -name "fio-job.cfg" -type f -delete
	-find . -path "*/out/*" -delete