test:
	bashful run run.bashful.yaml

boxes:
	bashful run build-boxes.bashful.yaml

clean:
	-rm -r .bashful/
	-rm -r build/
	-find . -name "test_template*.sh" -type f -delete
	-find . -name "fio-job.cfg" -type f -delete
	-find . -path "*/out/*" -delete