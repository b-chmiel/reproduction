test:
	bash test.sh

boxes:
	bash build_boxes.sh

clean:
	-rm -r build/
	-rm -r logs/
	-find . -name "test_template*.sh" -type f -delete
	-find . -name "fio-job.cfg" -type f -delete
	-find . -path "*/out/*" -delete